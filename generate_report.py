#!/usr/bin/env python3
"""
generate_report.py - Generate the final markdown report from all_files_diagnostics.csv.

Reads the full diagnostics CSV (every file, including failures) and produces
results/report.md with:
  - Overall and per-group compression summaries (SVG zstd, SVG zstd+dict,
    TVG, TVG zstd, TVG brotli, TVG zstd+dict)
  - Per-file tables for ALL files (with failures shown as 'n/a')
  - Conversion failure analysis with categorized error tallies
  - Best/worst compression ratio tables
"""

import csv
import os
from collections import Counter, defaultdict
from pathlib import Path

RESULTS_DIR = Path(__file__).resolve().parent / "results"

INT_FIELDS = ["ref_svg_size", "ref_tvg_size", "cur_svg_size", "svgo_size",
              "tvgt_size", "tvg_size",
              "svg_zstd_size", "svg_zstd_dict_size",
              "zstd_size", "brotli_size", "zstd_dict_size"]

BENCHMARK_GROUPS = {"zig", "w3c", "material-design", "papirus", "freesvg"}

GROUP_ORDER = ["zig", "w3c", "material-design", "papirus", "freesvg",
               "tabler", "lucide", "bootstrap", "simple-icons",
               "phosphor", "fontawesome", "remixicon"]


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
        if "Error Context" in detail or "InvalidOperationException" in detail:
            return "svg2tvgt:path_parse"
        if "unsupported transform" in detail.lower():
            return "svg2tvgt:transform"
        if "timeout" in detail.lower():
            return "svg2tvgt:timeout"
        if "currentColor" in detail or "color spec" in detail.lower():
            return "svg2tvgt:color"
        return "svg2tvgt:other"
    return f"{stage}:unknown"


