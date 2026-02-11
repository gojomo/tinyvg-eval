#!/usr/bin/env python3
"""
patch_svg_compression.py - Add SVG compression data to existing diagnostics.

Reads the existing all_files_diagnostics.csv, re-runs SVGO on source SVGs to save
optimized copies, trains SVG dictionary, compresses SVGs, and rewrites the CSV
with svg_zstd_size and svg_zstd_dict_size columns. Also retrains TVG dictionary
at the correct 112640 byte size and recompresses TVGs with it.
"""

import csv
import os
import shutil
import subprocess
import tempfile
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

WORK = Path("/tmp/tinyvg-eval-work")
SVG_BASE = WORK / "svg-sources"
RESULTS_DIR = Path(__file__).resolve().parent / "results"
SVGO_CONFIG = str(Path(__file__).resolve().parent / "svgo.config.js")
DICT_SIZE = 112640
PARALLEL_WORKERS = 8

SVG_DIRS = {
    "zig":             SVG_BASE / "zig-logo",
    "w3c":             SVG_BASE / "w3c",
    "material-design": SVG_BASE / "material-design",
    "papirus":         SVG_BASE / "papirus",
    "tabler":          SVG_BASE / "tabler",
    "lucide":          SVG_BASE / "lucide",
    "bootstrap":       SVG_BASE / "bootstrap",
    "simple-icons":    SVG_BASE / "simple-icons",
    "phosphor":        SVG_BASE / "phosphor",
    "fontawesome":     SVG_BASE / "fontawesome",
    "remixicon":       SVG_BASE / "remixicon",
}


def file_size(path):
    return os.path.getsize(path) if os.path.isfile(path) else 0


def svgo_one(args):
    """Optimize one SVG and save it. Returns (group, basename, svgo_path) or (group, basename, None)."""
    svg_path, basename, group = args
    if not svg_path or not os.path.isfile(svg_path):
        return group, basename, None

    dst = WORK / "svgo-files" / group / basename
    dst.parent.mkdir(parents=True, exist_ok=True)

    tmpdir = tempfile.mkdtemp(prefix="svgo-")
    try:
        opt = os.path.join(tmpdir, "opt.svg")
        shutil.copy2(svg_path, opt)
        r = subprocess.run(["svgo", "--quiet", "--config", SVGO_CONFIG, opt],
                           capture_output=True, text=True, timeout=60)
        if r.returncode != 0 or file_size(opt) == 0:
            return group, basename, None
        shutil.copy2(opt, str(dst))
        return group, basename, str(dst)
    except Exception:
        return group, basename, None
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def compress_one(path, dict_path=None):
    tmpdir = tempfile.mkdtemp(prefix="comp-")
    try:
        zstd_out = os.path.join(tmpdir, "out.zst")
        r = subprocess.run(["zstd", "-22", "--ultra", "-f", "-o", zstd_out, path],
                           capture_output=True, timeout=60)
        zstd_sz = file_size(zstd_out) if r.returncode == 0 else 0

        zdict_sz = 0
        if dict_path and os.path.isfile(str(dict_path)):
            zdict_out = os.path.join(tmpdir, "out.zdict")
            r = subprocess.run(["zstd", "-22", "--ultra", "-D", str(dict_path),
                                "-f", "-o", zdict_out, path],
                               capture_output=True, timeout=60)
            zdict_sz = file_size(zdict_out) if r.returncode == 0 else 0

        return zstd_sz, zdict_sz
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def compress_tvg(path, dict_path=None):
    tmpdir = tempfile.mkdtemp(prefix="comp-")
    try:
        zdict_out = os.path.join(tmpdir, "out.zdict")
        zdict_sz = 0
        if dict_path and os.path.isfile(str(dict_path)):
            r = subprocess.run(["zstd", "-22", "--ultra", "-D", str(dict_path),
                                "-f", "-o", zdict_out, path],
                               capture_output=True, timeout=60)
            zdict_sz = file_size(zdict_out) if r.returncode == 0 else 0
        return zdict_sz
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def train_dict(file_list, dict_path, maxdict=DICT_SIZE):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        for p in file_list:
            f.write(str(p) + "\n")
        listfile = f.name
    try:
        r = subprocess.run(["zstd", "--train", f"--maxdict={maxdict}",
                            f"--filelist={listfile}", "-o", str(dict_path)],
                           capture_output=True, timeout=600)
        return r.returncode == 0 and os.path.isfile(str(dict_path))
    finally:
        os.unlink(listfile)


