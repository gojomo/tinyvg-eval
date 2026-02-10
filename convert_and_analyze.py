#!/usr/bin/env python3
"""
convert_and_analyze.py - Full pipeline for TinyVG compression analysis.

For each SVG in the benchmark datasets:
  1. Optimize with SVGO (matching TinyVG benchmark settings)
  2. Convert SVG -> TVGT (text) -> TVG (binary)
  3. Compress .tvg with zstd --ultra -22, brotli -q 11
  4. Train a zstd dictionary on all .tvg files, then compress with it
  5. Emit per-file, per-group, and overall statistics

Produces:
  - results/compression_data.csv   (per-file raw data)
  - results/tvg_dict.zstd          (trained zstd dictionary)
  - results/report.md              (human-readable summary)
"""

import csv
import os
import shutil
import subprocess
import sys
import tempfile
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
WORK = Path("/tmp/tinyvg-eval-work")
SVG_BASE = WORK / "svg-sources"
SDK_DIR = WORK / "tinyvg-sdk"
RESULTS_DIR = Path(__file__).resolve().parent / "results"
SVGO_CONFIG = str(Path(__file__).resolve().parent / "svgo.config.js")

TVG_TEXT_BIN = str(SDK_DIR / "zig-out" / "bin" / "tvg-text")
SVG2TVGT_DLL = str(SDK_DIR / "src" / "tools" / "svg2tvgt" / "bin" / "Debug" / "net8.0" / "svg2tvgt.dll")

BENCHMARK_CSVS = {
    "zig":             "https://raw.githubusercontent.com/TinyVG/website/main/src/benchmark/zig.csv",
    "w3c":             "https://raw.githubusercontent.com/TinyVG/website/main/src/benchmark/w3c.csv",
    "material-design": "https://raw.githubusercontent.com/TinyVG/website/main/src/benchmark/material-design.csv",
    "papirus":         "https://raw.githubusercontent.com/TinyVG/website/main/src/benchmark/papirus.csv",
    "freesvg":         "https://raw.githubusercontent.com/TinyVG/website/main/src/benchmark/freesvg.csv",
}

SVG_DIRS = {
    "zig":             SVG_BASE / "zig-logo",
    "w3c":             SVG_BASE / "w3c",
    "material-design": SVG_BASE / "material-design",
    "papirus":         SVG_BASE / "papirus",
}

PARALLEL_WORKERS = 8  # Number of parallel conversion workers

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def run(cmd, **kwargs):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=120, **kwargs)


def file_size(path):
    return os.path.getsize(path) if os.path.isfile(path) else 0


def download_benchmark_csv(group):
    """Download and parse the official benchmark CSV, returning {basename: (svg_size, tvg_size)}."""
    url = BENCHMARK_CSVS[group]
    cache = WORK / "benchmark-csvs" / f"{group}.csv"
    cache.parent.mkdir(parents=True, exist_ok=True)
    if not cache.exists():
        subprocess.run(["curl", "-sL", url, "-o", str(cache)], check=True, timeout=30)
    rows = {}
    with open(cache) as f:
        reader = csv.reader(f, delimiter="\t")
        next(reader)  # skip header
        for row in reader:
            if len(row) >= 3:
                basename = os.path.basename(row[0])
                rows[basename] = (int(row[1]), int(row[2]))
    return rows


