#!/usr/bin/env python3
"""
svg_dict_size_extended.py - Extend dictionary size study with 1MB/2MB + shrink from 2MB.
Loads existing results from CSV, trains new dicts, compresses, rewrites CSV and report.
"""
import csv, filecmp, os, shutil, subprocess, sys, tempfile, time
from collections import defaultdict
from pathlib import Path

RESULTS_DIR = Path(__file__).resolve().parent / "results"
WORK = Path("/tmp/tinyvg-eval-work")
SVGO_DIR = WORK / "svgo-files"

ALL_DICT_SIZES = {"64KB": 65536, "110KB": 112640, "256KB": 262144,
                  "512KB": 524288, "1MB": 1048576, "2MB": 2097152}
NEW_SIZES = {"1MB": 1048576, "2MB": 2097152}
SHRINK_CEILING = 2097152

def file_size(p):
    return os.path.getsize(p) if os.path.isfile(p) else 0

def collect_svgo_files():
    files = []
    if SVGO_DIR.exists():
        for gd in sorted(SVGO_DIR.iterdir()):
            if gd.is_dir():
                for s in sorted(gd.iterdir()):
                    if s.suffix.lower() == ".svg" and s.stat().st_size > 0:
                        files.append((gd.name, s.name, str(s)))
    return files

def train_dict(fps, dp, maxdict, use_shrink=False, shrink_pct=1):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        for p in fps: f.write(p + "\n")
        lf = f.name
    try:
        cmd = (["zstd", f"--train-fastcover=d=8,steps=40,shrink={shrink_pct}",
                f"--maxdict={maxdict}", f"--filelist={lf}", "-o", str(dp)]
               if use_shrink else
               ["zstd", "--train", f"--maxdict={maxdict}", f"--filelist={lf}", "-o", str(dp)])
        t0 = time.time()
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=1200)
        return r.returncode == 0 and os.path.isfile(str(dp)), file_size(str(dp)), time.time()-t0
    finally:
        os.unlink(lf)

def compress_batch(file_list, dict_path=None):
    results = {}
    td = tempfile.mkdtemp(prefix="dsize-")
    try:
        for i, (g, fn, fp) in enumerate(file_list):
            out = os.path.join(td, "out.zst")
            cmd = ["zstd", "-22", "--ultra", "-f", "-o", out, fp]
            if dict_path:
                cmd = ["zstd", "-22", "--ultra", "-D", str(dict_path), "-f", "-o", out, fp]
            r = subprocess.run(cmd, capture_output=True, timeout=60)
            results[(g, fn)] = file_size(out) if r.returncode == 0 else 0
            if (i+1) % 2000 == 0 or (i+1) == len(file_list):
                print(f"    {i+1}/{len(file_list)}", flush=True)
    finally:
        shutil.rmtree(td, ignore_errors=True)
    return results