def load_diagnostics():
    csv_path = RESULTS_DIR / "all_files_diagnostics.csv"
    results = []
    with open(csv_path) as f:
        for row in csv.DictReader(f):
            for k in INT_FIELDS:
                try:
                    row[k] = int(row[k]) if row.get(k) else 0
                except (ValueError, KeyError):
                    row[k] = 0
            row["category"] = categorize_failure(row) if row["status"] != "ok" else "ok"
            if row["status"] == "ok" and row["group"] in BENCHMARK_GROUPS:
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
    tvg_dict_path = RESULTS_DIR / "tvg_dict.zstd"
    svg_dict_path = RESULTS_DIR / "svg_dict.zstd"

    ok_recs = [r for r in all_recs if r["status"] == "ok"]
    non_outlier = [r for r in ok_recs if not r["is_outlier"]]
    fail_recs = [r for r in all_recs if r["status"] != "ok"]

    groups_all = defaultdict(list)
    groups_ok = defaultdict(list)
    for r in all_recs:
        groups_all[r["group"]].append(r)
    for r in ok_recs:
        groups_ok[r["group"]].append(r)

    L = []

    L.append("# TinyVG Compression Analysis Report")
    L.append("")
    L.append("This report extends the [TinyVG benchmark](https://tinyvg.tech/) by measuring")
    L.append("the additional compression achievable on `.tvg` (TinyVG binary) files using")
    L.append("modern general-purpose compressors, and compares against compressing the")
    L.append("original SVG files directly.")
    L.append("")

    L.append("## Methodology")
    L.append("")
    L.append("- **Source SVGs**: Original TinyVG benchmark datasets (Zig logos, W3C SVG samples,")
    L.append("  Material Design icons, Papirus icons) plus 7 additional icon sets: Tabler,")
    L.append("  Lucide, Bootstrap Icons, Simple Icons, Phosphor, Font Awesome (free), and Remix Icon.")
    L.append("- **SVG optimization**: Each SVG is first optimized with SVGO (multipass, precision 3)")
    L.append("  matching the original benchmark pipeline.")
    L.append("- **SVG -> TVG conversion**: `svg2tvgt` (SVG to TinyVG text) then `tvg-text`")
    L.append("  (TinyVG text to binary), from the [TinyVG SDK](https://github.com/TinyVG/sdk).")
    L.append("- **Compression schemes compared**:")
    L.append("  - **SVG + zstd -22**: SVGO-optimized SVG compressed with `zstd --ultra -22`")
    L.append("  - **SVG + zstd +dict**: SVG compressed with zstd + 110KB dictionary trained on all SVGs")
    L.append("  - **TVG (uncompressed)**: TinyVG binary format alone")
    L.append("  - **TVG + zstd -22**: TVG compressed with `zstd --ultra -22`")
    L.append("  - **TVG + brotli -11**: TVG compressed with `brotli -q 11`")
    L.append("  - **TVG + zstd +dict**: TVG compressed with zstd + 110KB dictionary trained on all TVGs")
    L.append("")
    L.append("All sizes in bytes. Percentages are relative to the SVGO-optimized SVG size.")

    dict_note = []
    if tvg_dict_path.exists():
        dict_note.append(f"TVG dictionary: {file_size(str(tvg_dict_path)):,} bytes")
    if svg_dict_path.exists():
        dict_note.append(f"SVG dictionary: {file_size(str(svg_dict_path)):,} bytes")
    if dict_note:
        L.append("")
        L.append(f"**Trained zstd dictionaries** (zstd default 110 KB): {'; '.join(dict_note)}")
    L.append("")

    # Dataset summary
    L.append("### Dataset Summary")
    L.append("")
    L.append("| Group | Source | SVGs | Converted | Success % |")
    L.append("|-------|--------|------|-----------|-----------|")
    for gname in GROUP_ORDER:
        grecs = groups_all.get(gname, [])
        if not grecs:
            continue
        n_ok = len(groups_ok.get(gname, []))
        n_total = len(grecs)
        source = "TinyVG benchmark" if gname in BENCHMARK_GROUPS else "Extended"
        pct_ok = f"{100*n_ok/n_total:.0f}%" if n_total > 0 else "n/a"
        L.append(f"| {gname} | {source} | {n_total:,} | {n_ok:,} | {pct_ok} |")
    L.append(f"| **Total** | | **{len(all_recs):,}** | **{len(ok_recs):,}** | **{100*len(ok_recs)/len(all_recs):.0f}%** |")
    L.append("")

    n_outliers = sum(1 for r in ok_recs if r["is_outlier"])
    if n_outliers > 0:
        L.append(f"*{n_outliers} outlier(s) in benchmark groups excluded from aggregate statistics.*")
        L.append("")

    # ================================================================
    # Overall Summary
    # ================================================================
    L.append("## Overall Summary")
    L.append("")

    total_svg = sum(r["ref_svg_size"] for r in non_outlier)
    total_svg_zstd = sum(r["svg_zstd_size"] for r in non_outlier)
    total_svg_zstd_dict = sum(r["svg_zstd_dict_size"] for r in non_outlier)
    total_tvg = sum(r["tvg_size"] for r in non_outlier)
    total_zstd = sum(r["zstd_size"] for r in non_outlier)
    total_brotli = sum(r["brotli_size"] for r in non_outlier)
    total_zstd_dict = sum(r["zstd_dict_size"] for r in non_outlier)

    L.append("| Scheme | Total bytes | % of SVG | % of TVG |")
    L.append("|--------|------------|----------|----------|")
    L.append(f"| **SVG (SVGO-optimized)** | {total_svg:,} | 100.0% | - |")
    L.append(f"| **SVG + zstd -22** | {total_svg_zstd:,} | {pct(total_svg_zstd, total_svg)} | - |")
    L.append(f"| **SVG + zstd +dict** | {total_svg_zstd_dict:,} | {pct(total_svg_zstd_dict, total_svg)} | - |")
    L.append(f"| **TVG (uncompressed)** | {total_tvg:,} | {pct(total_tvg, total_svg)} | 100.0% |")
    L.append(f"| **TVG + zstd -22** | {total_zstd:,} | {pct(total_zstd, total_svg)} | {pct(total_zstd, total_tvg)} |")
    L.append(f"| **TVG + brotli -11** | {total_brotli:,} | {pct(total_brotli, total_svg)} | {pct(total_brotli, total_tvg)} |")
    L.append(f"| **TVG + zstd +dict** | {total_zstd_dict:,} | {pct(total_zstd_dict, total_svg)} | {pct(total_zstd_dict, total_tvg)} |")
    L.append("")
    L.append(f"*{len(non_outlier):,} files with successful TVG conversion.*")
    L.append("")

    # Medians
    def safe_pcts(field, denom_field, recs):
        return [r[field] / r[denom_field] * 100 for r in recs
                if r[denom_field] > 0 and r[field] > 0]

    svg_zstd_pcts = safe_pcts("svg_zstd_size", "ref_svg_size", non_outlier)
    svg_dict_pcts = safe_pcts("svg_zstd_dict_size", "ref_svg_size", non_outlier)
    tvg_pcts = safe_pcts("tvg_size", "ref_svg_size", non_outlier)
    zstd_pcts = safe_pcts("zstd_size", "ref_svg_size", non_outlier)
    brotli_pcts = safe_pcts("brotli_size", "ref_svg_size", non_outlier)
    dict_pcts = safe_pcts("zstd_dict_size", "ref_svg_size", non_outlier)

    L.append("### Median per-file ratios (% of SVG)")
    L.append("")
    L.append("| Scheme | Median % of SVG |")
    L.append("|--------|----------------|")
    L.append(f"| SVG + zstd -22 | {median(svg_zstd_pcts):.1f}% |")
    L.append(f"| SVG + zstd +dict | {median(svg_dict_pcts):.1f}% |")
    L.append(f"| TVG | {median(tvg_pcts):.1f}% |")
    L.append(f"| TVG + zstd -22 | {median(zstd_pcts):.1f}% |")
    L.append(f"| TVG + brotli -11 | {median(brotli_pcts):.1f}% |")
    L.append(f"| TVG + zstd +dict | {median(dict_pcts):.1f}% |")
    L.append("")

    # Key findings
    L.append("### Key Findings")
    L.append("")
    L.append(f"1. **SVG + zstd** alone achieves a median of **{median(svg_zstd_pcts):.1f}%** of SVGO-optimized SVG size.")
    L.append(f"2. **SVG + zstd +dict** improves this to **{median(svg_dict_pcts):.1f}%** of SVG size.")
    L.append(f"3. **TVG alone** reduces SVGs to a median of **{median(tvg_pcts):.1f}%** of their size.")
    L.append(f"4. **TVG + brotli** achieves a median of **{median(brotli_pcts):.1f}%** of SVG size.")
    tvg_dict_pcts_of_tvg = safe_pcts("zstd_dict_size", "tvg_size", non_outlier)
    L.append(f"5. **TVG + zstd +dict** achieves a median of just **{median(dict_pcts):.1f}%**")
    L.append(f"   of SVG size (reducing TVG to {median(tvg_dict_pcts_of_tvg):.1f}% of its uncompressed size).")
    if svg_dict_pcts and dict_pcts and median(dict_pcts) < median(svg_dict_pcts):
        improvement = median(svg_dict_pcts) - median(dict_pcts)
        L.append(f"6. **TVG + zstd +dict beats SVG + zstd +dict** by {improvement:.1f} percentage points at median,")
        L.append(f"   demonstrating that TinyVG's binary format provides genuine structural compression")
        L.append(f"   beyond what generic text compression can achieve on SVG source.")
    L.append("")

    # ================================================================
    # Per-Group Summary
    # ================================================================
    L.append("## Per-Group Summary")
    L.append("")

    for gname in GROUP_ORDER:
        grecs = [r for r in groups_ok.get(gname, []) if not r["is_outlier"]]
        if not grecs:
            continue
        g_svg = sum(r["ref_svg_size"] for r in grecs)
        g_svg_zstd = sum(r["svg_zstd_size"] for r in grecs)
        g_svg_zstd_dict = sum(r["svg_zstd_dict_size"] for r in grecs)
        g_tvg = sum(r["tvg_size"] for r in grecs)
        g_zstd = sum(r["zstd_size"] for r in grecs)
        g_brotli = sum(r["brotli_size"] for r in grecs)
        g_zstd_dict = sum(r["zstd_dict_size"] for r in grecs)
        outlier_count = sum(1 for r in groups_ok.get(gname, []) if r["is_outlier"])
        outlier_note = f" ({outlier_count} outlier excluded)" if outlier_count else ""

        L.append(f"### {gname} ({len(grecs):,} files{outlier_note})")
        L.append("")
        L.append("| Scheme | Total bytes | % of SVG | % of TVG |")
        L.append("|--------|------------|----------|----------|")
        L.append(f"| SVG (optimized) | {g_svg:,} | 100.0% | - |")
        L.append(f"| SVG + zstd -22 | {g_svg_zstd:,} | {pct(g_svg_zstd, g_svg)} | - |")
        L.append(f"| SVG + zstd +dict | {g_svg_zstd_dict:,} | {pct(g_svg_zstd_dict, g_svg)} | - |")
        L.append(f"| TVG | {g_tvg:,} | {pct(g_tvg, g_svg)} | 100.0% |")
        L.append(f"| TVG + zstd -22 | {g_zstd:,} | {pct(g_zstd, g_svg)} | {pct(g_zstd, g_tvg)} |")
        L.append(f"| TVG + brotli -11 | {g_brotli:,} | {pct(g_brotli, g_svg)} | {pct(g_brotli, g_tvg)} |")
        L.append(f"| TVG + zstd +dict | {g_zstd_dict:,} | {pct(g_zstd_dict, g_svg)} | {pct(g_zstd_dict, g_tvg)} |")
        L.append("")

    # ================================================================
    # Conversion Failure Analysis
    # ================================================================
    L.append("## Conversion Failure Analysis")
    L.append("")

    cat_counts = Counter(r["category"] for r in all_recs)
    total_fail = sum(1 for r in all_recs if r["status"] != "ok")
    L.append(f"### Failure categories ({total_fail:,} of {len(all_recs):,} files)")
    L.append("")
    L.append("| Category | Count | Description |")
    L.append("|----------|-------|-------------|")
    L.append(f"| ok | {cat_counts['ok']:,} | Successful conversion |")

    cat_descs = {
        "svg2tvgt:path_parse": "svg2tvgt fails parsing SVG path `d` data (complex/compound paths)",
        "svg2tvgt:moveto_bug": "svg2tvgt throws `New MoveTo detected without ClosePath` -- open subpaths",
        "svg2tvgt:color": "svg2tvgt cannot translate color spec (e.g. `currentColor`)",
        "no_source": "SVG file not found in current source dataset",
        "svg2tvgt:transform": "svg2tvgt does not support the SVG transform",
        "svg2tvgt:timeout": "svg2tvgt timed out (>60s)",
        "svg2tvgt:other": "Other svg2tvgt error",
        "svgo_fail": "SVGO optimization failed",
        "tvg-text:syntax": "tvg-text rejects TVGT with syntax error",
        "tvg-text:range": "tvg-text value out of range",
        "tvg-text:other": "Other tvg-text error",
    }
    for cat in ["svg2tvgt:path_parse", "svg2tvgt:moveto_bug", "svg2tvgt:color",
                "svg2tvgt:other", "svg2tvgt:transform", "svg2tvgt:timeout",
                "no_source", "svgo_fail",
                "tvg-text:syntax", "tvg-text:range", "tvg-text:other"]:
        if cat_counts.get(cat, 0) > 0:
            L.append(f"| {cat} | {cat_counts[cat]:,} | {cat_descs.get(cat, '')} |")
    L.append("")

    L.append("### Failure breakdown by group")
    L.append("")
    L.append("| Group | Total | OK | path_parse | moveto_bug | color | no_source | other |")
    L.append("|-------|-------|----|------------|------------|-------|-----------|-------|")
    for gname in GROUP_ORDER:
        grecs = groups_all.get(gname, [])
        if not grecs:
            continue
        gcats = Counter(r["category"] for r in grecs)
        other = sum(v for k, v in gcats.items()
                    if k not in ("ok", "svg2tvgt:path_parse", "svg2tvgt:moveto_bug",
                                 "svg2tvgt:color", "no_source"))
        L.append(
            f"| {gname} | {len(grecs):,} | {gcats['ok']:,} "
            f"| {gcats.get('svg2tvgt:path_parse', 0):,} "
            f"| {gcats.get('svg2tvgt:moveto_bug', 0):,} "
            f"| {gcats.get('svg2tvgt:color', 0):,} "
            f"| {gcats.get('no_source', 0):,} "
            f"| {other:,} |")
    L.append("")

    # ================================================================
    # Per-File Details
    # ================================================================
    L.append("## Per-File Details")
    L.append("")
    L.append("Every file is listed below. Files that failed TVG conversion show `n/a` for TVG")
    L.append("compression columns but may still have SVG compression data. The `notes` column")
    L.append("indicates failure category or `(*)` for outliers.")
    L.append("")

    for gname in GROUP_ORDER:
        grecs = sorted(groups_all.get(gname, []), key=lambda r: r["ref_svg_size"], reverse=True)
        if not grecs:
            continue

        L.append(f"### {gname} ({len(grecs):,} files)")
        L.append("")
        L.append("| File | SVG | SVG+zstd | SVG+dict | TVG | TVG+zstd | TVG+brotli | TVG+dict | dict/SVG | notes |")
        L.append("|------|-----|----------|----------|-----|----------|------------|----------|----------|-------|")

        if len(grecs) <= 40:
            show = grecs
        else:
            show = grecs[:15] + [None] + grecs[-15:]

        for rec in show:
            if rec is None:
                L.append("| ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |")
                continue

            fname = rec["file"][:40]
            svg_s = f"{rec['ref_svg_size']:,}"
            svg_zstd_s = f"{rec['svg_zstd_size']:,}" if rec["svg_zstd_size"] > 0 else "n/a"
            svg_dict_s = f"{rec['svg_zstd_dict_size']:,}" if rec["svg_zstd_dict_size"] > 0 else "n/a"

            if rec["status"] == "ok":
                tvg_s = f"{rec['tvg_size']:,}"
                zstd_s = f"{rec['zstd_size']:,}"
                brotli_s = f"{rec['brotli_size']:,}"
                dict_s = f"{rec['zstd_dict_size']:,}"
                dict_pct_s = pct(rec["zstd_dict_size"], rec["ref_svg_size"])
                notes = "(*)" if rec["is_outlier"] else ""
            else:
                tvg_s = "n/a"
                zstd_s = "n/a"
                brotli_s = "n/a"
                dict_s = "n/a"
                dict_pct_s = "n/a"
                notes = rec["category"]

            L.append(f"| {fname} | {svg_s} | {svg_zstd_s} | {svg_dict_s} | {tvg_s} | {zstd_s} | {brotli_s} | {dict_s} | {dict_pct_s} | {notes} |")

        L.append("")

    # ================================================================
    # Best / Worst
    # ================================================================
    L.append("## Top 20 Best Compression Ratios (TVG+zstd+dict as % of SVG)")
    L.append("")
    sorted_by_ratio = sorted(
        non_outlier,
        key=lambda r: r["zstd_dict_size"] / r["ref_svg_size"] if r["ref_svg_size"] > 0 else 1)
    L.append("| File | Group | SVG | SVG+zstd | TVG | TVG+dict | dict/SVG |")
    L.append("|------|-------|-----|----------|-----|----------|----------|")
    for rec in sorted_by_ratio[:20]:
        L.append(
            f"| {rec['file'][:40]} | {rec['group']} "
            f"| {rec['ref_svg_size']:,} | {rec['svg_zstd_size']:,} "
            f"| {rec['tvg_size']:,} "
            f"| {rec['zstd_dict_size']:,} | {pct(rec['zstd_dict_size'], rec['ref_svg_size'])} |")
    L.append("")

    L.append("## Bottom 20 Worst Compression Ratios (TVG+zstd+dict as % of SVG)")
    L.append("")
    L.append("| File | Group | SVG | SVG+zstd | TVG | TVG+dict | dict/SVG |")
    L.append("|------|-------|-----|----------|-----|----------|----------|")
    for rec in sorted_by_ratio[-20:]:
        L.append(
            f"| {rec['file'][:40]} | {rec['group']} "
            f"| {rec['ref_svg_size']:,} | {rec['svg_zstd_size']:,} "
            f"| {rec['tvg_size']:,} "
            f"| {rec['zstd_dict_size']:,} | {pct(rec['zstd_dict_size'], rec['ref_svg_size'])} |")
    L.append("")

    report_path = RESULTS_DIR / "report.md"
    with open(report_path, "w") as f:
        f.write("\n".join(L))
    print(f"Report written to {report_path} ({len(L)} lines)")


if __name__ == "__main__":
    main()