def convert_one_svg_worker(args):
    """Worker function for parallel conversion. Returns (basename, svg_size, tvg_bytes) or (basename, None, None)."""
    svg_path, basename = args
    tmpdir = tempfile.mkdtemp(prefix="tvg-conv-")
    try:
        opt_svg = os.path.join(tmpdir, "optimized.svg")
        tvgt = os.path.join(tmpdir, "output.tvgt")
        tvg = os.path.join(tmpdir, "output.tvg")

        # SVGO
        shutil.copy2(str(svg_path), opt_svg)
        r = run(["svgo", "--quiet", "--config", SVGO_CONFIG, opt_svg])
        if r.returncode != 0:
            return basename, None, None

        # svg2tvgt
        r = run(["dotnet", SVG2TVGT_DLL, opt_svg, "--output", tvgt])
        if r.returncode != 0 or not os.path.isfile(tvgt):
            return basename, None, None

        # tvg-text
        r = run([TVG_TEXT_BIN, tvgt, "--output", tvg])
        if r.returncode != 0 or not os.path.isfile(tvg):
            return basename, None, None

        svg_size = file_size(opt_svg)
        tvg_size = file_size(tvg)
        if svg_size == 0 or tvg_size == 0:
            return basename, None, None

        with open(tvg, "rb") as f:
            tvg_bytes = f.read()

        return basename, svg_size, tvg_bytes
    except Exception:
        return basename, None, None
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def compress_zstd(inpath, outpath, level=22, dict_path=None):
    cmd = ["zstd", f"-{level}", "--ultra", "-f", "-o", str(outpath), str(inpath)]
    if dict_path:
        cmd.insert(1, "-D")
        cmd.insert(2, str(dict_path))
    r = run(cmd)
    return file_size(outpath) if r.returncode == 0 else 0


def compress_brotli(inpath, outpath, quality=11):
    cmd = ["brotli", "-q", str(quality), "-f", "-o", str(outpath), str(inpath)]
    r = run(cmd)
    return file_size(outpath) if r.returncode == 0 else 0


def train_zstd_dict(tvg_files, dict_path, maxdict=65536):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        for tvg in tvg_files:
            f.write(str(tvg) + "\n")
        listfile = f.name
    try:
        cmd = ["zstd", "--train", f"--maxdict={maxdict}",
               f"--filelist={listfile}", "-o", str(dict_path)]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        return r.returncode == 0 and os.path.isfile(dict_path)
    finally:
        os.unlink(listfile)


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def process_group(group_name, benchmark_data, svg_dir, tvg_output_dir):
    """Process all files in a group using parallel workers."""
    tvg_output_dir.mkdir(parents=True, exist_ok=True)

    # Build work items: (svg_path, basename)
    work_items = []
    missing = 0
    # Build a case-insensitive index of the SVG dir
    svg_index = {}
    if svg_dir.exists():
        for f in svg_dir.iterdir():
            if f.suffix.lower() == ".svg":
                svg_index[f.name.lower()] = f

    for basename in benchmark_data:
        svg_path = svg_dir / basename
        if svg_path.exists():
            work_items.append((str(svg_path), basename))
        elif basename.lower() in svg_index:
            work_items.append((str(svg_index[basename.lower()]), basename))
        else:
            missing += 1

    total = len(work_items)
    if missing:
        print(f"  [{group_name}] {missing} files not found in SVG source dir")
    print(f"  [{group_name}] Converting {total} files with {PARALLEL_WORKERS} workers...")

    results = []
    converted = 0
    skipped = 0
    done = 0

    with ProcessPoolExecutor(max_workers=PARALLEL_WORKERS) as executor:
        futures = {executor.submit(convert_one_svg_worker, item): item for item in work_items}
        for future in as_completed(futures):
            done += 1
            basename, svg_size, tvg_bytes = future.result()
            if tvg_bytes is None:
                skipped += 1
            else:
                ref_svg_size, ref_tvg_size = benchmark_data[basename]
                tvg_path = tvg_output_dir / basename.replace(".svg", ".tvg")
                with open(tvg_path, "wb") as f:
                    f.write(tvg_bytes)
                results.append({
                    "group": group_name,
                    "file": basename,
                    "svg_size": ref_svg_size,
                    "tvg_size": len(tvg_bytes),
                    "ref_tvg_size": ref_tvg_size,
                    "tvg_path": str(tvg_path),
                })
                converted += 1

            if done % 100 == 0 or done == total:
                print(f"  [{group_name}] {done}/{total}  (converted: {converted}, skipped: {skipped})")

    print(f"  [{group_name}] Done: {converted} converted, {skipped} skipped out of {len(benchmark_data)}")
    return results


