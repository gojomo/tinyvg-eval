#!/usr/bin/env python3
"""
diagnose_failures.py - Attempt conversion of ALL benchmark files, recording
the failure stage and error message for each.

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

BENCHMARK_CSVS = {
    "zig":             WORK / "benchmark-csvs" / "zig.csv",
    "w3c":             WORK / "benchmark-csvs" / "w3c.csv",
    "material-design": WORK / "benchmark-csvs" / "material-design.csv",
    "papirus":         WORK / "benchmark-csvs" / "papirus.csv",
    "freesvg":         WORK / "benchmark-csvs" / "freesvg.csv",
}

SVG_DIRS = {
    "zig":             SVG_BASE / "zig-logo",
    "w3c":             SVG_BASE / "w3c",
    "material-design": SVG_BASE / "material-design",
    "papirus":         SVG_BASE / "papirus",
}

PARALLEL_WORKERS = 8


def file_size(path):
    return os.path.getsize(path) if os.path.isfile(path) else 0


def load_benchmark(group):
    path = BENCHMARK_CSVS[group]
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
            # Capture warnings even on success
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


def compress_file(tvg_path, dict_path=None):
    """Return (zstd_size, brotli_size, zstd_dict_size) for a TVG file."""
    tmpdir = tempfile.mkdtemp(prefix="tvg-comp-")
    try:
        zstd_out = os.path.join(tmpdir, "out.zst")
        br_out = os.path.join(tmpdir, "out.br")
        zdict_out = os.path.join(tmpdir, "out.zdict")

        r = subprocess.run(["zstd", "-22", "--ultra", "-f", "-o", zstd_out, tvg_path],
                           capture_output=True, timeout=60)
        zstd_sz = file_size(zstd_out) if r.returncode == 0 else 0

        r = subprocess.run(["brotli", "-q", "11", "-f", "-o", br_out, tvg_path],
                           capture_output=True, timeout=60)
        br_sz = file_size(br_out) if r.returncode == 0 else 0

        zdict_sz = 0
        if dict_path and os.path.isfile(dict_path):
            r = subprocess.run(["zstd", "-22", "--ultra", "-D", str(dict_path),
                                "-f", "-o", zdict_out, tvg_path],
                               capture_output=True, timeout=60)
            zdict_sz = file_size(zdict_out) if r.returncode == 0 else 0

        return zstd_sz, br_sz, zdict_sz
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


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

    # Build work items for ALL benchmark files
    work_items = []
    for gname in ["zig", "w3c", "material-design", "papirus", "freesvg"]:
        benchmark = load_benchmark(gname)
        idx = svg_indexes.get(gname, {})
        for basename, (ref_svg, ref_tvg) in benchmark.items():
            svg_path = idx.get(basename) or idx.get(basename.lower())
            work_items.append((svg_path, basename, gname, ref_svg, ref_tvg))

    total = len(work_items)
    print(f"Diagnosing {total} files from all benchmark groups...")

    # Phase 1: Convert (parallel)
    all_recs = []
    done = 0
    with ProcessPoolExecutor(max_workers=PARALLEL_WORKERS) as executor:
        futures = {executor.submit(diagnose_one, item): item for item in work_items}
        for future in as_completed(futures):
            rec = future.result()
            all_recs.append(rec)
            done += 1
            if done % 200 == 0 or done == total:
                ok = sum(1 for r in all_recs if r["status"] == "ok")
                print(f"  {done}/{total} (ok: {ok})")

    ok_recs = [r for r in all_recs if r["status"] == "ok"]
    print(f"\nConversion: {len(ok_recs)} ok, {total - len(ok_recs)} failed/missing")

    # Phase 2: Compress successful files
    print("Compressing TVG files...")
    dict_path = RESULTS_DIR / "tvg_dict.zstd"
    if not dict_path.exists():
        dict_path = None

    for i, rec in enumerate(all_recs):
        if rec["status"] == "ok" and rec.get("tvg_path"):
            z, b, d = compress_file(rec["tvg_path"], dict_path)
            rec["zstd_size"] = z
            rec["brotli_size"] = b
            rec["zstd_dict_size"] = d
        if (i + 1) % 200 == 0 or (i + 1) == total:
            print(f"  {i+1}/{total}")

    # Phase 3: If no dict yet, train one and re-compress
    if dict_path is None or not dict_path.exists():
        tvg_files = [r["tvg_path"] for r in all_recs if r["status"] == "ok" and r.get("tvg_path")]
        dict_path = RESULTS_DIR / "tvg_dict.zstd"
        print(f"Training dictionary on {len(tvg_files)} TVG files...")
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            for p in tvg_files:
                f.write(p + "\n")
            listfile = f.name
        try:
            subprocess.run(["zstd", "--train", "--maxdict=65536",
                            f"--filelist={listfile}", "-o", str(dict_path)],
                           capture_output=True, timeout=300)
        finally:
            os.unlink(listfile)

        if dict_path.exists():
            print(f"Dictionary: {file_size(dict_path):,} bytes. Re-compressing...")
            for rec in all_recs:
                if rec["status"] == "ok" and rec.get("tvg_path"):
                    _, _, d = compress_file(rec["tvg_path"], dict_path)
                    rec["zstd_dict_size"] = d

    # Write CSV
    csv_path = RESULTS_DIR / "all_files_diagnostics.csv"
    fieldnames = ["group", "file", "ref_svg_size", "ref_tvg_size", "cur_svg_size",
                  "svgo_size", "tvgt_size", "tvg_size",
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
    detail_counts = Counter()
    for rec in all_recs:
        if rec["status"] != "ok":
            stage_counts[rec["fail_stage"]] += 1
            # Normalize detail for counting
            detail = rec["fail_detail"]
            # Truncate long details to find patterns
            if "Unhandled exception" in detail:
                # Extract exception type
                if "System." in detail:
                    exc = detail[detail.index("System."):].split()[0].rstrip(":")
                    detail = f"Exception: {exc}"
                else:
                    detail = "Unhandled exception (other)"
            elif "error:" in detail.lower():
                detail = detail[:80]
            detail_counts[(rec["fail_stage"], detail[:100])] += 1

    print(f"\nBy stage:")
    for stage, count in stage_counts.most_common():
        print(f"  {stage}: {count}")

    print(f"\nBy stage + error pattern (top 30):")
    for (stage, detail), count in detail_counts.most_common(30):
        print(f"  [{stage}] {detail}: {count}")


if __name__ == "__main__":
    main()
