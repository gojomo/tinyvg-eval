# TinyVG Compression Evaluation

An extended benchmark measuring how well SVG icon files compress as
[TinyVG](https://tinyvg.tech/) binaries versus as optimized SVG text, using
modern compressors (zstd, brotli) and trained zstd dictionaries.

## Key Results

**21,539 SVGO-optimized SVGs** from 12 icon sets (8,010 successfully converted to
TinyVG). Median per-file compression ratios (% of optimized SVG size):

| Scheme | Median |
|--------|--------|
| SVG + zstd -22 | 65.7% |
| SVG + zstd + 110KB dict | 31.7% |
| TVG (uncompressed) | 42.8% |
| TVG + brotli -11 | 37.2% |
| TVG + zstd + 110KB dict | **28.4%** |

TVG + zstd + dictionary achieves the best compression, but SVG + zstd + dictionary
is within 3.3 percentage points at median, while being applicable to the full
corpus (not just the 37% of files the converter handles).

Dictionary size matters: a 64KB dictionary provides the biggest jump (54% -> 32%),
with diminishing but steady returns up through at least 2MB. The zstd `shrink`
optimizer finds that even at 5% regression tolerance, no dictionary can be reduced
from its trained size, indicating all content is utilized.

## Dataset

| Group | Source | SVGs | Converted to TVG |
|-------|--------|------|------------------|
| zig | TinyVG benchmark | 9 | 8 (89%) |
| w3c | TinyVG benchmark | 115 | 76 (66%) |
| material-design | TinyVG benchmark | 1,000 | 346 (35%) |
| papirus | TinyVG benchmark | 1,000 | 519 (52%) |
| freesvg | TinyVG benchmark | 5 | 0 (0%) |
| tabler | [tabler-icons](https://github.com/tabler/tabler-icons) | 4,985 | 1,005 (20%) |
| lucide | [lucide](https://github.com/lucide-icons/lucide) | 1,669 | 459 (28%) |
| bootstrap | [bootstrap-icons](https://github.com/twbs/icons) | 2,078 | 918 (44%) |
| simple-icons | [simple-icons](https://github.com/simple-icons/simple-icons) | 3,395 | 1,345 (40%) |
| phosphor | [phosphor-icons](https://github.com/phosphor-icons/core) | 1,512 | 524 (35%) |
| fontawesome | [Font Awesome Free](https://github.com/FortAwesome/Font-Awesome) | 2,583 | 1,060 (41%) |
| remixicon | [Remix Icon](https://github.com/nicedoc/remixicon) | 3,229 | 1,750 (54%) |

Most conversion failures are due to unsupported SVG features (e.g. `currentColor`,
complex gradients, masks) in the TinyVG `svg2tvgt` converter.

## Scripts

| Script | Purpose |
|--------|---------|
| `setup.sh` | Download source SVGs, build TinyVG SDK tools |
| `diagnose_failures.py` | Full pipeline: convert all SVGs, compress TVGs and SVGs, train dictionaries, produce diagnostics CSV |
| `generate_report.py` | Generate `results/report.md` from the diagnostics CSV |
| `svg_dict_size_study.py` | Train dictionaries at multiple sizes (64KB-512KB), measure compression for each |
| `svg_dict_size_extended.py` | Extend dictionary study to 1MB and 2MB + shrink optimization |
| `patch_svg_compression.py` | Utility to add SVG compression columns to an existing diagnostics CSV without re-running conversions |
| `convert_and_analyze.py` | Earlier single-pass pipeline (superseded by `diagnose_failures.py`) |
| `svgo.config.js` | SVGO configuration matching the original TinyVG benchmark |

## Output Files

| File | Description |
|------|-------------|
| `results/report.md` | Main compression analysis report (TVG vs SVG, all schemes) |
| `results/svg_dict_size_report.md` | Dictionary size study report (SVG-only, 64KB through 2MB) |
| `results/all_files_diagnostics.csv` | Per-file data for all 21,580 files |
| `results/svg_dict_size_details.csv` | Per-file compression at each dictionary size |
| `results/tvg_dict.zstd` | Trained zstd dictionary for TVG files (110KB) |
| `results/svg_dict.zstd` | Trained zstd dictionary for SVG files (110KB) |
| `results/svg_dicts/` | Dictionaries at all tested sizes (64KB through 2MB) |

## Prerequisites

- Python 3.8+
- Node.js + SVGO (`npm install -g svgo`)
- Zig 0.14.0 (for building `tvg-text`)
- .NET 8 SDK (for `svg2tvgt`)
- zstd, brotli CLI tools

See `setup.sh` for full environment setup.
