#!/usr/bin/env python3
"""
svg_dict_size_study.py - Study how SVG compression varies with zstd dictionary size.

Trains zstd dictionaries at multiple sizes on SVGO-optimized SVG files, then
measures compression of every file with each dictionary. Also uses --train-fastcover
with shrink to find the automatically-optimal dictionary size.

Produces results/svg_dict_size_report.md and results/svg_dict_size_details.csv
"""

import csv
import os
import shutil
import subprocess
import tempfile
import time
from collections import defaultdict
from pathlib import Path

RESULTS_DIR = Path(__file__).resolve().parent / "results"
WORK = Path("/tmp/tinyvg-eval-work")
SVGO_DIR = WORK / "svgo-files"

# Dictionary sizes to test (bytes)
DICT_SIZES = {
    "64KB":  65536,
    "110KB": 112640,
    "256KB": 262144,
    "512KB": 524288,
}

SHRINK_CEILING = 524288


def file_size(path):
    return os.path.getsize(path) if os.path.isfile(path) else 0


def collect_svgo_files():
    """Collect all SVGO-optimized SVGs from the work directory."""
    files = []
    if SVGO_DIR.exists():
        for group_dir in sorted(SVGO_DIR.iterdir()):
            if group_dir.is_dir():
                for svg in sorted(group_dir.iterdir()):
                    if svg.suffix.lower() == ".svg" and svg.stat().st_size > 0:
                        files.append((group_dir.name, svg.name, str(svg)))
    return files


