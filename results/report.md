# TinyVG Compression Analysis Report

This report extends the [TinyVG benchmark](https://tinyvg.tech/) by measuring
the additional compression achievable on `.tvg` (TinyVG binary) files using
modern general-purpose compressors.

## Methodology

- **Source SVGs**: Drawn from the same public datasets used by the official
  TinyVG benchmark: Zig logos, W3C SVG samples, Material Design icons, and
  Papirus icons. (5 FreeSVG.org files omitted as no longer retrievable from source.)
- **SVG optimization**: Each SVG is first optimized with SVGO (multipass, precision 3)
  matching the original benchmark pipeline. SVG sizes in the tables below are the
  SVGO-optimized sizes as reported by the official TinyVG benchmark.
- **SVG -> TVG conversion**: `svg2tvgt` (SVG to TinyVG text) then `tvg-text`
  (TinyVG text to binary), from the [TinyVG SDK](https://github.com/TinyVG/sdk).
- **Compression**:
  - **zstd -22**: `zstd --ultra -22` (maximum compression level)
  - **brotli -11**: `brotli -q 11` (maximum quality)
  - **zstd -22 +dict**: A custom dictionary trained on all TVG files via
    `zstd --train --maxdict=65536`, then compressed with `zstd --ultra -22 -D dict`

All sizes in bytes. "% of SVG" = size / SVGO-optimized SVG size.
"% of TVG" = size / uncompressed TVG binary size.

### Dataset Notes

The original TinyVG benchmark used 2,129 SVG files. Our re-conversion using
current versions of the source datasets and TinyVG SDK yielded:

- **zig**: 8 of 9 files converted successfully
- **w3c**: 76 of 115 files converted successfully
- **material-design**: 346 of 1000 files converted successfully
- **papirus**: 519 of 1000 files converted successfully
- **freesvg**: 0 of 5 (files no longer retrievable from freesvg.org)

**Total: 949 files** analyzed. Of these, 948 have TVG sizes
within reasonable range of the original benchmark; 1 are outliers
(typically due to changed source SVGs or TinyVG SDK version differences).

Not all original files convert successfully because: (a) source SVG repos have
evolved since the benchmark was created, (b) `svg2tvgt` only supports a subset
of SVG features, and (c) some icon variants were drawn from different size
directories in the Papirus theme.

**Trained zstd dictionary size**: 65,536 bytes

## Overall Summary

| Metric | Total bytes | % of SVG | % of TVG |
|--------|------------|----------|----------|
| **SVG (SVGO-optimized)** | 763,431 | 100.0% | - |
| **TVG (uncompressed)** | 391,156 | 51.2% | 100.0% |
| **TVG + zstd -22** | 260,250 | 34.1% | 66.5% |
| **TVG + brotli -11** | 242,225 | 31.7% | 61.9% |
| **TVG + zstd -22 +dict** | 119,190 | 15.6% | 30.5% |

*948 files (excluding 1 outlier(s)) across 4 dataset groups.*

### Median per-file ratios (% of SVG)

| Metric | Median % of SVG |
|--------|----------------|
| TVG | 51.5% |
| TVG + zstd -22 | 41.0% |
| TVG + brotli -11 | 37.7% |
| TVG + zstd -22 +dict | 19.3% |

### Key Findings

1. **TVG alone** reduces SVGO-optimized SVGs to a median of **51.5%** of their size.
2. **TVG + brotli** achieves a median of **37.7%** of SVG size
   (further 27% reduction beyond TVG alone).
3. **TVG + zstd with a trained dictionary** achieves a median of just **19.3%**
   of SVG size -- reducing TVG files to a median of 40.5% of their
   uncompressed size. This is the most effective scheme tested.
4. The dictionary is most effective for **icon sets** with shared structure
   (Papirus: 12.6% of SVG), where common TVG header/structure
   patterns are factored out.

## Per-Group Summary

### zig (7 files (1 outlier(s) excluded))

| Metric | Total bytes | % of SVG | % of TVG |
|--------|------------|----------|----------|
| SVG (optimized) | 6,613 | 100.0% | - |
| TVG | 3,052 | 46.2% | 100.0% |
| TVG + zstd -22 | 2,202 | 33.3% | 72.1% |
| TVG + brotli -11 | 2,137 | 32.3% | 70.0% |
| TVG + zstd -22 +dict | 351 | 5.3% | 11.5% |

### w3c (76 files)

| Metric | Total bytes | % of SVG | % of TVG |
|--------|------------|----------|----------|
| SVG (optimized) | 34,546 | 100.0% | - |
| TVG | 17,036 | 49.3% | 100.0% |
| TVG + zstd -22 | 12,849 | 37.2% | 75.4% |
| TVG + brotli -11 | 11,636 | 33.7% | 68.3% |
| TVG + zstd -22 +dict | 9,561 | 27.7% | 56.1% |

### material-design (346 files)

| Metric | Total bytes | % of SVG | % of TVG |
|--------|------------|----------|----------|
| SVG (optimized) | 107,678 | 100.0% | - |
| TVG | 51,872 | 48.2% | 100.0% |
| TVG + zstd -22 | 45,096 | 41.9% | 86.9% |
| TVG + brotli -11 | 42,162 | 39.2% | 81.3% |
| TVG + zstd -22 +dict | 32,034 | 29.7% | 61.8% |

### papirus (519 files)

| Metric | Total bytes | % of SVG | % of TVG |
|--------|------------|----------|----------|
| SVG (optimized) | 614,594 | 100.0% | - |
| TVG | 319,196 | 51.9% | 100.0% |
| TVG + zstd -22 | 200,103 | 32.6% | 62.7% |
| TVG + brotli -11 | 186,290 | 30.3% | 58.4% |
| TVG + zstd -22 +dict | 77,244 | 12.6% | 24.2% |

## Per-File Details

Full per-file data is in `compression_data.csv`. Below are highlights per group,
sorted by SVG size (largest first). Outliers are marked with (*).

### zig

| File | SVG | TVG | zstd | brotli | zstd+dict | TVG/SVG | zstd/SVG | brotli/SVG | dict/SVG |
|------|-----|-----|------|--------|-----------|---------|----------|------------|----------|
| zero.svg (*) | 26,352 | 66,962 | 56,513 | 51,956 | 56,814 | 254.1% | 214.5% | 197.2% | 215.6% |
| zig-logo-dark.svg | 1,200 | 549 | 407 | 398 | 61 | 45.8% | 33.9% | 33.2% | 5.1% |
| zig-logo-light.svg | 1,197 | 549 | 405 | 392 | 62 | 45.9% | 33.8% | 32.7% | 5.2% |
| zig-logo-neg-black.svg | 1,178 | 545 | 401 | 397 | 66 | 46.3% | 34.0% | 33.7% | 5.6% |
| zig-logo-neg-white.svg | 1,175 | 545 | 401 | 395 | 71 | 46.4% | 34.1% | 33.6% | 6.0% |
| zig-mark-neg-black.svg | 622 | 288 | 196 | 182 | 27 | 46.3% | 31.5% | 29.3% | 4.3% |
| zig-mark.svg | 622 | 288 | 197 | 185 | 32 | 46.3% | 31.7% | 29.7% | 5.1% |
| zig-mark-neg-white.svg | 619 | 288 | 195 | 188 | 32 | 46.5% | 31.5% | 30.4% | 5.2% |

### w3c

| File | SVG | TVG | zstd | brotli | zstd+dict | TVG/SVG | zstd/SVG | brotli/SVG | dict/SVG |
|------|-----|-----|------|--------|-----------|---------|----------|------------|----------|
| penrose-staircase.svg | 3,231 | 649 | 335 | 339 | 74 | 20.1% | 10.4% | 10.5% | 2.3% |
| faux-art.svg | 2,456 | 667 | 639 | 621 | 639 | 27.2% | 26.0% | 25.3% | 26.0% |
| instiki.svg | 965 | 645 | 438 | 344 | 429 | 66.8% | 45.4% | 35.6% | 44.5% |
| ie-lock.svg | 910 | 479 | 342 | 300 | 328 | 52.6% | 37.6% | 33.0% | 36.0% |
| ielock.svg | 906 | 426 | 299 | 265 | 164 | 47.0% | 33.0% | 29.2% | 18.1% |
| rails.svg | 902 | 570 | 388 | 344 | 234 | 63.2% | 43.0% | 38.1% | 25.9% |
| mudflap.svg | 797 | 563 | 376 | 307 | 366 | 70.6% | 47.2% | 38.5% | 45.9% |
| couch.svg | 783 | 461 | 334 | 293 | 310 | 58.9% | 42.7% | 37.4% | 39.6% |
| vote.svg | 747 | 501 | 345 | 280 | 325 | 67.1% | 46.2% | 37.5% | 43.5% |
| accessible.svg | 731 | 466 | 268 | 239 | 244 | 63.7% | 36.7% | 32.7% | 33.4% |
| ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |
| openid.svg | 195 | 89 | 88 | 83 | 77 | 45.6% | 45.1% | 42.6% | 39.5% |
| iw.svg | 191 | 99 | 87 | 79 | 79 | 51.8% | 45.5% | 41.4% | 41.4% |
| heart.svg | 178 | 82 | 77 | 66 | 71 | 46.1% | 43.3% | 37.1% | 39.9% |
| osi.svg | 178 | 64 | 70 | 64 | 62 | 36.0% | 39.3% | 36.0% | 34.8% |
| star.svg | 177 | 71 | 70 | 60 | 26 | 40.1% | 39.5% | 33.9% | 14.7% |
| odf.svg | 176 | 78 | 77 | 73 | 63 | 44.3% | 43.8% | 41.5% | 35.8% |
| betterplace.svg | 163 | 51 | 61 | 56 | 26 | 31.3% | 37.4% | 34.4% | 16.0% |
| image.svg | 157 | 54 | 63 | 57 | 71 | 34.4% | 40.1% | 36.3% | 45.2% |
| x11.svg | 144 | 75 | 70 | 60 | 26 | 52.1% | 48.6% | 41.7% | 18.1% |
| adobe.svg | 143 | 63 | 71 | 65 | 67 | 44.1% | 49.7% | 45.5% | 46.9% |

### material-design

| File | SVG | TVG | zstd | brotli | zstd+dict | TVG/SVG | zstd/SVG | brotli/SVG | dict/SVG |
|------|-----|-----|------|--------|-----------|---------|----------|------------|----------|
| rabbit.svg | 1,099 | 437 | 404 | 379 | 395 | 39.8% | 36.8% | 34.5% | 35.9% |
| campfire.svg | 1,045 | 414 | 383 | 359 | 373 | 39.6% | 36.7% | 34.4% | 35.7% |
| book-cog-outline.svg | 1,034 | 497 | 379 | 364 | 323 | 48.1% | 36.7% | 35.2% | 31.2% |
| gantry-crane.svg | 947 | 473 | 336 | 325 | 308 | 49.9% | 35.5% | 34.3% | 32.5% |
| car-turbocharger.svg | 889 | 426 | 355 | 331 | 334 | 47.9% | 39.9% | 37.2% | 37.6% |
| handshake-outline.svg | 876 | 423 | 372 | 346 | 360 | 48.3% | 42.5% | 39.5% | 41.1% |
| hand-okay.svg | 822 | 340 | 318 | 288 | 297 | 41.4% | 38.7% | 35.0% | 36.1% |
| space-station.svg | 821 | 541 | 326 | 286 | 309 | 65.9% | 39.7% | 34.8% | 37.6% |
| vpn.svg | 738 | 377 | 273 | 257 | 234 | 51.1% | 37.0% | 34.8% | 31.7% |
| qqchat.svg | 730 | 285 | 277 | 256 | 109 | 39.0% | 37.9% | 35.1% | 14.9% |
| ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |
| tie.svg | 138 | 53 | 55 | 49 | 51 | 38.4% | 39.9% | 35.5% | 37.0% |
| roman-numeral-5.svg | 136 | 49 | 55 | 49 | 42 | 36.0% | 40.4% | 36.0% | 30.9% |
| play.svg | 131 | 31 | 44 | 36 | 39 | 23.7% | 33.6% | 27.5% | 29.8% |
| flash.svg | 131 | 45 | 54 | 44 | 44 | 34.4% | 41.2% | 33.6% | 33.6% |
| forward.svg | 131 | 45 | 54 | 47 | 46 | 34.4% | 41.2% | 35.9% | 35.1% |
| format-title.svg | 130 | 44 | 57 | 49 | 42 | 33.8% | 43.8% | 37.7% | 32.3% |
| alpha-t.svg | 126 | 44 | 57 | 46 | 42 | 34.9% | 45.2% | 36.5% | 33.3% |
| moon-last-quarter.svg | 125 | 35 | 48 | 38 | 37 | 28.0% | 38.4% | 30.4% | 29.6% |
| menu-right.svg | 122 | 33 | 46 | 38 | 26 | 27.0% | 37.7% | 31.1% | 21.3% |
| power-on.svg | 118 | 32 | 45 | 37 | 38 | 27.1% | 38.1% | 31.4% | 32.2% |

### papirus

| File | SVG | TVG | zstd | brotli | zstd+dict | TVG/SVG | zstd/SVG | brotli/SVG | dict/SVG |
|------|-----|-----|------|--------|-----------|---------|----------|------------|----------|
| komodo-edit.svg | 7,445 | 2,418 | 1,438 | 1,321 | 1,332 | 32.5% | 19.3% | 17.7% | 17.9% |
| full-throttle-remastered.svg | 7,403 | 2,168 | 1,328 | 1,248 | 753 | 29.3% | 17.9% | 16.9% | 10.2% |
| subsurface-icon.svg | 6,418 | 2,310 | 1,414 | 1,293 | 1,318 | 36.0% | 22.0% | 20.1% | 20.5% |
| text-x-cobol.svg | 6,290 | 2,100 | 1,266 | 1,164 | 641 | 33.4% | 20.1% | 18.5% | 10.2% |
| nexuiz.svg | 5,914 | 2,067 | 1,203 | 1,108 | 1,162 | 35.0% | 20.3% | 18.7% | 19.6% |
| write_stylus.svg | 4,649 | 2,214 | 1,336 | 1,274 | 1,335 | 47.6% | 28.7% | 27.4% | 28.7% |
| performous.svg | 4,055 | 1,556 | 930 | 836 | 790 | 38.4% | 22.9% | 20.6% | 19.5% |
| com.github.thejambi.dayjournal.svg | 4,051 | 1,734 | 1,245 | 1,082 | 913 | 42.8% | 30.7% | 26.7% | 22.5% |
| netbeans.svg | 3,871 | 1,683 | 995 | 947 | 626 | 43.5% | 25.7% | 24.5% | 16.2% |
| ms-onedrive.svg | 3,642 | 962 | 606 | 575 | 232 | 26.4% | 16.6% | 15.8% | 6.4% |
| ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |
| emblem-unlocked.svg | 428 | 178 | 162 | 163 | 134 | 41.6% | 37.9% | 38.1% | 31.3% |
| mame.svg | 378 | 159 | 117 | 107 | 98 | 42.1% | 31.0% | 28.3% | 25.9% |
| emblem-photos.svg | 321 | 157 | 137 | 128 | 99 | 48.9% | 42.7% | 39.9% | 30.8% |
| vcs-conflicting.svg | 245 | 78 | 86 | 83 | 66 | 31.8% | 35.1% | 33.9% | 26.9% |
| emblem-default.svg | 240 | 81 | 94 | 86 | 26 | 33.8% | 39.2% | 35.8% | 10.8% |
| emblem-important.svg | 219 | 84 | 78 | 76 | 48 | 38.4% | 35.6% | 34.7% | 21.9% |
| emblem-new.svg | 196 | 78 | 78 | 77 | 52 | 39.8% | 39.8% | 39.3% | 26.5% |
| Nextcloud_ok.svg | 189 | 76 | 89 | 81 | 26 | 40.2% | 47.1% | 42.9% | 13.8% |
| emblem-downloads.svg | 187 | 91 | 84 | 84 | 56 | 48.7% | 44.9% | 44.9% | 29.9% |
| emblem-remove.svg | 156 | 60 | 69 | 65 | 41 | 38.5% | 44.2% | 41.7% | 26.3% |

## Top 20 Best Compression Ratios (zstd+dict as % of SVG)

| File | Group | SVG | TVG | zstd+dict | % of SVG |
|------|-------|-----|-----|-----------|----------|
| singular.svg | papirus | 1,491 | 496 | 27 | 1.8% |
| mx-select-sound.svg | papirus | 1,742 | 900 | 35 | 2.0% |
| opengl.svg | papirus | 1,234 | 480 | 27 | 2.2% |
| folder-green-kde.svg | papirus | 1,722 | 902 | 38 | 2.2% |
| folder-red-kde.svg | papirus | 1,722 | 902 | 38 | 2.2% |
| folder-bluegrey-kde.svg | papirus | 1,722 | 902 | 38 | 2.2% |
| penrose-staircase.svg | w3c | 3,231 | 649 | 74 | 2.3% |
| folder-grey-github.svg | papirus | 1,637 | 833 | 38 | 2.3% |
| folder-cyan-github.svg | papirus | 1,637 | 833 | 38 | 2.3% |
| folder-nordic-github.svg | papirus | 1,637 | 833 | 38 | 2.3% |
| folder-deeporange-github.svg | papirus | 1,637 | 833 | 38 | 2.3% |
| folder-green-github.svg | papirus | 1,637 | 833 | 38 | 2.3% |
| folder-indigo-github.svg | papirus | 1,637 | 833 | 38 | 2.3% |
| application-x-asp.svg | papirus | 1,239 | 666 | 32 | 2.6% |
| flareget.svg | papirus | 983 | 350 | 27 | 2.7% |
| folder-yellow-kde.svg | papirus | 1,722 | 902 | 48 | 2.8% |
| folder-magenta-kde.svg | papirus | 1,722 | 902 | 48 | 2.8% |
| face-uncertain.svg | papirus | 932 | 141 | 26 | 2.8% |
| text-x-texmacs.svg | papirus | 1,321 | 556 | 37 | 2.8% |
| steadyflow.svg | papirus | 1,086 | 432 | 31 | 2.9% |

## Bottom 20 Worst Compression Ratios (zstd+dict as % of SVG)

| File | Group | SVG | TVG | zstd+dict | % of SVG |
|------|-------|-----|-----|-----------|----------|
| feedsync.svg | w3c | 321 | 214 | 137 | 42.7% |
| touchpad-indicator.svg | papirus | 602 | 476 | 257 | 42.7% |
| script-text.svg | material-design | 337 | 196 | 146 | 43.3% |
| emblem-dropbox-app.svg | papirus | 459 | 226 | 199 | 43.4% |
| vector-polyline-plus.svg | material-design | 269 | 166 | 117 | 43.5% |
| vote.svg | w3c | 747 | 501 | 325 | 43.5% |
| instiki.svg | w3c | 965 | 645 | 429 | 44.5% |
| image.svg | w3c | 157 | 54 | 71 | 45.2% |
| shape-oval-plus.svg | material-design | 298 | 173 | 135 | 45.3% |
| mudflap.svg | w3c | 797 | 563 | 366 | 45.9% |
| adobe.svg | w3c | 143 | 63 | 67 | 46.9% |
| unicode.svg | w3c | 224 | 133 | 106 | 47.3% |
| m.svg | w3c | 339 | 238 | 162 | 47.8% |
| yahoo.svg | w3c | 443 | 287 | 215 | 48.5% |
| genshi.svg | w3c | 290 | 189 | 141 | 48.6% |
| microformat.svg | w3c | 329 | 251 | 168 | 51.1% |
| check.svg | w3c | 296 | 202 | 154 | 52.0% |
| cloud-upload.svg | material-design | 279 | 170 | 149 | 53.4% |
| facebook.svg | w3c | 299 | 242 | 161 | 53.8% |
| vmware.svg | w3c | 274 | 243 | 159 | 58.0% |