def main():
    sys.stdout.reconfigure(line_buffering=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    dd = RESULTS_DIR / "svg_dicts"; dd.mkdir(exist_ok=True)

    all_files = collect_svgo_files()
    print(f"Found {len(all_files)} SVGO files")
    if not all_files: return

    fps = [f[2] for f in all_files]
    orig = {(g, fn): file_size(fp) for g, fn, fp in all_files}
    total_svgo = sum(orig.values())

    # Load existing
    existing = {}
    csv_path = RESULTS_DIR / "svg_dict_size_details.csv"
    if csv_path.exists():
        with open(csv_path) as f:
            for row in csv.DictReader(f):
                for col in row:
                    if col.startswith("zstd_"):
                        lab = col[5:]
                        existing.setdefault(lab, {})[(row["group"], row["file"])] = int(row[col])
        print(f"Loaded: {', '.join(sorted(existing.keys()))}")
    results = dict(existing)

    all_dicts = {}
    for lab, sz in ALL_DICT_SIZES.items():
        dp = dd / f"svg_dict_{lab}.zstd"
        if dp.exists(): all_dicts[lab] = (str(dp), file_size(str(dp)), 0)
    for pct in [1, 2, 5]:
        dp = dd / f"svg_dict_shrink_{pct}pct.zstd"
        if dp.exists(): all_dicts[f"shrink-{pct}%"] = (str(dp), file_size(str(dp)), 0)

    # Train new fixed dicts
    for lab, sz in sorted(NEW_SIZES.items(), key=lambda x: x[1]):
        dp = dd / f"svg_dict_{lab}.zstd"
        print(f"\nTraining {lab} ({sz:,})...", flush=True)
        ok, actual, elapsed = train_dict(fps, dp, sz)
        if ok:
            all_dicts[lab] = (str(dp), actual, elapsed)
            print(f"  OK: {actual:,} bytes, {elapsed:.1f}s")
        else:
            print(f"  FAILED")

    # Shrink from 2MB
    shrink2m = {}
    for pct in [1, 2, 5]:
        lab = f"shrink2M-{pct}%"
        dp = dd / f"svg_dict_shrink2M_{pct}pct.zstd"
        print(f"\nTraining shrink={pct} from 2MB...", flush=True)
        ok, actual, elapsed = train_dict(fps, dp, SHRINK_CEILING, use_shrink=True, shrink_pct=pct)
        if ok:
            shrink2m[lab] = (str(dp), actual, elapsed)
            all_dicts[lab] = (str(dp), actual, elapsed)
            print(f"  OK: {actual:,} bytes ({actual//1024}KB), {elapsed:.1f}s")
        else:
            print(f"  FAILED")

    # Compress with new dicts
    print(f"\n{'='*60}\nCompressing {len(all_files)} files...", flush=True)
    for lab in ["1MB", "2MB"]:
        if lab in results and len(results[lab]) >= len(all_files):
            print(f"\n  {lab}: already done, skipping"); continue
        dp = dd / f"svg_dict_{lab}.zstd"
        if not dp.exists(): continue
        print(f"\n  {lab} ({file_size(str(dp)):,} bytes)...", flush=True)
        results[lab] = compress_batch(all_files, str(dp))

    # Shrink dicts - check for byte-identical to skip
    for lab, (dp, dsz, _) in shrink2m.items():
        skip = False
        for elab, (ep, esz, _) in all_dicts.items():
            if elab != lab and elab in results and len(results[elab]) >= len(all_files) and esz == dsz:
                if os.path.isfile(ep) and filecmp.cmp(dp, ep, shallow=False):
                    print(f"\n  {lab}: byte-identical to {elab}, reusing")
                    results[lab] = results[elab]; skip = True; break
        if not skip:
            print(f"\n  {lab} ({dsz:,} bytes = {dsz//1024}KB)...", flush=True)
            results[lab] = compress_batch(all_files, dp)

    # Write CSV
    all_labels = ["no-dict"] + sorted(
        [l for l in results if l != "no-dict" and l in all_dicts],
        key=lambda l: all_dicts[l][1])
    for l in results:
        if l not in all_labels: all_labels.append(l)
    fnames = ["group", "file", "svgo_size"] + [f"zstd_{l}" for l in all_labels]
    with open(csv_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fnames); w.writeheader()
        for g, fn, fp in all_files:
            row = {"group": g, "file": fn, "svgo_size": orig[(g, fn)]}
            for l in all_labels: row[f"zstd_{l}"] = results.get(l, {}).get((g, fn), 0)
            w.writerow(row)
    print(f"\nCSV: {csv_path}")

    # Report
    generate_report(all_files, orig, all_dicts, results)

def generate_report(all_files, orig, dicts, results):
    lines = []; w = lines.append
    total_svgo = sum(orig.values())
    groups = defaultdict(list)
    for g, fn, fp in all_files: groups[g].append((fn, fp))

    fixed = ["no-dict"] + sorted([l for l in ALL_DICT_SIZES if l in results], key=lambda l: ALL_DICT_SIZES[l])

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
    w(f"- **Total uncompressed size**: {total_svgo:,} bytes ({total_svgo/1024/1024:.1f} MB)")
    w("- **Compression**: `zstd --ultra -22` (maximum compression level)")
    w("- **Dictionary training**: `zstd --train` (default fastCOVER) for fixed sizes;")
    w("  `--train-fastcover=d=8,steps=40,shrink=N` for auto-optimized sizes")
    w("- **Dictionaries trained on the same corpus** being compressed (best-case scenario)")
    w("")

    # Overall
    w("## Overall Summary")
    w("")
    w("| Dictionary | Dict size | Total compressed | % of SVG | Savings vs no-dict |")
    w("|------------|-----------|-----------------|----------|-------------------|")
    nd = sum(results.get("no-dict", {}).values())
    w(f"| no-dict (zstd -22) | - | {nd:,} | {nd/total_svgo:.1%} | - |")
    for lab in fixed[1:]:
        if lab not in dicts or lab not in results: continue
        _, dsz, _ = dicts[lab]
        tc = sum(results[lab].values())
        sav = 1 - tc/nd if nd else 0
        w(f"| {lab} | {dsz:,} | {tc:,} | {tc/total_svgo:.1%} | {sav:.1%} |")
    w("")
    w(f"**Total uncompressed SVG**: {total_svgo:,} bytes")
    w("")

    # Marginal
    w("## Marginal Value of Dictionary Size")
    w("")
    w("| From | To | Additional savings | Marginal % | Bytes saved per KB of dict |")
    w("|------|-----|-------------------|-----------|--------------------------|")
    for i in range(1, len(fixed)):
        prev, curr = fixed[i-1], fixed[i]
        if prev not in results or curr not in results: continue
        pt, ct = sum(results[prev].values()), sum(results[curr].values())
        saved = pt - ct; pct = saved/pt if pt else 0
        psz = dicts[prev][1] if prev in dicts else 0
        csz = dicts[curr][1] if curr in dicts else 0
        dkb = (csz - psz)/1024 if csz > psz else 1
        w(f"| {prev} ({psz:,}B) | {curr} ({csz:,}B) | "
          f"{saved:,} bytes | {pct:.2%} | {saved/dkb:.0f} |")
    w("")

    # Shrink 512KB
    s512 = sorted([l for l in dicts if l.startswith("shrink-") and l in results], key=lambda l: dicts[l][1])
    if s512:
        w("## Auto-Optimized Dictionary Sizes (shrink from 512KB)")
        w("")
        w("| Variant | Tolerance | Resulting size | Total compressed | % of SVG |")
        w("|---------|-----------|---------------|-----------------|----------|")
        for lab in s512:
            _, dsz, _ = dicts[lab]; tc = sum(results[lab].values())
            w(f"| {lab} | {lab.split('-')[1]} | {dsz:,} ({dsz//1024}KB) | {tc:,} | {tc/total_svgo:.1%} |")
        w("")

    # Shrink 2MB
    s2m = sorted([l for l in dicts if l.startswith("shrink2M-") and l in results], key=lambda l: dicts[l][1])
    if s2m:
        w("## Auto-Optimized Dictionary Sizes (shrink from 2MB)")
        w("")
        w("Starting from a 2MB ceiling to see if the optimizer finds a sweet spot:")
        w("")
        w("| Variant | Tolerance | Resulting size | Total compressed | % of SVG |")
        w("|---------|-----------|---------------|-----------------|----------|")
        for lab in s2m:
            _, dsz, _ = dicts[lab]; tc = sum(results[lab].values())
            w(f"| {lab} | {lab.split('-')[1]} | {dsz:,} ({dsz//1024}KB) | {tc:,} | {tc/total_svgo:.1%} |")
        w("")
        if all(dicts[l][1] == SHRINK_CEILING for l in s2m):
            w("**Finding**: The shrink optimizer kept the full 2MB dictionary at all tolerance")
            w("levels (1%, 2%, 5%), indicating compression returns have not plateaued at 2MB.")
        else:
            for lab in s2m:
                if dicts[lab][1] < SHRINK_CEILING:
                    w(f"**Finding**: At {lab.split('-')[1]} tolerance, the optimizer shrunk the")
                    w(f"dictionary from 2MB to {dicts[lab][1]:,} bytes ({dicts[lab][1]//1024}KB).")
        w("")

    # Per-group
    w("## Per-Group Comparison")
    w("")
    hdr = "| Group | Files | SVG size |"
    sep = "|-------|-------|----------|"
    for c in fixed: hdr += f" {c} |"; sep += "------|"
    w(hdr); w(sep)
    for gn in sorted(groups):
        gf = groups[gn]; gs = sum(orig[(gn, fn)] for fn, _ in gf)
        row = f"| {gn} | {len(gf):,} | {gs:,} |"
        for lab in fixed:
            if lab not in results: row += " - |"; continue
            t = sum(results[lab].get((gn, fn), 0) for fn, _ in gf)
            row += f" {t/gs:.1%} |" if gs else " - |"
        w(row)
    row = f"| **Total** | **{len(all_files):,}** | **{total_svgo:,}** |"
    for lab in fixed:
        if lab not in results: row += " - |"; continue
        t = sum(results[lab].values())
        row += f" **{t/total_svgo:.1%}** |"
    w(row); w("")

    # Distribution
    w("## Compression Ratio Distribution (compressed / SVG)")
    w("")
    hdr = "| Percentile |"; sep = "|------------|"
    for c in fixed: hdr += f" {c} |"; sep += "------|"
    w(hdr); w(sep)
    pf = {}
    for lab in fixed:
        if lab not in results: pf[lab] = []; continue
        rats = []
        for g, fn, fp in all_files:
            s = orig.get((g, fn), 0); c = results[lab].get((g, fn), 0)
            if s > 0 and c > 0: rats.append(c/s)
        rats.sort(); pf[lab] = rats
    for pn, func in [("p5", lambda r: r[len(r)//20]), ("p10", lambda r: r[len(r)//10]),
                      ("p25", lambda r: r[len(r)//4]), ("Median", lambda r: r[len(r)//2]),
                      ("p75", lambda r: r[3*len(r)//4]), ("p90", lambda r: r[9*len(r)//10]),
                      ("p95", lambda r: r[19*len(r)//20]), ("Mean", lambda r: sum(r)/len(r))]:
        row = f"| {pn} |"
        for lab in fixed:
            row += f" {func(pf[lab]):.1%} |" if pf[lab] else " - |"
        w(row)
    w("")

    # Findings
    w("## Key Findings")
    w("")
    totals = {l: sum(results[l].values()) for l in fixed if l in results}
    n = 1
    for prev, curr in [("no-dict","64KB"),("64KB","110KB"),("110KB","256KB"),
                        ("256KB","512KB"),("512KB","1MB"),("1MB","2MB")]:
        if prev in totals and curr in totals:
            imp = 1 - totals[curr]/totals[prev]; saved = totals[prev]-totals[curr]
            w(f"{n}. **{prev} to {curr}**: {imp:.2%} additional compression ({saved:,} bytes saved)")
            n += 1
    if s2m:
        af = all(dicts[l][1] == SHRINK_CEILING for l in s2m)
        if af:
            w(f"{n}. **Shrink from 2MB**: At all tolerance levels (1-5%), the optimizer kept the")
            w(f"   full 2MB dictionary — compression gains have not yet plateaued.")
        else:
            for lab in s2m:
                if dicts[lab][1] < SHRINK_CEILING:
                    w(f"{n}. **Shrink from 2MB ({lab.split('-')[1]})**: Optimized to "
                      f"{dicts[lab][1]:,} bytes ({dicts[lab][1]//1024}KB)")
                    n += 1
    w("")

    rp = RESULTS_DIR / "svg_dict_size_report.md"
    with open(rp, "w") as f: f.write("\n".join(lines) + "\n")
    print(f"\nReport: {rp} ({len(lines)} lines)")

if __name__ == "__main__":
    main()
