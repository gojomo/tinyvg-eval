# TinyVG Compression Analysis Report

This report extends the [TinyVG benchmark](https://tinyvg.tech/) by measuring
the additional compression achievable on `.tvg` (TinyVG binary) files using
modern general-purpose compressors, and compares against compressing the
original SVG files directly.

## Methodology

- **Source SVGs**: Original TinyVG benchmark datasets (Zig logos, W3C SVG samples,
  Material Design icons, Papirus icons) plus 7 additional icon sets: Tabler,
  Lucide, Bootstrap Icons, Simple Icons, Phosphor, Font Awesome (free), and Remix Icon.
- **SVG optimization**: Each SVG is first optimized with SVGO (multipass, precision 3)
  matching the original benchmark pipeline.
- **SVG -> TVG conversion**: `svg2tvgt` (SVG to TinyVG text) then `tvg-text`
  (TinyVG text to binary), from the [TinyVG SDK](https://github.com/TinyVG/sdk).
- **Compression schemes compared**:
  - **SVG + zstd -22**: SVGO-optimized SVG compressed with `zstd --ultra -22`
  - **SVG + zstd +dict**: SVG compressed with zstd + 110KB dictionary trained on all SVGs
  - **TVG (uncompressed)**: TinyVG binary format alone
  - **TVG + zstd -22**: TVG compressed with `zstd --ultra -22`
  - **TVG + brotli -11**: TVG compressed with `brotli -q 11`
  - **TVG + zstd +dict**: TVG compressed with zstd + 110KB dictionary trained on all TVGs

All sizes in bytes. Percentages are relative to the SVGO-optimized SVG size.

**Trained zstd dictionaries** (zstd default 110 KB): TVG dictionary: 112,640 bytes; SVG dictionary: 112,640 bytes

### Dataset Summary

| Group | Source | SVGs | Converted | Success % |
|-------|--------|------|-----------|-----------|
| zig | TinyVG benchmark | 9 | 8 | 89% |
| w3c | TinyVG benchmark | 115 | 76 | 66% |
| material-design | TinyVG benchmark | 1,000 | 346 | 35% |
| papirus | TinyVG benchmark | 1,000 | 519 | 52% |
| freesvg | TinyVG benchmark | 5 | 0 | 0% |
| tabler | Extended | 4,985 | 1,005 | 20% |
| lucide | Extended | 1,669 | 459 | 28% |
| bootstrap | Extended | 2,078 | 918 | 44% |
| simple-icons | Extended | 3,395 | 1,345 | 40% |
| phosphor | Extended | 1,512 | 524 | 35% |
| fontawesome | Extended | 2,583 | 1,060 | 41% |
| remixicon | Extended | 3,229 | 1,750 | 54% |
| **Total** | | **21,580** | **8,010** | **37%** |

*1 outlier(s) in benchmark groups excluded from aggregate statistics.*

## Overall Summary

| Scheme | Total bytes | % of SVG | % of TVG |
|--------|------------|----------|----------|
| **SVG (SVGO-optimized)** | 4,195,845 | 100.0% | - |
| **SVG + zstd -22** | 2,425,701 | 57.8% | - |
| **SVG + zstd +dict** | 1,255,865 | 29.9% | - |
| **TVG (uncompressed)** | 1,860,450 | 44.3% | 100.0% |
| **TVG + zstd -22** | 1,540,704 | 36.7% | 82.8% |
| **TVG + brotli -11** | 1,466,345 | 34.9% | 78.8% |
| **TVG + zstd +dict** | 1,125,682 | 26.8% | 60.5% |

*8,009 files with successful TVG conversion.*

### Median per-file ratios (% of SVG)

| Scheme | Median % of SVG |
|--------|----------------|
| SVG + zstd -22 | 65.7% |
| SVG + zstd +dict | 31.7% |
| TVG | 42.8% |
| TVG + zstd -22 | 39.0% |
| TVG + brotli -11 | 37.2% |
| TVG + zstd +dict | 28.4% |

### Key Findings

1. **SVG + zstd** alone achieves a median of **65.7%** of SVGO-optimized SVG size.
2. **SVG + zstd +dict** improves this to **31.7%** of SVG size.
3. **TVG alone** reduces SVGs to a median of **42.8%** of their size.
4. **TVG + brotli** achieves a median of **37.2%** of SVG size.
5. **TVG + zstd +dict** achieves a median of just **28.4%**
   of SVG size (reducing TVG to 67.9% of its uncompressed size).
6. **TVG + zstd +dict beats SVG + zstd +dict** by 3.3 percentage points at median,
   demonstrating that TinyVG's binary format provides genuine structural compression
   beyond what generic text compression can achieve on SVG source.

## Per-Group Summary

### zig (7 files (1 outlier excluded))

| Scheme | Total bytes | % of SVG | % of TVG |
|--------|------------|----------|----------|
| SVG (optimized) | 6,613 | 100.0% | - |
| SVG + zstd -22 | 3,083 | 46.6% | - |
| SVG + zstd +dict | 1,247 | 18.9% | - |
| TVG | 3,052 | 46.2% | 100.0% |
| TVG + zstd -22 | 2,202 | 33.3% | 72.1% |
| TVG + brotli -11 | 2,137 | 32.3% | 70.0% |
| TVG + zstd +dict | 772 | 11.7% | 25.3% |

### w3c (76 files)

| Scheme | Total bytes | % of SVG | % of TVG |
|--------|------------|----------|----------|
| SVG (optimized) | 34,546 | 100.0% | - |
| SVG + zstd -22 | 18,977 | 54.9% | - |
| SVG + zstd +dict | 12,712 | 36.8% | - |
| TVG | 17,036 | 49.3% | 100.0% |
| TVG + zstd -22 | 12,849 | 37.2% | 75.4% |
| TVG + brotli -11 | 11,636 | 33.7% | 68.3% |
| TVG + zstd +dict | 11,762 | 34.0% | 69.0% |

### material-design (346 files)

| Scheme | Total bytes | % of SVG | % of TVG |
|--------|------------|----------|----------|
| SVG (optimized) | 107,678 | 100.0% | - |
| SVG + zstd -22 | 64,309 | 59.7% | - |
| SVG + zstd +dict | 36,833 | 34.2% | - |
| TVG | 51,872 | 48.2% | 100.0% |
| TVG + zstd -22 | 45,096 | 41.9% | 86.9% |
| TVG + brotli -11 | 42,162 | 39.2% | 81.3% |
| TVG + zstd +dict | 36,260 | 33.7% | 69.9% |

### papirus (519 files)

| Scheme | Total bytes | % of SVG | % of TVG |
|--------|------------|----------|----------|
| SVG (optimized) | 614,594 | 100.0% | - |
| SVG + zstd -22 | 245,722 | 40.0% | - |
| SVG + zstd +dict | 118,512 | 19.3% | - |
| TVG | 319,196 | 51.9% | 100.0% |
| TVG + zstd -22 | 200,103 | 32.6% | 62.7% |
| TVG + brotli -11 | 186,290 | 30.3% | 58.4% |
| TVG + zstd +dict | 106,475 | 17.3% | 33.4% |

### tabler (1,005 files)

| Scheme | Total bytes | % of SVG | % of TVG |
|--------|------------|----------|----------|
| SVG (optimized) | 373,968 | 100.0% | - |
| SVG + zstd -22 | 238,810 | 63.9% | - |
| SVG + zstd +dict | 102,726 | 27.5% | - |
| TVG | 163,233 | 43.6% | 100.0% |
| TVG + zstd -22 | 136,898 | 36.6% | 83.9% |
| TVG + brotli -11 | 130,988 | 35.0% | 80.2% |
| TVG + zstd +dict | 93,763 | 25.1% | 57.4% |

### lucide (459 files)

| Scheme | Total bytes | % of SVG | % of TVG |
|--------|------------|----------|----------|
| SVG (optimized) | 140,494 | 100.0% | - |
| SVG + zstd -22 | 93,145 | 66.3% | - |
| SVG + zstd +dict | 32,917 | 23.4% | - |
| TVG | 58,361 | 41.5% | 100.0% |
| TVG + zstd -22 | 46,008 | 32.7% | 78.8% |
| TVG + brotli -11 | 43,072 | 30.7% | 73.8% |
| TVG + zstd +dict | 29,923 | 21.3% | 51.3% |

### bootstrap (918 files)

| Scheme | Total bytes | % of SVG | % of TVG |
|--------|------------|----------|----------|
| SVG (optimized) | 465,637 | 100.0% | - |
| SVG + zstd -22 | 275,409 | 59.1% | - |
| SVG + zstd +dict | 143,397 | 30.8% | - |
| TVG | 229,074 | 49.2% | 100.0% |
| TVG + zstd -22 | 170,839 | 36.7% | 74.6% |
| TVG + brotli -11 | 163,363 | 35.1% | 71.3% |
| TVG + zstd +dict | 114,377 | 24.6% | 49.9% |

### simple-icons (1,345 files)

| Scheme | Total bytes | % of SVG | % of TVG |
|--------|------------|----------|----------|
| SVG (optimized) | 924,472 | 100.0% | - |
| SVG + zstd -22 | 522,052 | 56.5% | - |
| SVG + zstd +dict | 381,941 | 41.3% | - |
| TVG | 416,637 | 45.1% | 100.0% |
| TVG + zstd -22 | 388,420 | 42.0% | 93.2% |
| TVG + brotli -11 | 371,185 | 40.2% | 89.1% |
| TVG + zstd +dict | 353,193 | 38.2% | 84.8% |

### phosphor (524 files)

| Scheme | Total bytes | % of SVG | % of TVG |
|--------|------------|----------|----------|
| SVG (optimized) | 228,264 | 100.0% | - |
| SVG + zstd -22 | 120,198 | 52.7% | - |
| SVG + zstd +dict | 41,647 | 18.2% | - |
| TVG | 56,345 | 24.7% | 100.0% |
| TVG + zstd -22 | 47,286 | 20.7% | 83.9% |
| TVG + brotli -11 | 44,401 | 19.5% | 78.8% |
| TVG + zstd +dict | 33,576 | 14.7% | 59.6% |

### fontawesome (1,060 files)

| Scheme | Total bytes | % of SVG | % of TVG |
|--------|------------|----------|----------|
| SVG (optimized) | 814,221 | 100.0% | - |
| SVG + zstd -22 | 490,341 | 60.2% | - |
| SVG + zstd +dict | 208,743 | 25.6% | - |
| TVG | 301,345 | 37.0% | 100.0% |
| TVG + zstd -22 | 276,151 | 33.9% | 91.6% |
| TVG + brotli -11 | 267,244 | 32.8% | 88.7% |
| TVG + zstd +dict | 197,640 | 24.3% | 65.6% |

### remixicon (1,750 files)

| Scheme | Total bytes | % of SVG | % of TVG |
|--------|------------|----------|----------|
| SVG (optimized) | 485,358 | 100.0% | - |
| SVG + zstd -22 | 353,655 | 72.9% | - |
| SVG + zstd +dict | 175,190 | 36.1% | - |
| TVG | 244,299 | 50.3% | 100.0% |
| TVG + zstd -22 | 214,852 | 44.3% | 87.9% |
| TVG + brotli -11 | 203,867 | 42.0% | 83.4% |
| TVG + zstd +dict | 147,941 | 30.5% | 60.6% |

## Conversion Failure Analysis

### Failure categories (13,570 of 21,580 files)

| Category | Count | Description |
|----------|-------|-------------|
| ok | 8,010 | Successful conversion |
| svg2tvgt:path_parse | 10,306 | svg2tvgt fails parsing SVG path `d` data (complex/compound paths) |
| svg2tvgt:moveto_bug | 3,193 | svg2tvgt throws `New MoveTo detected without ClosePath` -- open subpaths |
| svg2tvgt:color | 20 | svg2tvgt cannot translate color spec (e.g. `currentColor`) |
| svg2tvgt:transform | 5 | svg2tvgt does not support the SVG transform |
| no_source | 41 | SVG file not found in current source dataset |
| tvg-text:syntax | 1 | tvg-text rejects TVGT with syntax error |
| tvg-text:range | 4 | tvg-text value out of range |

### Failure breakdown by group

| Group | Total | OK | path_parse | moveto_bug | color | no_source | other |
|-------|-------|----|------------|------------|-------|-----------|-------|
| zig | 9 | 8 | 1 | 0 | 0 | 0 | 0 |
| w3c | 115 | 76 | 13 | 26 | 0 | 0 | 0 |
| material-design | 1,000 | 346 | 437 | 214 | 0 | 3 | 0 |
| papirus | 1,000 | 519 | 395 | 51 | 0 | 33 | 2 |
| freesvg | 5 | 0 | 0 | 0 | 0 | 5 | 0 |
| tabler | 4,985 | 1,005 | 2,339 | 1,641 | 0 | 0 | 0 |
| lucide | 1,669 | 459 | 350 | 860 | 0 | 0 | 0 |
| bootstrap | 2,078 | 918 | 1,106 | 54 | 0 | 0 | 0 |
| simple-icons | 3,395 | 1,345 | 2,023 | 24 | 0 | 0 | 3 |
| phosphor | 1,512 | 524 | 650 | 313 | 20 | 0 | 5 |
| fontawesome | 2,583 | 1,060 | 1,523 | 0 | 0 | 0 | 0 |
| remixicon | 3,229 | 1,750 | 1,469 | 10 | 0 | 0 | 0 |

## Per-File Details

Every file is listed below. Files that failed TVG conversion show `n/a` for TVG
compression columns but may still have SVG compression data. The `notes` column
indicates failure category or `(*)` for outliers.

### zig (9 files)

| File | SVG | SVG+zstd | SVG+dict | TVG | TVG+zstd | TVG+brotli | TVG+dict | dict/SVG | notes |
|------|-----|----------|----------|-----|----------|------------|----------|----------|-------|
| ziggy.svg | 27,873 | 9,338 | 9,039 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| zero.svg | 26,352 | 49,093 | 47,733 | 66,962 | 56,513 | 51,956 | 56,858 | 215.8% | (*) |
| zig-logo-dark.svg | 1,200 | 537 | 261 | 549 | 407 | 398 | 39 | 3.2% |  |
| zig-logo-light.svg | 1,197 | 535 | 267 | 549 | 405 | 392 | 42 | 3.5% |  |
| zig-logo-neg-black.svg | 1,178 | 524 | 257 | 545 | 401 | 397 | 51 | 4.3% |  |
| zig-logo-neg-white.svg | 1,175 | 525 | 261 | 545 | 401 | 395 | 53 | 4.5% |  |
| zig-mark-neg-black.svg | 622 | 320 | 62 | 288 | 196 | 182 | 192 | 30.9% |  |
| zig-mark.svg | 622 | 322 | 72 | 288 | 197 | 185 | 200 | 32.2% |  |
| zig-mark-neg-white.svg | 619 | 320 | 67 | 288 | 195 | 188 | 195 | 31.5% |  |

### w3c (115 files)

| File | SVG | SVG+zstd | SVG+dict | TVG | TVG+zstd | TVG+brotli | TVG+dict | dict/SVG | notes |
|------|-----|----------|----------|-----|----------|------------|----------|----------|-------|
| penrose-staircase.svg | 3,231 | 563 | 459 | 649 | 335 | 339 | 326 | 10.1% |  |
| ibm.svg | 2,696 | 1,178 | 1,081 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| acid.svg | 2,590 | 769 | 687 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| faux-art.svg | 2,456 | 1,198 | 1,040 | 667 | 639 | 621 | 624 | 25.4% |  |
| mozilla.svg | 2,167 | 786 | 709 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| hg0.svg | 1,980 | 765 | 691 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| debian.svg | 1,697 | 637 | 567 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| scion.svg | 1,419 | 604 | 538 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| aa.svg | 1,385 | 529 | 446 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| cartman.svg | 1,157 | 544 | 452 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| penrose-tiling.svg | 1,133 | 380 | 314 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| eee.svg | 1,065 | 493 | 435 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| ruby.svg | 1,061 | 434 | 365 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| instiki.svg | 965 | 441 | 376 | 645 | 438 | 344 | 449 | 46.5% |  |
| fsm.svg | 956 | 456 | 352 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |
| poi.svg | 211 | 150 | 75 | 82 | 69 | 61 | 62 | 29.4% |  |
| openweb.svg | 206 | 165 | 99 | 86 | 93 | 90 | 83 | 40.3% |  |
| copyleft.svg | 202 | 166 | 73 | 76 | 73 | 61 | 66 | 32.7% |  |
| copyright.svg | 202 | 168 | 73 | 76 | 73 | 62 | 66 | 32.7% |  |
| openid.svg | 195 | 157 | 92 | 89 | 88 | 83 | 26 | 13.3% |  |
| iw.svg | 191 | 158 | 90 | 99 | 87 | 79 | 83 | 43.5% |  |
| mars.svg | 185 | 161 | 80 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| heart.svg | 178 | 154 | 81 | 82 | 77 | 66 | 74 | 41.6% |  |
| osi.svg | 178 | 148 | 73 | 64 | 70 | 64 | 66 | 37.1% |  |
| star.svg | 177 | 152 | 80 | 71 | 70 | 60 | 67 | 37.9% |  |
| odf.svg | 176 | 154 | 82 | 78 | 77 | 73 | 65 | 36.9% |  |
| betterplace.svg | 163 | 141 | 73 | 51 | 61 | 56 | 59 | 36.2% |  |
| image.svg | 157 | 278 | 219 | 54 | 63 | 57 | 71 | 45.2% |  |
| x11.svg | 144 | 133 | 73 | 75 | 70 | 60 | 69 | 47.9% |  |
| adobe.svg | 143 | 137 | 77 | 63 | 71 | 65 | 66 | 46.2% |  |

### material-design (1,000 files)

| File | SVG | SVG+zstd | SVG+dict | TVG | TVG+zstd | TVG+brotli | TVG+dict | dict/SVG | notes |
|------|-----|----------|----------|-----|----------|------------|----------|----------|-------|
| kubernetes.svg | 4,549 | 1,401 | 1,300 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| timer-3.svg | 2,932 | 928 | 843 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| timer-10.svg | 2,629 | 865 | 763 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| paw-off-outline.svg | 2,380 | 907 | 808 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| microsoft-teams.svg | 2,166 | 708 | 632 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| laravel.svg | 1,675 | 517 | 421 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| menorah-fire.svg | 1,630 | 432 | 318 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| smoke-detector-variant-off.svg | 1,538 | 664 | 551 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| klingon.svg | 1,492 | 621 | 513 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| webhook.svg | 1,454 | 619 | 525 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| storefront.svg | 1,426 | 588 | 488 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| microsoft-outlook.svg | 1,417 | 568 | 480 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| sort-numeric-ascending-variant.svg | 1,393 | 557 | 466 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| cog-transfer-outline.svg | 1,375 | 508 | 388 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| ship-wheel.svg | 1,334 | 524 | 427 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |
| view-carousel.svg | 141 | 118 | 53 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| arrow-left-bold.svg | 140 | 115 | 55 | 45 | 58 | 50 | 48 | 34.3% |  |
| numeric-negative-1.svg | 140 | 111 | 48 | 53 | 62 | 56 | 44 | 31.4% |  |
| square-wave.svg | 138 | 111 | 55 | 56 | 63 | 52 | 26 | 18.8% |  |
| tie.svg | 138 | 110 | 53 | 53 | 55 | 49 | 48 | 34.8% |  |
| roman-numeral-5.svg | 136 | 108 | 51 | 49 | 55 | 49 | 29 | 21.3% |  |
| flash.svg | 131 | 106 | 45 | 45 | 54 | 44 | 43 | 32.8% |  |
| forward.svg | 131 | 105 | 45 | 45 | 54 | 47 | 42 | 32.1% |  |
| play.svg | 131 | 101 | 41 | 31 | 44 | 36 | 38 | 29.0% |  |
| format-title.svg | 130 | 106 | 44 | 44 | 57 | 49 | 26 | 20.0% |  |
| alpha-t.svg | 126 | 102 | 42 | 44 | 57 | 46 | 35 | 27.8% |  |
| step-forward.svg | 126 | 104 | 43 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| moon-last-quarter.svg | 125 | 102 | 39 | 35 | 48 | 38 | 34 | 27.2% |  |
| menu-right.svg | 122 | 100 | 37 | 33 | 46 | 38 | 25 | 20.5% |  |
| power-on.svg | 118 | 98 | 36 | 32 | 45 | 37 | 38 | 32.2% |  |

### papirus (1,000 files)

| File | SVG | SVG+zstd | SVG+dict | TVG | TVG+zstd | TVG+brotli | TVG+dict | dict/SVG | notes |
|------|-----|----------|----------|-----|----------|------------|----------|----------|-------|
| bluegriffon.svg | 18,509 | 4,472 | 4,275 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| preferences-system-services.svg | 14,975 | 3,253 | 2,853 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| aks.svg | 14,043 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | no_source |
| freac.svg | 12,945 | 2,974 | 2,565 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| conky.svg | 12,821 | 2,562 | 2,451 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| com.github.birros.WebArchives.svg | 11,893 | 1,207 | 814 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| im.fluffychat.Fluffychat.svg | 11,127 | 2,563 | 2,382 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| meshlab.svg | 10,827 | 3,486 | 3,300 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| net.pioneerspacesim.Pioneer.svg | 10,449 | 2,449 | 2,260 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| com.github.donadigo.eddy.svg | 10,108 | 2,040 | 1,797 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| cc3d.svg | 10,011 | 2,971 | 2,701 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| thunderbird.svg | 9,386 | 1,556 | 1,428 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| xdman.svg | 8,923 | 2,811 | 2,599 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| cadence.svg | 8,894 | 1,912 | 1,656 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| skyrim-script-extender.svg | 8,879 | 2,155 | 1,762 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |
| emblem-favorite.svg | 485 | 295 | 173 | 180 | 171 | 169 | 147 | 30.3% |  |
| battery-empty.svg | 470 | 266 | 188 | 110 | 103 | 97 | 33 | 7.0% |  |
| battery-low.svg | 470 | 259 | 176 | 118 | 90 | 87 | 62 | 13.2% |  |
| emblem-dropbox-app.svg | 459 | 328 | 219 | 226 | 201 | 201 | 194 | 42.3% |  |
| nightsky.svg | 458 | 226 | 73 | 223 | 137 | 133 | 77 | 16.8% |  |
| emblem-unlocked.svg | 428 | 277 | 166 | 178 | 162 | 163 | 143 | 33.4% |  |
| mame.svg | 378 | 204 | 117 | 159 | 117 | 107 | 103 | 27.2% |  |
| emblem-photos.svg | 321 | 228 | 125 | 157 | 137 | 128 | 108 | 33.6% |  |
| vcs-conflicting.svg | 245 | 178 | 92 | 78 | 86 | 83 | 71 | 29.0% |  |
| emblem-default.svg | 240 | 177 | 92 | 81 | 94 | 86 | 71 | 29.6% |  |
| emblem-important.svg | 219 | 165 | 72 | 84 | 78 | 76 | 54 | 24.7% |  |
| emblem-new.svg | 196 | 169 | 79 | 78 | 78 | 77 | 61 | 31.1% |  |
| Nextcloud_ok.svg | 189 | 169 | 80 | 76 | 89 | 81 | 72 | 38.1% |  |
| emblem-downloads.svg | 187 | 179 | 78 | 91 | 84 | 84 | 69 | 36.9% |  |
| emblem-remove.svg | 156 | 160 | 68 | 60 | 69 | 65 | 51 | 32.7% |  |

### freesvg (5 files)

| File | SVG | SVG+zstd | SVG+dict | TVG | TVG+zstd | TVG+brotli | TVG+dict | dict/SVG | notes |
|------|-----|----------|----------|-----|----------|------------|----------|----------|-------|
| woman-in-blue-bikini.svg | 158,938 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | no_source |
| reddresslady-1919-remix.svg | 29,820 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | no_source |
| spatula.svg | 10,911 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | no_source |
| chip.svg | 5,641 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | no_source |
| 1638862592editor FreeSVG updated Vector  | 1,868 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | no_source |

### tabler (4,985 files)

| File | SVG | SVG+zstd | SVG+dict | TVG | TVG+zstd | TVG+brotli | TVG+dict | dict/SVG | notes |
|------|-----|----------|----------|-----|----------|------------|----------|----------|-------|
| laurel-wreath-3.svg | 2,114 | 1,015 | 847 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| laurel-wreath-2.svg | 2,000 | 957 | 783 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| laurel-wreath-1.svg | 1,999 | 964 | 799 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| laurel-wreath.svg | 1,886 | 911 | 756 | 927 | 790 | 765 | 745 | 39.5% |  |
| blender.svg | 1,683 | 790 | 653 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| caret-left-right.svg | 1,607 | 531 | 315 | 838 | 583 | 520 | 572 | 35.6% |  |
| brand-snapchat.svg | 1,554 | 740 | 409 | 775 | 687 | 634 | 670 | 43.1% |  |
| paw.svg | 1,486 | 808 | 674 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| caret-up-down.svg | 1,458 | 543 | 251 | 831 | 598 | 513 | 588 | 40.3% |  |
| stars.svg | 1,265 | 389 | 270 | 563 | 438 | 411 | 412 | 32.6% |  |
| live-photo.svg | 1,207 | 335 | 205 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| receipt-rupee.svg | 1,130 | 528 | 192 | 614 | 490 | 460 | 151 | 13.4% |  |
| biohazard.svg | 1,117 | 552 | 414 | 525 | 436 | 437 | 394 | 35.3% |  |
| brand-messenger.svg | 1,101 | 514 | 395 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| cookie.svg | 1,079 | 527 | 373 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |
| player-play.svg | 171 | 144 | 58 | 71 | 72 | 71 | 56 | 32.7% |  |
| columns-1.svg | 170 | 138 | 42 | 80 | 65 | 53 | 37 | 21.8% |  |
| crop-1-1.svg | 170 | 139 | 38 | 80 | 65 | 55 | 39 | 22.9% |  |
| crop-16-9.svg | 170 | 138 | 43 | 80 | 69 | 62 | 48 | 28.2% |  |
| crop-5-4.svg | 170 | 140 | 43 | 80 | 69 | 63 | 48 | 28.2% |  |
| crop-portrait.svg | 170 | 140 | 39 | 80 | 69 | 57 | 26 | 15.3% |  |
| crop-3-2.svg | 169 | 137 | 44 | 80 | 65 | 60 | 48 | 28.4% |  |
| crop-7-5.svg | 169 | 139 | 44 | 80 | 69 | 63 | 49 | 29.0% |  |
| crop-landscape.svg | 169 | 139 | 44 | 80 | 69 | 63 | 49 | 29.0% |  |
| oval-vertical.svg | 167 | 147 | 62 | 74 | 75 | 79 | 71 | 42.5% |  |
| test-pipe-2.svg | 167 | 146 | 53 | 80 | 77 | 63 | 51 | 30.5% |  |
| circle.svg | 166 | 148 | 26 | 56 | 66 | 53 | 54 | 32.5% |  |
| capsule-horizontal.svg | 165 | 142 | 60 | 69 | 71 | 65 | 50 | 30.3% |  |
| player-record.svg | 164 | 148 | 53 | 56 | 66 | 60 | 53 | 32.3% |  |
| point.svg | 158 | 143 | 53 | 56 | 61 | 54 | 50 | 31.6% |  |

### lucide (1,669 files)

| File | SVG | SVG+zstd | SVG+dict | TVG | TVG+zstd | TVG+brotli | TVG+dict | dict/SVG | notes |
|------|-----|----------|----------|-----|----------|------------|----------|----------|-------|
| hop.svg | 929 | 507 | 338 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| hop-off.svg | 846 | 483 | 306 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| wheat.svg | 724 | 286 | 152 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| brain-cog.svg | 722 | 398 | 226 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| wheat-off.svg | 721 | 371 | 209 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| gamepad-directional.svg | 699 | 324 | 166 | 348 | 201 | 198 | 91 | 13.0% |  |
| fish-off.svg | 682 | 413 | 245 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| component.svg | 663 | 251 | 116 | 300 | 172 | 160 | 153 | 23.1% |  |
| nut-off.svg | 649 | 412 | 243 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| puzzle.svg | 640 | 276 | 138 | 257 | 176 | 168 | 166 | 25.9% |  |
| receipt-text.svg | 636 | 256 | 116 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| dog.svg | 614 | 393 | 223 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| nut.svg | 612 | 383 | 226 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| server-cog.svg | 585 | 316 | 158 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| vault.svg | 584 | 247 | 95 | 292 | 158 | 151 | 86 | 14.7% |  |
| ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |
| move-up-right.svg | 197 | 153 | 45 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| signal-low.svg | 196 | 151 | 41 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| plus.svg | 195 | 151 | 43 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| check.svg | 194 | 151 | 41 | 39 | 52 | 40 | 38 | 19.6% |  |
| equal.svg | 194 | 151 | 42 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| chevron-left.svg | 193 | 150 | 39 | 39 | 48 | 40 | 35 | 18.1% |  |
| chevron-up.svg | 193 | 149 | 40 | 39 | 48 | 40 | 36 | 18.7% |  |
| tally-2.svg | 193 | 148 | 39 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| chevron-right.svg | 192 | 147 | 35 | 39 | 48 | 40 | 34 | 17.7% |  |
| chevron-down.svg | 191 | 147 | 37 | 39 | 48 | 40 | 35 | 18.3% |  |
| slash.svg | 189 | 144 | 34 | 34 | 47 | 35 | 32 | 16.9% |  |
| wifi-zero.svg | 189 | 146 | 34 | 32 | 45 | 35 | 31 | 16.4% |  |
| signal-zero.svg | 188 | 145 | 35 | 32 | 45 | 35 | 33 | 17.6% |  |
| minus.svg | 187 | 145 | 36 | 32 | 45 | 35 | 31 | 16.6% |  |
| tally-1.svg | 186 | 144 | 33 | 32 | 45 | 34 | 31 | 16.7% |  |

### bootstrap (2,078 files)

| File | SVG | SVG+zstd | SVG+dict | TVG | TVG+zstd | TVG+brotli | TVG+dict | dict/SVG | notes |
|------|-----|----------|----------|-----|----------|------------|----------|----------|-------|
| tux.svg | 4,757 | 2,220 | 1,982 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| flower1.svg | 2,953 | 1,114 | 994 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| filetype-scss.svg | 2,733 | 1,042 | 453 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| puzzle.svg | 2,518 | 1,061 | 947 | 1,339 | 1,018 | 994 | 628 | 24.9% |  |
| yelp.svg | 2,398 | 1,167 | 987 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| snapchat.svg | 2,346 | 1,177 | 1,007 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| filetype-sass.svg | 2,311 | 897 | 336 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| cup-hot.svg | 2,176 | 608 | 427 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| tornado.svg | 2,153 | 1,092 | 935 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| browser-safari.svg | 2,113 | 676 | 546 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| cup-hot-fill.svg | 2,086 | 567 | 388 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| filetype-css.svg | 2,069 | 1,006 | 436 | 1,134 | 920 | 870 | 725 | 35.0% |  |
| fingerprint.svg | 2,057 | 918 | 748 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| cake2.svg | 1,982 | 903 | 746 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| keyboard.svg | 1,829 | 338 | 199 | 1,154 | 289 | 263 | 256 | 14.0% |  |
| ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |
| record-circle-fill.svg | 201 | 164 | 53 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| slash.svg | 200 | 159 | 55 | 68 | 68 | 59 | 53 | 26.5% |  |
| substack.svg | 199 | 174 | 84 | 72 | 78 | 77 | 71 | 35.7% |  |
| magnet-fill.svg | 198 | 170 | 75 | 92 | 83 | 72 | 58 | 29.3% |  |
| person-fill.svg | 198 | 165 | 67 | 104 | 84 | 75 | 70 | 35.4% |  |
| square-fill.svg | 196 | 151 | 48 | 80 | 64 | 51 | 29 | 14.8% |  |
| toggle-on.svg | 194 | 159 | 67 | 79 | 69 | 63 | 26 | 13.4% |  |
| circle.svg | 189 | 158 | 35 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| record.svg | 188 | 155 | 60 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| record-fill.svg | 181 | 155 | 49 | 46 | 54 | 50 | 26 | 14.4% |  |
| circle-half.svg | 180 | 155 | 49 | 64 | 63 | 49 | 46 | 25.6% |  |
| dash.svg | 176 | 147 | 49 | 64 | 61 | 59 | 45 | 25.6% |  |
| egg-fill.svg | 174 | 152 | 59 | 60 | 64 | 61 | 54 | 31.0% |  |
| dot.svg | 161 | 139 | 39 | 46 | 54 | 40 | 38 | 23.6% |  |
| circle-fill.svg | 144 | 131 | 41 | 38 | 48 | 36 | 36 | 25.0% |  |

### simple-icons (3,395 files)

| File | SVG | SVG+zstd | SVG+dict | TVG | TVG+zstd | TVG+brotli | TVG+dict | dict/SVG | notes |
|------|-----|----------|----------|-----|----------|------------|----------|----------|-------|
| elsevier.svg | 53,004 | 19,624 | 19,177 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| composer.svg | 35,877 | 13,669 | 13,032 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| newjapanprowrestling.svg | 23,795 | 10,120 | 9,714 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| interactiondesignfoundation.svg | 21,893 | 7,369 | 6,975 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| porsche.svg | 21,328 | 7,623 | 7,095 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| unilever.svg | 21,222 | 8,119 | 7,906 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| postcss.svg | 20,747 | 7,623 | 7,426 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| ferrari.svg | 19,139 | 6,872 | 6,654 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| gutenberg.svg | 18,031 | 6,307 | 6,071 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| unitednations.svg | 17,957 | 6,038 | 5,866 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| virgin.svg | 16,894 | 6,309 | 6,112 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| openbsd.svg | 15,794 | 6,875 | 6,646 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| libuv.svg | 14,693 | 6,274 | 6,010 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| gnu.svg | 14,516 | 6,261 | 6,028 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| habr.svg | 14,289 | 6,326 | 6,150 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |
| istio.svg | 129 | 124 | 62 | 61 | 65 | 54 | 54 | 41.9% |  |
| wgpu.svg | 129 | 122 | 55 | 64 | 65 | 59 | 54 | 41.9% |  |
| elevenlabs.svg | 128 | 121 | 58 | 47 | 60 | 52 | 47 | 36.7% |  |
| radar.svg | 128 | 122 | 47 | 38 | 51 | 43 | 45 | 35.2% |  |
| telegraph.svg | 126 | 122 | 59 | 59 | 60 | 53 | 45 | 35.7% |  |
| saltproject.svg | 125 | 121 | 56 | 48 | 61 | 53 | 49 | 39.2% |  |
| bandcamp.svg | 124 | 122 | 51 | 36 | 49 | 41 | 44 | 35.5% |  |
| framer.svg | 124 | 120 | 51 | 61 | 64 | 54 | 51 | 41.1% |  |
| ktor.svg | 123 | 119 | 50 | 61 | 57 | 46 | 54 | 43.9% |  |
| suckless.svg | 122 | 119 | 50 | 56 | 62 | 55 | 48 | 39.3% |  |
| cratedb.svg | 120 | 120 | 52 | 56 | 64 | 58 | 47 | 39.2% |  |
| netapp.svg | 118 | 115 | 48 | 44 | 57 | 49 | 45 | 38.1% |  |
| kedro.svg | 112 | 111 | 40 | 38 | 46 | 36 | 41 | 36.6% |  |
| vercel.svg | 111 | 110 | 43 | 31 | 44 | 36 | 37 | 33.3% |  |
| kotlin.svg | 109 | 110 | 42 | 37 | 50 | 42 | 40 | 36.7% |  |

### phosphor (1,512 files)

| File | SVG | SVG+zstd | SVG+dict | TVG | TVG+zstd | TVG+brotli | TVG+dict | dict/SVG | notes |
|------|-----|----------|----------|-----|----------|------------|----------|----------|-------|
| flower.svg | 1,485 | 455 | 274 | 328 | 255 | 261 | 237 | 16.0% |  |
| hands-clapping.svg | 1,179 | 388 | 224 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:color |
| fediverse-logo.svg | 1,092 | 358 | 183 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:color |
| open-ai-logo.svg | 1,078 | 320 | 164 | 198 | 155 | 137 | 129 | 12.0% |  |
| seal-percent.svg | 1,049 | 412 | 241 | 299 | 245 | 237 | 32 | 3.1% |  |
| flower-lotus.svg | 1,019 | 459 | 290 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| cow.svg | 1,011 | 362 | 173 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:color |
| graph.svg | 976 | 293 | 122 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:color |
| users-four.svg | 941 | 232 | 91 | 189 | 102 | 98 | 81 | 8.6% |  |
| paw-print.svg | 920 | 292 | 131 | 212 | 141 | 146 | 124 | 13.5% |  |
| fingerprint.svg | 912 | 371 | 208 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| git-pull-request.svg | 903 | 261 | 101 | 151 | 100 | 101 | 80 | 8.9% |  |
| film-reel.svg | 893 | 226 | 77 | 157 | 95 | 91 | 26 | 2.9% |  |
| globe-hemisphere-west.svg | 884 | 421 | 231 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| seal-question.svg | 873 | 424 | 248 | 315 | 279 | 264 | 82 | 9.4% |  |
| ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |
| control.svg | 237 | 171 | 41 | 34 | 47 | 38 | 37 | 15.6% |  |
| caret-right.svg | 236 | 172 | 38 | 34 | 47 | 39 | 36 | 15.3% |  |
| cell-signal-low.svg | 236 | 172 | 46 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| number-seven.svg | 235 | 171 | 42 | 32 | 45 | 37 | 34 | 14.5% |  |
| number-one.svg | 234 | 172 | 44 | 32 | 45 | 37 | 36 | 15.4% |  |
| x.svg | 232 | 175 | 48 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| line-vertical.svg | 229 | 167 | 33 | 27 | 40 | 32 | 33 | 14.4% |  |
| minus.svg | 229 | 168 | 36 | 27 | 40 | 32 | 33 | 14.4% |  |
| cell-signal-none.svg | 227 | 166 | 34 | 27 | 40 | 32 | 33 | 14.5% |  |
| equals.svg | 227 | 173 | 46 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| dot-outline.svg | 216 | 172 | 33 | 40 | 50 | 44 | 35 | 16.2% |  |
| dots-three-vertical.svg | 208 | 140 | 42 | 86 | 62 | 63 | 45 | 21.6% |  |
| dots-three.svg | 208 | 139 | 41 | 86 | 62 | 65 | 46 | 22.1% |  |
| dot.svg | 141 | 131 | 30 | 38 | 48 | 40 | 31 | 22.0% |  |
| wifi-none.svg | 141 | 134 | 33 | 38 | 48 | 40 | 36 | 25.5% |  |

### fontawesome (2,583 files)

| File | SVG | SVG+zstd | SVG+dict | TVG | TVG+zstd | TVG+brotli | TVG+dict | dict/SVG | notes |
|------|-----|----------|----------|-----|----------|------------|----------|----------|-------|
| old-republic.svg | 8,857 | 3,682 | 3,475 | 4,869 | 4,141 | 4,154 | 3,927 | 44.3% |  |
| wizards-of-the-coast.svg | 6,647 | 2,895 | 2,699 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| reacteurope.svg | 6,459 | 2,239 | 2,099 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| critical-role.svg | 6,421 | 2,846 | 2,660 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| the-red-yeti.svg | 6,328 | 2,777 | 2,583 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| grunt.svg | 5,667 | 2,515 | 2,320 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| rust.svg | 5,643 | 2,267 | 2,066 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| mandalorian.svg | 5,200 | 2,281 | 2,086 | 2,924 | 2,494 | 2,379 | 2,496 | 48.0% |  |
| optin-monster.svg | 4,900 | 2,135 | 1,962 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| openstreetmap.svg | 4,816 | 2,235 | 2,047 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| d-and-d.svg | 4,738 | 2,182 | 1,949 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| debian.svg | 4,680 | 2,144 | 1,934 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| jenkins.svg | 4,518 | 2,092 | 1,887 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| salesforce.svg | 4,230 | 1,776 | 1,520 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| d-and-d-beyond.svg | 4,210 | 1,936 | 1,729 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |
| o.svg | 405 | 275 | 71 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| circle.svg | 404 | 279 | 37 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| genderless.svg | 404 | 274 | 70 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| flutter.svg | 403 | 297 | 79 | 67 | 75 | 72 | 66 | 16.4% |  |
| minus.svg | 402 | 289 | 42 | 80 | 74 | 71 | 27 | 6.7% |  |
| subtract.svg | 402 | 289 | 42 | 80 | 74 | 71 | 27 | 6.7% |  |
| window-minimize.svg | 402 | 288 | 50 | 80 | 71 | 60 | 64 | 15.9% |  |
| microsoft.svg | 399 | 285 | 75 | 77 | 79 | 68 | 64 | 16.0% |  |
| black-tie.svg | 396 | 302 | 80 | 66 | 79 | 71 | 66 | 16.7% |  |
| unsplash.svg | 391 | 285 | 71 | 62 | 75 | 67 | 66 | 16.9% |  |
| bandcamp.svg | 387 | 284 | 71 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| ethereum.svg | 384 | 281 | 69 | 59 | 69 | 64 | 57 | 14.8% |  |
| yandex-international.svg | 380 | 292 | 74 | 55 | 68 | 60 | 59 | 15.5% |  |
| flipboard.svg | 379 | 284 | 68 | 59 | 72 | 64 | 63 | 16.6% |  |
| houzz.svg | 370 | 285 | 67 | 52 | 65 | 57 | 57 | 15.4% |  |

### remixicon (3,229 files)

| File | SVG | SVG+zstd | SVG+dict | TVG | TVG+zstd | TVG+brotli | TVG+dict | dict/SVG | notes |
|------|-----|----------|----------|-----|----------|------------|----------|----------|-------|
| blender-fill.svg | 2,308 | 728 | 588 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| java-line.svg | 2,179 | 1,127 | 990 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| deepseek-fill.svg | 2,007 | 1,037 | 879 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| reactjs-line.svg | 1,969 | 910 | 789 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| openai-fill.svg | 1,930 | 845 | 734 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| reactjs-fill.svg | 1,885 | 850 | 745 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| java-fill.svg | 1,819 | 965 | 824 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| ghost-4-line.svg | 1,790 | 907 | 770 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| snapchat-line.svg | 1,748 | 912 | 762 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| wechat-channels-line.svg | 1,685 | 897 | 759 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| deepseek-line.svg | 1,587 | 855 | 720 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| instagram-line.svg | 1,516 | 688 | 566 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| evernote-line.svg | 1,503 | 797 | 650 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| behance-fill.svg | 1,493 | 753 | 626 | n/a | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| github-line.svg | 1,493 | 781 | 640 | 677 | 633 | 586 | 609 | 40.8% |  |
| ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |
| arrow-left-fill.svg | 122 | 121 | 44 | 45 | 54 | 49 | 40 | 32.8% |  |
| arrow-right-fill.svg | 122 | 121 | 43 | 45 | 54 | 46 | 44 | 36.1% |  |
| skip-up-fill.svg | 122 | 121 | 46 | 46 | 59 | 51 | 48 | 39.3% |  |
| text.svg | 121 | 122 | 43 | 44 | 57 | 49 | 40 | 33.1% |  |
| vercel-fill.svg | 120 | 120 | 41 | 31 | 44 | 36 | 40 | 33.3% |  |
| arrow-down-s-fill.svg | 112 | 113 | 36 | 31 | 44 | 36 | 35 | 31.2% |  |
| subtract-fill.svg | 112 | 115 | 38 | 32 | 45 | 37 | 36 | 32.1% |  |
| subtract-line.svg | 112 | 114 | 36 | 32 | 45 | 37 | 38 | 33.9% |  |
| arrow-drop-down-fill.svg | 111 | 112 | 33 | 31 | 44 | 36 | 37 | 33.3% |  |
| arrow-drop-right-fill.svg | 111 | 113 | 36 | 31 | 44 | 36 | 37 | 33.3% |  |
| arrow-drop-up-fill.svg | 111 | 112 | 34 | 31 | 44 | 36 | 35 | 31.5% |  |
| arrow-left-s-fill.svg | 111 | 113 | 38 | 31 | 44 | 36 | 37 | 33.3% |  |
| arrow-right-s-fill.svg | 111 | 113 | 37 | 31 | 44 | 36 | 37 | 33.3% |  |
| arrow-drop-left-fill.svg | 110 | 113 | 37 | 31 | 44 | 36 | 38 | 34.5% |  |
| arrow-up-s-fill.svg | 110 | 112 | 34 | 31 | 44 | 36 | 36 | 32.7% |  |

## Top 20 Best Compression Ratios (TVG+zstd+dict as % of SVG)

| File | Group | SVG | SVG+zstd | TVG | TVG+dict | dict/SVG |
|------|-------|-----|----------|-----|----------|----------|
| folder-red-kde.svg | papirus | 1,722 | 735 | 902 | 41 | 2.4% |
| ladder-water.svg | fontawesome | 1,280 | 662 | 527 | 31 | 2.4% |
| swimming-pool.svg | fontawesome | 1,280 | 662 | 527 | 31 | 2.4% |
| water-ladder.svg | fontawesome | 1,280 | 662 | 527 | 31 | 2.4% |
| folder-bluegrey-kde.svg | papirus | 1,722 | 735 | 902 | 42 | 2.4% |
| screwdriver-wrench.svg | fontawesome | 1,094 | 649 | 411 | 28 | 2.6% |
| tools.svg | fontawesome | 1,094 | 649 | 411 | 28 | 2.6% |
| folder-grey-github.svg | papirus | 1,637 | 723 | 833 | 42 | 2.6% |
| folder-nordic-github.svg | papirus | 1,637 | 732 | 833 | 42 | 2.6% |
| chain-broken.svg | fontawesome | 1,167 | 669 | 442 | 30 | 2.6% |
| chain-slash.svg | fontawesome | 1,167 | 669 | 442 | 30 | 2.6% |
| link-slash.svg | fontawesome | 1,167 | 669 | 442 | 30 | 2.6% |
| unlink.svg | fontawesome | 1,167 | 669 | 442 | 30 | 2.6% |
| earth-america.svg | fontawesome | 1,107 | 601 | 476 | 31 | 2.8% |
| earth-americas.svg | fontawesome | 1,107 | 601 | 476 | 31 | 2.8% |
| earth.svg | fontawesome | 1,107 | 601 | 476 | 31 | 2.8% |
| globe-americas.svg | fontawesome | 1,107 | 601 | 476 | 31 | 2.8% |
| cc-square.svg | bootstrap | 1,595 | 403 | 784 | 45 | 2.8% |
| opengl.svg | papirus | 1,234 | 431 | 480 | 35 | 2.8% |
| heart-pulse.svg | fontawesome | 969 | 603 | 356 | 28 | 2.9% |

## Bottom 20 Worst Compression Ratios (TVG+zstd+dict as % of SVG)

| File | Group | SVG | SVG+zstd | TVG | TVG+dict | dict/SVG |
|------|-------|-----|----------|-----|----------|----------|
| stubhub.svg | simple-icons | 2,264 | 1,038 | 1,247 | 1,104 | 48.8% |
| playstation3.svg | simple-icons | 1,028 | 517 | 539 | 503 | 48.9% |
| libreoffice-calc.svg | papirus | 895 | 409 | 966 | 440 | 49.2% |
| yahoo.svg | w3c | 443 | 271 | 287 | 218 | 49.2% |
| ardour.svg | simple-icons | 1,014 | 471 | 501 | 504 | 49.7% |
| couchdb.svg | w3c | 447 | 289 | 302 | 224 | 50.1% |
| stock-line.svg | remixicon | 199 | 147 | 125 | 100 | 50.3% |
| mono.svg | w3c | 402 | 274 | 287 | 203 | 50.5% |
| genshi.svg | w3c | 290 | 196 | 189 | 147 | 50.7% |
| crown.svg | tabler | 269 | 209 | 147 | 137 | 50.9% |
| bookbub.svg | simple-icons | 680 | 310 | 445 | 347 | 51.0% |
| cmplid.svg | fontawesome | 1,894 | 860 | 1,128 | 973 | 51.4% |
| claude-fill.svg | remixicon | 1,227 | 637 | 787 | 642 | 52.3% |
| rescript.svg | simple-icons | 646 | 392 | 386 | 341 | 52.8% |
| facebook.svg | w3c | 299 | 212 | 242 | 158 | 52.8% |
| check.svg | w3c | 296 | 207 | 202 | 158 | 53.4% |
| microformat.svg | w3c | 329 | 189 | 251 | 176 | 53.5% |
| python.svg | simple-icons | 1,493 | 711 | 1,006 | 807 | 54.1% |
| cloud-upload.svg | material-design | 279 | 243 | 170 | 155 | 55.6% |
| vmware.svg | w3c | 274 | 161 | 243 | 159 | 58.0% |