def main():
    # Load existing diagnostics
    csv_path = RESULTS_DIR / "all_files_diagnostics.csv"
    recs = []
    with open(csv_path) as f:
        for row in csv.DictReader(f):
            # Initialize new fields
            row["svg_zstd_size"] = 0
            row["svg_zstd_dict_size"] = 0
            recs.append(row)
    print(f"Loaded {len(recs)} records from diagnostics CSV")

    # Build SVG source index
    svg_indexes = {}
    for gname, svg_dir in SVG_DIRS.items():
        idx = {}
        if svg_dir.exists():
            for f in svg_dir.iterdir():
                if f.suffix.lower() == ".svg":
                    idx[f.name] = str(f)
                    idx[f.name.lower()] = str(f)
        svg_indexes[gname] = idx

    # Phase 1: Run SVGO on all source SVGs and save optimized versions (parallel)
    svgo_items = []
    for rec in recs:
        if rec["status"] == "no_source" or rec["fail_stage"] == "source":
            continue
        idx = svg_indexes.get(rec["group"], {})
        svg_path = idx.get(rec["file"]) or idx.get(rec["file"].lower())
        if svg_path:
            svgo_items.append((svg_path, rec["file"], rec["group"]))

    print(f"\nRunning SVGO on {len(svgo_items)} files with {PARALLEL_WORKERS} workers...")
    svgo_map = {}  # (group, file) -> svgo_path
    done = 0
    with ProcessPoolExecutor(max_workers=PARALLEL_WORKERS) as executor:
        futures = {executor.submit(svgo_one, item): item for item in svgo_items}
        for future in as_completed(futures):
            group, basename, svgo_path = future.result()
            if svgo_path:
                svgo_map[(group, basename)] = svgo_path
            done += 1
            if done % 500 == 0 or done == len(svgo_items):
                print(f"  SVGO {done}/{len(svgo_items)} ({len(svgo_map)} saved)")

    print(f"SVGO completed: {len(svgo_map)} optimized SVGs saved")

    # Assign svgo_path to records
    for rec in recs:
        key = (rec["group"], rec["file"])
        if key in svgo_map:
            rec["svgo_path"] = svgo_map[key]

    # Phase 2: Compress SVGs with zstd (no dict)
    has_svgo = [r for r in recs if r.get("svgo_path")]
    print(f"\nCompressing {len(has_svgo)} SVGs with zstd...")
    for i, rec in enumerate(recs):
        if rec.get("svgo_path"):
            z, _ = compress_one(rec["svgo_path"])
            rec["svg_zstd_size"] = z
        if (i + 1) % 500 == 0 or (i + 1) == len(recs):
            print(f"  {i+1}/{len(recs)}")

    # Phase 3: Train SVG dictionary
    svg_files = [r["svgo_path"] for r in recs if r.get("svgo_path")]
    svg_dict_path = RESULTS_DIR / "svg_dict.zstd"
    print(f"\nTraining SVG dictionary ({DICT_SIZE:,} bytes) on {len(svg_files)} files...")
    train_dict(svg_files, svg_dict_path)
    if svg_dict_path.exists():
        print(f"  SVG dictionary: {file_size(str(svg_dict_path)):,} bytes")
    else:
        print("  WARNING: SVG dictionary training failed!")

    # Phase 4: Compress SVGs with dict
    if svg_dict_path.exists():
        print("\nCompressing SVGs with dictionary...")
        for i, rec in enumerate(recs):
            if rec.get("svgo_path"):
                _, d = compress_one(rec["svgo_path"], svg_dict_path)
                rec["svg_zstd_dict_size"] = d
            if (i + 1) % 500 == 0 or (i + 1) == len(recs):
                print(f"  {i+1}/{len(recs)}")

    # Phase 5: Retrain TVG dictionary at correct 112640 size (was 65536 before)
    tvg_files = []
    for rec in recs:
        if rec["status"] == "ok":
            tvg_path = WORK / "tvg-files" / rec["group"] / rec["file"].replace(".svg", ".tvg")
            if tvg_path.exists():
                tvg_files.append(str(tvg_path))
    tvg_dict_path = RESULTS_DIR / "tvg_dict.zstd"
    print(f"\nRetraining TVG dictionary ({DICT_SIZE:,} bytes) on {len(tvg_files)} files...")
    train_dict(tvg_files, tvg_dict_path)
    if tvg_dict_path.exists():
        print(f"  TVG dictionary: {file_size(str(tvg_dict_path)):,} bytes")

    # Phase 6: Recompress TVGs with new dictionary
    if tvg_dict_path.exists():
        print("\nRecompressing TVGs with new dictionary...")
        for i, rec in enumerate(recs):
            if rec["status"] == "ok":
                tvg_path = WORK / "tvg-files" / rec["group"] / rec["file"].replace(".svg", ".tvg")
                if tvg_path.exists():
                    d = compress_tvg(str(tvg_path), tvg_dict_path)
                    rec["zstd_dict_size"] = d
            if (i + 1) % 500 == 0 or (i + 1) == len(recs):
                print(f"  {i+1}/{len(recs)}")

    # Write updated CSV
    fieldnames = ["group", "file", "ref_svg_size", "ref_tvg_size", "cur_svg_size",
                  "svgo_size", "tvgt_size", "tvg_size",
                  "svg_zstd_size", "svg_zstd_dict_size",
                  "zstd_size", "brotli_size", "zstd_dict_size",
                  "status", "fail_stage", "fail_detail"]
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        for rec in sorted(recs, key=lambda r: (r["group"], r["file"])):
            writer.writerow(rec)
    print(f"\nUpdated CSV: {csv_path}")
    print(f"Done!")


if __name__ == "__main__":
    main()
