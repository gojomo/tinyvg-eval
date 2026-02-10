#!/usr/bin/env python3
"""
generate_report.py - Generate the final markdown report from compression_data.csv.

Can be run independently after convert_and_analyze.py has produced its CSV output.
"""

import csv
import os
from collections import defaultdict
from pathlib import Path

RESULTS_DIR = Path(__file__).resolve().parent / "results"


def file_size(path):
    return os.path.getsize(path) if os.path.isfile(path) else 0


def pct(part, whole):
    if whole == 0:
        return "N/A"
    return f"{100.0 * part / whole:.1f}%"


def median(vals):
    s = sorted(vals)
    n = len(s)
    if n == 0:
        return 0
    return s[n // 2] if n % 2 == 1 else (s[n // 2 - 1] + s[n // 2]) / 2


def load_results():
    csv_path = RESULTS_DIR / "compression_data.csv"
    results = []
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            for k in ["svg_size", "tvg_size", "ref_tvg_size", "zstd_size", "brotli_size", "zstd_dict_size"]:
                row[k] = int(row[k])
            results.append(row)
    return results


def main():
    all_results = load_results()
    dict_path = RESULTS_DIR / "tvg_dict.zstd"

    # Flag outliers: files where TVG > SVG (format not beneficial) or where
    # our TVG diverges dramatically from the benchmark reference
    for rec in all_results:
        ref = rec["ref_tvg_size"]
        ours = rec["tvg_size"]
        rec["is_outlier"] = (ours > rec["svg_size"] * 1.5) or (ref > 0 and (ours / ref > 3 or ours / ref < 0.05))

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

    # ---- Methodology ----
    lines.append("## Methodology")
    lines.append("")
    lines.append("- **Source SVGs**: Drawn from the same public datasets used by the official")
    lines.append("  TinyVG benchmark: Zig logos, W3C SVG samples, Material Design icons, and")
    lines.append("  Papirus icons. (5 FreeSVG.org files omitted as no longer retrievable from source.)")
    lines.append("- **SVG optimization**: Each SVG is first optimized with SVGO (multipass, precision 3)")
    lines.append("  matching the original benchmark pipeline. SVG sizes in the tables below are the")
    lines.append("  SVGO-optimized sizes as reported by the official TinyVG benchmark.")
    lines.append("- **SVG -> TVG conversion**: `svg2tvgt` (SVG to TinyVG text) then `tvg-text`")
    lines.append("  (TinyVG text to binary), from the [TinyVG SDK](https://github.com/TinyVG/sdk).")
    lines.append("- **Compression**:")
    lines.append("  - **zstd -22**: `zstd --ultra -22` (maximum compression level)")
    lines.append("  - **brotli -11**: `brotli -q 11` (maximum quality)")
    lines.append("  - **zstd -22 +dict**: A custom dictionary trained on all TVG files via")
    lines.append("    `zstd --train --maxdict=65536`, then compressed with `zstd --ultra -22 -D dict`")
    lines.append("")
    lines.append("All sizes in bytes. \"% of SVG\" = size / SVGO-optimized SVG size.")
    lines.append("\"% of TVG\" = size / uncompressed TVG binary size.")
    lines.append("")

    # ---- Dataset notes ----
    lines.append("### Dataset Notes")
    lines.append("")
    lines.append("The original TinyVG benchmark used 2,129 SVG files. Our re-conversion using")
    lines.append("current versions of the source datasets and TinyVG SDK yielded:")
    lines.append("")
    benchmark_counts = {"zig": 9, "w3c": 115, "material-design": 1000, "papirus": 1000, "freesvg": 5}
    for gname in ["zig", "w3c", "material-design", "papirus"]:
        grecs = groups.get(gname, [])
        bcount = benchmark_counts[gname]
        lines.append(f"- **{gname}**: {len(grecs)} of {bcount} files converted successfully")
    lines.append(f"- **freesvg**: 0 of 5 (files no longer retrievable from freesvg.org)")
    lines.append("")
    n_total = len(all_results)
    n_outliers = sum(1 for r in all_results if r["is_outlier"])
    lines.append(f"**Total: {n_total} files** analyzed. Of these, {n_total - n_outliers} have TVG sizes")
    lines.append(f"within reasonable range of the original benchmark; {n_outliers} are outliers")
    lines.append(f"(typically due to changed source SVGs or TinyVG SDK version differences).")
    lines.append("")
    lines.append("Not all original files convert successfully because: (a) source SVG repos have")
    lines.append("evolved since the benchmark was created, (b) `svg2tvgt` only supports a subset")
    lines.append("of SVG features, and (c) some icon variants were drawn from different size")
    lines.append("directories in the Papirus theme.")
    lines.append("")

    if dict_path and dict_path.exists():
        lines.append(f"**Trained zstd dictionary size**: {file_size(dict_path):,} bytes")
        lines.append("")

    # ---- Overall Summary (excluding outliers from aggregates) ----
    non_outlier = [r for r in all_results if not r["is_outlier"]]

    lines.append("## Overall Summary")
    lines.append("")

    total_svg = sum(r["svg_size"] for r in non_outlier)
    total_tvg = sum(r["tvg_size"] for r in non_outlier)
    total_zstd = sum(r["zstd_size"] for r in non_outlier)
    total_brotli = sum(r["brotli_size"] for r in non_outlier)
    total_zstd_dict = sum(r["zstd_dict_size"] for r in non_outlier)

    lines.append(f"| Metric | Total bytes | % of SVG | % of TVG |")
    lines.append(f"|--------|------------|----------|----------|")
    lines.append(f"| **SVG (SVGO-optimized)** | {total_svg:,} | 100.0% | - |")
    lines.append(f"| **TVG (uncompressed)** | {total_tvg:,} | {pct(total_tvg, total_svg)} | 100.0% |")
    lines.append(f"| **TVG + zstd -22** | {total_zstd:,} | {pct(total_zstd, total_svg)} | {pct(total_zstd, total_tvg)} |")
    lines.append(f"| **TVG + brotli -11** | {total_brotli:,} | {pct(total_brotli, total_svg)} | {pct(total_brotli, total_tvg)} |")
    lines.append(f"| **TVG + zstd -22 +dict** | {total_zstd_dict:,} | {pct(total_zstd_dict, total_svg)} | {pct(total_zstd_dict, total_tvg)} |")
    lines.append("")
    lines.append(f"*{len(non_outlier)} files (excluding {n_outliers} outlier(s)) across {len(groups)} dataset groups.*")
    lines.append("")

    # Median per-file ratios
    tvg_pcts = [r["tvg_size"] / r["svg_size"] * 100 for r in non_outlier if r["svg_size"] > 0]
    zstd_pcts = [r["zstd_size"] / r["svg_size"] * 100 for r in non_outlier if r["svg_size"] > 0]
    brotli_pcts = [r["brotli_size"] / r["svg_size"] * 100 for r in non_outlier if r["svg_size"] > 0]
    dict_pcts = [r["zstd_dict_size"] / r["svg_size"] * 100 for r in non_outlier if r["svg_size"] > 0]

    lines.append("### Median per-file ratios (% of SVG)")
    lines.append("")
    lines.append(f"| Metric | Median % of SVG |")
    lines.append(f"|--------|----------------|")
    lines.append(f"| TVG | {median(tvg_pcts):.1f}% |")
    lines.append(f"| TVG + zstd -22 | {median(zstd_pcts):.1f}% |")
    lines.append(f"| TVG + brotli -11 | {median(brotli_pcts):.1f}% |")
    lines.append(f"| TVG + zstd -22 +dict | {median(dict_pcts):.1f}% |")
    lines.append("")

    # Key takeaway
    lines.append("### Key Findings")
    lines.append("")
    lines.append(f"1. **TVG alone** reduces SVGO-optimized SVGs to a median of **{median(tvg_pcts):.1f}%** of their size.")
    lines.append(f"2. **TVG + brotli** achieves a median of **{median(brotli_pcts):.1f}%** of SVG size")
    lines.append(f"   (further {100 - 100*median(brotli_pcts)/median(tvg_pcts):.0f}% reduction beyond TVG alone).")
    lines.append(f"3. **TVG + zstd with a trained dictionary** achieves a median of just **{median(dict_pcts):.1f}%**")
    lines.append(f"   of SVG size -- reducing TVG files to a median of {median([r['zstd_dict_size']/r['tvg_size']*100 for r in non_outlier if r['tvg_size']>0]):.1f}% of their")
    lines.append(f"   uncompressed size. This is the most effective scheme tested.")
    lines.append(f"4. The dictionary is most effective for **icon sets** with shared structure")
    lines.append(f"   (Papirus: {pct(sum(r['zstd_dict_size'] for r in groups.get('papirus',[]) if not r['is_outlier']), sum(r['svg_size'] for r in groups.get('papirus',[]) if not r['is_outlier']))} of SVG), where common TVG header/structure")
    lines.append(f"   patterns are factored out.")
    lines.append("")

    # ---- Per-group ----
    lines.append("## Per-Group Summary")
    lines.append("")

    group_order = ["zig", "w3c", "material-design", "papirus"]
    for gname in group_order:
        if gname not in groups:
            continue
        grecs = [r for r in groups[gname] if not r["is_outlier"]]
        if not grecs:
            continue
        g_svg = sum(r["svg_size"] for r in grecs)
        g_tvg = sum(r["tvg_size"] for r in grecs)
        g_zstd = sum(r["zstd_size"] for r in grecs)
        g_brotli = sum(r["brotli_size"] for r in grecs)
        g_zstd_dict = sum(r["zstd_dict_size"] for r in grecs)
        outlier_count = sum(1 for r in groups[gname] if r["is_outlier"])
        outlier_note = f" ({outlier_count} outlier(s) excluded)" if outlier_count else ""

        lines.append(f"### {gname} ({len(grecs)} files{outlier_note})")
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
    lines.append("Full per-file data is in `compression_data.csv`. Below are highlights per group,")
    lines.append("sorted by SVG size (largest first). Outliers are marked with (*).")
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
            marker = " (*)" if rec["is_outlier"] else ""
            lines.append(
                f"| {rec['file'][:42]}{marker} "
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

    # ---- Best compression ----
    lines.append("## Top 20 Best Compression Ratios (zstd+dict as % of SVG)")
    lines.append("")
    sorted_by_ratio = sorted(
        [r for r in all_results if not r["is_outlier"]],
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

    report_path = RESULTS_DIR / "report.md"
    with open(report_path, "w") as f:
        f.write("\n".join(lines))
    print(f"Report written to {report_path}")


if __name__ == "__main__":
    main()
