# SVG Compression vs Zstd Dictionary Size

This report studies how SVG compression with zstd varies as a function of
dictionary size. All files are SVGO-optimized SVGs from the TinyVG benchmark
and extended icon set corpus.

## Methodology

- **Corpus**: 21,539 SVGO-optimized SVG files across 11 icon set groups
- **Total uncompressed size**: 14,135,315 bytes (13.5 MB)
- **Compression**: `zstd --ultra -22` (maximum compression level)
- **Dictionary training**: `zstd --train` (default fastCOVER) for fixed sizes;
  `--train-fastcover=d=8,steps=40,shrink=N` for auto-optimized sizes
- **Dictionaries trained on the same corpus** being compressed (best-case scenario)

## Overall Summary

| Dictionary | Dict size | Total compressed | % of SVG | Savings vs no-dict |
|------------|-----------|-----------------|----------|-------------------|
| no-dict (zstd -22) | - | 7,676,895 | 54.3% | - |
| 64KB | 65,536 | 4,495,334 | 31.8% | 41.4% |
| 110KB | 112,640 | 4,392,493 | 31.1% | 42.8% |
| 256KB | 262,144 | 4,238,599 | 30.0% | 44.8% |
| 512KB | 524,288 | 4,092,692 | 29.0% | 46.7% |

**Total uncompressed SVG**: 14,135,315 bytes

## Marginal Value of Dictionary Size

How much additional compression does each step up in dictionary size provide?

| From | To | Additional savings | Marginal % |
|------|-----|-------------------|-----------|
| no-dict (0B) | 64KB (65,536B) | 3,181,561 bytes | 41.44% |
| 64KB (65,536B) | 110KB (112,640B) | 102,841 bytes | 2.29% |
| 110KB (112,640B) | 256KB (262,144B) | 153,894 bytes | 3.50% |
| 256KB (262,144B) | 512KB (524,288B) | 145,907 bytes | 3.44% |

## Auto-Optimized Dictionary Sizes (shrink)

The zstd `--train-fastcover` `shrink` flag trains a full-size dictionary,
then binary-searches for the smallest dictionary within N% of full-size
compression ratio. Starting from a 512KB ceiling:

| Variant | Regression tolerance | Resulting dict size | Total compressed | % of SVG |
|---------|---------------------|--------------------|-----------------| ---------|
| shrink-1% | 1% | 524,288 (512KB) | 4,079,350 | 28.9% |
| shrink-2% | 2% | 524,288 (512KB) | 4,079,350 | 28.9% |
| shrink-5% | 5% | 524,288 (512KB) | 4,079,350 | 28.9% |

**Finding**: The shrink optimizer kept the full 512KB dictionary at all
tolerance levels (1%, 2%, 5%). This means that even small reductions
in dictionary size cause more than 5% regression in total compression
ratio — the dictionary content is genuinely utilized at 512KB.

## Per-Group Comparison

| Group | Files | SVG size | no-dict | 64KB | 110KB | 256KB | 512KB |
|-------|-------|----------|------|------|------|------|------|
| bootstrap | 2,078 | 1,192,520 | 56.2% | 30.8% | 29.5% | 27.8% | 27.2% |
| fontawesome | 2,583 | 2,331,044 | 57.0% | 28.2% | 26.8% | 26.1% | 24.7% |
| lucide | 1,669 | 523,261 | 67.3% | 25.5% | 25.3% | 24.6% | 24.4% |
| material-design | 997 | 345,387 | 66.3% | 41.3% | 40.9% | 39.4% | 39.3% |
| papirus | 967 | 1,565,679 | 38.0% | 22.7% | 21.9% | 20.8% | 20.0% |
| phosphor | 1,512 | 671,547 | 54.1% | 21.0% | 20.0% | 19.8% | 20.2% |
| remixicon | 3,229 | 1,127,942 | 67.1% | 35.4% | 35.0% | 34.0% | 33.1% |
| simple-icons | 3,395 | 4,382,749 | 48.8% | 40.1% | 39.6% | 38.4% | 36.6% |
| tabler | 4,985 | 1,771,748 | 64.9% | 26.0% | 25.5% | 24.3% | 24.1% |
| w3c | 115 | 57,797 | 57.8% | 41.5% | 41.6% | 40.7% | 40.7% |
| zig | 9 | 165,641 | 37.1% | 36.0% | 35.0% | 34.3% | 32.9% |
| **Total** | **21,539** | **14,135,315** | **54.3%** | **31.8%** | **31.1%** | **30.0%** | **29.0%** |

## Compression Ratio Distribution (compressed / SVG)

Percentiles of per-file compression ratio for each dictionary size:

| Percentile | no-dict | 64KB | 110KB | 256KB | 512KB |
|------------|------|------|------|------|------|
| p5 | 42.5% | 15.1% | 13.9% | 12.9% | 12.0% |
| p10 | 47.1% | 18.3% | 17.1% | 16.0% | 15.4% |
| p25 | 55.5% | 23.5% | 22.7% | 21.6% | 21.1% |
| Median | 64.4% | 29.5% | 28.9% | 28.2% | 27.6% |
| p75 | 71.7% | 38.0% | 37.5% | 36.8% | 36.3% |
| p90 | 77.1% | 43.3% | 43.0% | 42.3% | 41.9% |
| p95 | 81.2% | 45.2% | 44.8% | 44.2% | 44.0% |
| Mean | 63.3% | 30.3% | 29.6% | 28.8% | 28.2% |

## Key Findings

1. **no-dict to 64KB**: The first 64KB of dictionary provides the largest jump — 41.4% total savings (3,181,561 bytes)
2. **64KB to 110KB**: 2.3% additional savings (102,841 bytes)
3. **110KB to 256KB**: 3.5% additional savings (153,894 bytes)
4. **256KB to 512KB**: 3.4% additional savings (145,907 bytes)
5. **Shrink optimization**: The zstd shrink flag (tested at 1%, 2%, 5% regression tolerance) did not reduce the 512KB dictionary at all, indicating all dictionary content contributes meaningfully to compression of this corpus.