def load_phase2_cache():
    """Try to load cached Phase 1+2 results from a previous run."""
    cache_path = WORK / "phase2_cache.csv"
    if not cache_path.exists():
        return None
    results = []
    with open(cache_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            for k in ["svg_size", "tvg_size", "ref_tvg_size", "zstd_size", "brotli_size"]:
                row[k] = int(row[k])
            if os.path.isfile(row["tvg_path"]):
                results.append(row)
    return results if results else None


def save_phase2_cache(all_results):
    cache_path = WORK / "phase2_cache.csv"
    fieldnames = ["group", "file", "svg_size", "tvg_size", "ref_tvg_size",
                  "tvg_path", "zstd_size", "brotli_size"]
    with open(cache_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for rec in all_results:
            writer.writerow({k: rec[k] for k in fieldnames})


def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    tvg_dir = WORK / "tvg-files"
    tvg_dir.mkdir(parents=True, exist_ok=True)

    # Verify tools
    for tool in [TVG_TEXT_BIN, SVG2TVGT_DLL]:
        if not os.path.isfile(tool):
            print(f"ERROR: Tool not found: {tool}")
            print("Run setup.sh first.")
            sys.exit(1)
    for tool in ["svgo", "zstd", "brotli"]:
        if shutil.which(tool) is None:
            print(f"ERROR: {tool} not found in PATH. Run setup.sh first.")
            sys.exit(1)

    # Check for cached Phase 1+2 results
    cached = load_phase2_cache()
    if cached and "--no-cache" not in sys.argv:
        print(f"Loaded {len(cached)} cached results from Phase 1+2. Skipping to Phase 3.")
        print("(Use --no-cache to re-run conversion.)")
        all_results = cached
    else:
        # ---- Phase 1: Convert SVGs to TVGs ----
        print("=" * 60)
        print("Phase 1: Converting SVGs to TVG binary format")
        print("=" * 60)

        all_results = []
        for group_name, svg_dir in SVG_DIRS.items():
            print(f"\nProcessing group: {group_name}")
            if not svg_dir.exists():
                print(f"  WARNING: SVG directory not found: {svg_dir}")
                continue
            benchmark = download_benchmark_csv(group_name)
            group_tvg_dir = tvg_dir / group_name
            results = process_group(group_name, benchmark, svg_dir, group_tvg_dir)
            all_results.extend(results)

        if not all_results:
            print("ERROR: No files were converted. Check setup.")
            sys.exit(1)

        print(f"\nTotal files converted: {len(all_results)}")

        # ---- Phase 2: Compress each TVG ----
        print("\n" + "=" * 60)
        print("Phase 2: Compressing TVG files (zstd -22, brotli -q 11)")
        print("=" * 60)

        for i, rec in enumerate(all_results):
            tvg_path = rec["tvg_path"]
            zstd_path = tvg_path + ".zst"
            brotli_path = tvg_path + ".br"
            rec["zstd_size"] = compress_zstd(tvg_path, zstd_path)
            rec["brotli_size"] = compress_brotli(tvg_path, brotli_path)
            for p in [zstd_path, brotli_path]:
                if os.path.exists(p):
                    os.unlink(p)
            if (i + 1) % 200 == 0 or (i + 1) == len(all_results):
                print(f"  Compressed {i+1}/{len(all_results)}")

        # Save cache
        save_phase2_cache(all_results)

    # ---- Phase 3: Train zstd dictionary ----
    print("\n" + "=" * 60)
    print("Phase 3: Training zstd dictionary on all TVG files")
    print("=" * 60)

    tvg_files = [Path(r["tvg_path"]) for r in all_results]
    dict_path = RESULTS_DIR / "tvg_dict.zstd"

    if not train_zstd_dict(tvg_files, dict_path):
        print("WARNING: Dict training failed. Trying smaller size...")
        if not train_zstd_dict(tvg_files, dict_path, maxdict=32768):
            print("ERROR: Dictionary training failed entirely.")
            dict_path = None

    if dict_path and dict_path.exists():
        print(f"  Dictionary trained: {file_size(dict_path):,} bytes")
        print(f"  Re-compressing with dictionary...")
        for i, rec in enumerate(all_results):
            tvg_path = rec["tvg_path"]
            zstd_dict_out = tvg_path + ".zstd"
            rec["zstd_dict_size"] = compress_zstd(tvg_path, zstd_dict_out, dict_path=dict_path)
            if os.path.exists(zstd_dict_out):
                os.unlink(zstd_dict_out)
            if (i + 1) % 200 == 0 or (i + 1) == len(all_results):
                print(f"  Dict-compressed {i+1}/{len(all_results)}")
    else:
        for rec in all_results:
            rec["zstd_dict_size"] = 0

    # ---- Phase 4: Write CSV ----
    print("\n" + "=" * 60)
    print("Phase 4: Writing results")
    print("=" * 60)

    csv_path = RESULTS_DIR / "compression_data.csv"
    fieldnames = ["group", "file", "svg_size", "tvg_size", "ref_tvg_size",
                  "zstd_size", "brotli_size", "zstd_dict_size"]
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for rec in all_results:
            writer.writerow({k: rec[k] for k in fieldnames})
    print(f"  CSV: {csv_path}")

    # ---- Phase 5: Generate report ----
    generate_report(all_results, dict_path)
    print("\nDone! See results/ directory.")


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def pct(part, whole):
    if whole == 0:
        return "N/A"
    return f"{100.0 * part / whole:.1f}%"


def generate_report(all_results, dict_path):
    report_path = RESULTS_DIR / "report.md"

    groups = defaultdict(list)
    for rec in all_results:
        groups[rec["group"]].append(rec)

    lines = []
    lines.append("# TinyVG Compression Analysis Report")
    lines.append("")
    lines.append("This report extends the [TinyVG benchmark](https://tinyvg.tech/) by measuring")
    lines.append("the additional compression achievable on `.tvg` (TinyVG binary) files using")
    lines.append("modern general-purpose compressors.")
    lines.append("")
    lines.append("## Methodology")
    lines.append("")
    lines.append("- **Source SVGs**: Drawn from the same public datasets used by the official")
    lines.append("  TinyVG benchmark: Zig logos, W3C SVG samples, Material Design icons, and")
    lines.append("  Papirus icons. (5 FreeSVG.org files omitted as no longer retrievable from source.)")
    lines.append("- **SVG optimization**: Each SVG is first optimized with SVGO (multipass, precision 3)")
    lines.append("  matching the original benchmark pipeline. SVG sizes in the tables below are the")
    lines.append("  SVGO-optimized sizes from the official benchmark data.")
    lines.append("- **SVG -> TVG conversion**: `svg2tvgt` (SVG to TinyVG text) then `tvg-text`")
    lines.append("  (TinyVG text to binary), from the TinyVG SDK.")
    lines.append("- **Compression**:")
    lines.append("  - **zstd -22**: `zstd --ultra -22` (maximum compression level)")
    lines.append("  - **brotli -11**: `brotli -q 11` (maximum quality)")
    lines.append("  - **zstd -22 +dict**: A custom dictionary trained on all TVG files via")
    lines.append("    `zstd --train --maxdict=65536`, then compressed with `zstd --ultra -22 -D dict`")
    lines.append("")
    lines.append("All sizes are in bytes. \"% of SVG\" = compressed size / SVGO-optimized SVG size.")
    lines.append("\"% of TVG\" = compressed size / uncompressed TVG size.")
    lines.append("")

    if dict_path and dict_path.exists():
        lines.append(f"**Trained zstd dictionary size**: {file_size(dict_path):,} bytes")
        lines.append("")

    # ---- Overall ----
    lines.append("## Overall Summary")
    lines.append("")

    total_svg = sum(r["svg_size"] for r in all_results)
    total_tvg = sum(r["tvg_size"] for r in all_results)
    total_zstd = sum(r["zstd_size"] for r in all_results)
    total_brotli = sum(r["brotli_size"] for r in all_results)
    total_zstd_dict = sum(r["zstd_dict_size"] for r in all_results)
    n = len(all_results)

    lines.append(f"| Metric | Total bytes | % of SVG | % of TVG |")
    lines.append(f"|--------|------------|----------|----------|")
    lines.append(f"| **SVG (SVGO-optimized)** | {total_svg:,} | 100.0% | - |")
    lines.append(f"| **TVG (uncompressed)** | {total_tvg:,} | {pct(total_tvg, total_svg)} | 100.0% |")
    lines.append(f"| **TVG + zstd -22** | {total_zstd:,} | {pct(total_zstd, total_svg)} | {pct(total_zstd, total_tvg)} |")
    lines.append(f"| **TVG + brotli -11** | {total_brotli:,} | {pct(total_brotli, total_svg)} | {pct(total_brotli, total_tvg)} |")
    lines.append(f"| **TVG + zstd -22 +dict** | {total_zstd_dict:,} | {pct(total_zstd_dict, total_svg)} | {pct(total_zstd_dict, total_tvg)} |")
    lines.append("")
    lines.append(f"*{n} files analyzed across {len(groups)} dataset groups.*")
    lines.append("")

    # Median per-file ratios
    def median(vals):
        s = sorted(vals)
        n = len(s)
        if n == 0:
            return 0
        return s[n // 2] if n % 2 == 1 else (s[n//2 - 1] + s[n//2]) / 2

    tvg_pcts = [r["tvg_size"] / r["svg_size"] * 100 for r in all_results if r["svg_size"] > 0]
    zstd_pcts = [r["zstd_size"] / r["svg_size"] * 100 for r in all_results if r["svg_size"] > 0]
    brotli_pcts = [r["brotli_size"] / r["svg_size"] * 100 for r in all_results if r["svg_size"] > 0]
    dict_pcts = [r["zstd_dict_size"] / r["svg_size"] * 100 for r in all_results if r["svg_size"] > 0]

    lines.append("### Median per-file compression ratios (% of SVG)")
    lines.append("")
    lines.append(f"| Metric | Median % of SVG |")
    lines.append(f"|--------|----------------|")
    lines.append(f"| TVG | {median(tvg_pcts):.1f}% |")
    lines.append(f"| TVG + zstd -22 | {median(zstd_pcts):.1f}% |")
    lines.append(f"| TVG + brotli -11 | {median(brotli_pcts):.1f}% |")
    lines.append(f"| TVG + zstd -22 +dict | {median(dict_pcts):.1f}% |")
    lines.append("")

    # ---- Per-group ----
    lines.append("## Per-Group Summary")
    lines.append("")

    group_order = ["zig", "w3c", "material-design", "papirus"]
    for gname in group_order:
        if gname not in groups:
            continue
        grecs = groups[gname]
        g_svg = sum(r["svg_size"] for r in grecs)
        g_tvg = sum(r["tvg_size"] for r in grecs)
        g_zstd = sum(r["zstd_size"] for r in grecs)
        g_brotli = sum(r["brotli_size"] for r in grecs)
        g_zstd_dict = sum(r["zstd_dict_size"] for r in grecs)

        lines.append(f"### {gname} ({len(grecs)} files)")
        lines.append("")
        lines.append(f"| Metric | Total bytes | % of SVG | % of TVG |")
        lines.append(f"|--------|------------|----------|----------|")
        lines.append(f"| SVG (optimized) | {g_svg:,} | 100.0% | - |")
        lines.append(f"| TVG | {g_tvg:,} | {pct(g_tvg, g_svg)} | 100.0% |")
        lines.append(f"| TVG + zstd -22 | {g_zstd:,} | {pct(g_zstd, g_svg)} | {pct(g_zstd, g_tvg)} |")
        lines.append(f"| TVG + brotli -11 | {g_brotli:,} | {pct(g_brotli, g_svg)} | {pct(g_brotli, g_tvg)} |")
        lines.append(f"| TVG + zstd -22 +dict | {g_zstd_dict:,} | {pct(g_zstd_dict, g_svg)} | {pct(g_zstd_dict, g_tvg)} |")
        lines.append("")

    # ---- Per-file detail ----
    lines.append("## Per-File Details")
    lines.append("")
    lines.append("Full per-file data is in `compression_data.csv`. Below are highlights per group.")
    lines.append("")

    for gname in group_order:
        if gname not in groups:
            continue
        grecs = sorted(groups[gname], key=lambda r: r["svg_size"], reverse=True)

        lines.append(f"### {gname}")
        lines.append("")
        lines.append("| File | SVG | TVG | zstd | brotli | zstd+dict | TVG/SVG | zstd/SVG | brotli/SVG | dict/SVG |")
        lines.append("|------|-----|-----|------|--------|-----------|---------|----------|------------|----------|")

        if len(grecs) <= 30:
            show = grecs
        else:
            show = grecs[:10] + [None] + grecs[-10:]

        for rec in show:
            if rec is None:
                lines.append(f"| ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |")
                continue
            lines.append(
                f"| {rec['file'][:45]} "
                f"| {rec['svg_size']:,} "
                f"| {rec['tvg_size']:,} "
                f"| {rec['zstd_size']:,} "
                f"| {rec['brotli_size']:,} "
                f"| {rec['zstd_dict_size']:,} "
                f"| {pct(rec['tvg_size'], rec['svg_size'])} "
                f"| {pct(rec['zstd_size'], rec['svg_size'])} "
                f"| {pct(rec['brotli_size'], rec['svg_size'])} "
                f"| {pct(rec['zstd_dict_size'], rec['svg_size'])} |"
            )
        lines.append("")

    # ---- Best overall compression ----
    lines.append("## Top 20 Best Compression Ratios (zstd+dict as % of SVG)")
    lines.append("")
    sorted_by_ratio = sorted(all_results,
                             key=lambda r: r["zstd_dict_size"] / r["svg_size"] if r["svg_size"] > 0 else 1)
    lines.append("| File | Group | SVG | TVG | zstd+dict | % of SVG |")
    lines.append("|------|-------|-----|-----|-----------|----------|")
    for rec in sorted_by_ratio[:20]:
        lines.append(
            f"| {rec['file'][:45]} | {rec['group']} "
            f"| {rec['svg_size']:,} | {rec['tvg_size']:,} "
            f"| {rec['zstd_dict_size']:,} | {pct(rec['zstd_dict_size'], rec['svg_size'])} |"
        )
    lines.append("")

    # ---- Worst compression ----
    lines.append("## Bottom 20 Worst Compression Ratios (zstd+dict as % of SVG)")
    lines.append("")
    lines.append("| File | Group | SVG | TVG | zstd+dict | % of SVG |")
    lines.append("|------|-------|-----|-----|-----------|----------|")
    for rec in sorted_by_ratio[-20:]:
        lines.append(
            f"| {rec['file'][:45]} | {rec['group']} "
            f"| {rec['svg_size']:,} | {rec['tvg_size']:,} "
            f"| {rec['zstd_dict_size']:,} | {pct(rec['zstd_dict_size'], rec['svg_size'])} |"
        )
    lines.append("")

    with open(report_path, "w") as f:
        f.write("\n".join(lines))
    print(f"  Report: {report_path}")


if __name__ == "__main__":
    main()
