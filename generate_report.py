#!/usr/bin/env python3
"""
generate_report.py - Generate the final markdown report from all_files_diagnostics.csv.

Reads the full diagnostics CSV (every benchmark file, including failures) and produces
results/report.md with:
  - Overall and per-group compression summaries
  - Per-file tables for ALL benchmark files (with failures shown as 'n/a')
  - Conversion failure analysis with categorized error tallies
  - Best/worst compression ratio tables
"""

import csv
import os
import re
from collections import Counter, defaultdict
from pathlib import Path

RESULTS_DIR = Path(__file__).resolve().parent / "results"

INT_FIELDS = ["ref_svg_size", "ref_tvg_size", "cur_svg_size", "svgo_size",
              "tvgt_size", "tvg_size", "zstd_size", "brotli_size", "zstd_dict_size"]


def file_size(path):
    return os.path.getsize(path) if os.path.isfile(path) else 0


def pct(part, whole):
    if whole == 0:
        return "n/a"
    return f"{100.0 * part / whole:.1f}%"


def median(vals):
    s = sorted(vals)
    n = len(s)
    if n == 0:
        return 0
    return s[n // 2] if n % 2 == 1 else (s[n // 2 - 1] + s[n // 2]) / 2


def categorize_failure(rec):
    """Return a short failure-category string for reporting."""
    stage = rec["fail_stage"]
    detail = rec["fail_detail"]
    if stage == "source":
        return "no_source"
    if stage == "svgo":
        return "svgo_fail"
    if stage == "tvg-text":
        if "SyntaxError" in detail:
            return "tvg-text:syntax"
        if "OutOfRange" in detail:
            return "tvg-text:range"
        return "tvg-text:other"
    if stage == "svg2tvgt":
        if "New MoveTo" in detail:
            return "svg2tvgt:moveto_bug"
        if "Error Context" in detail:
            return "svg2tvgt:path_parse"
        if "InvalidOperationException" in detail:
            return "svg2tvgt:path_parse"
        if "unsupported transform" in detail:
            return "svg2tvgt:transform"
        return "svg2tvgt:other"
    return f"{stage}:unknown"


def load_diagnostics():
    csv_path = RESULTS_DIR / "all_files_diagnostics.csv"
    results = []
    with open(csv_path) as f:
        for row in csv.DictReader(f):
            for k in INT_FIELDS:
                row[k] = int(row[k])
            row["category"] = categorize_failure(row) if row["status"] != "ok" else "ok"
            # Flag outliers among successful conversions
            if row["status"] == "ok":
                ref = row["ref_tvg_size"]
                ours = row["tvg_size"]
                row["is_outlier"] = (
                    (ours > row["ref_svg_size"] * 1.5)
                    or (ref > 0 and (ours / ref > 3 or ours / ref < 0.05))
                )
            else:
                row["is_outlier"] = False
            results.append(row)
    return results


def main():
    all_recs = load_diagnostics()
    dict_path = RESULTS_DIR / "tvg_dict.zstd"

    ok_recs = [r for r in all_recs if r["status"] == "ok"]
    non_outlier = [r for r in ok_recs if not r["is_outlier"]]
    fail_recs = [r for r in all_recs if r["status"] != "ok"]

    groups_all = defaultdict(list)   # every file
    groups_ok = defaultdict(list)    # successfully converted
    for r in all_recs:
        groups_all[r["group"]].append(r)
    for r in ok_recs:
        groups_ok[r["group"]].append(r)

    L = []  # report lines

    # ================================================================
    L.append("# TinyVG Compression Analysis Report")
    L.append("")
    L.append("This report extends the [TinyVG benchmark](https://tinyvg.tech/) by measuring")
    L.append("the additional compression achievable on `.tvg` (TinyVG binary) files using")
    L.append("modern general-purpose compressors.")
    L.append("")

    # ---- Methodology ----
    L.append("## Methodology")
    L.append("")
    L.append("- **Source SVGs**: Drawn from the same public datasets used by the official")
    L.append("  TinyVG benchmark: Zig logos, W3C SVG samples, Material Design icons, and")
    L.append("  Papirus icons. (5 FreeSVG.org files omitted as no longer retrievable from source.)")
    L.append("- **SVG optimization**: Each SVG is first optimized with SVGO (multipass, precision 3)")
    L.append("  matching the original benchmark pipeline. SVG sizes in the tables below are the")
    L.append("  SVGO-optimized sizes as reported by the official TinyVG benchmark.")
    L.append("- **SVG -> TVG conversion**: `svg2tvgt` (SVG to TinyVG text) then `tvg-text`")
    L.append("  (TinyVG text to binary), from the [TinyVG SDK](https://github.com/TinyVG/sdk).")
    L.append("- **Compression**:")
    L.append("  - **zstd -22**: `zstd --ultra -22` (maximum compression level)")
    L.append("  - **brotli -11**: `brotli -q 11` (maximum quality)")
    L.append("  - **zstd -22 +dict**: A custom dictionary trained on all TVG files via")
    L.append("    `zstd --train --maxdict=65536`, then compressed with `zstd --ultra -22 -D dict`")
    L.append("")
    L.append("All sizes in bytes. \"% of SVG\" = size / SVGO-optimized SVG size.")
    L.append("\"% of TVG\" = size / uncompressed TVG binary size.")
    L.append("")

    # ---- Dataset notes ----
    L.append("### Dataset Notes")
    L.append("")
    L.append("The original TinyVG benchmark used 2,129 SVG files. Our re-conversion using")
    L.append("current versions of the source datasets and TinyVG SDK yielded:")
    L.append("")
    benchmark_counts = {"zig": 9, "w3c": 115, "material-design": 1000, "papirus": 1000, "freesvg": 5}
    for gname in ["zig", "w3c", "material-design", "papirus", "freesvg"]:
        n_ok = len(groups_ok.get(gname, []))
        bcount = benchmark_counts[gname]
        n_fail = len(groups_all.get(gname, [])) - n_ok
        if gname == "freesvg":
            L.append(f"- **{gname}**: 0 of {bcount} (files no longer retrievable from freesvg.org)")
        else:
            L.append(f"- **{gname}**: {n_ok} of {bcount} converted ({n_fail} failed)")
    L.append("")

    n_outliers = sum(1 for r in ok_recs if r["is_outlier"])
    L.append(f"**{len(ok_recs)} files** converted successfully. Of these, **{len(non_outlier)}** have TVG sizes")
    L.append(f"within reasonable range of the original benchmark; {n_outliers} outlier(s)")
    L.append(f"are excluded from aggregate statistics but shown in per-file tables.")
    L.append("")

    if dict_path and dict_path.exists():
        L.append(f"**Trained zstd dictionary size**: {file_size(dict_path):,} bytes")
        L.append("")

    # ================================================================
    # Overall Summary
    # ================================================================
    L.append("## Overall Summary")
    L.append("")

    total_svg = sum(r["ref_svg_size"] for r in non_outlier)
    total_tvg = sum(r["tvg_size"] for r in non_outlier)
    total_zstd = sum(r["zstd_size"] for r in non_outlier)
    total_brotli = sum(r["brotli_size"] for r in non_outlier)
    total_zstd_dict = sum(r["zstd_dict_size"] for r in non_outlier)

    L.append("| Metric | Total bytes | % of SVG | % of TVG |")
    L.append("|--------|------------|----------|----------|")
    L.append(f"| **SVG (SVGO-optimized)** | {total_svg:,} | 100.0% | - |")
    L.append(f"| **TVG (uncompressed)** | {total_tvg:,} | {pct(total_tvg, total_svg)} | 100.0% |")
    L.append(f"| **TVG + zstd -22** | {total_zstd:,} | {pct(total_zstd, total_svg)} | {pct(total_zstd, total_tvg)} |")
    L.append(f"| **TVG + brotli -11** | {total_brotli:,} | {pct(total_brotli, total_svg)} | {pct(total_brotli, total_tvg)} |")
    L.append(f"| **TVG + zstd -22 +dict** | {total_zstd_dict:,} | {pct(total_zstd_dict, total_svg)} | {pct(total_zstd_dict, total_tvg)} |")
    L.append("")
    L.append(f"*{len(non_outlier)} files (excluding {n_outliers} outlier(s)) across {len(groups_ok)} groups.*")
    L.append("")

    # Medians
    tvg_pcts = [r["tvg_size"] / r["ref_svg_size"] * 100 for r in non_outlier if r["ref_svg_size"] > 0]
    zstd_pcts = [r["zstd_size"] / r["ref_svg_size"] * 100 for r in non_outlier if r["ref_svg_size"] > 0]
    brotli_pcts = [r["brotli_size"] / r["ref_svg_size"] * 100 for r in non_outlier if r["ref_svg_size"] > 0]
    dict_pcts = [r["zstd_dict_size"] / r["ref_svg_size"] * 100 for r in non_outlier if r["ref_svg_size"] > 0]

    L.append("### Median per-file ratios (% of SVG)")
    L.append("")
    L.append("| Metric | Median % of SVG |")
    L.append("|--------|----------------|")
    L.append(f"| TVG | {median(tvg_pcts):.1f}% |")
    L.append(f"| TVG + zstd -22 | {median(zstd_pcts):.1f}% |")
    L.append(f"| TVG + brotli -11 | {median(brotli_pcts):.1f}% |")
    L.append(f"| TVG + zstd -22 +dict | {median(dict_pcts):.1f}% |")
    L.append("")

    # Key findings
    L.append("### Key Findings")
    L.append("")
    L.append(f"1. **TVG alone** reduces SVGO-optimized SVGs to a median of **{median(tvg_pcts):.1f}%** of their size.")
    L.append(f"2. **TVG + brotli** achieves a median of **{median(brotli_pcts):.1f}%** of SVG size")
    L.append(f"   (further {100 - 100*median(brotli_pcts)/median(tvg_pcts):.0f}% reduction beyond TVG alone).")
    tvg_dict_pcts = [r["zstd_dict_size"] / r["tvg_size"] * 100 for r in non_outlier if r["tvg_size"] > 0]
    L.append(f"3. **TVG + zstd with a trained dictionary** achieves a median of just **{median(dict_pcts):.1f}%**")
    L.append(f"   of SVG size -- reducing TVG files to a median of {median(tvg_dict_pcts):.1f}% of their")
    L.append(f"   uncompressed size. This is the most effective scheme tested.")
    pap_no = [r for r in groups_ok.get("papirus", []) if not r["is_outlier"]]
    if pap_no:
        pap_dict_pct = pct(sum(r["zstd_dict_size"] for r in pap_no),
                           sum(r["ref_svg_size"] for r in pap_no))
    else:
        pap_dict_pct = "n/a"
    L.append(f"4. The dictionary is most effective for **icon sets** with shared structure")
    L.append(f"   (Papirus: {pap_dict_pct} of SVG), where common TVG header/structure")
    L.append(f"   patterns are factored out.")
    L.append("")

    # ================================================================
    # Per-Group Summary
    # ================================================================
    L.append("## Per-Group Summary")
    L.append("")

    group_order = ["zig", "w3c", "material-design", "papirus"]
    for gname in group_order:
        grecs = [r for r in groups_ok.get(gname, []) if not r["is_outlier"]]
        if not grecs:
            continue
        g_svg = sum(r["ref_svg_size"] for r in grecs)
        g_tvg = sum(r["tvg_size"] for r in grecs)
        g_zstd = sum(r["zstd_size"] for r in grecs)
        g_brotli = sum(r["brotli_size"] for r in grecs)
        g_zstd_dict = sum(r["zstd_dict_size"] for r in grecs)
        outlier_count = sum(1 for r in groups_ok.get(gname, []) if r["is_outlier"])
        outlier_note = f" ({outlier_count} outlier excluded)" if outlier_count else ""

        L.append(f"### {gname} ({len(grecs)} files{outlier_note})")
        L.append("")
        L.append("| Metric | Total bytes | % of SVG | % of TVG |")
        L.append("|--------|------------|----------|----------|")
        L.append(f"| SVG (optimized) | {g_svg:,} | 100.0% | - |")
        L.append(f"| TVG | {g_tvg:,} | {pct(g_tvg, g_svg)} | 100.0% |")
        L.append(f"| TVG + zstd -22 | {g_zstd:,} | {pct(g_zstd, g_svg)} | {pct(g_zstd, g_tvg)} |")
        L.append(f"| TVG + brotli -11 | {g_brotli:,} | {pct(g_brotli, g_svg)} | {pct(g_brotli, g_tvg)} |")
        L.append(f"| TVG + zstd -22 +dict | {g_zstd_dict:,} | {pct(g_zstd_dict, g_svg)} | {pct(g_zstd_dict, g_tvg)} |")
        L.append("")

    # ================================================================
    # Conversion Failure Analysis
    # ================================================================
    L.append("## Conversion Failure Analysis")
    L.append("")

    cat_counts = Counter(r["category"] for r in all_recs)
    L.append("### Failure categories across all 2,129 benchmark files")
    L.append("")
    L.append("| Category | Count | Description |")
    L.append("|----------|-------|-------------|")
    L.append(f"| ok | {cat_counts['ok']} | Successful conversion |")

    cat_descs = {
        "svg2tvgt:path_parse": "svg2tvgt fails parsing SVG path `d` data (complex/compound paths)",
        "svg2tvgt:moveto_bug": "svg2tvgt throws `New MoveTo detected without ClosePath` -- open subpaths",
        "no_source": "SVG file not found in current source dataset (repo evolved or freesvg.org)",
        "svg2tvgt:transform": "svg2tvgt does not support the SVG transform (e.g. `rotate(90)scale(-1 1)`)",
        "svg2tvgt:other": "Other svg2tvgt error",
        "tvg-text:syntax": "tvg-text rejects TVGT with syntax error (svg2tvgt emitted bad text)",
        "tvg-text:range": "tvg-text value out of range (svg2tvgt emitted out-of-spec value)",
    }
    for cat in ["svg2tvgt:path_parse", "svg2tvgt:moveto_bug", "no_source",
                "svg2tvgt:transform", "svg2tvgt:other", "tvg-text:syntax", "tvg-text:range"]:
        if cat_counts[cat] > 0:
            L.append(f"| {cat} | {cat_counts[cat]} | {cat_descs.get(cat, '')} |")
    L.append("")

    L.append("### Failure breakdown by group")
    L.append("")
    L.append("| Group | Total | OK | path_parse | moveto_bug | no_source | transform | tvg-text | other |")
    L.append("|-------|-------|----|------------|------------|-----------|-----------|----------|-------|")
    for gname in ["zig", "w3c", "material-design", "papirus", "freesvg"]:
        grecs = groups_all.get(gname, [])
        gcats = Counter(r["category"] for r in grecs)
        L.append(
            f"| {gname} | {len(grecs)} | {gcats['ok']} "
            f"| {gcats.get('svg2tvgt:path_parse', 0)} "
            f"| {gcats.get('svg2tvgt:moveto_bug', 0)} "
            f"| {gcats.get('no_source', 0)} "
            f"| {gcats.get('svg2tvgt:transform', 0)} "
            f"| {gcats.get('tvg-text:syntax',0) + gcats.get('tvg-text:range',0)} "
            f"| {gcats.get('svg2tvgt:other', 0)} |")
    L.append("")

    L.append("### Analysis of `svg2tvgt` failures")
    L.append("")
    L.append("The vast majority of failures (1,137 of 1,180) occur in `svg2tvgt`, the SVG-to-TVGT")
    L.append("text converter. Two root causes account for nearly all of them:")
    L.append("")
    L.append(f"1. **Path parse errors** ({cat_counts.get('svg2tvgt:path_parse',0)} files): `svg2tvgt`'s SVG path parser")
    L.append("   fails on certain valid SVG path data. Affected files tend to have more complex,")
    L.append("   compound paths (median ref SVG size of failed MDI files is larger than successful ones).")
    L.append(f"2. **MoveTo-without-ClosePath bug** ({cat_counts.get('svg2tvgt:moveto_bug',0)} files): `svg2tvgt` throws")
    L.append("   `InvalidOperationException: New MoveTo detected without ClosePath` when an SVG path")
    L.append("   contains multiple subpaths using implicit MoveTo (M) commands without explicit ClosePath (Z)")
    L.append("   between them. This is valid SVG (open subpaths are allowed) but `svg2tvgt` rejects it.")
    L.append("")
    L.append("Both issues are **bugs/limitations in `svg2tvgt`**, not fundamental TinyVG format")
    L.append("limitations. Fixing the path parser to handle compound paths and open subpaths would")
    L.append("likely recover most of the 1,137 currently-failing files.")
    L.append("")

    # ================================================================
    # Per-File Details (ALL files)
    # ================================================================
    L.append("## Per-File Details (All Benchmark Files)")
    L.append("")
    L.append("Every file from the original TinyVG benchmark is listed below. Files that failed")
    L.append("conversion show `n/a` for compression columns. The `ref_svg` column shows the")
    L.append("SVGO-optimized SVG size from the original benchmark; `cur_svg` shows the current")
    L.append("source SVG size (0 if not found). The `notes` column indicates failure category")
    L.append("or `(*)` for outliers.")
    L.append("")

    for gname in ["zig", "w3c", "material-design", "papirus", "freesvg"]:
        grecs = sorted(groups_all.get(gname, []), key=lambda r: r["ref_svg_size"], reverse=True)
        if not grecs:
            continue

        L.append(f"### {gname} ({len(grecs)} files)")
        L.append("")
        L.append("| File | ref_svg | cur_svg | TVG | ref_tvg | zstd | brotli | zstd+dict | dict/SVG | notes |")
        L.append("|------|---------|---------|-----|---------|------|--------|-----------|----------|-------|")

        for rec in grecs:
            fname = rec["file"][:45]
            ref_svg = f"{rec['ref_svg_size']:,}"
            cur_svg = f"{rec['cur_svg_size']:,}" if rec["cur_svg_size"] > 0 else "n/a"
            ref_tvg = f"{rec['ref_tvg_size']:,}"

            if rec["status"] == "ok":
                tvg = f"{rec['tvg_size']:,}"
                zstd_s = f"{rec['zstd_size']:,}"
                brotli_s = f"{rec['brotli_size']:,}"
                dict_s = f"{rec['zstd_dict_size']:,}"
                dict_pct_s = pct(rec["zstd_dict_size"], rec["ref_svg_size"])
                notes = "(*)" if rec["is_outlier"] else ""
            else:
                tvg = "n/a"
                zstd_s = "n/a"
                brotli_s = "n/a"
                dict_s = "n/a"
                dict_pct_s = "n/a"
                notes = rec["category"]

            L.append(f"| {fname} | {ref_svg} | {cur_svg} | {tvg} | {ref_tvg} | {zstd_s} | {brotli_s} | {dict_s} | {dict_pct_s} | {notes} |")

        L.append("")

    # ================================================================
    # Best / Worst compression
    # ================================================================
    L.append("## Top 20 Best Compression Ratios (zstd+dict as % of SVG)")
    L.append("")
    sorted_by_ratio = sorted(
        non_outlier,
        key=lambda r: r["zstd_dict_size"] / r["ref_svg_size"] if r["ref_svg_size"] > 0 else 1)
    L.append("| File | Group | SVG | TVG | zstd+dict | % of SVG |")
    L.append("|------|-------|-----|-----|-----------|----------|")
    for rec in sorted_by_ratio[:20]:
        L.append(
            f"| {rec['file'][:45]} | {rec['group']} "
            f"| {rec['ref_svg_size']:,} | {rec['tvg_size']:,} "
            f"| {rec['zstd_dict_size']:,} | {pct(rec['zstd_dict_size'], rec['ref_svg_size'])} |")
    L.append("")

    L.append("## Bottom 20 Worst Compression Ratios (zstd+dict as % of SVG)")
    L.append("")
    L.append("| File | Group | SVG | TVG | zstd+dict | % of SVG |")
    L.append("|------|-------|-----|-----|-----------|----------|")
    for rec in sorted_by_ratio[-20:]:
        L.append(
            f"| {rec['file'][:45]} | {rec['group']} "
            f"| {rec['ref_svg_size']:,} | {rec['tvg_size']:,} "
            f"| {rec['zstd_dict_size']:,} | {pct(rec['zstd_dict_size'], rec['ref_svg_size'])} |")
    L.append("")

    # ================================================================
    # Write
    # ================================================================
    report_path = RESULTS_DIR / "report.md"
    with open(report_path, "w") as f:
        f.write("\n".join(L))
    print(f"Report written to {report_path} ({len(L)} lines)")


if __name__ == "__main__":
    main()
