#!/usr/bin/env python3
"""
diagnose_failures.py - Attempt conversion of ALL files (benchmark + extended),
recording the failure stage and error message for each.

Produces results/all_files_diagnostics.csv with columns:
  group, file, ref_svg_size, ref_tvg_size, cur_svg_size,
  svgo_size, tvgt_size, tvg_size,
  zstd_size, brotli_size, zstd_dict_size,
  status, fail_stage, fail_detail
"""

import csv
import os
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

WORK = Path("/tmp/tinyvg-eval-work")
SVG_BASE = WORK / "svg-sources"
SDK_DIR = WORK / "tinyvg-sdk"
RESULTS_DIR = Path(__file__).resolve().parent / "results"
SVGO_CONFIG = str(Path(__file__).resolve().parent / "svgo.config.js")

TVG_TEXT_BIN = str(SDK_DIR / "zig-out" / "bin" / "tvg-text")
SVG2TVGT_DLL = str(SDK_DIR / "src" / "tools" / "svg2tvgt" / "bin" / "Debug" / "net8.0" / "svg2tvgt.dll")

# Default zstd dictionary size (zstd CLI default = 112640 = 110KB)
DICT_SIZE = 112640

# Original benchmark groups (have reference CSVs with known file lists)
BENCHMARK_CSVS = {
    "zig":             WORK / "benchmark-csvs" / "zig.csv",
    "w3c":             WORK / "benchmark-csvs" / "w3c.csv",
    "material-design": WORK / "benchmark-csvs" / "material-design.csv",
    "papirus":         WORK / "benchmark-csvs" / "papirus.csv",
    "freesvg":         WORK / "benchmark-csvs" / "freesvg.csv",
}

# All SVG directories
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

PARALLEL_WORKERS = 8


def file_size(path):
    return os.path.getsize(path) if os.path.isfile(path) else 0


def load_benchmark(group):
    path = BENCHMARK_CSVS[group]
    if not path.exists():
        return {}
    rows = {}
    with open(path) as f:
        reader = csv.reader(f, delimiter="\t")
        next(reader)
        for row in reader:
            if len(row) >= 3:
                basename = os.path.basename(row[0])
                rows[basename] = (int(row[1]), int(row[2]))
    return rows