def train_dict(file_paths, dict_path, maxdict, use_shrink=False, shrink_pct=1):
    """Train a zstd dictionary. Returns (success, actual_size, elapsed, output)."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        for p in file_paths:
            f.write(p + "\n")
        listfile = f.name
    try:
        if use_shrink:
            cmd = ["zstd",
                   f"--train-fastcover=d=8,steps=40,shrink={shrink_pct}",
                   f"--maxdict={maxdict}",
                   f"--filelist={listfile}",
                   "-o", str(dict_path)]
        else:
            cmd = ["zstd", "--train",
                   f"--maxdict={maxdict}",
                   f"--filelist={listfile}",
                   "-o", str(dict_path)]
        t0 = time.time()
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=1200)
        elapsed = time.time() - t0
        success = r.returncode == 0 and os.path.isfile(str(dict_path))
        actual_size = file_size(str(dict_path)) if success else 0
        return success, actual_size, elapsed, (r.stderr or "") + (r.stdout or "")
    finally:
        os.unlink(listfile)


def compress_batch(file_list, dict_path=None):
    """Compress all files with zstd -22 --ultra, optionally with dict.
    Returns dict of (group, file) -> compressed_size."""
    results = {}
    tmpdir = tempfile.mkdtemp(prefix="dsize-")
    try:
        for i, (group, fname, fpath) in enumerate(file_list):
            out = os.path.join(tmpdir, "out.zst")
            cmd = ["zstd", "-22", "--ultra", "-f", "-o", out, fpath]
            if dict_path:
                cmd = ["zstd", "-22", "--ultra", "-D", str(dict_path),
                       "-f", "-o", out, fpath]
            r = subprocess.run(cmd, capture_output=True, timeout=60)
            results[(group, fname)] = file_size(out) if r.returncode == 0 else 0
            if (i + 1) % 2000 == 0 or (i + 1) == len(file_list):
                print(f"    {i+1}/{len(file_list)}", flush=True)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return results


def main():
    import sys
    sys.stdout.reconfigure(line_buffering=True)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    dict_dir = RESULTS_DIR / "svg_dicts"
    dict_dir.mkdir(exist_ok=True)

    all_files = collect_svgo_files()
    print(f"Found {len(all_files)} SVGO-optimized SVG files")
    if not all_files:
        print("ERROR: No SVGO files found.")
        return

    file_paths = [f[2] for f in all_files]
    orig_sizes = {(g, fn): file_size(fp) for g, fn, fp in all_files}
    total_svgo = sum(orig_sizes.values())

    # Phase 1: Train dictionaries
    dicts = {}  # label -> (dict_path, actual_size, train_time)

    for label, size in sorted(DICT_SIZES.items(), key=lambda x: x[1]):
        dict_path = dict_dir / f"svg_dict_{label}.zstd"
        print(f"\nTraining {label} dictionary (maxdict={size:,})...", flush=True)
        ok, actual, elapsed, output = train_dict(file_paths, dict_path, size)
        if ok:
            dicts[label] = (str(dict_path), actual, elapsed)
            print(f"  OK: {actual:,} bytes, {elapsed:.1f}s")
        else:
            print(f"  FAILED: {output[:200]}")

    # Shrink runs
    shrink_results = {}
    for shrink_pct in [1, 2, 5]:
        label = f"shrink-{shrink_pct}%"
        dict_path = dict_dir / f"svg_dict_shrink_{shrink_pct}pct.zstd"
        print(f"\nTraining with shrink={shrink_pct} (maxdict={SHRINK_CEILING:,})...", flush=True)
        ok, actual, elapsed, output = train_dict(
            file_paths, dict_path, SHRINK_CEILING,
            use_shrink=True, shrink_pct=shrink_pct)
        if ok:
            shrink_results[label] = (str(dict_path), actual, elapsed)
            print(f"  OK: {actual:,} bytes, {elapsed:.1f}s")
        else:
            print(f"  FAILED: {output[:500]}")

    # Phase 2: Compress with each UNIQUE dictionary
    # Determine which shrink dicts are distinct from fixed ones
    results = {}  # label -> {(group,file)->size}

    print(f"\n{'='*60}")
    print(f"Compressing {len(all_files)} files...")

    print(f"\n  no-dict (zstd -22)...", flush=True)
    results["no-dict"] = compress_batch(all_files)

    for label in sorted(dicts.keys(), key=lambda l: dicts[l][1]):
        dict_path, dict_size, _ = dicts[label]
        print(f"\n  {label} ({dict_size:,} bytes)...", flush=True)
        results[label] = compress_batch(all_files, dict_path)

    # Only compress with shrink dicts that differ from 512KB
    for label, (dict_path, dict_size, _) in shrink_results.items():
        if dict_size == SHRINK_CEILING and "512KB" in results:
            print(f"\n  {label}: same size as 512KB ({dict_size:,}), reusing results")
            # Still need to compress since it's a different dict (different content)
            # But let's check if the dict bytes are actually identical
            if "512KB" in dicts:
                import filecmp
                if filecmp.cmp(dict_path, dicts["512KB"][0], shallow=False):
                    results[label] = results["512KB"]
                    print(f"    Dict is byte-identical to 512KB, skipping")
                    continue
            print(f"    Dict differs from 512KB, compressing...", flush=True)
            results[label] = compress_batch(all_files, dict_path)
        else:
            print(f"\n  {label} ({dict_size:,} bytes)...", flush=True)
            results[label] = compress_batch(all_files, dict_path)

    # Merge shrink info into dicts for reporting
    all_dicts = {**dicts, **shrink_results}

    # Phase 3: Write detailed CSV
    csv_path = RESULTS_DIR / "svg_dict_size_details.csv"
    all_labels = ["no-dict"] + sorted(
        [l for l in all_dicts.keys()], key=lambda l: all_dicts[l][1])
    fieldnames = ["group", "file", "svgo_size"] + [f"zstd_{l}" for l in all_labels]
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for group, fname, fpath in all_files:
            row = {"group": group, "file": fname, "svgo_size": orig_sizes[(group, fname)]}
            for label in all_labels:
                row[f"zstd_{label}"] = results.get(label, {}).get((group, fname), 0)
            writer.writerow(row)
    print(f"\nDetailed CSV: {csv_path}")

    # Phase 4: Generate report
    generate_report(all_files, orig_sizes, all_dicts, results, all_labels)


def generate_report(all_files, orig_sizes, dicts, results, all_labels):
    lines = []
    w = lines.append

    w("# SVG Compression vs Zstd Dictionary Size")
    w("")
    w("This report studies how SVG compression with zstd varies as a function of")
    w("dictionary size. All files are SVGO-optimized SVGs from the TinyVG benchmark")
    w("and extended icon set corpus.")
    w("")
    w("## Methodology")
    w("")
    w(f"- **Corpus**: {len(all_files):,} SVGO-optimized SVG files across "
      f"{len(set(g for g,_,_ in all_files))} icon set groups")
    total_svgo = sum(orig_sizes.values())
    w(f"- **Total uncompressed size**: {total_svgo:,} bytes ({total_svgo/1024/1024:.1f} MB)")
    w("- **Compression**: `zstd --ultra -22` (maximum compression level)")
    w("- **Dictionary training**: `zstd --train` (default fastCOVER) for fixed sizes;")
    w("  `--train-fastcover=d=8,steps=40,shrink=N` for auto-optimized sizes")
    w("- **Dictionaries trained on the same corpus** being compressed (best-case scenario)")
    w("")

    groups = defaultdict(list)
    for group, fname, fpath in all_files:
        groups[group].append((fname, fpath))

    # Fixed-size labels (for main comparison)
    fixed_labels = ["no-dict"] + sorted(
        [l for l in DICT_SIZES.keys() if l in dicts],
        key=lambda l: dicts[l][1])

    # Overall summary
    w("## Overall Summary")
    w("")
    w("| Dictionary | Dict size | Total compressed | % of SVG | Savings vs no-dict |")
    w("|------------|-----------|-----------------|----------|-------------------|")

    no_dict_total = sum(results["no-dict"].values())
    w(f"| no-dict (zstd -22) | - | {no_dict_total:,} | {no_dict_total/total_svgo:.1%} | - |")

    for label in fixed_labels[1:]:
        dict_path, dict_size, train_time = dicts[label]
        total_comp = sum(results[label].values())
        savings = 1 - total_comp / no_dict_total if no_dict_total else 0
        w(f"| {label} | {dict_size:,} | {total_comp:,} | "
          f"{total_comp/total_svgo:.1%} | {savings:.1%} |")

    w("")
    w(f"**Total uncompressed SVG**: {total_svgo:,} bytes")
    w("")

    # Marginal value
    w("## Marginal Value of Dictionary Size")
    w("")
    w("How much additional compression does each step up in dictionary size provide?")
    w("")
    w("| From | To | Additional savings | Marginal % |")
    w("|------|-----|-------------------|-----------|")

    for i in range(1, len(fixed_labels)):
        prev = fixed_labels[i-1]
        curr = fixed_labels[i]
        prev_total = sum(results[prev].values())
        curr_total = sum(results[curr].values())
        saved = prev_total - curr_total
        pct = saved / prev_total if prev_total else 0
        prev_sz = f"{dicts[prev][1]:,}" if prev in dicts else "0"
        curr_sz = f"{dicts[curr][1]:,}"
        w(f"| {prev} ({prev_sz}B) | {curr} ({curr_sz}B) | "
          f"{saved:,} bytes | {pct:.2%} |")

    w("")

    # Shrink
    shrink_labels = sorted(
        [l for l in dicts if l.startswith("shrink")],
        key=lambda l: dicts[l][1])
    if shrink_labels:
        w("## Auto-Optimized Dictionary Sizes (shrink)")
        w("")
        w("The zstd `--train-fastcover` `shrink` flag trains a full-size dictionary,")
        w("then binary-searches for the smallest dictionary within N% of full-size")
        w("compression ratio. Starting from a 512KB ceiling:")
        w("")
        w("| Variant | Regression tolerance | Resulting dict size | Total compressed | % of SVG |")
        w("|---------|---------------------|--------------------|-----------------| ---------|")

        for label in shrink_labels:
            dict_path, dict_size, train_time = dicts[label]
            total_comp = sum(results[label].values())
            pct_name = label.split("-")[1]
            w(f"| {label} | {pct_name} | {dict_size:,} ({dict_size//1024}KB) | "
              f"{total_comp:,} | {total_comp/total_svgo:.1%} |")

        w("")
        all_full = all(dicts[l][1] == SHRINK_CEILING for l in shrink_labels)
        if all_full:
            w("**Finding**: The shrink optimizer kept the full 512KB dictionary at all")
            w("tolerance levels (1%, 2%, 5%). This means that even small reductions")
            w("in dictionary size cause more than 5% regression in total compression")
            w("ratio — the dictionary content is genuinely utilized at 512KB.")
        w("")

    # Per-group
    w("## Per-Group Comparison")
    w("")

    header = "| Group | Files | SVG size |"
    sep = "|-------|-------|----------|"
    for c in fixed_labels:
        header += f" {c} |"
        sep += "------|"
    w(header)
    w(sep)

    for gname in sorted(groups.keys()):
        gfiles = groups[gname]
        gsvgo = sum(orig_sizes[(gname, fn)] for fn, _ in gfiles)
        row = f"| {gname} | {len(gfiles):,} | {gsvgo:,} |"
        for label in fixed_labels:
            total = sum(results[label].get((gname, fn), 0) for fn, _ in gfiles)
            pct = total / gsvgo if gsvgo else 0
            row += f" {pct:.1%} |"
        w(row)

    row = f"| **Total** | **{len(all_files):,}** | **{total_svgo:,}** |"
    for label in fixed_labels:
        total = sum(results[label].values())
        row += f" **{total/total_svgo:.1%}** |"
    w(row)
    w("")

    # Distribution
    w("## Compression Ratio Distribution (compressed / SVG)")
    w("")
    w("Percentiles of per-file compression ratio for each dictionary size:")
    w("")
    header = "| Percentile |"
    sep = "|------------|"
    for c in fixed_labels:
        header += f" {c} |"
        sep += "------|"
    w(header)
    w(sep)

    per_file = {}
    for label in fixed_labels:
        ratios = []
        for group, fname, fpath in all_files:
            svgo = orig_sizes.get((group, fname), 0)
            comp = results[label].get((group, fname), 0)
            if svgo > 0 and comp > 0:
                ratios.append(comp / svgo)
        ratios.sort()
        per_file[label] = ratios

    for pname, pfunc in [("p5", lambda r: r[len(r)//20]),
                          ("p10", lambda r: r[len(r)//10]),
                          ("p25", lambda r: r[len(r)//4]),
                          ("Median", lambda r: r[len(r)//2]),
                          ("p75", lambda r: r[3*len(r)//4]),
                          ("p90", lambda r: r[9*len(r)//10]),
                          ("p95", lambda r: r[19*len(r)//20]),
                          ("Mean", lambda r: sum(r)/len(r))]:
        row = f"| {pname} |"
        for label in fixed_labels:
            ratios = per_file[label]
            if ratios:
                val = pfunc(ratios)
                row += f" {val:.1%} |"
            else:
                row += " - |"
        w(row)

    w("")

    # Key findings
    w("## Key Findings")
    w("")

    totals = {l: sum(results[l].values()) for l in fixed_labels}

    if "64KB" in totals and "no-dict" in totals:
        imp = 1 - totals["64KB"] / totals["no-dict"]
        w(f"1. **no-dict to 64KB**: The first 64KB of dictionary provides the largest jump — "
          f"{imp:.1%} total savings ({totals['no-dict']-totals['64KB']:,} bytes)")

    if "64KB" in totals and "110KB" in totals:
        imp = 1 - totals["110KB"] / totals["64KB"]
        w(f"2. **64KB to 110KB**: {imp:.1%} additional savings "
          f"({totals['64KB']-totals['110KB']:,} bytes)")

    if "110KB" in totals and "256KB" in totals:
        imp = 1 - totals["256KB"] / totals["110KB"]
        w(f"3. **110KB to 256KB**: {imp:.1%} additional savings "
          f"({totals['110KB']-totals['256KB']:,} bytes)")

    if "256KB" in totals and "512KB" in totals:
        imp = 1 - totals["512KB"] / totals["256KB"]
        w(f"4. **256KB to 512KB**: {imp:.1%} additional savings "
          f"({totals['256KB']-totals['512KB']:,} bytes)")

    if all_full and shrink_labels:
        w(f"5. **Shrink optimization**: The zstd shrink flag (tested at 1%, 2%, 5% regression "
          f"tolerance) did not reduce the 512KB dictionary at all, indicating all dictionary "
          f"content contributes meaningfully to compression of this corpus.")

    w("")

    report_path = RESULTS_DIR / "svg_dict_size_report.md"
    with open(report_path, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"\nReport: {report_path} ({len(lines)} lines)")


if __name__ == "__main__":
    main()