def diagnose_one(args):
    """Try full pipeline on one SVG, returning detailed diagnostic dict."""
    svg_path, basename, group, ref_svg_size, ref_tvg_size = args
    rec = {
        "group": group,
        "file": basename,
        "ref_svg_size": ref_svg_size,
        "ref_tvg_size": ref_tvg_size,
        "cur_svg_size": 0,
        "svgo_size": 0,
        "tvgt_size": 0,
        "tvg_size": 0,
        "zstd_size": 0,
        "brotli_size": 0,
        "zstd_dict_size": 0,
        "status": "no_source",
        "fail_stage": "source",
        "fail_detail": "SVG not found in current source dataset",
    }

    if not svg_path or not os.path.isfile(svg_path):
        return rec

    rec["cur_svg_size"] = file_size(svg_path)

    tmpdir = tempfile.mkdtemp(prefix="tvg-diag-")
    try:
        opt_svg = os.path.join(tmpdir, "optimized.svg")
        tvgt = os.path.join(tmpdir, "output.tvgt")
        tvg = os.path.join(tmpdir, "output.tvg")

        # Step 1: SVGO
        shutil.copy2(svg_path, opt_svg)
        try:
            r = subprocess.run(
                ["svgo", "--quiet", "--config", SVGO_CONFIG, opt_svg],
                capture_output=True, text=True, timeout=60)
            if r.returncode != 0:
                rec["status"] = "fail"
                rec["fail_stage"] = "svgo"
                rec["fail_detail"] = (r.stderr or r.stdout or "nonzero exit")[:200].replace('\n', ' ').strip()
                return rec
        except subprocess.TimeoutExpired:
            rec["status"] = "fail"
            rec["fail_stage"] = "svgo"
            rec["fail_detail"] = "timeout (>60s)"
            return rec

        rec["svgo_size"] = file_size(opt_svg)
        if rec["svgo_size"] == 0:
            rec["status"] = "fail"
            rec["fail_stage"] = "svgo"
            rec["fail_detail"] = "SVGO produced empty output"
            return rec

        # For new groups without benchmark ref, use SVGO size as ref_svg_size
        if rec["ref_svg_size"] == 0:
            rec["ref_svg_size"] = rec["svgo_size"]

        # Always save optimized SVG for SVG compression benchmarks
        svg_dst = WORK / "svgo-files" / group / basename
        svg_dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(opt_svg, str(svg_dst))
        rec["svgo_path"] = str(svg_dst)

        # Step 2: svg2tvgt
        try:
            r = subprocess.run(
                ["dotnet", SVG2TVGT_DLL, opt_svg, "--output", tvgt],
                capture_output=True, text=True, timeout=60)
            stderr_combined = ((r.stderr or "") + " " + (r.stdout or "")).strip()
            if r.returncode != 0:
                rec["status"] = "fail"
                rec["fail_stage"] = "svg2tvgt"
                rec["fail_detail"] = stderr_combined[:200].replace('\n', ' ').strip()
                return rec
            if not os.path.isfile(tvgt) or file_size(tvgt) == 0:
                rec["status"] = "fail"
                rec["fail_stage"] = "svg2tvgt"
                rec["fail_detail"] = "no output; " + stderr_combined[:150].replace('\n', ' ').strip()
                return rec
            warnings = stderr_combined if stderr_combined else ""
        except subprocess.TimeoutExpired:
            rec["status"] = "fail"
            rec["fail_stage"] = "svg2tvgt"
            rec["fail_detail"] = "timeout (>60s)"
            return rec

        rec["tvgt_size"] = file_size(tvgt)

        # Step 3: tvg-text
        try:
            r = subprocess.run(
                [TVG_TEXT_BIN, tvgt, "--output", tvg],
                capture_output=True, text=True, timeout=60)
            if r.returncode != 0:
                tvg_stderr = ((r.stderr or "") + " " + (r.stdout or "")).strip()
                rec["status"] = "fail"
                rec["fail_stage"] = "tvg-text"
                rec["fail_detail"] = tvg_stderr[:200].replace('\n', ' ').strip()
                return rec
            if not os.path.isfile(tvg) or file_size(tvg) == 0:
                rec["status"] = "fail"
                rec["fail_stage"] = "tvg-text"
                rec["fail_detail"] = "no output produced"
                return rec
        except subprocess.TimeoutExpired:
            rec["status"] = "fail"
            rec["fail_stage"] = "tvg-text"
            rec["fail_detail"] = "timeout (>60s)"
            return rec

        rec["tvg_size"] = file_size(tvg)
        rec["status"] = "ok"
        rec["fail_stage"] = ""
        rec["fail_detail"] = warnings[:200].replace('\n', ' ').strip() if warnings else ""

        # Save TVG for later compression
        dst = WORK / "tvg-files" / group / basename.replace(".svg", ".tvg")
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(tvg, str(dst))
        rec["tvg_path"] = str(dst)

        return rec
    except Exception as e:
        rec["status"] = "fail"
        rec["fail_stage"] = "exception"
        rec["fail_detail"] = str(e)[:200]
        return rec
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def compress_one(path, dict_path=None):
    """Compress a single file with zstd -22 (and optionally with dict). Returns (zstd_size, zstd_dict_size)."""
    tmpdir = tempfile.mkdtemp(prefix="tvg-comp-")
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


def compress_tvg_file(tvg_path, dict_path=None):
    """Return (zstd_size, brotli_size, zstd_dict_size) for a TVG file."""
    tmpdir = tempfile.mkdtemp(prefix="tvg-comp-")
    try:
        zstd_out = os.path.join(tmpdir, "out.zst")
        br_out = os.path.join(tmpdir, "out.br")

        r = subprocess.run(["zstd", "-22", "--ultra", "-f", "-o", zstd_out, tvg_path],
                           capture_output=True, timeout=60)
        zstd_sz = file_size(zstd_out) if r.returncode == 0 else 0

        r = subprocess.run(["brotli", "-q", "11", "-f", "-o", br_out, tvg_path],
                           capture_output=True, timeout=60)
        br_sz = file_size(br_out) if r.returncode == 0 else 0

        zdict_sz = 0
        if dict_path and os.path.isfile(str(dict_path)):
            zdict_out = os.path.join(tmpdir, "out.zdict")
            r = subprocess.run(["zstd", "-22", "--ultra", "-D", str(dict_path),
                                "-f", "-o", zdict_out, tvg_path],
                               capture_output=True, timeout=60)
            zdict_sz = file_size(zdict_out) if r.returncode == 0 else 0

        return zstd_sz, br_sz, zdict_sz
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def train_dict(file_list, dict_path, maxdict=DICT_SIZE):
    """Train a zstd dictionary from a list of file paths."""
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
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # Build SVG index per group (case-insensitive)
    svg_indexes = {}
    for gname, svg_dir in SVG_DIRS.items():
        idx = {}
        if svg_dir.exists():
            for f in svg_dir.iterdir():
                if f.suffix.lower() == ".svg":
                    idx[f.name] = str(f)
                    idx[f.name.lower()] = str(f)
        svg_indexes[gname] = idx

    # Build work items for ALL files
    work_items = []

    # Original benchmark groups (with reference CSVs)
    for gname in ["zig", "w3c", "material-design", "papirus", "freesvg"]:
        if gname in BENCHMARK_CSVS and BENCHMARK_CSVS[gname].exists():
            benchmark = load_benchmark(gname)
        else:
            benchmark = {}
        idx = svg_indexes.get(gname, {})
        for basename, (ref_svg, ref_tvg) in benchmark.items():
            svg_path = idx.get(basename) or idx.get(basename.lower())
            work_items.append((svg_path, basename, gname, ref_svg, ref_tvg))

    # Extended icon set groups (no benchmark reference)
    for gname in ["tabler", "lucide", "bootstrap", "simple-icons",
                   "phosphor", "fontawesome", "remixicon"]:
        svg_dir = SVG_DIRS.get(gname)
        if not svg_dir or not svg_dir.exists():
            continue
        idx = svg_indexes.get(gname, {})
        seen = set()
        for basename_key, svg_path in idx.items():
            basename = os.path.basename(svg_path)
            if basename not in seen:
                seen.add(basename)
                work_items.append((svg_path, basename, gname, 0, 0))

    total = len(work_items)
    print(f"Diagnosing {total} files from all groups...")

    # Phase 1: Convert (parallel)
    all_recs = []
    done = 0
    with ProcessPoolExecutor(max_workers=PARALLEL_WORKERS) as executor:
        futures = {executor.submit(diagnose_one, item): item for item in work_items}
        for future in as_completed(futures):
            rec = future.result()
            all_recs.append(rec)
            done += 1
            if done % 500 == 0 or done == total:
                ok = sum(1 for r in all_recs if r["status"] == "ok")
                print(f"  {done}/{total} (ok: {ok})")

    ok_recs = [r for r in all_recs if r["status"] == "ok"]
    has_svgo = [r for r in all_recs if r.get("svgo_path")]
    print(f"\nConversion: {len(ok_recs)} ok, {total - len(ok_recs)} failed/missing")
    print(f"SVGO succeeded: {len(has_svgo)} files (available for SVG compression)")

    # Phase 2: Compress TVG files (zstd + brotli, no dict yet)
    print("\nCompressing TVG files (zstd + brotli)...")
    for i, rec in enumerate(all_recs):
        if rec["status"] == "ok" and rec.get("tvg_path"):
            z, b, _ = compress_tvg_file(rec["tvg_path"], dict_path=None)
            rec["zstd_size"] = z
            rec["brotli_size"] = b
        if (i + 1) % 500 == 0 or (i + 1) == total:
            print(f"  {i+1}/{total}")

    # Phase 3: Compress SVG files (zstd, no dict yet)
    print("\nCompressing SVGO-optimized SVG files (zstd)...")
    for i, rec in enumerate(all_recs):
        if rec.get("svgo_path"):
            z, _ = compress_one(rec["svgo_path"], dict_path=None)
            rec["svg_zstd_size"] = z
        if (i + 1) % 500 == 0 or (i + 1) == total:
            print(f"  {i+1}/{total}")

    # Phase 4: Train dictionaries
    # 4a: TVG dictionary
    tvg_files = [r["tvg_path"] for r in all_recs if r["status"] == "ok" and r.get("tvg_path")]
    tvg_dict_path = RESULTS_DIR / "tvg_dict.zstd"
    print(f"\nTraining TVG dictionary ({DICT_SIZE:,} bytes) on {len(tvg_files)} TVG files...")
    train_dict(tvg_files, tvg_dict_path)
    if tvg_dict_path.exists():
        print(f"  TVG dictionary: {file_size(str(tvg_dict_path)):,} bytes")
    else:
        print("  WARNING: TVG dictionary training failed!")

    # 4b: SVG dictionary
    svg_files = [r["svgo_path"] for r in all_recs if r.get("svgo_path")]
    svg_dict_path = RESULTS_DIR / "svg_dict.zstd"
    print(f"Training SVG dictionary ({DICT_SIZE:,} bytes) on {len(svg_files)} SVG files...")
    train_dict(svg_files, svg_dict_path)
    if svg_dict_path.exists():
        print(f"  SVG dictionary: {file_size(str(svg_dict_path)):,} bytes")
    else:
        print("  WARNING: SVG dictionary training failed!")

    # Phase 5: Compress with dictionaries
    if tvg_dict_path.exists():
        print("\nCompressing TVG files with dictionary...")
        for i, rec in enumerate(all_recs):
            if rec["status"] == "ok" and rec.get("tvg_path"):
                _, _, d = compress_tvg_file(rec["tvg_path"], tvg_dict_path)
                rec["zstd_dict_size"] = d
            if (i + 1) % 500 == 0 or (i + 1) == total:
                print(f"  {i+1}/{total}")

    if svg_dict_path.exists():
        print("\nCompressing SVG files with dictionary...")
        for i, rec in enumerate(all_recs):
            if rec.get("svgo_path"):
                _, d = compress_one(rec["svgo_path"], svg_dict_path)
                rec["svg_zstd_dict_size"] = d
            if (i + 1) % 500 == 0 or (i + 1) == total:
                print(f"  {i+1}/{total}")

    # Write CSV
    csv_path = RESULTS_DIR / "all_files_diagnostics.csv"
    fieldnames = ["group", "file", "ref_svg_size", "ref_tvg_size", "cur_svg_size",
                  "svgo_size", "tvgt_size", "tvg_size",
                  "svg_zstd_size", "svg_zstd_dict_size",
                  "zstd_size", "brotli_size", "zstd_dict_size",
                  "status", "fail_stage", "fail_detail"]
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        for rec in sorted(all_recs, key=lambda r: (r["group"], r["file"])):
            writer.writerow(rec)
    print(f"\nDiagnostics CSV: {csv_path}")

    # Print failure summary
    from collections import Counter
    print("\n=== Failure Summary ===")
    stage_counts = Counter()
    for rec in all_recs:
        if rec["status"] != "ok":
            stage_counts[rec["fail_stage"]] += 1

    print(f"\nBy stage:")
    for stage, count in stage_counts.most_common():
        print(f"  {stage}: {count}")

    # Per-group summary
    group_counts = Counter()
    group_ok = Counter()
    for rec in all_recs:
        group_counts[rec["group"]] += 1
        if rec["status"] == "ok":
            group_ok[rec["group"]] += 1
    print(f"\nBy group:")
    for gname in sorted(group_counts.keys()):
        ok = group_ok[gname]
        total_g = group_counts[gname]
        print(f"  {gname}: {ok}/{total_g} ok ({100*ok/total_g:.0f}%)")


if __name__ == "__main__":
    main()
