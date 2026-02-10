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

- **zig**: 8 of 9 converted (1 failed)
- **w3c**: 76 of 115 converted (39 failed)
- **material-design**: 346 of 1000 converted (654 failed)
- **papirus**: 519 of 1000 converted (481 failed)
- **freesvg**: 0 of 5 (files no longer retrievable from freesvg.org)

**949 files** converted successfully. Of these, **948** have TVG sizes
within reasonable range of the original benchmark; 1 outlier(s)
are excluded from aggregate statistics but shown in per-file tables.

**Trained zstd dictionary size**: 65,536 bytes

## Overall Summary

| Metric | Total bytes | % of SVG | % of TVG |
|--------|------------|----------|----------|
| **SVG (SVGO-optimized)** | 763,431 | 100.0% | - |
| **TVG (uncompressed)** | 391,156 | 51.2% | 100.0% |
| **TVG + zstd -22** | 260,250 | 34.1% | 66.5% |
| **TVG + brotli -11** | 242,225 | 31.7% | 61.9% |
| **TVG + zstd -22 +dict** | 119,190 | 15.6% | 30.5% |

*948 files (excluding 1 outlier(s)) across 4 groups.*

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

### zig (7 files (1 outlier excluded))

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

## Conversion Failure Analysis

### Failure categories across all 2,129 benchmark files

| Category | Count | Description |
|----------|-------|-------------|
| ok | 949 | Successful conversion |
| svg2tvgt:path_parse | 846 | svg2tvgt fails parsing SVG path `d` data (complex/compound paths) |
| svg2tvgt:moveto_bug | 291 | svg2tvgt throws `New MoveTo detected without ClosePath` -- open subpaths |
| no_source | 41 | SVG file not found in current source dataset (repo evolved or freesvg.org) |
| tvg-text:syntax | 1 | tvg-text rejects TVGT with syntax error (svg2tvgt emitted bad text) |
| tvg-text:range | 1 | tvg-text value out of range (svg2tvgt emitted out-of-spec value) |

### Failure breakdown by group

| Group | Total | OK | path_parse | moveto_bug | no_source | transform | tvg-text | other |
|-------|-------|----|------------|------------|-----------|-----------|----------|-------|
| zig | 9 | 8 | 1 | 0 | 0 | 0 | 0 | 0 |
| w3c | 115 | 76 | 13 | 26 | 0 | 0 | 0 | 0 |
| material-design | 1000 | 346 | 437 | 214 | 3 | 0 | 0 | 0 |
| papirus | 1000 | 519 | 395 | 51 | 33 | 0 | 2 | 0 |
| freesvg | 5 | 0 | 0 | 0 | 5 | 0 | 0 | 0 |

### Analysis of `svg2tvgt` failures

The vast majority of failures (1,137 of 1,180) occur in `svg2tvgt`, the SVG-to-TVGT
text converter. Two root causes account for nearly all of them:

1. **Path parse errors** (846 files): `svg2tvgt`'s SVG path parser
   fails on certain valid SVG path data. Affected files tend to have more complex,
   compound paths (median ref SVG size of failed MDI files is larger than successful ones).
2. **MoveTo-without-ClosePath bug** (291 files): `svg2tvgt` throws
   `InvalidOperationException: New MoveTo detected without ClosePath` when an SVG path
   contains multiple subpaths using implicit MoveTo (M) commands without explicit ClosePath (Z)
   between them. This is valid SVG (open subpaths are allowed) but `svg2tvgt` rejects it.

Both issues are **bugs/limitations in `svg2tvgt`**, not fundamental TinyVG format
limitations. Fixing the path parser to handle compound paths and open subpaths would
likely recover most of the 1,137 currently-failing files.

## Per-File Details (All Benchmark Files)

Every file from the original TinyVG benchmark is listed below. Files that failed
conversion show `n/a` for compression columns. The `ref_svg` column shows the
SVGO-optimized SVG size from the original benchmark; `cur_svg` shows the current
source SVG size (0 if not found). The `notes` column indicates failure category
or `(*)` for outliers.

### zig (9 files)

| File | ref_svg | cur_svg | TVG | ref_tvg | zstd | brotli | zstd+dict | dict/SVG | notes |
|------|---------|---------|-----|---------|------|--------|-----------|----------|-------|
| ziggy.svg | 27,873 | 21,988 | n/a | 7,933 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| zero.svg | 26,352 | 246,055 | 66,962 | 11,056 | 56,513 | 51,956 | 56,814 | 215.6% | (*) |
| zig-logo-dark.svg | 1,200 | 1,571 | 549 | 542 | 407 | 398 | 61 | 5.1% |  |
| zig-logo-light.svg | 1,197 | 1,568 | 549 | 542 | 405 | 392 | 62 | 5.2% |  |
| zig-logo-neg-black.svg | 1,178 | 1,547 | 545 | 538 | 401 | 397 | 66 | 5.6% |  |
| zig-logo-neg-white.svg | 1,175 | 1,544 | 545 | 538 | 401 | 395 | 71 | 6.0% |  |
| zig-mark-neg-black.svg | 622 | 831 | 288 | 282 | 196 | 182 | 27 | 4.3% |  |
| zig-mark.svg | 622 | 832 | 288 | 282 | 197 | 185 | 32 | 5.1% |  |
| zig-mark-neg-white.svg | 619 | 829 | 288 | 282 | 195 | 188 | 32 | 5.2% |  |

### w3c (115 files)

| File | ref_svg | cur_svg | TVG | ref_tvg | zstd | brotli | zstd+dict | dict/SVG | notes |
|------|---------|---------|-----|---------|------|--------|-----------|----------|-------|
| penrose-staircase.svg | 3,231 | 3,896 | 649 | 741 | 335 | 339 | 74 | 2.3% |  |
| ibm.svg | 2,696 | 4,474 | n/a | 1,013 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| acid.svg | 2,590 | 1,720 | n/a | 1,246 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| faux-art.svg | 2,456 | 5,503 | 667 | 666 | 639 | 621 | 639 | 26.0% |  |
| mozilla.svg | 2,167 | 1,755 | n/a | 1,507 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| hg0.svg | 1,980 | 1,687 | n/a | 1,363 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| debian.svg | 1,697 | 1,322 | n/a | 1,239 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| scion.svg | 1,419 | 1,339 | n/a | 1,007 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| aa.svg | 1,385 | 993 | n/a | 703 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| cartman.svg | 1,157 | 1,148 | n/a | 770 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| penrose-tiling.svg | 1,133 | 1,593 | n/a | 490 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| eee.svg | 1,065 | 920 | n/a | 732 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| ruby.svg | 1,061 | 1,072 | n/a | 536 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| instiki.svg | 965 | 785 | 645 | 645 | 438 | 344 | 429 | 44.5% |  |
| fsm.svg | 956 | 987 | n/a | 700 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| ie-lock.svg | 910 | 775 | 479 | 485 | 342 | 300 | 328 | 36.0% |  |
| opera.svg | 907 | 817 | n/a | 668 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| ielock.svg | 906 | 847 | 426 | 430 | 299 | 265 | 164 | 18.1% |  |
| rails.svg | 902 | 880 | 570 | 570 | 388 | 344 | 234 | 25.9% |  |
| yadis.svg | 869 | 634 | n/a | 215 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| mudflap.svg | 797 | 649 | 563 | 568 | 376 | 307 | 366 | 45.9% |  |
| couch.svg | 783 | 793 | 461 | 461 | 334 | 293 | 310 | 39.6% |  |
| vote.svg | 747 | 920 | 501 | 506 | 345 | 280 | 325 | 43.5% |  |
| dojo.svg | 746 | 789 | n/a | 569 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| accessible.svg | 731 | 764 | 466 | 474 | 268 | 239 | 244 | 33.4% |  |
| gcheck.svg | 729 | 594 | 351 | 352 | 309 | 285 | 300 | 41.2% |  |
| http.svg | 723 | 708 | 467 | 467 | 321 | 296 | 120 | 16.6% |  |
| heliocentric.svg | 656 | 733 | 344 | 344 | 163 | 165 | 149 | 22.7% |  |
| ietf.svg | 627 | 644 | 407 | 407 | 261 | 213 | 218 | 34.8% |  |
| basura.svg | 606 | 659 | n/a | 317 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| jabber.svg | 584 | 510 | n/a | 366 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| ca.svg | 579 | 535 | n/a | 369 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| moonlight.svg | 564 | 398 | 193 | 193 | 151 | 141 | 26 | 4.6% |  |
| rest.svg | 558 | 522 | 262 | 263 | 225 | 203 | 215 | 38.5% |  |
| wso2.svg | 547 | 583 | 249 | 249 | 176 | 169 | 26 | 4.8% |  |
| padlock.svg | 535 | 573 | 272 | 276 | 184 | 182 | 31 | 5.8% |  |
| osa.svg | 533 | 627 | n/a | 314 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| usaf.svg | 522 | 528 | 319 | 324 | 236 | 203 | 44 | 8.4% |  |
| bzr.svg | 482 | 487 | 230 | 230 | 170 | 164 | 162 | 33.6% |  |
| gpg.svg | 467 | 459 | n/a | 303 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| utensils.svg | 467 | 382 | 282 | 282 | 202 | 182 | 28 | 6.0% |  |
| integral.svg | 452 | 386 | 294 | 295 | 221 | 179 | 28 | 6.2% |  |
| couchdb.svg | 447 | 447 | 302 | 302 | 226 | 203 | 32 | 7.2% |  |
| pull.svg | 443 | 462 | 203 | 203 | 142 | 139 | 132 | 29.8% |  |
| yahoo.svg | 443 | 401 | 287 | 291 | 222 | 187 | 215 | 48.5% |  |
| android.svg | 432 | 471 | n/a | 181 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| duck.svg | 414 | 530 | 229 | 234 | 176 | 164 | 175 | 42.3% |  |
| caution.svg | 404 | 422 | 142 | 142 | 107 | 100 | 26 | 6.4% |  |
| mono.svg | 402 | 397 | 287 | 287 | 204 | 189 | 125 | 31.1% |  |
| evol.svg | 399 | 367 | n/a | 262 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| msft.svg | 398 | 388 | 199 | 219 | 177 | 151 | 157 | 39.4% |  |
| cc.svg | 397 | 374 | 221 | 221 | 159 | 143 | 90 | 22.7% |  |
| wp.svg | 395 | 404 | n/a | 194 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| obama.svg | 387 | 365 | n/a | 222 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| unicode-han.svg | 377 | 546 | 105 | 106 | 118 | 110 | 26 | 6.9% |  |
| msie.svg | 374 | 384 | 189 | 189 | 157 | 134 | 148 | 39.6% |  |
| why.svg | 367 | 423 | n/a | 187 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| legal.svg | 355 | 663 | n/a | 183 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| mail.svg | 355 | 388 | n/a | 93 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| rack.svg | 355 | 373 | 159 | 159 | 120 | 108 | 121 | 34.1% |  |
| raleigh.svg | 355 | 375 | 172 | 172 | 139 | 147 | 120 | 33.8% |  |
| gnome2.svg | 351 | 344 | n/a | 229 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| w3c.svg | 350 | 351 | n/a | 216 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| m.svg | 339 | 319 | 238 | 238 | 168 | 154 | 162 | 47.8% |  |
| ch.svg | 338 | 351 | n/a | 108 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| cygwin.svg | 335 | 349 | 157 | 157 | 118 | 112 | 26 | 7.8% |  |
| google.svg | 331 | 331 | 159 | 159 | 139 | 125 | 125 | 37.8% |  |
| microformat.svg | 329 | 352 | 251 | 251 | 183 | 173 | 168 | 51.1% |  |
| digg.svg | 326 | 339 | 201 | 201 | 140 | 140 | 130 | 39.9% |  |
| dh.svg | 321 | 343 | 171 | 171 | 131 | 128 | 117 | 36.4% |  |
| feedsync.svg | 321 | 350 | 214 | 214 | 149 | 146 | 137 | 42.7% |  |
| wii.svg | 318 | 325 | 181 | 181 | 143 | 131 | 131 | 41.2% |  |
| mac.svg | 311 | 295 | n/a | 183 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| myspace.svg | 307 | 351 | 167 | 167 | 129 | 120 | 113 | 36.8% |  |
| facebook.svg | 299 | 305 | 242 | 245 | 168 | 169 | 161 | 53.8% |  |
| check.svg | 296 | 301 | 202 | 203 | 157 | 130 | 154 | 52.0% |  |
| no.svg | 292 | 304 | 102 | 102 | 99 | 88 | 86 | 29.5% |  |
| genshi.svg | 290 | 273 | 189 | 190 | 150 | 126 | 141 | 48.6% |  |
| irony.svg | 286 | 264 | 155 | 155 | 131 | 109 | 122 | 42.7% |  |
| wireless.svg | 285 | 306 | n/a | 106 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| feed.svg | 282 | 302 | n/a | 155 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| rfeed.svg | 282 | 302 | n/a | 155 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| zillow.svg | 279 | 293 | n/a | 155 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| pdftk.svg | 274 | 296 | 151 | 151 | 124 | 110 | 26 | 9.5% |  |
| vmware.svg | 274 | 297 | 243 | 243 | 159 | 145 | 159 | 58.0% |  |
| beacon.svg | 272 | 363 | 126 | 126 | 112 | 108 | 100 | 36.8% |  |
| whatwg.svg | 272 | 273 | 125 | 125 | 113 | 101 | 96 | 35.3% |  |
| yinyang.svg | 270 | 282 | 136 | 136 | 95 | 84 | 84 | 31.1% |  |
| mt.svg | 267 | 270 | 136 | 137 | 113 | 107 | 99 | 37.1% |  |
| wikimedia.svg | 265 | 273 | 129 | 129 | 106 | 97 | 91 | 34.3% |  |
| eff.svg | 258 | 281 | n/a | 133 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| italian-flag.svg | 244 | 287 | 100 | 100 | 84 | 78 | 79 | 32.4% |  |
| erlang.svg | 243 | 238 | 122 | 122 | 109 | 106 | 102 | 42.0% |  |
| git.svg | 239 | 240 | n/a | 106 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| semweb.svg | 239 | 257 | 106 | 106 | 98 | 96 | 26 | 10.9% |  |
| alphachannel.svg | 238 | 263 | 94 | 94 | 77 | 68 | 67 | 28.2% |  |
| rubyforge.svg | 231 | 252 | 96 | 96 | 96 | 87 | 80 | 34.6% |  |
| unicode.svg | 224 | 233 | 133 | 133 | 112 | 101 | 106 | 47.3% |  |
| jquery.svg | 222 | 227 | n/a | 112 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| venus.svg | 221 | 233 | 72 | 72 | 74 | 71 | 67 | 30.3% |  |
| poi.svg | 211 | 217 | 82 | 82 | 69 | 61 | 62 | 29.4% |  |
| openweb.svg | 206 | 215 | 86 | 86 | 93 | 90 | 29 | 14.1% |  |
| copyleft.svg | 202 | 207 | 76 | 76 | 73 | 61 | 60 | 29.7% |  |
| copyright.svg | 202 | 208 | 76 | 76 | 73 | 62 | 60 | 29.7% |  |
| openid.svg | 195 | 213 | 89 | 89 | 88 | 83 | 77 | 39.5% |  |
| iw.svg | 191 | 201 | 99 | 99 | 87 | 79 | 79 | 41.4% |  |
| mars.svg | 185 | 199 | n/a | 72 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| heart.svg | 178 | 187 | 82 | 82 | 77 | 66 | 71 | 39.9% |  |
| osi.svg | 178 | 182 | 64 | 64 | 70 | 64 | 62 | 34.8% |  |
| star.svg | 177 | 184 | 71 | 71 | 70 | 60 | 26 | 14.7% |  |
| odf.svg | 176 | 184 | 78 | 78 | 77 | 73 | 63 | 35.8% |  |
| betterplace.svg | 163 | 165 | 51 | 51 | 61 | 56 | 26 | 16.0% |  |
| image.svg | 157 | 787 | 54 | 54 | 63 | 57 | 71 | 45.2% |  |
| x11.svg | 144 | 290 | 75 | 75 | 70 | 60 | 26 | 18.1% |  |
| adobe.svg | 143 | 149 | 63 | 63 | 71 | 65 | 67 | 46.9% |  |

### material-design (1000 files)

| File | ref_svg | cur_svg | TVG | ref_tvg | zstd | brotli | zstd+dict | dict/SVG | notes |
|------|---------|---------|-----|---------|------|--------|-----------|----------|-------|
| kubernetes.svg | 4,549 | 4,697 | n/a | 1,892 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| timer-3.svg | 2,932 | 3,074 | n/a | 1,186 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| timer-10.svg | 2,629 | 2,735 | n/a | 1,075 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| paw-off-outline.svg | 2,380 | 2,494 | n/a | 1,001 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| microsoft-teams.svg | 2,166 | 2,180 | n/a | 932 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| laravel.svg | 1,675 | 1,989 | n/a | 737 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| menorah-fire.svg | 1,630 | 1,685 | n/a | 952 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| smoke-detector-variant-off.svg | 1,538 | 1,553 | n/a | 717 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| klingon.svg | 1,492 | 1,543 | n/a | 590 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| webhook.svg | 1,454 | 1,487 | n/a | 574 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| storefront.svg | 1,426 | 1,468 | n/a | 632 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| microsoft-outlook.svg | 1,417 | 1,438 | n/a | 645 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| sort-numeric-ascending-variant.svg | 1,393 | 1,411 | n/a | 562 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| cog-transfer-outline.svg | 1,375 | 1,408 | n/a | 737 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| ship-wheel.svg | 1,334 | 1,410 | n/a | 602 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| virus-off.svg | 1,332 | 1,499 | n/a | 567 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| badminton.svg | 1,297 | 1,320 | n/a | 536 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| account-cog-outline.svg | 1,289 | 1,296 | n/a | 581 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| shield-link-variant-outline.svg | 1,265 | 1,303 | n/a | 542 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| sheep.svg | 1,254 | 1,275 | n/a | 633 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| basketball.svg | 1,200 | 1,204 | n/a | 480 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| shield-link-variant.svg | 1,188 | 1,220 | n/a | 495 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| google-earth.svg | 1,166 | 1,202 | n/a | 504 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| office-building-cog.svg | 1,157 | 1,235 | n/a | 596 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| scent-off.svg | 1,120 | 1,126 | n/a | 546 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| book-open-variant.svg | 1,111 | 1,069 | n/a | 472 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| rabbit.svg | 1,099 | 1,135 | 437 | 440 | 404 | 379 | 395 | 35.9% |  |
| cog-box.svg | 1,077 | 1,097 | n/a | 487 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| link-box-variant-outline.svg | 1,073 | 1,235 | n/a | 487 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| web-plus.svg | 1,073 | 1,098 | n/a | 522 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| link-box-variant.svg | 1,058 | 1,212 | n/a | 470 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| fire-circle.svg | 1,051 | 1,056 | n/a | 427 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| cookie-plus-outline.svg | 1,048 | 1,178 | n/a | 576 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| cookie-check-outline.svg | 1,046 | 1,215 | n/a | 559 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| campfire.svg | 1,045 | 1,074 | 414 | 426 | 383 | 359 | 373 | 35.7% |  |
| emoticon-sick-outline.svg | 1,039 | 1,097 | n/a | 505 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| blur-linear.svg | 1,036 | 1,074 | n/a | 682 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| book-cog-outline.svg | 1,034 | 1,046 | 497 | 504 | 379 | 364 | 323 | 31.2% |  |
| lightbulb-group-off-outline.svg | 1,017 | 1,056 | n/a | 495 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| turtle.svg | 1,012 | 1,057 | n/a | 429 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| book-cog.svg | 1,009 | 1,013 | n/a | 492 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| fire-off.svg | 997 | 1,002 | n/a | 394 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| at.svg | 990 | 1,019 | n/a | 488 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| format-letter-case-lower.svg | 988 | 1,017 | n/a | 396 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| database-eye-off-outline.svg | 987 | 1,006 | n/a | 492 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| movie-cog.svg | 987 | 1,019 | n/a | 494 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| format-letter-case-upper.svg | 984 | 1,013 | n/a | 396 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| account-group-outline.svg | 983 | 1,080 | n/a | 472 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| application-cog-outline.svg | 980 | 991 | n/a | 474 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| string-lights.svg | 980 | 1,003 | n/a | 458 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| selection-ellipse-remove.svg | 956 | 996 | n/a | 405 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| gantry-crane.svg | 947 | 1,008 | 473 | 500 | 336 | 325 | 308 | 32.5% |  |
| face-agent.svg | 936 | 1,043 | n/a | 363 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| incognito-circle.svg | 933 | 989 | n/a | 389 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| billiards-rack.svg | 927 | 990 | n/a | 381 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| fan-speed-2.svg | 897 | 930 | n/a | 418 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| mastodon.svg | 896 | 904 | n/a | 380 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| cookie-remove.svg | 893 | 963 | n/a | 503 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| car-turbocharger.svg | 889 | 905 | 426 | 431 | 355 | 331 | 334 | 37.6% |  |
| golf-tee.svg | 885 | 881 | n/a | 644 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| handshake-outline.svg | 876 | 893 | 423 | 430 | 372 | 346 | 360 | 41.1% |  |
| cookie-outline.svg | 875 | 945 | n/a | 493 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| monitor-eye.svg | 868 | 970 | n/a | 412 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| help-network-outline.svg | 851 | 859 | n/a | 425 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| professional-hexagon.svg | 845 | 912 | n/a | 444 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| grill-outline.svg | 835 | 836 | n/a | 403 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| cookie-check.svg | 826 | 895 | n/a | 473 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| hand-okay.svg | 822 | 883 | 340 | 345 | 318 | 288 | 297 | 36.1% |  |
| space-station.svg | 821 | 831 | 541 | 564 | 326 | 286 | 309 | 37.6% |  |
| fan-speed-1.svg | 817 | 843 | n/a | 362 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| bicycle.svg | 815 | 816 | n/a | 397 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| gift-open.svg | 812 | 815 | n/a | 344 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| database-lock-outline.svg | 805 | 835 | n/a | 430 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| map-marker-path.svg | 801 | 855 | n/a | 506 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| antenna.svg | 793 | 794 | n/a | 378 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| comment-question-outline.svg | 792 | 837 | n/a | 386 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| wifi-sync.svg | 784 | 834 | n/a | 364 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| phone-classic.svg | 783 | 830 | n/a | 399 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| table-eye-off.svg | 781 | 796 | n/a | 349 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| induction.svg | 775 | 781 | n/a | 427 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| access-point-check.svg | 768 | 780 | n/a | 368 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| clover.svg | 756 | 750 | n/a | 350 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| emoticon-cry.svg | 745 | 797 | n/a | 358 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| attachment-lock.svg | 743 | 746 | n/a | 391 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| clipboard-text-search-outline.svg | 743 | 812 | n/a | 411 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| ear-hearing.svg | 741 | 749 | n/a | 353 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| vpn.svg | 738 | 742 | 377 | 390 | 273 | 257 | 234 | 31.7% |  |
| database-sync.svg | 734 | 758 | n/a | 378 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| wiper-wash-alert.svg | 733 | 777 | n/a | 433 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| access-point-plus.svg | 730 | 762 | n/a | 374 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| phone-voip.svg | 730 | 767 | n/a | 378 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| qqchat.svg | 730 | 732 | 285 | 286 | 277 | 256 | 109 | 14.9% |  |
| cryengine.svg | 729 | 821 | n/a | 278 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| torch.svg | 729 | 729 | n/a | 371 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| database-eye-outline.svg | 724 | 732 | n/a | 435 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| account-supervisor-circle.svg | 715 | 728 | n/a | 305 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| dice-multiple-outline.svg | 709 | 801 | n/a | 462 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| ornament-variant.svg | 709 | 724 | n/a | 406 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| pi-hole.svg | 709 | 742 | n/a | 283 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| leak-off.svg | 707 | 709 | n/a | 333 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| access-point-minus.svg | 706 | 739 | n/a | 350 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| clipboard-text-search.svg | 695 | 750 | n/a | 382 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| database-remove-outline.svg | 695 | 717 | n/a | 360 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| fan-alert.svg | 694 | 691 | n/a | 322 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| snowflake.svg | 693 | 690 | 305 | 312 | 274 | 255 | 259 | 37.4% |  |
| account-sync-outline.svg | 692 | 700 | n/a | 383 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| social-distance-2-meters.svg | 692 | 710 | n/a | 454 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| contactless-payment-circle-outline.svg | 684 | 706 | n/a | 333 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| gavel.svg | 683 | 717 | n/a | 294 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| controller-classic-outline.svg | 681 | 695 | n/a | 335 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| twitter.svg | 679 | 738 | 265 | 270 | 267 | 252 | 27 | 4.0% |  |
| tag-heart-outline.svg | 677 | 689 | n/a | 315 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| weather-hail.svg | 677 | 677 | n/a | 407 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| led-strip-variant.svg | 676 | 681 | 248 | 293 | 233 | 212 | 214 | 31.7% |  |
| tag-arrow-left-outline.svg | 675 | 685 | n/a | 393 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| tag-arrow-up-outline.svg | 675 | 683 | n/a | 393 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| android.svg | 673 | 692 | n/a | 262 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| train-car.svg | 673 | 679 | n/a | 404 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| head-heart-outline.svg | 667 | 675 | n/a | 317 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| guitar-pick-outline.svg | 665 | 739 | n/a | 320 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| source-branch.svg | 662 | 665 | n/a | 388 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| archive-sync-outline.svg | 661 | 705 | n/a | 327 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| robot-angry-outline.svg | 660 | 721 | n/a | 354 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| wifi-lock-open.svg | 658 | 716 | n/a | 323 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| database-clock.svg | 653 | 664 | n/a | 338 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| license.svg | 652 | 647 | n/a | 317 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| wifi-strength-3-lock-open.svg | 650 | 670 | n/a | 314 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| kite.svg | 649 | 652 | 251 | 256 | 245 | 228 | 236 | 36.4% |  |
| mosque.svg | 645 | 499 | n/a | 411 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| face-mask.svg | 642 | 679 | n/a | 297 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| map-search-outline.svg | 642 | 668 | n/a | 321 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| account-wrench-outline.svg | 639 | 639 | n/a | 358 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| human-white-cane.svg | 636 | 682 | n/a | 276 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| language-cpp.svg | 636 | 647 | n/a | 307 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| fruit-watermelon.svg | 634 | 714 | n/a | 406 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| pretzel.svg | 634 | 644 | n/a | 296 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| wifi-remove.svg | 634 | 633 | n/a | 297 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| emoticon-devil.svg | 633 | 667 | n/a | 294 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| card-account-phone-outline.svg | 629 | 670 | n/a | 389 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| truck-remove-outline.svg | 626 | 634 | n/a | 361 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| cake-variant.svg | 625 | 691 | n/a | 313 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| source-merge.svg | 623 | 627 | n/a | 362 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| file-find-outline.svg | 620 | 632 | 286 | 293 | 250 | 239 | 205 | 33.1% |  |
| gas-station-off-outline.svg | 620 | 674 | 319 | 336 | 276 | 254 | 247 | 39.8% |  |
| git.svg | 620 | 617 | 275 | 276 | 226 | 240 | 206 | 33.2% |  |
| sun-wireless.svg | 618 | 727 | n/a | 320 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| meditation.svg | 617 | 621 | n/a | 313 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| penguin.svg | 616 | 606 | n/a | 358 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| select-color.svg | 615 | 670 | n/a | 373 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| bus-stop.svg | 613 | 617 | n/a | 349 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| weather-sunset-up.svg | 612 | 736 | n/a | 319 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| paragliding.svg | 610 | 614 | n/a | 328 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| washing-machine-off.svg | 610 | 629 | n/a | 305 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| rickshaw-electric.svg | 608 | 698 | n/a | 335 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| spider-thread.svg | 606 | 607 | n/a | 315 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| ornament.svg | 605 | 601 | n/a | 333 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| script-text-key-outline.svg | 605 | 616 | n/a | 383 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| wifi-strength-lock-outline.svg | 603 | 641 | n/a | 284 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| bottle-wine-outline.svg | 602 | 624 | n/a | 280 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| speedometer-slow.svg | 602 | 627 | n/a | 273 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| cube-off-outline.svg | 601 | 605 | 253 | 270 | 235 | 230 | 30 | 5.0% |  |
| glass-mug-variant-off.svg | 600 | 645 | n/a | 311 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| xamarin.svg | 596 | 591 | n/a | 278 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| android-studio.svg | 595 | 597 | 284 | 291 | 227 | 220 | 202 | 33.9% |  |
| google-chrome.svg | 594 | 597 | n/a | 311 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| printer-eye.svg | 592 | 591 | n/a | 365 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| mixed-martial-arts.svg | 589 | 595 | n/a | 290 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| database-arrow-down-outline.svg | 588 | 614 | n/a | 326 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| progress-alert.svg | 588 | 605 | n/a | 269 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| shaker.svg | 588 | 590 | n/a | 347 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| scatter-plot-outline.svg | 587 | 595 | n/a | 340 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| currency-bdt.svg | 586 | 594 | 241 | 244 | 213 | 214 | 196 | 33.4% |  |
| puzzle-remove.svg | 584 | 622 | n/a | 287 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| briefcase-eye.svg | 583 | 584 | n/a | 349 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| help-rhombus.svg | 582 | 582 | n/a | 240 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| earth-box-remove.svg | 581 | 600 | n/a | 262 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| cards-playing-outline.svg | 580 | 611 | n/a | 240 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| map-clock-outline.svg | 579 | 610 | n/a | 316 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| account-convert-outline.svg | 578 | 646 | n/a | 304 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| dice-5-outline.svg | 578 | 625 | n/a | 389 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| microphone-variant-off.svg | 578 | 595 | n/a | 314 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| code-json.svg | 574 | 571 | n/a | 410 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| facebook-messenger.svg | 574 | 606 | n/a | 248 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| hammer-wrench.svg | 573 | 580 | 233 | 238 | 220 | 204 | 204 | 35.6% |  |
| dice-6.svg | 571 | 565 | n/a | 401 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| gamepad-circle-up.svg | 571 | 576 | n/a | 389 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| remote-off.svg | 569 | 568 | n/a | 277 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| sunglasses.svg | 569 | 576 | 236 | 237 | 225 | 215 | 215 | 37.8% |  |
| scooter.svg | 568 | 573 | n/a | 315 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| file-eye.svg | 567 | 599 | n/a | 297 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| radar.svg | 567 | 560 | 292 | 293 | 213 | 197 | 28 | 4.9% |  |
| smoking.svg | 567 | 590 | n/a | 266 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| heart-plus-outline.svg | 566 | 572 | n/a | 269 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| snake.svg | 564 | 580 | n/a | 330 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| cash-fast.svg | 563 | 694 | n/a | 305 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| truck-remove.svg | 563 | 563 | n/a | 315 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| emoticon-lol.svg | 562 | 562 | n/a | 272 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| flower-tulip-outline.svg | 560 | 594 | n/a | 285 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| timeline-help.svg | 558 | n/a | n/a | 316 | n/a | n/a | n/a | n/a | no_source |
| arm-flex-outline.svg | 557 | 561 | n/a | 227 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| baby-carriage.svg | 555 | 567 | n/a | 273 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| head-sync.svg | 555 | 562 | n/a | 265 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| dishwasher-off.svg | 554 | 571 | 269 | 280 | 253 | 235 | 188 | 33.9% |  |
| wind-turbine.svg | 554 | 583 | n/a | 251 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| dishwasher-alert.svg | 553 | 576 | n/a | 337 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| file-phone.svg | 553 | 551 | 237 | 246 | 215 | 219 | 30 | 5.4% |  |
| tailwind.svg | 553 | 549 | n/a | 236 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| truck-check-outline.svg | 552 | 639 | n/a | 331 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| beaker-question.svg | 550 | 571 | 315 | 332 | 260 | 239 | 223 | 40.5% |  |
| movie-open-star.svg | 550 | 558 | n/a | 253 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| emoticon-cool.svg | 549 | 582 | 245 | 254 | 214 | 195 | 26 | 4.7% |  |
| flask-empty-remove-outline.svg | 548 | 567 | 262 | 267 | 243 | 218 | 212 | 38.7% |  |
| alien.svg | 547 | 575 | n/a | 246 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| database-arrow-right.svg | 547 | 563 | n/a | 291 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| wifi-strength-4-lock.svg | 546 | 555 | n/a | 255 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| briefcase-search-outline.svg | 545 | 574 | n/a | 302 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| mine.svg | 545 | 553 | 249 | 254 | 193 | 188 | 182 | 33.4% |  |
| rug.svg | 545 | 607 | n/a | 297 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| airplane-marker.svg | 542 | 557 | n/a | 248 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| email-search-outline.svg | 541 | 583 | n/a | 276 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| car-brake-parking.svg | 540 | 596 | n/a | 330 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| harddisk-plus.svg | 540 | 541 | n/a | 315 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| archive-eye.svg | 539 | 581 | n/a | 287 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| earbuds-off.svg | 539 | 558 | n/a | 249 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| camera-flip-outline.svg | 535 | 562 | n/a | 288 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| newspaper-remove.svg | 534 | 543 | 248 | 261 | 206 | 204 | 196 | 36.7% |  |
| book-open-page-variant.svg | 530 | 540 | 222 | 225 | 196 | 184 | 188 | 35.5% |  |
| file-lock-open.svg | 528 | 530 | n/a | 276 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| transmission-tower-import.svg | 526 | 539 | 228 | 253 | 214 | 226 | 194 | 36.9% |  |
| hand-back-right-off.svg | 524 | 614 | n/a | 238 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| package-variant-closed-plus.svg | 522 | 537 | n/a | 289 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| lock-remove.svg | 521 | 572 | n/a | 281 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| table-lock.svg | 521 | 548 | n/a | 293 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| axis-x-rotate-clockwise.svg | 520 | 531 | n/a | 234 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| database-edit.svg | 520 | 585 | n/a | 260 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| folder-eye.svg | 520 | 518 | n/a | 301 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| sofa-single-outline.svg | 520 | 527 | n/a | 313 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| map-marker-question-outline.svg | 519 | 534 | n/a | 239 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| map-marker-radius-outline.svg | 519 | 532 | n/a | 308 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| ticket-percent-outline.svg | 517 | 673 | n/a | 314 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| store-search-outline.svg | 516 | 557 | n/a | 262 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| selection-marker.svg | 515 | 550 | n/a | 315 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| lock-off-outline.svg | 514 | 534 | n/a | 264 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| credit-card-wireless-off.svg | 512 | 537 | n/a | 249 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| heart-settings-outline.svg | 511 | 521 | n/a | 258 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| lotion-outline.svg | 511 | 521 | n/a | 285 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| clipboard-edit.svg | 510 | 536 | n/a | 258 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| circle-off-outline.svg | 508 | 520 | n/a | 227 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| calendar-search.svg | 506 | 520 | n/a | 272 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| android-messages.svg | 505 | n/a | n/a | 296 | n/a | n/a | n/a | n/a | no_source |
| cube-outline.svg | 504 | 508 | 206 | 219 | 196 | 199 | 130 | 25.8% |  |
| dice-d6.svg | 502 | 530 | n/a | 233 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| bus-side.svg | 501 | 497 | n/a | 291 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| calendar-refresh-outline.svg | 500 | 512 | n/a | 278 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| cart-arrow-up.svg | 500 | 429 | n/a | 289 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| seat-recline-normal.svg | 500 | 507 | n/a | 236 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-search-outline.svg | 499 | 519 | n/a | 256 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| gift.svg | 499 | 493 | n/a | 286 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| rotate-right.svg | 498 | 517 | n/a | 207 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| clock-remove.svg | 497 | 503 | n/a | 222 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| puzzle-check.svg | 494 | 508 | 256 | 262 | 214 | 202 | 27 | 5.5% |  |
| account-network-outline.svg | 493 | 521 | n/a | 282 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| account-off-outline.svg | 493 | 499 | n/a | 248 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-search.svg | 493 | 510 | n/a | 255 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| truck-fast.svg | 492 | 491 | n/a | 280 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| face-man-profile.svg | 491 | 496 | n/a | 231 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| lock-open-check-outline.svg | 491 | 515 | n/a | 278 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| volume-off.svg | 491 | 491 | n/a | 217 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| basket-minus-outline.svg | 490 | 518 | n/a | 255 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| briefcase-off-outline.svg | 490 | 499 | 248 | 259 | 210 | 209 | 179 | 36.5% |  |
| account-filter-outline.svg | 489 | 509 | n/a | 289 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| shopping-search.svg | 489 | 492 | n/a | 264 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| bell-circle-outline.svg | 487 | 494 | n/a | 268 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| video-input-component.svg | 485 | 494 | 302 | 315 | 190 | 174 | 27 | 5.6% |  |
| truck-minus-outline.svg | 484 | 491 | n/a | 313 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| movie-search.svg | 483 | 521 | n/a | 261 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| transit-transfer.svg | 483 | 487 | n/a | 252 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-key-network.svg | 482 | 502 | n/a | 318 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| credit-card-marker-outline.svg | 481 | 513 | n/a | 250 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| bus-electric.svg | 480 | 518 | n/a | 309 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| calendar-lock-outline.svg | 480 | 493 | n/a | 278 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| application-braces-outline.svg | 478 | 522 | n/a | 321 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| wifi-strength-off-outline.svg | 478 | 493 | n/a | 205 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| power-socket-eu.svg | 477 | 480 | n/a | 245 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| archive-marker-outline.svg | 476 | 494 | n/a | 251 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| cloud-upload-outline.svg | 476 | 652 | n/a | 232 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| battery-clock-outline.svg | 475 | 484 | n/a | 254 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| boom-gate-up.svg | 473 | 473 | n/a | 257 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| camera-enhance-outline.svg | 473 | 483 | n/a | 293 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| clock-fast.svg | 473 | 471 | n/a | 294 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| mushroom.svg | 471 | 467 | n/a | 289 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| car.svg | 470 | 461 | n/a | 255 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| email-fast-outline.svg | 470 | 490 | n/a | 273 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| rewind-30.svg | 470 | 481 | n/a | 271 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| arrow-right-bold-hexagon-outline.svg | 469 | 493 | 202 | 213 | 191 | 203 | 126 | 26.9% |  |
| variable-box.svg | 469 | 469 | n/a | 278 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| bowling.svg | 468 | 463 | n/a | 234 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| language-ruby.svg | 468 | 477 | 182 | 189 | 179 | 178 | 169 | 36.1% |  |
| book-marker.svg | 466 | 473 | n/a | 244 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| calendar-lock.svg | 466 | 474 | n/a | 261 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| calendar-sync.svg | 466 | 473 | 227 | 236 | 191 | 197 | 161 | 34.5% |  |
| head-dots-horizontal.svg | 466 | 474 | n/a | 282 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| watering-can.svg | 466 | 480 | 209 | 216 | 191 | 205 | 173 | 37.1% |  |
| lock-open-check.svg | 465 | 481 | n/a | 266 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| slot-machine.svg | 464 | 464 | n/a | 317 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| clock-edit.svg | 463 | 461 | n/a | 210 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| menorah.svg | 463 | 465 | n/a | 262 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| watch-vibrate.svg | 463 | 472 | n/a | 222 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| thermometer-bluetooth.svg | 462 | 479 | n/a | 249 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| camera-wireless-outline.svg | 461 | 476 | n/a | 284 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| briefcase-variant-off-outline.svg | 459 | 500 | 253 | 266 | 211 | 200 | 85 | 18.5% |  |
| lock-open-plus-outline.svg | 459 | 482 | n/a | 284 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| cloud-print-outline.svg | 458 | 849 | n/a | 277 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| gesture-tap-hold.svg | 458 | 462 | 221 | 224 | 188 | 178 | 162 | 35.4% |  |
| radioactive-circle.svg | 458 | 499 | n/a | 248 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| hail.svg | 457 | 449 | 231 | 236 | 195 | 181 | 165 | 36.1% |  |
| food-kosher.svg | 456 | 455 | 266 | 273 | 200 | 182 | 184 | 40.4% |  |
| movie-open-minus.svg | 456 | 465 | n/a | 215 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| connection.svg | 453 | 451 | 191 | 200 | 174 | 152 | 70 | 15.5% |  |
| hammer-screwdriver.svg | 453 | 459 | 183 | 190 | 183 | 167 | 164 | 36.2% |  |
| movie-remove-outline.svg | 453 | 469 | n/a | 228 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| glass-mug-variant.svg | 452 | 485 | n/a | 243 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| ice-cream-off.svg | 452 | 453 | 184 | 197 | 188 | 166 | 150 | 33.2% |  |
| podium.svg | 452 | 446 | 215 | 234 | 186 | 180 | 167 | 36.9% |  |
| run.svg | 451 | 454 | n/a | 206 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| shield-sync.svg | 451 | 450 | n/a | 210 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| water-remove-outline.svg | 451 | 480 | n/a | 195 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| car-arrow-left.svg | 450 | 452 | n/a | 249 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| vector-square-edit.svg | 450 | 456 | n/a | 267 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| key-change.svg | 449 | 447 | n/a | 300 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| dump-truck.svg | 447 | 453 | n/a | 264 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| baseball-diamond-outline.svg | 446 | 463 | n/a | 237 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| arrow-decision-auto.svg | 445 | 476 | 195 | 208 | 184 | 171 | 161 | 36.2% |  |
| data-matrix-scan.svg | 445 | 450 | n/a | 371 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| cone.svg | 444 | 452 | n/a | 210 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| truck-delivery.svg | 444 | 446 | n/a | 258 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| wall-sconce-round-outline.svg | 444 | 460 | n/a | 203 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| sack-percent.svg | 443 | 468 | n/a | 250 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| bag-personal-off-outline.svg | 442 | 454 | 245 | 258 | 200 | 189 | 31 | 7.0% |  |
| image-frame.svg | 442 | 441 | 202 | 215 | 180 | 182 | 173 | 39.1% |  |
| file-image-plus-outline.svg | 441 | 455 | n/a | 251 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| car-pickup.svg | 440 | 438 | n/a | 241 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| account-reactivate.svg | 439 | 485 | 224 | 227 | 194 | 195 | 176 | 40.1% |  |
| shield-search.svg | 438 | 439 | n/a | 216 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| wifi-settings.svg | 438 | 439 | n/a | 244 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| file-lock-open-outline.svg | 437 | 447 | n/a | 236 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| human-male-child.svg | 437 | 441 | n/a | 259 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| margin.svg | 437 | 431 | n/a | 290 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| shield-moon-outline.svg | 437 | 463 | n/a | 191 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| box-cutter.svg | 436 | 434 | 153 | 162 | 159 | 154 | 26 | 6.0% |  |
| subway-alert-variant.svg | 436 | 474 | n/a | 282 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| battery-10-bluetooth.svg | 434 | 442 | 206 | 217 | 180 | 178 | 29 | 6.7% |  |
| subway-variant.svg | 434 | 436 | n/a | 232 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| vote-outline.svg | 434 | 459 | n/a | 217 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| battery-80-bluetooth.svg | 433 | 441 | 206 | 217 | 181 | 180 | 26 | 6.0% |  |
| battery-90-bluetooth.svg | 433 | 441 | 206 | 217 | 181 | 179 | 29 | 6.7% |  |
| wall-sconce-round-variant-outline.svg | 433 | 466 | 190 | 203 | 178 | 159 | 156 | 36.0% |  |
| basket-minus.svg | 432 | 479 | n/a | 230 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| cards-playing-club.svg | 432 | 438 | n/a | 241 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| link-box-outline.svg | 432 | 436 | n/a | 267 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| briefcase-remove-outline.svg | 431 | 447 | n/a | 226 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| email-lock.svg | 431 | 541 | n/a | 256 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| routes-clock.svg | 431 | 431 | n/a | 231 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| lightbulb-alert-outline.svg | 429 | 440 | n/a | 253 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| stadium.svg | 428 | 317 | n/a | 217 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| update.svg | 428 | 428 | 168 | 173 | 171 | 168 | 156 | 36.4% |  |
| grease-pencil.svg | 424 | 425 | n/a | 158 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| nativescript.svg | 424 | 424 | n/a | 228 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| newspaper-plus.svg | 424 | 429 | 227 | 236 | 185 | 179 | 151 | 35.6% |  |
| restart.svg | 423 | 419 | 178 | 189 | 173 | 147 | 162 | 38.3% |  |
| blender.svg | 422 | 417 | n/a | 238 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| phone-message.svg | 422 | 433 | n/a | 188 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| airplane-off.svg | 421 | 421 | 165 | 174 | 171 | 155 | 142 | 33.7% |  |
| vote.svg | 420 | 421 | 191 | 200 | 170 | 167 | 144 | 34.3% |  |
| death-star-variant.svg | 419 | 446 | n/a | 197 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| octagram-outline.svg | 419 | 423 | 179 | 188 | 144 | 138 | 144 | 34.4% |  |
| calculator-variant.svg | 418 | 424 | n/a | 244 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| movie-remove.svg | 418 | 426 | n/a | 211 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| new-box.svg | 418 | 413 | 225 | 232 | 180 | 163 | 142 | 34.0% |  |
| pail-plus-outline.svg | 418 | 468 | n/a | 211 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-refresh.svg | 417 | 539 | n/a | 205 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| pencil-box-multiple.svg | 417 | 429 | n/a | 199 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| account-voice.svg | 415 | 416 | n/a | 193 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| archive-clock.svg | 415 | 416 | n/a | 217 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| clipboard-text-off.svg | 414 | 472 | 238 | 249 | 204 | 209 | 159 | 38.4% |  |
| book-remove.svg | 413 | 420 | n/a | 195 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| database-plus.svg | 413 | 451 | n/a | 244 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| circle-expand.svg | 412 | 420 | n/a | 177 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| help-circle.svg | 411 | 421 | n/a | 209 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| percent-outline.svg | 411 | 512 | n/a | 271 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| bell-plus-outline.svg | 410 | 533 | n/a | 224 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| chart-bubble.svg | 410 | 410 | n/a | 183 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| flask-empty-outline.svg | 410 | 417 | n/a | 226 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| battery-heart.svg | 409 | 410 | n/a | 179 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| compare-remove.svg | 408 | 410 | n/a | 226 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| pyramid.svg | 408 | 431 | n/a | 168 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| card-multiple.svg | 407 | 408 | 183 | 188 | 164 | 155 | 157 | 38.6% |  |
| seat-passenger.svg | 407 | 414 | n/a | 198 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| emoticon-wink.svg | 406 | 440 | n/a | 212 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| filter-off.svg | 405 | 415 | 157 | 164 | 166 | 146 | 132 | 32.6% |  |
| microsoft-xbox-controller-battery-empty.svg | 405 | 444 | 218 | 223 | 170 | 167 | 143 | 35.3% |  |
| exponent.svg | 404 | 400 | 162 | 167 | 164 | 152 | 26 | 6.4% |  |
| phone-paused.svg | 404 | 407 | n/a | 193 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| select-group.svg | 404 | 404 | n/a | 325 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| eye-minus.svg | 403 | 400 | n/a | 194 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| filter-check.svg | 403 | 439 | 168 | 174 | 159 | 148 | 142 | 35.2% |  |
| pencil-box-multiple-outline.svg | 403 | 436 | n/a | 216 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| archive-check-outline.svg | 401 | 410 | n/a | 203 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| format-text-variant-outline.svg | 401 | 416 | n/a | 175 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| zodiac-scorpio.svg | 401 | 405 | 215 | 220 | 159 | 149 | 127 | 31.7% |  |
| account-box-multiple-outline.svg | 400 | 431 | n/a | 231 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| chili-alert.svg | 397 | 396 | n/a | 202 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| escalator-up.svg | 397 | 443 | n/a | 216 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| hamburger-plus.svg | 397 | 444 | n/a | 234 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| pencil-off-outline.svg | 397 | 403 | n/a | 199 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| phone-check.svg | 397 | 396 | n/a | 184 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| store-check-outline.svg | 397 | 404 | n/a | 198 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| alphabetical-variant.svg | 396 | 404 | n/a | 270 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| palette-swatch-variant.svg | 396 | 406 | n/a | 235 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| clock-in.svg | 395 | 395 | n/a | 184 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| human-female-female.svg | 395 | 408 | n/a | 228 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| scanner-off.svg | 395 | 394 | 181 | 198 | 173 | 160 | 142 | 35.9% |  |
| battery-charging-wireless-40.svg | 394 | 428 | n/a | 192 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| battery-charging-wireless-60.svg | 394 | 428 | n/a | 192 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| chart-donut.svg | 394 | 395 | n/a | 171 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| battery-charging-wireless-90.svg | 392 | 426 | n/a | 192 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| message-text-lock-outline.svg | 392 | 425 | n/a | 246 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| water-pump.svg | 392 | 403 | n/a | 255 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| power-socket-us.svg | 391 | 394 | n/a | 210 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| shield-remove.svg | 391 | 395 | 163 | 172 | 154 | 146 | 137 | 35.0% |  |
| lead-pencil.svg | 390 | 389 | n/a | 146 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| map-marker-question.svg | 390 | 403 | n/a | 174 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| ribbon.svg | 390 | 398 | n/a | 182 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| horizontal-rotate-counterclockwise.svg | 389 | 411 | n/a | 201 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| comment-account-outline.svg | 388 | 414 | 236 | 243 | 161 | 158 | 76 | 19.6% |  |
| water-percent-alert.svg | 388 | 470 | n/a | 192 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| car-light-fog.svg | 387 | 443 | n/a | 241 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| folder-pound-outline.svg | 387 | 400 | n/a | 236 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| circle-edit-outline.svg | 386 | 399 | n/a | 190 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| umbrella-beach.svg | 386 | 388 | n/a | 156 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| wallet-outline.svg | 386 | 411 | 229 | 236 | 139 | 131 | 108 | 28.0% |  |
| toslink.svg | 385 | 380 | n/a | 243 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| lock-smart.svg | 384 | 382 | n/a | 283 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| marker.svg | 384 | 380 | n/a | 143 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| texture.svg | 384 | 379 | n/a | 170 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| chat-sleep-outline.svg | 383 | 393 | n/a | 209 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| layers-edit.svg | 383 | 404 | n/a | 164 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| shield-lock-open.svg | 383 | 387 | 194 | 201 | 164 | 154 | 157 | 41.0% |  |
| video-wireless-outline.svg | 382 | 396 | n/a | 198 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| account-key.svg | 381 | 380 | n/a | 250 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| bunk-bed.svg | 381 | 377 | n/a | 208 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| currency-btc.svg | 381 | 371 | n/a | 215 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| lan-connect.svg | 381 | 385 | 226 | 237 | 175 | 153 | 30 | 7.9% |  |
| card-bulleted-off.svg | 380 | 385 | 180 | 197 | 172 | 156 | 58 | 15.3% |  |
| pound-box-outline.svg | 380 | 385 | n/a | 224 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| mouse-off.svg | 379 | 381 | n/a | 180 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| phone-minus.svg | 379 | 381 | n/a | 173 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| piggy-bank.svg | 379 | 408 | 195 | 200 | 182 | 175 | 157 | 41.4% |  |
| alarm-panel.svg | 378 | 377 | n/a | 257 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| sort-clock-ascending-outline.svg | 378 | 410 | n/a | 187 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| water-check-outline.svg | 378 | 406 | 160 | 165 | 157 | 142 | 134 | 35.4% |  |
| cloud-outline.svg | 377 | 555 | n/a | 190 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| comment-off-outline.svg | 376 | 411 | 179 | 188 | 161 | 144 | 94 | 25.0% |  |
| comment-remove-outline.svg | 376 | 392 | 206 | 215 | 154 | 145 | 26 | 6.9% |  |
| ip-network-outline.svg | 375 | 381 | n/a | 265 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| track-light.svg | 375 | 374 | 144 | 159 | 157 | 136 | 111 | 29.6% |  |
| hamburger-minus.svg | 373 | 421 | n/a | 210 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| star-check-outline.svg | 372 | 378 | 163 | 171 | 152 | 131 | 138 | 37.1% |  |
| clock-minus.svg | 371 | 376 | n/a | 174 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| rice.svg | 371 | 363 | n/a | 180 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| printer-outline.svg | 370 | 404 | 222 | 231 | 180 | 159 | 152 | 41.1% |  |
| shopping-outline.svg | 370 | 374 | n/a | 230 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| soy-sauce.svg | 369 | 376 | n/a | 191 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| chess-bishop.svg | 367 | 382 | 162 | 169 | 157 | 152 | 132 | 36.0% |  |
| elevator-passenger.svg | 367 | 404 | n/a | 207 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| format-bold.svg | 367 | 366 | n/a | 157 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| weather-hurricane.svg | 367 | 454 | n/a | 178 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| zodiac-taurus.svg | 367 | 373 | n/a | 182 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| elevator-passenger-off.svg | 366 | 423 | 168 | 179 | 161 | 151 | 118 | 32.2% |  |
| keyboard-outline.svg | 366 | 370 | 260 | 287 | 136 | 115 | 109 | 29.8% |  |
| notebook-plus-outline.svg | 366 | 375 | 248 | 259 | 184 | 177 | 152 | 41.5% |  |
| white-balance-incandescent.svg | 366 | 407 | n/a | 169 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| fridge-off-outline.svg | 365 | 381 | 191 | 202 | 170 | 176 | 26 | 7.1% |  |
| pig-variant.svg | 365 | 395 | 180 | 183 | 172 | 164 | 148 | 40.5% |  |
| google-nearby.svg | 364 | 365 | n/a | 145 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| projector-screen-off-outline.svg | 364 | 380 | 171 | 180 | 159 | 146 | 126 | 34.6% |  |
| zodiac-libra.svg | 364 | 367 | 160 | 165 | 156 | 136 | 126 | 34.6% |  |
| audio-input-rca.svg | 363 | 366 | 211 | 220 | 162 | 162 | 26 | 7.2% |  |
| cursor-default.svg | 363 | 415 | 143 | 148 | 144 | 148 | 125 | 34.4% |  |
| clipboard-arrow-right-outline.svg | 362 | 379 | n/a | 224 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| walk.svg | 361 | 376 | n/a | 176 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| rv-truck.svg | 360 | 356 | n/a | 214 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| pipe-wrench.svg | 359 | 358 | 128 | 141 | 133 | 124 | 121 | 33.7% |  |
| delete-off-outline.svg | 357 | 363 | 175 | 188 | 160 | 141 | 140 | 39.2% |  |
| keyboard-esc.svg | 357 | 381 | n/a | 241 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| bed-king.svg | 355 | 351 | n/a | 202 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| inbox-remove.svg | 355 | 355 | n/a | 195 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| pencil-box-outline.svg | 355 | 368 | n/a | 177 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| star-off-outline.svg | 355 | 359 | 155 | 168 | 144 | 125 | 132 | 37.2% |  |
| bus-stop-uncovered.svg | 354 | 360 | n/a | 203 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| comment-account.svg | 354 | 372 | 210 | 215 | 143 | 141 | 72 | 20.3% |  |
| doorbell-video.svg | 354 | 373 | n/a | 215 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| hand-pointing-down.svg | 354 | 360 | n/a | 158 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| gesture-swipe-vertical.svg | 353 | 363 | 176 | 181 | 160 | 146 | 129 | 36.5% |  |
| text-box-minus-outline.svg | 353 | 363 | n/a | 193 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| close-box-multiple.svg | 352 | 363 | n/a | 187 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| account-details-outline.svg | 351 | 423 | n/a | 245 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| clipboard-play-multiple.svg | 351 | 383 | n/a | 218 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| fast-forward-15.svg | 351 | 361 | n/a | 185 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| numeric-6-circle-outline.svg | 351 | 363 | n/a | 218 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| table-check.svg | 351 | 368 | n/a | 191 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| content-save-off.svg | 350 | 401 | 157 | 166 | 152 | 135 | 76 | 21.7% |  |
| file-code-outline.svg | 350 | 358 | 156 | 171 | 145 | 137 | 95 | 27.1% |  |
| mailbox-open-up-outline.svg | 350 | 361 | n/a | 180 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| artstation.svg | 349 | 350 | n/a | 131 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| cards-spade-outline.svg | 349 | 368 | n/a | 216 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| receipt-outline.svg | 349 | 306 | 159 | 208 | 106 | 95 | 89 | 25.5% |  |
| block-helper.svg | 348 | 346 | n/a | 165 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| curling.svg | 348 | 343 | n/a | 161 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| movie-off-outline.svg | 348 | 358 | 169 | 180 | 161 | 144 | 101 | 29.0% |  |
| wifi-strength-2.svg | 348 | 353 | n/a | 142 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| fire-hydrant.svg | 347 | 367 | n/a | 216 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| store-minus-outline.svg | 347 | 354 | n/a | 181 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| vector-combine.svg | 347 | 473 | 205 | 214 | 146 | 131 | 136 | 39.2% |  |
| zend.svg | 347 | 400 | 153 | 162 | 145 | 143 | 98 | 28.2% |  |
| check-network.svg | 346 | 347 | 195 | 202 | 133 | 126 | 105 | 30.3% |  |
| quality-high.svg | 346 | 351 | n/a | 210 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| wifi-strength-1.svg | 346 | 353 | n/a | 141 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| clipboard-play-outline.svg | 344 | 356 | n/a | 212 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| sprinkler-fire.svg | 344 | 346 | 238 | 261 | 151 | 138 | 129 | 37.5% |  |
| coffee-maker.svg | 343 | 345 | n/a | 205 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| file-move-outline.svg | 343 | 348 | 164 | 171 | 152 | 141 | 126 | 36.7% |  |
| rss.svg | 343 | 334 | n/a | 143 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| ticket.svg | 342 | 353 | n/a | 187 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| table-arrow-down.svg | 341 | 363 | n/a | 186 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| weight-lifter.svg | 340 | 359 | n/a | 212 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| comment-text-multiple-outline.svg | 339 | 356 | 208 | 219 | 148 | 143 | 30 | 8.8% |  |
| signal-3g.svg | 339 | 336 | n/a | 189 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| tower-beach.svg | 339 | 338 | 153 | 168 | 145 | 136 | 127 | 37.5% |  |
| xmpp.svg | 339 | 376 | 142 | 143 | 140 | 138 | 126 | 37.2% |  |
| account-multiple-minus.svg | 338 | 348 | n/a | 193 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| order-numeric-descending.svg | 338 | 366 | n/a | 234 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| content-save-off-outline.svg | 337 | 446 | 155 | 166 | 150 | 135 | 84 | 24.9% |  |
| script-text.svg | 337 | 348 | 196 | 205 | 165 | 149 | 146 | 43.3% |  |
| vector-circle-variant.svg | 337 | 346 | n/a | 156 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| crosshairs.svg | 335 | 333 | n/a | 164 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| share-off-outline.svg | 335 | 340 | n/a | 150 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| star-box-multiple-outline.svg | 335 | 358 | n/a | 193 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| battery-arrow-down-outline.svg | 334 | 348 | n/a | 153 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| keyboard-close.svg | 334 | 341 | n/a | 251 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| table-column-remove.svg | 334 | 341 | n/a | 199 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| book-arrow-left-outline.svg | 333 | 352 | 167 | 172 | 145 | 143 | 26 | 7.8% |  |
| decimal.svg | 333 | 328 | n/a | 205 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| sprinkler-variant.svg | 333 | 338 | 243 | 272 | 156 | 148 | 127 | 38.1% |  |
| abugida-devanagari.svg | 332 | 354 | 175 | 178 | 157 | 149 | 136 | 41.0% |  |
| airport.svg | 332 | 332 | n/a | 165 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| sim-outline.svg | 332 | 331 | n/a | 203 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| email-box.svg | 331 | 328 | n/a | 182 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-remove.svg | 331 | 411 | n/a | 157 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| opacity.svg | 331 | 374 | n/a | 140 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| timeline-plus-outline.svg | 331 | 392 | n/a | 220 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| multiplication-box.svg | 330 | 341 | 162 | 167 | 133 | 135 | 105 | 31.8% |  |
| chart-bell-curve.svg | 329 | 340 | 150 | 151 | 142 | 149 | 132 | 40.1% |  |
| flag-variant-outline.svg | 329 | 379 | n/a | 229 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| format-header-2.svg | 329 | 332 | 180 | 185 | 149 | 138 | 115 | 35.0% |  |
| screw-machine-round-top.svg | 329 | 349 | n/a | 180 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| sort-numeric-descending.svg | 329 | 362 | n/a | 219 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| calendar-multiple-check.svg | 327 | 348 | 183 | 194 | 142 | 144 | 26 | 8.0% |  |
| send-lock.svg | 327 | 324 | n/a | 179 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| cake-layered.svg | 326 | 340 | n/a | 183 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| fast-forward-5.svg | 326 | 335 | n/a | 162 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| message-fast-outline.svg | 326 | 341 | n/a | 221 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| tilde-off.svg | 326 | 349 | 137 | 142 | 136 | 126 | 90 | 27.6% |  |
| water-off.svg | 325 | 323 | 130 | 135 | 134 | 131 | 102 | 31.4% |  |
| border-bottom.svg | 324 | 325 | n/a | 259 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| video-account.svg | 324 | 333 | 187 | 192 | 127 | 121 | 105 | 32.4% |  |
| account-box-multiple.svg | 323 | 339 | n/a | 211 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| projector-screen-off.svg | 323 | 331 | 143 | 150 | 138 | 130 | 115 | 35.6% |  |
| battery-check.svg | 322 | 328 | 141 | 146 | 135 | 128 | 114 | 35.4% |  |
| border-vertical.svg | 322 | 325 | n/a | 259 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| battery-charging-high.svg | 321 | 330 | n/a | 185 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| clipboard-play.svg | 321 | 325 | n/a | 183 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| table-plus.svg | 321 | 327 | n/a | 197 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| surround-sound-2-0.svg | 320 | 326 | 192 | 201 | 148 | 129 | 26 | 8.1% |  |
| sync.svg | 320 | 319 | n/a | 165 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| text-box-minus.svg | 320 | 330 | 169 | 178 | 140 | 143 | 105 | 32.8% |  |
| comment-processing-outline.svg | 318 | 338 | 190 | 201 | 143 | 136 | 56 | 17.6% |  |
| comment-bookmark-outline.svg | 316 | 328 | 170 | 179 | 146 | 140 | 98 | 31.0% |  |
| multicast.svg | 316 | 325 | 182 | 193 | 153 | 149 | 121 | 38.3% |  |
| numeric-10-box-outline.svg | 316 | 336 | n/a | 201 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| arrow-up-circle-outline.svg | 315 | 326 | n/a | 168 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| bookmark-remove-outline.svg | 315 | 331 | 147 | 156 | 137 | 134 | 116 | 36.8% |  |
| briefcase-variant.svg | 315 | 322 | n/a | 193 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| certificate-outline.svg | 315 | 322 | n/a | 222 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| watch.svg | 314 | 314 | n/a | 151 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| cash-refund.svg | 313 | 312 | n/a | 173 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| battery-charging-20.svg | 312 | 319 | n/a | 133 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| radiobox-marked.svg | 312 | 315 | n/a | 177 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| reiterate.svg | 312 | 309 | n/a | 154 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| briefcase-minus.svg | 311 | 324 | n/a | 180 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| content-paste.svg | 311 | 316 | n/a | 191 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| vector-arrange-above.svg | 311 | 359 | 171 | 178 | 129 | 116 | 114 | 36.7% |  |
| printer-settings.svg | 310 | 314 | n/a | 209 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| radio.svg | 309 | 302 | 176 | 181 | 132 | 135 | 103 | 33.3% |  |
| ticket-confirmation.svg | 309 | 326 | 181 | 188 | 115 | 107 | 82 | 26.5% |  |
| pail-outline.svg | 308 | 342 | 132 | 139 | 132 | 125 | 114 | 37.0% |  |
| timeline-text.svg | 308 | 361 | n/a | 196 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| bell-sleep.svg | 307 | 341 | n/a | 175 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| fence.svg | 307 | 300 | 227 | 240 | 122 | 98 | 26 | 8.5% |  |
| calendar-star.svg | 306 | 327 | n/a | 169 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| escalator-box.svg | 306 | 350 | 144 | 151 | 125 | 122 | 26 | 8.5% |  |
| cursor-text.svg | 305 | 304 | 162 | 165 | 124 | 123 | 26 | 8.5% |  |
| shield-crown.svg | 305 | 330 | 135 | 146 | 133 | 124 | 116 | 38.0% |  |
| flip-horizontal.svg | 304 | 307 | n/a | 202 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| pencil-minus-outline.svg | 304 | 312 | n/a | 151 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| zip-box-outline.svg | 304 | 307 | n/a | 201 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| language-haskell.svg | 303 | 307 | 117 | 126 | 115 | 118 | 103 | 34.0% |  |
| locker-multiple.svg | 303 | 306 | n/a | 219 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| laptop-off.svg | 302 | 305 | 155 | 164 | 133 | 123 | 98 | 32.5% |  |
| note-plus.svg | 302 | 304 | n/a | 161 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| reload-alert.svg | 302 | 302 | n/a | 171 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| food-variant.svg | 301 | 307 | 149 | 152 | 139 | 131 | 115 | 38.2% |  |
| key-plus.svg | 301 | 297 | n/a | 194 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| leek.svg | 301 | 293 | 132 | 147 | 128 | 112 | 103 | 34.2% |  |
| spoon-sugar.svg | 300 | 299 | 145 | 154 | 140 | 136 | 112 | 37.3% |  |
| bell-outline.svg | 299 | 299 | n/a | 180 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| briefcase-off.svg | 299 | 315 | 152 | 161 | 130 | 122 | 94 | 31.4% |  |
| gamepad-round-outline.svg | 299 | 308 | n/a | 196 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| shield-check-outline.svg | 299 | 307 | n/a | 141 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| tournament.svg | 299 | 297 | 182 | 185 | 141 | 130 | 124 | 41.5% |  |
| pizza.svg | 298 | 301 | n/a | 166 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| rhombus.svg | 298 | 293 | 107 | 108 | 101 | 104 | 96 | 32.2% |  |
| shape-oval-plus.svg | 298 | 333 | 173 | 176 | 152 | 151 | 135 | 45.3% |  |
| square-rounded-outline.svg | 298 | 308 | n/a | 156 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| wifi-strength-outline.svg | 298 | 310 | n/a | 122 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| circle-slice-8.svg | 297 | 369 | n/a | 189 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| axis-arrow-info.svg | 296 | 299 | 148 | 157 | 136 | 118 | 108 | 36.5% |  |
| numeric-2-box-multiple.svg | 296 | 311 | 188 | 195 | 122 | 120 | 29 | 9.8% |  |
| balloon.svg | 295 | 290 | 119 | 120 | 120 | 115 | 102 | 34.6% |  |
| cast.svg | 295 | 292 | n/a | 184 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| camera-rear.svg | 294 | 298 | n/a | 181 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| drag.svg | 294 | 286 | 197 | 222 | 104 | 81 | 90 | 30.6% |  |
| folder-lock.svg | 294 | 520 | n/a | 180 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| fridge-alert-outline.svg | 294 | 312 | 190 | 205 | 140 | 129 | 109 | 37.1% |  |
| gender-female.svg | 294 | 295 | n/a | 159 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| movie-play.svg | 294 | 300 | 159 | 164 | 134 | 133 | 26 | 8.8% |  |
| shield-home-outline.svg | 294 | 301 | n/a | 153 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| battery-minus-outline.svg | 292 | 301 | n/a | 141 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| card-bulleted-settings.svg | 292 | 302 | n/a | 202 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| movie-minus.svg | 292 | 299 | n/a | 163 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| view-agenda.svg | 292 | 291 | n/a | 156 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| wall-sconce-round.svg | 292 | 297 | 119 | 132 | 123 | 115 | 97 | 33.2% |  |
| alpha-r-box-outline.svg | 290 | 297 | n/a | 178 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| inbox-outline.svg | 290 | 291 | n/a | 164 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| network-outline.svg | 290 | 293 | 179 | 184 | 118 | 111 | 89 | 30.7% |  |
| binoculars.svg | 289 | 287 | n/a | 191 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| currency-inr.svg | 289 | 298 | 135 | 140 | 133 | 115 | 107 | 37.0% |  |
| format-text-rotation-angle-up.svg | 289 | 306 | n/a | 106 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| music-box.svg | 289 | 286 | n/a | 149 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| animation-play-outline.svg | 287 | 297 | n/a | 188 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| book-minus.svg | 287 | 293 | n/a | 147 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| content-save-outline.svg | 287 | 303 | n/a | 173 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| comment-alert.svg | 286 | 287 | n/a | 158 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| relation-only-one-to-zero-or-one.svg | 286 | 306 | n/a | 175 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| bank-transfer.svg | 285 | 286 | 162 | 179 | 132 | 128 | 114 | 40.0% |  |
| hammer.svg | 285 | 279 | 102 | 107 | 115 | 107 | 97 | 34.0% |  |
| sausage.svg | 285 | 280 | 122 | 127 | 112 | 106 | 102 | 35.8% |  |
| battery-medium.svg | 284 | 286 | n/a | 147 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| consolidate.svg | 284 | 283 | n/a | 184 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| star-circle.svg | 284 | 283 | 122 | 127 | 115 | 122 | 83 | 29.2% |  |
| file-word.svg | 283 | 280 | 141 | 152 | 126 | 112 | 47 | 16.6% |  |
| black-mesa.svg | 282 | 283 | n/a | 139 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-lock-open.svg | 282 | 520 | n/a | 169 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| numeric-5-box-multiple.svg | 282 | 297 | 178 | 183 | 119 | 106 | 60 | 21.3% |  |
| alpha-h-circle-outline.svg | 281 | 291 | n/a | 165 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| medical-bag.svg | 281 | 280 | 164 | 171 | 139 | 132 | 110 | 39.1% |  |
| relation-zero-or-one-to-only-one.svg | 281 | 301 | n/a | 175 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| lighthouse.svg | 280 | 278 | 138 | 149 | 133 | 118 | 105 | 37.5% |  |
| cloud-upload.svg | 279 | 380 | 170 | 127 | 167 | 151 | 149 | 53.4% |  |
| format-letter-spacing.svg | 279 | 288 | n/a | 145 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| shuffle.svg | 279 | 274 | n/a | 112 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| alpha-v-circle-outline.svg | 278 | 288 | n/a | 158 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| chart-scatter-plot-hexbin.svg | 278 | 291 | 119 | 134 | 113 | 104 | 94 | 33.8% |  |
| file-music-outline.svg | 278 | 284 | 161 | 168 | 118 | 130 | 86 | 30.9% |  |
| led-variant-off.svg | 278 | 281 | n/a | 143 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| relation-one-or-many-to-zero-or-one.svg | 278 | 301 | n/a | 161 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| tray-remove.svg | 278 | 277 | n/a | 128 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| alpha-r-circle.svg | 277 | 279 | 144 | 149 | 106 | 95 | 70 | 25.3% |  |
| battery-charging-60.svg | 277 | 284 | n/a | 138 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| arrow-left-bold-circle-outline.svg | 276 | 294 | n/a | 154 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| file-replace.svg | 276 | 281 | n/a | 172 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| pac-man.svg | 276 | 270 | 119 | 124 | 101 | 95 | 85 | 30.8% |  |
| vector-union.svg | 276 | 276 | 149 | 154 | 118 | 107 | 107 | 38.8% |  |
| alpha-f-circle-outline.svg | 275 | 285 | n/a | 159 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| numeric-4-circle-outline.svg | 275 | 287 | n/a | 159 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| fuse-blade.svg | 274 | 275 | 149 | 160 | 120 | 119 | 100 | 36.5% |  |
| map-marker-alert-outline.svg | 274 | 292 | n/a | 162 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| close-box.svg | 273 | 306 | n/a | 148 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| yoga.svg | 273 | 294 | n/a | 133 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| countertop.svg | 272 | 270 | 161 | 166 | 138 | 135 | 49 | 18.0% |  |
| numeric-2-box-outline.svg | 272 | 286 | n/a | 171 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| solar-panel.svg | 272 | 271 | n/a | 187 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| clock-time-seven-outline.svg | 271 | 296 | n/a | 161 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| home-remove.svg | 271 | 324 | n/a | 113 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| alpha-o-circle.svg | 270 | 272 | 148 | 153 | 96 | 84 | 57 | 21.1% |  |
| google-hangouts.svg | 270 | 274 | n/a | 132 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| layers-triple.svg | 270 | 271 | 110 | 123 | 98 | 103 | 85 | 31.5% |  |
| numeric-0-circle.svg | 270 | 274 | 148 | 153 | 96 | 84 | 57 | 21.1% |  |
| sim.svg | 270 | 268 | 163 | 178 | 115 | 100 | 81 | 30.0% |  |
| chevron-left-box-outline.svg | 269 | 286 | n/a | 136 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| delete-variant.svg | 269 | 271 | 117 | 128 | 116 | 104 | 97 | 36.1% |  |
| vector-polyline-plus.svg | 269 | 277 | 166 | 177 | 138 | 135 | 117 | 43.5% |  |
| bed-king-outline.svg | 268 | 272 | n/a | 163 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| clock-time-twelve-outline.svg | 268 | 287 | n/a | 149 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| skip-previous-circle-outline.svg | 268 | 309 | n/a | 154 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| television-guide.svg | 267 | 271 | 167 | 180 | 118 | 99 | 72 | 27.0% |  |
| bluetooth.svg | 266 | 263 | n/a | 113 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| message-star.svg | 266 | 266 | n/a | 134 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| table-row-height.svg | 266 | 270 | n/a | 180 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| flag-checkered.svg | 265 | 267 | 173 | 184 | 127 | 116 | 102 | 38.5% |  |
| palette-advanced.svg | 265 | 276 | 147 | 158 | 113 | 115 | 100 | 37.7% |  |
| relation-zero-or-many-to-one-or-many.svg | 265 | 289 | n/a | 153 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| arrow-left-drop-circle-outline.svg | 264 | 282 | n/a | 142 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| arrow-right-drop-circle-outline.svg | 264 | 283 | n/a | 142 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| file-word-box.svg | 264 | 270 | n/a | 139 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| lamps-outline.svg | 263 | 264 | 143 | 160 | 124 | 117 | 26 | 9.9% |  |
| relation-one-to-zero-or-many.svg | 263 | 279 | n/a | 143 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| wardrobe.svg | 263 | 259 | n/a | 156 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| account-plus.svg | 262 | 262 | n/a | 149 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| application-array-outline.svg | 262 | 275 | n/a | 161 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| calendar-range.svg | 262 | 267 | n/a | 175 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| sickle.svg | 261 | 255 | 102 | 103 | 111 | 104 | 94 | 36.0% |  |
| battery-low.svg | 260 | 259 | n/a | 129 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| format-columns.svg | 260 | 262 | 167 | 188 | 94 | 78 | 26 | 10.0% |  |
| select-inverse.svg | 260 | 262 | 200 | 203 | 92 | 99 | 89 | 34.2% |  |
| text-account.svg | 260 | 273 | n/a | 152 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| sort-clock-descending.svg | 259 | 284 | n/a | 134 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| wall-sconce-flat-outline.svg | 259 | 271 | 104 | 119 | 109 | 109 | 85 | 32.8% |  |
| calendar-end.svg | 258 | 270 | 155 | 160 | 126 | 124 | 96 | 37.2% |  |
| arrow-top-right-bold-box-outline.svg | 257 | 277 | n/a | 140 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| clock-time-three-outline.svg | 257 | 282 | n/a | 155 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| image-off.svg | 257 | 254 | 115 | 124 | 114 | 108 | 88 | 34.2% |  |
| alpha-g-circle.svg | 256 | 258 | n/a | 142 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| archive-off.svg | 256 | 265 | 112 | 121 | 115 | 103 | 84 | 32.8% |  |
| inbox-arrow-up.svg | 256 | 267 | 152 | 156 | 106 | 104 | 83 | 32.4% |  |
| file-excel-box.svg | 255 | 262 | n/a | 136 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| head-minus.svg | 255 | 253 | n/a | 128 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| printer.svg | 255 | 250 | n/a | 152 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| calendar-alert.svg | 254 | 266 | 151 | 160 | 118 | 114 | 74 | 29.1% |  |
| numeric-4-box-multiple-outline.svg | 254 | 272 | n/a | 164 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| contrast-box.svg | 253 | 258 | n/a | 149 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| keg.svg | 253 | 252 | 163 | 166 | 116 | 108 | 87 | 34.4% |  |
| water-circle.svg | 253 | 253 | n/a | 132 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| arrow-bottom-left-bold-box.svg | 252 | 266 | 118 | 123 | 113 | 108 | 91 | 36.1% |  |
| signal-4g.svg | 252 | 249 | n/a | 130 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| keyboard-f6.svg | 251 | 264 | n/a | 149 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| pencil-plus.svg | 251 | 250 | n/a | 131 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| star-settings.svg | 251 | 252 | 113 | 124 | 117 | 100 | 26 | 10.4% |  |
| ufo.svg | 251 | 242 | 100 | 101 | 103 | 103 | 92 | 36.7% |  |
| volume-vibrate.svg | 251 | 253 | 113 | 120 | 100 | 95 | 26 | 10.4% |  |
| alpha-a-circle.svg | 250 | 252 | n/a | 141 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| pause-octagon-outline.svg | 250 | 259 | 115 | 126 | 106 | 100 | 96 | 38.4% |  |
| view-day-outline.svg | 249 | 253 | n/a | 138 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| clock-time-six-outline.svg | 248 | 271 | n/a | 149 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| arrow-up-box.svg | 247 | 252 | 122 | 127 | 97 | 94 | 65 | 26.3% |  |
| fridge-variant-outline.svg | 247 | 267 | n/a | 149 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| table-merge-cells.svg | 247 | 252 | 157 | 170 | 120 | 108 | 26 | 10.5% |  |
| battery-10.svg | 246 | 244 | n/a | 111 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| battery-40.svg | 246 | 244 | n/a | 111 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| battery-60.svg | 246 | 244 | n/a | 111 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| dice-1.svg | 246 | 240 | n/a | 136 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| source-commit.svg | 246 | 298 | n/a | 130 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| battery-80.svg | 245 | 243 | n/a | 111 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| grid-large.svg | 245 | 243 | n/a | 152 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| subtitles.svg | 245 | 242 | n/a | 151 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| alpha-w-circle.svg | 244 | 246 | n/a | 136 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| file-export.svg | 244 | 246 | n/a | 116 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| numeric-4-box-multiple.svg | 244 | 254 | 146 | 153 | 104 | 96 | 51 | 20.9% |  |
| chart-box.svg | 243 | 240 | n/a | 138 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| format-wrap-square.svg | 242 | 248 | 151 | 172 | 106 | 88 | 26 | 10.7% |  |
| arrow-up-down.svg | 241 | 242 | 84 | 89 | 93 | 86 | 80 | 33.2% |  |
| fire-extinguisher.svg | 241 | 246 | 124 | 125 | 102 | 91 | 84 | 34.9% |  |
| gamepad-down.svg | 241 | 241 | 118 | 131 | 93 | 91 | 85 | 35.3% |  |
| home-thermometer.svg | 241 | 412 | n/a | 131 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| message-plus-outline.svg | 241 | 249 | n/a | 142 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| alpha-x-circle.svg | 240 | 242 | 125 | 128 | 89 | 82 | 56 | 23.3% |  |
| book-alert.svg | 240 | 248 | n/a | 138 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| drawing.svg | 240 | 235 | 96 | 97 | 85 | 81 | 72 | 30.0% |  |
| file-download.svg | 240 | 241 | 114 | 125 | 102 | 96 | 48 | 20.0% |  |
| fridge-variant.svg | 240 | 252 | n/a | 137 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| mustache.svg | 240 | 236 | 152 | 153 | 107 | 94 | 102 | 42.5% |  |
| swap-horizontal-circle.svg | 240 | 250 | n/a | 135 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| alpha-x-box.svg | 239 | 238 | 137 | 140 | 97 | 83 | 56 | 23.4% |  |
| briefcase.svg | 239 | 241 | n/a | 138 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| credit-card-plus-outline.svg | 239 | 256 | 141 | 148 | 114 | 102 | 87 | 36.4% |  |
| folder-settings.svg | 239 | 247 | 134 | 143 | 105 | 91 | 43 | 18.0% |  |
| map-marker-left.svg | 239 | 281 | n/a | 122 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| timer-sand.svg | 239 | 257 | 122 | 133 | 97 | 89 | 87 | 36.4% |  |
| altimeter.svg | 238 | 235 | 122 | 139 | 106 | 102 | 91 | 38.2% |  |
| check-outline.svg | 238 | 239 | 79 | 88 | 92 | 84 | 77 | 32.4% |  |
| credit-card-settings.svg | 238 | 246 | n/a | 145 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| format-text-rotation-up.svg | 238 | 249 | 92 | 103 | 95 | 81 | 26 | 10.9% |  |
| message-arrow-right.svg | 238 | 245 | n/a | 123 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| volume-mute.svg | 238 | 237 | 103 | 110 | 101 | 100 | 84 | 35.3% |  |
| format-align-middle.svg | 237 | 244 | 114 | 123 | 101 | 98 | 85 | 35.9% |  |
| star-plus.svg | 237 | 234 | 113 | 120 | 110 | 104 | 87 | 36.7% |  |
| calendar-week.svg | 236 | 247 | 136 | 143 | 110 | 107 | 80 | 33.9% |  |
| comment.svg | 236 | 237 | 119 | 122 | 94 | 88 | 29 | 12.3% |  |
| image-filter-frames.svg | 236 | 243 | n/a | 137 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| music-accidental-double-sharp.svg | 235 | 252 | 106 | 111 | 93 | 84 | 86 | 36.6% |  |
| pencil-minus.svg | 235 | 235 | n/a | 107 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| sort-alphabetical-ascending.svg | 235 | 255 | n/a | 149 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| filmstrip.svg | 234 | 231 | n/a | 167 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| launch.svg | 234 | 228 | n/a | 125 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| npm.svg | 234 | 225 | 146 | 157 | 114 | 99 | 86 | 36.8% |  |
| star-four-points-outline.svg | 234 | 246 | 99 | 108 | 83 | 79 | 81 | 34.6% |  |
| store-settings.svg | 234 | 236 | 139 | 154 | 113 | 98 | 71 | 30.3% |  |
| bank-transfer-in.svg | 233 | 237 | 125 | 140 | 107 | 98 | 85 | 36.5% |  |
| download-off.svg | 233 | 233 | 93 | 102 | 106 | 97 | 69 | 29.6% |  |
| message-bookmark-outline.svg | 233 | 245 | n/a | 124 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| microsoft-azure-devops.svg | 233 | 243 | 89 | 96 | 99 | 93 | 81 | 34.8% |  |
| arrow-u-up-left.svg | 232 | 255 | 103 | 106 | 92 | 91 | 49 | 21.1% |  |
| not-equal-variant.svg | 232 | 237 | 94 | 99 | 104 | 98 | 81 | 34.9% |  |
| watch-variant.svg | 232 | 243 | 127 | 132 | 94 | 91 | 26 | 11.2% |  |
| window-open.svg | 232 | 231 | 139 | 146 | 99 | 86 | 69 | 29.7% |  |
| keyboard-f2.svg | 231 | 235 | 127 | 132 | 107 | 98 | 26 | 11.3% |  |
| surround-sound-2-1.svg | 231 | 237 | 131 | 138 | 115 | 101 | 87 | 37.7% |  |
| file-delimited.svg | 230 | 232 | 116 | 125 | 103 | 99 | 61 | 26.5% |  |
| home-floor-0.svg | 230 | 230 | 121 | 130 | 96 | 85 | 72 | 31.3% |  |
| mailbox-open.svg | 230 | 230 | n/a | 138 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| open-in-new.svg | 230 | 232 | n/a | 124 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| code-array.svg | 228 | 231 | 134 | 141 | 96 | 91 | 26 | 11.4% |  |
| alpha-n-box-outline.svg | 227 | 234 | n/a | 139 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| folder-download-outline.svg | 227 | 238 | n/a | 132 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| folder-open.svg | 227 | 236 | 108 | 109 | 101 | 89 | 26 | 11.5% |  |
| card-plus-outline.svg | 226 | 239 | 126 | 131 | 105 | 95 | 80 | 35.4% |  |
| cellphone-text.svg | 226 | 233 | 126 | 135 | 101 | 97 | 76 | 33.6% |  |
| flashlight-off.svg | 226 | 228 | 100 | 111 | 102 | 89 | 81 | 35.8% |  |
| floor-lamp-torchiere-variant-outline.svg | 225 | 249 | 94 | 103 | 97 | 99 | 80 | 35.6% |  |
| folder-home.svg | 225 | 224 | n/a | 130 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| arrow-up-bold-box-outline.svg | 224 | 237 | n/a | 130 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| checkbox-marked-circle.svg | 224 | 234 | n/a | 101 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| pin-off.svg | 224 | 219 | 106 | 113 | 102 | 95 | 85 | 37.9% |  |
| arrow-right-bold-box-outline.svg | 223 | 239 | n/a | 130 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| cellphone-play.svg | 223 | 230 | n/a | 118 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| credit-card-multiple.svg | 223 | 231 | 128 | 132 | 94 | 81 | 57 | 25.6% |  |
| folder-download.svg | 223 | 231 | 114 | 116 | 96 | 95 | 45 | 20.2% |  |
| microsoft-windows.svg | 223 | 228 | 87 | 102 | 90 | 89 | 76 | 34.1% |  |
| card-text-outline.svg | 222 | 227 | n/a | 134 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| microsoft-xbox-controller-menu.svg | 222 | 240 | n/a | 122 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| page-layout-header-footer.svg | 222 | 243 | n/a | 119 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| seat-outline.svg | 222 | 222 | n/a | 139 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| alpha-f-box-outline.svg | 221 | 233 | 128 | 135 | 96 | 90 | 57 | 25.8% |  |
| calendar-today.svg | 221 | 226 | n/a | 135 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| cellphone-charging.svg | 220 | 231 | n/a | 120 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| diameter.svg | 220 | 216 | n/a | 114 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| shield-check.svg | 220 | 220 | n/a | 95 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| cabin-a-frame.svg | 218 | 219 | 90 | 103 | 93 | 89 | 77 | 35.3% |  |
| message-settings.svg | 218 | 222 | n/a | 127 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| vector-polyline.svg | 218 | 221 | n/a | 124 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| tooltip-minus.svg | 217 | 228 | n/a | 115 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| alpha-y-box.svg | 216 | 215 | 120 | 123 | 90 | 76 | 31 | 14.4% |  |
| currency-ils.svg | 216 | 216 | 121 | 124 | 99 | 89 | 80 | 37.0% |  |
| mouse.svg | 216 | 209 | n/a | 98 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| store-outline.svg | 216 | 217 | 113 | 124 | 98 | 96 | 80 | 37.0% |  |
| alpha-h-circle.svg | 214 | 216 | n/a | 112 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| alpha-i-box.svg | 214 | 213 | 121 | 124 | 93 | 85 | 54 | 25.2% |  |
| alpha-n-circle.svg | 214 | 216 | 107 | 110 | 83 | 69 | 45 | 21.0% |  |
| equal-box.svg | 214 | 216 | 111 | 118 | 92 | 92 | 62 | 29.0% |  |
| tablet-android.svg | 214 | n/a | n/a | 111 | n/a | n/a | n/a | n/a | no_source |
| alpha-h-box.svg | 213 | 212 | 121 | 124 | 91 | 83 | 49 | 23.0% |  |
| format-letter-matches.svg | 213 | 222 | n/a | 91 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| diamond-stone.svg | 212 | 213 | n/a | 133 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| routes.svg | 212 | 206 | 120 | 123 | 95 | 93 | 26 | 12.3% |  |
| alpha-v-circle.svg | 211 | 213 | 102 | 105 | 78 | 65 | 39 | 18.5% |  |
| keyboard-f5.svg | 210 | 216 | 114 | 119 | 98 | 87 | 57 | 27.1% |  |
| seat.svg | 210 | 202 | 116 | 125 | 99 | 88 | 26 | 12.4% |  |
| clock-time-one.svg | 209 | 226 | n/a | 107 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| message-bookmark.svg | 209 | 213 | n/a | 103 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| map-marker-alert.svg | 208 | 212 | n/a | 109 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| seat-individual-suite.svg | 208 | 217 | n/a | 112 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| timer-sand-empty.svg | 208 | 232 | 98 | 109 | 86 | 76 | 76 | 36.5% |  |
| axis-x-arrow.svg | 207 | 207 | 72 | 77 | 85 | 73 | 29 | 14.0% |  |
| door-closed.svg | 205 | 204 | n/a | 107 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| filter-variant-minus.svg | 205 | 213 | n/a | 96 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| human-child.svg | 205 | 204 | n/a | 112 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| information.svg | 205 | 204 | n/a | 99 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| message-reply-outline.svg | 205 | 214 | n/a | 101 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| magnet.svg | 204 | 198 | n/a | 113 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| message-plus.svg | 204 | 207 | 112 | 117 | 91 | 85 | 62 | 30.4% |  |
| pause-circle.svg | 204 | 204 | n/a | 99 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| ray-end.svg | 204 | 199 | 81 | 82 | 85 | 83 | 73 | 35.8% |  |
| spirit-level.svg | 204 | 216 | n/a | 116 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| pan-top-right.svg | 203 | 204 | n/a | 91 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| alpha-t-circle.svg | 201 | 203 | 97 | 100 | 79 | 66 | 40 | 19.9% |  |
| arrow-collapse-left.svg | 199 | 206 | 75 | 82 | 79 | 77 | 68 | 34.2% |  |
| eight-track.svg | 199 | 198 | 104 | 109 | 92 | 89 | 79 | 39.7% |  |
| view-gallery-outline.svg | 199 | 207 | 107 | 120 | 92 | 80 | 26 | 13.1% |  |
| table-of-contents.svg | 198 | 203 | 107 | 120 | 87 | 79 | 58 | 29.3% |  |
| alpha-l-circle.svg | 197 | 199 | 91 | 94 | 75 | 62 | 26 | 13.2% |  |
| heart-half.svg | 197 | 204 | 74 | 75 | 87 | 79 | 69 | 35.0% |  |
| ethereum.svg | 196 | 192 | 59 | 68 | 62 | 51 | 53 | 27.0% |  |
| share-all.svg | 195 | 192 | n/a | 96 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| sign-direction-minus.svg | 195 | 203 | n/a | 101 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| tray-full.svg | 195 | 192 | n/a | 110 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| ceiling-light-outline.svg | 194 | 225 | 87 | 92 | 86 | 75 | 69 | 35.6% |  |
| music-note-half.svg | 194 | 197 | 82 | 85 | 80 | 73 | 63 | 32.5% |  |
| reply-all.svg | 194 | 191 | n/a | 96 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| pan-down.svg | 193 | 189 | n/a | 89 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| ray-start.svg | 192 | 192 | 80 | 81 | 84 | 70 | 67 | 34.9% |  |
| credit-card.svg | 190 | 189 | n/a | 97 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| ladder.svg | 190 | 184 | 101 | 110 | 88 | 82 | 70 | 36.8% |  |
| page-layout-header.svg | 189 | 195 | n/a | 100 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| wall-sconce-outline.svg | 189 | 196 | 86 | 95 | 87 | 86 | 69 | 36.5% |  |
| floor-lamp-torchiere-variant.svg | 188 | 204 | 77 | 82 | 82 | 72 | 68 | 36.2% |  |
| format-list-bulleted-square.svg | 188 | 203 | 107 | 119 | 91 | 82 | 60 | 31.9% |  |
| stop-circle.svg | 188 | 187 | n/a | 84 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| valve-open.svg | 188 | 186 | n/a | 90 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| arrow-right-top-bold.svg | 187 | 195 | 77 | 80 | 80 | 71 | 65 | 34.8% |  |
| archive-arrow-up-outline.svg | 186 | 198 | n/a | 104 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| arrow-top-left-bottom-right-bold.svg | 186 | 206 | 60 | 65 | 69 | 65 | 62 | 33.3% |  |
| fullscreen-exit.svg | 186 | 189 | 101 | 110 | 85 | 72 | 53 | 28.5% |  |
| plus-minus-variant.svg | 185 | 191 | 88 | 97 | 91 | 93 | 61 | 33.0% |  |
| format-indent-increase.svg | 184 | 194 | n/a | 104 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| skew-less.svg | 183 | 180 | 79 | 90 | 81 | 73 | 66 | 36.1% |  |
| delete.svg | 182 | 176 | n/a | 89 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| checkbox-blank.svg | 181 | 188 | 83 | 84 | 72 | 63 | 52 | 28.7% |  |
| format-text-wrapping-overflow.svg | 180 | 197 | 88 | 99 | 82 | 78 | 63 | 35.0% |  |
| sort.svg | 180 | 172 | n/a | 101 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| home-import-outline.svg | 178 | 202 | 93 | 95 | 90 | 87 | 26 | 14.6% |  |
| view-split-vertical.svg | 178 | 185 | 92 | 103 | 83 | 74 | 64 | 36.0% |  |
| arrow-top-right-thick.svg | 177 | 186 | 51 | 56 | 64 | 56 | 26 | 14.7% |  |
| chart-timeline.svg | 177 | 179 | 95 | 104 | 87 | 81 | 69 | 39.0% |  |
| keyboard-tab-reverse.svg | 176 | 184 | n/a | 76 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| location-exit.svg | 176 | 177 | n/a | 75 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| moon-waning-gibbous.svg | 175 | 182 | 60 | 61 | 66 | 65 | 52 | 29.7% |  |
| page-last.svg | 173 | 170 | 63 | 70 | 70 | 61 | 57 | 32.9% |  |
| subdirectory-arrow-right.svg | 173 | 185 | 63 | 68 | 70 | 68 | 59 | 34.1% |  |
| format-list-group.svg | 172 | 177 | 89 | 98 | 81 | 70 | 26 | 15.1% |  |
| format-text-variant.svg | 171 | 178 | n/a | 70 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| subdirectory-arrow-left.svg | 171 | 182 | 63 | 68 | 73 | 68 | 60 | 35.1% |  |
| vanish-quarter.svg | 171 | 173 | 68 | 76 | 74 | 73 | 60 | 35.1% |  |
| relation-one-or-many-to-many.svg | 170 | 186 | 94 | 94 | 82 | 78 | 65 | 38.2% |  |
| home-analytics.svg | 167 | 169 | n/a | 84 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| moon-waxing-crescent.svg | 167 | 175 | 58 | 59 | 65 | 61 | 50 | 29.9% |  |
| microsoft-dynamics-365.svg | 166 | 176 | 67 | 72 | 69 | 56 | 57 | 34.3% |  |
| network-strength-3-alert.svg | 166 | 178 | n/a | 78 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| reply.svg | 166 | 159 | 64 | 65 | 69 | 59 | 58 | 34.9% |  |
| current-dc.svg | 165 | 163 | 77 | 86 | 73 | 60 | 53 | 32.1% |  |
| ellipse.svg | 165 | 184 | 74 | 75 | 71 | 70 | 65 | 39.4% |  |
| menu-right-outline.svg | 163 | 169 | 53 | 60 | 66 | 55 | 53 | 32.5% |  |
| share.svg | 163 | 156 | 60 | 65 | 70 | 65 | 57 | 35.0% |  |
| align-horizontal-center.svg | 162 | 173 | 80 | 83 | 75 | 72 | 59 | 36.4% |  |
| upload-multiple.svg | 162 | 165 | 75 | 82 | 74 | 64 | 26 | 16.0% |  |
| view-array-outline.svg | 162 | 168 | 77 | 86 | 76 | 69 | 59 | 36.4% |  |
| compare-horizontal.svg | 161 | 167 | 71 | 78 | 71 | 62 | 57 | 35.4% |  |
| greater-than.svg | 161 | 161 | 48 | 53 | 61 | 53 | 25 | 15.5% |  |
| home-variant-outline.svg | 161 | 169 | 73 | 78 | 77 | 63 | 61 | 37.9% |  |
| keyboard-f7.svg | 161 | 160 | 76 | 83 | 74 | 68 | 46 | 28.6% |  |
| text-long.svg | 161 | 158 | 77 | 86 | 75 | 66 | 55 | 34.2% |  |
| bowl.svg | 160 | 152 | 58 | 61 | 66 | 62 | 55 | 34.4% |  |
| call-missed.svg | 160 | 159 | 60 | 60 | 73 | 65 | 57 | 35.6% |  |
| chevron-down.svg | 159 | 159 | 48 | 53 | 61 | 53 | 49 | 30.8% |  |
| view-quilt.svg | 159 | 157 | n/a | 77 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| apple-keyboard-option.svg | 158 | 167 | 63 | 68 | 76 | 68 | 59 | 37.3% |  |
| arrow-down-thin.svg | 156 | 159 | 45 | 45 | 58 | 50 | 51 | 32.7% |  |
| format-italic.svg | 156 | 157 | 60 | 63 | 67 | 64 | 58 | 37.2% |  |
| navigation.svg | 156 | 154 | 48 | 53 | 61 | 51 | 49 | 31.4% |  |
| bookmark.svg | 155 | 156 | 65 | 66 | 68 | 55 | 49 | 31.6% |  |
| format-strikethrough.svg | 155 | 163 | n/a | 75 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| arrow-top-left.svg | 153 | 155 | 51 | 56 | 64 | 56 | 49 | 32.0% |  |
| format-size.svg | 153 | 152 | 71 | 76 | 75 | 66 | 54 | 35.3% |  |
| arrow-top-right.svg | 152 | 155 | 51 | 56 | 64 | 56 | 26 | 17.1% |  |
| garage-open-variant.svg | 152 | 159 | 64 | 71 | 68 | 59 | 50 | 32.9% |  |
| star-three-points.svg | 152 | 157 | 48 | 53 | 61 | 53 | 26 | 17.1% |  |
| glass-pint-outline.svg | 150 | 156 | 53 | 60 | 63 | 55 | 52 | 34.7% |  |
| arrange-bring-forward.svg | 149 | 158 | 65 | 70 | 67 | 62 | 56 | 37.6% |  |
| view-compact.svg | 149 | 149 | 62 | 69 | 66 | 62 | 48 | 32.2% |  |
| window-shutter-open.svg | 149 | 156 | 71 | 76 | 74 | 70 | 26 | 17.4% |  |
| code-brackets.svg | 148 | 149 | n/a | 73 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| curtains-closed.svg | 147 | 150 | 62 | 69 | 66 | 60 | 43 | 29.3% |  |
| nail.svg | 147 | 139 | 54 | 59 | 64 | 54 | 50 | 34.0% |  |
| filter-variant.svg | 144 | 146 | n/a | 63 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| loading.svg | 143 | 138 | 52 | 53 | 56 | 49 | 45 | 31.5% |  |
| alpha-y.svg | 142 | 137 | 55 | 58 | 61 | 52 | 29 | 20.4% |  |
| view-carousel.svg | 141 | 142 | n/a | 63 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| arrow-left-bold.svg | 140 | 143 | 45 | 48 | 58 | 50 | 48 | 34.3% |  |
| numeric-negative-1.svg | 140 | 146 | 53 | 58 | 62 | 56 | 42 | 30.0% |  |
| square-wave.svg | 138 | 137 | 56 | 59 | 63 | 52 | 51 | 37.0% |  |
| tie.svg | 138 | 129 | 53 | 53 | 55 | 49 | 51 | 37.0% |  |
| roman-numeral-5.svg | 136 | 139 | 49 | 52 | 55 | 49 | 42 | 30.9% |  |
| flash.svg | 131 | 124 | 45 | 48 | 54 | 44 | 44 | 33.6% |  |
| forward.svg | 131 | 126 | 45 | 48 | 54 | 47 | 46 | 35.1% |  |
| play.svg | 131 | 123 | 31 | 36 | 44 | 36 | 39 | 29.8% |  |
| format-title.svg | 130 | 130 | 44 | 47 | 57 | 49 | 42 | 32.3% |  |
| alpha-t.svg | 126 | 121 | 44 | 47 | 57 | 46 | 42 | 33.3% |  |
| step-forward.svg | 126 | 126 | n/a | 44 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| moon-last-quarter.svg | 125 | 130 | 35 | 35 | 48 | 38 | 37 | 29.6% |  |
| menu-right.svg | 122 | 120 | 33 | 36 | 46 | 38 | 26 | 21.3% |  |
| power-on.svg | 118 | 114 | 32 | 35 | 45 | 37 | 38 | 32.2% |  |

### papirus (1000 files)

| File | ref_svg | cur_svg | TVG | ref_tvg | zstd | brotli | zstd+dict | dict/SVG | notes |
|------|---------|---------|-----|---------|------|--------|-----------|----------|-------|
| bluegriffon.svg | 18,509 | 21,306 | n/a | 6,293 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| preferences-system-services.svg | 14,975 | 21,887 | n/a | 4,929 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| aks.svg | 14,043 | n/a | n/a | 4,541 | n/a | n/a | n/a | n/a | no_source |
| freac.svg | 12,945 | 19,461 | n/a | 4,407 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| conky.svg | 12,821 | 16,851 | n/a | 4,363 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| com.github.birros.WebArchives.svg | 11,893 | 8,416 | n/a | 4,464 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| im.fluffychat.Fluffychat.svg | 11,127 | 17,909 | n/a | 3,788 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| meshlab.svg | 10,827 | 16,247 | n/a | 3,718 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| net.pioneerspacesim.Pioneer.svg | 10,449 | 12,421 | n/a | 3,959 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| com.github.donadigo.eddy.svg | 10,108 | 14,132 | n/a | 3,411 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| cc3d.svg | 10,011 | 10,892 | n/a | 3,158 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| thunderbird.svg | 9,386 | 4,873 | n/a | 3,257 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| xdman.svg | 8,923 | 10,822 | n/a | 3,103 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| cadence.svg | 8,894 | 13,692 | n/a | 3,081 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| skyrim-script-extender.svg | 8,879 | 13,913 | n/a | 3,164 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| strawberry.svg | 8,877 | 13,168 | n/a | 2,873 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| sideka.svg | 8,386 | 12,674 | n/a | 3,129 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| torrenttools.svg | 8,172 | 14,126 | n/a | 3,324 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| slade.svg | 7,871 | 12,658 | n/a | 3,240 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| tizen-studio-ide.svg | 7,802 | 10,997 | n/a | 2,698 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| komodo-edit.svg | 7,445 | 7,729 | 2,418 | 2,417 | 1,438 | 1,321 | 1,332 | 17.9% |  |
| full-throttle-remastered.svg | 7,403 | 8,323 | 2,168 | 2,502 | 1,328 | 1,248 | 753 | 10.2% |  |
| portal2.svg | 7,386 | 10,263 | n/a | 3,049 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| distributor-logo-debian.svg | 7,322 | 13,096 | n/a | 2,381 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| electrum-ltc.svg | 6,746 | 10,210 | n/a | 2,417 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| hitori.svg | 6,722 | 10,703 | n/a | 3,445 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| jpexs-decompiler.svg | 6,509 | 9,342 | n/a | 2,378 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| subsurface-icon.svg | 6,418 | 9,060 | 2,310 | 2,345 | 1,414 | 1,293 | 1,318 | 20.5% |  |
| icecat.svg | 6,331 | 9,175 | n/a | 2,199 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| cscz.svg | 6,328 | 8,312 | n/a | 2,126 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| gnome-sudoku.svg | 6,290 | 9,481 | n/a | 2,432 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| text-x-cobol.svg | 6,290 | 8,486 | 2,100 | 2,098 | 1,266 | 1,164 | 641 | 10.2% |  |
| dying-light.svg | 6,198 | 8,397 | n/a | 2,123 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| armello.svg | 6,171 | 10,929 | n/a | 2,856 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| gtk-theme-config.svg | 6,154 | 9,958 | n/a | 2,327 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| opentyrian.svg | 5,920 | 11,106 | n/a | 2,754 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| nexuiz.svg | 5,914 | 7,481 | 2,067 | 2,053 | 1,203 | 1,108 | 1,162 | 19.6% |  |
| rkward.svg | 5,836 | 8,923 | n/a | 2,065 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| kitty.svg | 5,785 | 10,821 | n/a | 3,035 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| bluej.svg | 5,660 | 7,586 | n/a | 1,926 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| euro-truck-simulator-2.svg | 5,558 | 9,376 | n/a | 2,868 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| referencer.svg | 5,537 | 7,750 | n/a | 1,996 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| ktorrent.svg | 5,486 | 8,555 | n/a | 1,991 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| uqm.svg | 5,463 | 8,841 | n/a | 1,984 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| sdrangel.svg | 5,332 | 7,845 | n/a | 1,862 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| liferea.svg | 5,231 | 9,445 | n/a | 2,012 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| kolf.svg | 5,206 | 8,209 | n/a | 2,506 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| kvirc.svg | 5,190 | 8,669 | n/a | 1,978 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| twitter.svg | 5,112 | 7,914 | n/a | 1,844 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| magictree.svg | 5,066 | 9,188 | n/a | 2,254 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| seahorse.svg | 5,033 | 7,711 | n/a | 2,234 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| stardew-valley.svg | 4,998 | 8,803 | n/a | 1,936 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| text-x-vbscript.svg | 4,986 | 7,883 | n/a | 1,979 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| photoflare.svg | 4,965 | 7,171 | n/a | 1,952 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| firefox-trunk.svg | 4,934 | n/a | n/a | 1,662 | n/a | n/a | n/a | n/a | no_source |
| text-x-qml.svg | 4,917 | 7,883 | n/a | 1,977 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| frostwire.svg | 4,878 | 7,652 | n/a | 1,970 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| slay-the-spire.svg | 4,777 | 6,719 | n/a | 1,698 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| application-vnd.mysql-workbench-model.svg | 4,660 | 6,871 | n/a | 1,582 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| write_stylus.svg | 4,649 | 10,477 | 2,214 | 1,675 | 1,336 | 1,274 | 1,335 | 28.7% |  |
| weather-few-clouds-wind-night.svg | 4,644 | 1,557 | n/a | 2,157 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| distributor-logo-kaos.svg | 4,624 | 7,057 | n/a | 1,528 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| mysql-workbench.svg | 4,609 | 6,564 | n/a | 1,563 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| fritzing.svg | 4,575 | 6,506 | n/a | 1,557 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| org.gnome.FontViewer.svg | 4,518 | 6,445 | n/a | 1,749 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| distributor-logo-knoppix.svg | 4,430 | 5,207 | n/a | 2,125 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| inkscape.svg | 4,426 | 7,034 | n/a | 1,483 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| indivisible.svg | 4,385 | 6,002 | n/a | 2,343 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| com.github.donadigo.appeditor.svg | 4,376 | 6,143 | n/a | 1,626 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| obdautodoctor.svg | 4,288 | 6,091 | n/a | 1,732 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| com.github.bartzaalberg.php-tester.svg | 4,284 | 6,231 | n/a | 1,472 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| httrack.svg | 4,277 | 5,931 | n/a | 1,604 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| hubstaff-gray.svg | 4,242 | 6,313 | n/a | 1,477 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| audoban.applet.playbar.svg | 4,225 | 6,666 | n/a | 2,224 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| tetzle.svg | 4,221 | 6,608 | n/a | 2,541 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| hubstaff-red.svg | 4,215 | 6,313 | n/a | 1,466 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| revolt.svg | 4,197 | 5,316 | n/a | 2,158 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| konversation.svg | 4,147 | 7,114 | n/a | 1,453 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| distributor-logo-netrunner.svg | 4,135 | 6,106 | n/a | 1,503 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| factorio.svg | 4,099 | 6,288 | n/a | 1,504 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| ice-store.svg | 4,096 | 7,919 | n/a | 1,589 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| jabref.svg | 4,085 | 5,906 | n/a | 1,450 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| performous.svg | 4,055 | 5,507 | 1,556 | 1,570 | 930 | 836 | 790 | 19.5% |  |
| com.github.thejambi.dayjournal.svg | 4,051 | 5,770 | 1,734 | 1,861 | 1,245 | 1,082 | 913 | 22.5% |  |
| microsoft-edge-dev.svg | 4,044 | 5,722 | n/a | 1,455 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| coypu.svg | 4,034 | 4,834 | n/a | 1,490 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| com.github.ryonakano.konbucase.svg | 3,939 | 5,066 | n/a | 1,569 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| weather-few-clouds-night.svg | 3,938 | 943 | n/a | 1,681 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| Sci48M.svg | 3,930 | 6,119 | n/a | 1,474 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| ghex.svg | 3,927 | 6,517 | n/a | 1,436 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| netbeans.svg | 3,871 | 7,864 | 1,683 | 1,455 | 995 | 947 | 626 | 16.2% |  |
| com.github.avojak.iridium.svg | 3,870 | 6,519 | n/a | 1,434 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| deltachat.svg | 3,767 | 5,828 | n/a | 1,217 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| postman.svg | 3,735 | 5,537 | n/a | 1,381 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| ericWeb.svg | 3,674 | 5,395 | n/a | 1,322 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| nmap.svg | 3,674 | 5,395 | n/a | 1,322 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| playonlinux.svg | 3,659 | 5,867 | n/a | 1,194 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| ms-onedrive.svg | 3,642 | 3,984 | 962 | 1,365 | 606 | 575 | 232 | 6.4% |  |
| phd2.svg | 3,633 | 4,992 | n/a | 1,652 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| gnac.svg | 3,630 | 6,486 | n/a | 1,598 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| nsm-proxy.svg | 3,622 | 4,916 | n/a | 1,490 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| epic-games.svg | 3,615 | 5,820 | n/a | 1,730 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| okteta.svg | 3,606 | 6,279 | n/a | 1,772 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| librewolf.svg | 3,557 | 4,524 | n/a | 1,283 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| armagetronad.svg | 3,554 | 4,741 | n/a | 1,276 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| kmahjongg.svg | 3,485 | 4,074 | n/a | 1,252 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| atom-rpg.svg | 3,484 | 5,368 | n/a | 1,273 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| weather-showers.svg | 3,463 | 1,489 | n/a | 1,400 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| mat.svg | 3,457 | 5,598 | n/a | 1,355 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| com.github.dbhowell.peeq.svg | 3,439 | 5,537 | 1,267 | 1,236 | 810 | 779 | 782 | 22.7% |  |
| freedoom1.svg | 3,431 | 5,542 | n/a | 1,397 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| freedoom2.svg | 3,431 | 5,542 | n/a | 1,397 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| winemine.svg | 3,426 | 5,572 | n/a | 1,529 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| alexandra.svg | 3,379 | 3,967 | n/a | 1,605 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| tilp.svg | 3,368 | 5,775 | 1,059 | 1,190 | 778 | 738 | 546 | 16.2% |  |
| google-play-music-desktop-player.svg | 3,353 | 5,661 | 1,176 | 1,286 | 774 | 749 | 389 | 11.6% |  |
| checkra1n.svg | 3,279 | 5,071 | n/a | 1,332 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| microsoft-edge.svg | 3,275 | 4,894 | n/a | 1,046 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| zart.svg | 3,273 | 5,068 | n/a | 1,417 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| bareftp.svg | 3,248 | 5,096 | 1,127 | 1,123 | 672 | 635 | 293 | 9.0% |  |
| view-financial-budget.svg | 3,244 | 1,558 | 560 | 1,876 | 251 | 198 | 246 | 7.6% |  |
| spacemacs.svg | 3,231 | 4,892 | 1,164 | 1,179 | 746 | 696 | 391 | 12.1% |  |
| edge-game.svg | 3,230 | 6,533 | 1,483 | 1,224 | 909 | 840 | 243 | 7.5% |  |
| grsync.svg | 3,220 | 5,318 | n/a | 1,125 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| realtimesync.svg | 3,217 | 5,318 | n/a | 1,125 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| catarina.svg | 3,215 | 4,982 | n/a | 1,215 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| pop-cosmic-applications.svg | 3,197 | 4,950 | 1,894 | 1,921 | 612 | 505 | 620 | 19.4% |  |
| protonmail-desktop.svg | 3,168 | 4,855 | n/a | 1,195 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| blackmagicraw-speedtest.svg | 3,112 | 4,840 | 1,104 | 1,359 | 665 | 619 | 245 | 7.9% |  |
| folder-red-linux.svg | 3,099 | 3,790 | n/a | 1,292 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-white-linux.svg | 3,093 | 3,790 | n/a | 1,292 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| mikutter.svg | 3,048 | 5,148 | n/a | 1,104 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| google-earth-pro.svg | 3,036 | 4,557 | n/a | 1,052 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| nsm-legacy-gui.svg | 2,989 | 4,031 | n/a | 1,334 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| xfce4-session.svg | 2,975 | 5,603 | n/a | 1,171 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| com.pajuelo.plasmaConfSaver.svg | 2,972 | 4,205 | n/a | 1,377 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| org.glimpse_editor.Glimpse.svg | 2,956 | n/a | n/a | 1,340 | n/a | n/a | n/a | n/a | no_source |
| application-vnd.flatpak.svg | 2,933 | 3,419 | 810 | 1,136 | 388 | 369 | 223 | 7.6% |  |
| dolphin-emu.svg | 2,931 | 4,263 | n/a | 1,023 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| pencil2d.svg | 2,921 | 5,152 | n/a | 1,140 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| aircrack-ng.svg | 2,918 | 3,795 | n/a | 1,033 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| guitar.svg | 2,891 | 4,611 | n/a | 1,044 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| emblem-web.svg | 2,887 | 4,400 | n/a | 992 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| qubic.svg | 2,861 | 4,104 | 1,254 | 1,302 | 698 | 678 | 332 | 11.6% |  |
| albert.svg | 2,824 | 4,096 | n/a | 1,014 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| distributor-logo-midnightbsd.svg | 2,811 | 3,870 | n/a | 1,035 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| application-x-kicad-schematic.svg | 2,785 | 4,537 | 1,570 | 1,731 | 847 | 803 | 391 | 14.0% |  |
| foot.svg | 2,758 | 4,556 | n/a | 1,207 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| de.haeckerfelix.Fragments.svg | 2,753 | 4,403 | 998 | 1,027 | 720 | 710 | 643 | 23.4% |  |
| flamerobin.svg | 2,746 | 3,857 | n/a | 996 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| pdfstudio.svg | 2,701 | 3,991 | 1,127 | 1,320 | 703 | 641 | 612 | 22.7% |  |
| com.github.torikulhabib.mindi.wma.svg | 2,685 | 3,965 | 1,013 | 1,078 | 786 | 772 | 534 | 19.9% |  |
| xampp.svg | 2,683 | 3,480 | n/a | 1,353 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| text-x-eiffel.svg | 2,682 | 3,904 | 1,088 | 1,088 | 667 | 611 | 136 | 5.1% |  |
| etcher.svg | 2,665 | 4,184 | 959 | 983 | 544 | 524 | 509 | 19.1% |  |
| weather-snow-rain.svg | 2,665 | 1,228 | n/a | 1,174 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| ocrfeeder.svg | 2,664 | 4,027 | n/a | 1,096 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| kvantum.svg | 2,653 | 4,167 | n/a | 1,106 | n/a | n/a | n/a | n/a | tvg-text:range |
| bandcamp.svg | 2,628 | 4,254 | n/a | 1,312 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| tresorit.svg | 2,627 | 3,373 | n/a | 979 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| psi.svg | 2,623 | 3,674 | n/a | 882 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| helltaker.svg | 2,609 | 3,817 | n/a | 1,450 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| gnome-chess.svg | 2,595 | 3,906 | n/a | 1,014 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| winecfg.svg | 2,593 | 3,534 | n/a | 962 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| 2gis.svg | 2,590 | 3,986 | n/a | 1,157 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| ventoy.svg | 2,579 | 4,062 | 971 | 991 | 572 | 522 | 501 | 19.4% |  |
| void-wizard.svg | 2,575 | 4,583 | n/a | 1,162 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| epsxe.svg | 2,565 | 3,778 | 1,168 | 1,069 | 819 | 766 | 385 | 15.0% |  |
| FreeTexturePacker.svg | 2,560 | 2,978 | 950 | 956 | 589 | 533 | 321 | 12.5% |  |
| org.gnome.Keysign.svg | 2,558 | 3,544 | 994 | 1,006 | 546 | 525 | 94 | 3.7% |  |
| text-vcard.svg | 2,556 | 3,545 | 944 | 993 | 595 | 541 | 444 | 17.4% |  |
| visualvm.svg | 2,547 | 3,225 | n/a | 1,389 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| flameshot.svg | 2,537 | 4,136 | n/a | 977 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| openboardview.svg | 2,509 | 3,801 | n/a | 1,628 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| minetest.svg | 2,497 | 3,810 | 880 | 884 | 491 | 467 | 464 | 18.6% |  |
| krita.svg | 2,473 | 4,056 | 855 | 868 | 581 | 536 | 515 | 20.8% |  |
| etl.svg | 2,472 | 3,698 | n/a | 959 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| trillian.svg | 2,462 | 3,887 | n/a | 1,190 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| ADLplug.svg | 2,461 | 3,321 | n/a | 1,047 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| quake3-team-arena.svg | 2,459 | 3,857 | n/a | 961 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| weather-few-clouds-wind.svg | 2,458 | 1,557 | n/a | 1,472 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| raven-reader.svg | 2,449 | 3,040 | 874 | 891 | 580 | 544 | 470 | 19.2% |  |
| rare.svg | 2,447 | 3,868 | n/a | 1,115 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| application-vnd.wolfram.nb.svg | 2,439 | 3,348 | n/a | 919 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| darktable.svg | 2,438 | 4,068 | n/a | 863 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| application-pkix-cert.svg | 2,437 | 3,438 | n/a | 1,283 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| plasmafox.svg | 2,405 | 3,601 | n/a | 1,037 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| bespoke_icon.svg | 2,399 | 3,669 | 1,007 | 1,082 | 641 | 593 | 490 | 20.4% |  |
| com.github.alcadica.develop.svg | 2,399 | 3,791 | 976 | 1,056 | 524 | 485 | 112 | 4.7% |  |
| com.github.linuxhubit.gitscover.svg | 2,384 | 3,243 | n/a | 1,195 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| tizen-studio-certificatemanager.svg | 2,361 | 3,427 | n/a | 1,038 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| distributor-logo-chakra.svg | 2,356 | 2,763 | n/a | 807 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| application-x-gba-rom.svg | 2,353 | 3,209 | n/a | 979 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| pyrenamer.svg | 2,347 | 3,345 | 944 | 969 | 569 | 517 | 171 | 7.3% |  |
| text-x-common-lisp.svg | 2,334 | 2,592 | 705 | 919 | 585 | 546 | 429 | 18.4% |  |
| duckstation.svg | 2,332 | 4,036 | 928 | 956 | 580 | 552 | 374 | 16.0% |  |
| space-pirates-and-zombies.svg | 2,323 | 2,550 | n/a | 809 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| jackpatch.svg | 2,291 | 3,121 | n/a | 988 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-custom-arduino.svg | 2,282 | n/a | n/a | 1,109 | n/a | n/a | n/a | n/a | no_source |
| io.elementary.appcenter.svg | 2,282 | 5,261 | n/a | 1,193 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-darkcyan-arduino.svg | 2,273 | 3,148 | 1,174 | 1,109 | 836 | 790 | 467 | 20.5% |  |
| folder-violet-arduino.svg | 2,273 | 3,148 | 1,174 | 1,109 | 836 | 791 | 463 | 20.4% |  |
| acreloaded.svg | 2,269 | 3,463 | n/a | 962 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| Ripcord_Icon.svg | 2,250 | 3,263 | n/a | 851 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| non-starred.svg | 2,235 | 665 | 75 | 810 | 88 | 80 | 81 | 3.6% |  |
| freeplane.svg | 2,233 | 3,781 | 897 | 912 | 605 | 577 | 514 | 23.0% |  |
| gpk-prefs.svg | 2,223 | 3,380 | n/a | 915 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| artikulate.svg | 2,198 | 7,377 | n/a | 790 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-black-network.svg | 2,165 | 2,517 | n/a | 997 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-cyan-network.svg | 2,165 | 2,517 | n/a | 997 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-darkcyan-network.svg | 2,165 | 2,517 | n/a | 997 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-white-network.svg | 2,159 | 2,517 | n/a | 997 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| airvpn.svg | 2,152 | 3,160 | 778 | 785 | 484 | 445 | 458 | 21.3% |  |
| akira.svg | 2,148 | 2,639 | 663 | 787 | 416 | 396 | 345 | 16.1% |  |
| Impactor.svg | 2,136 | 3,394 | 1,086 | 1,046 | 775 | 703 | 757 | 35.4% |  |
| makemkv.svg | 2,136 | 3,641 | n/a | 816 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| winetricks.svg | 2,133 | 2,845 | n/a | 759 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| easyeda.svg | 2,130 | 3,285 | 925 | 926 | 672 | 623 | 279 | 13.1% |  |
| phototonic.svg | 2,127 | 3,077 | 856 | 886 | 639 | 615 | 602 | 28.3% |  |
| citrix-receiver.svg | 2,118 | 2,086 | n/a | 1,049 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| 0cc-famitracker.svg | 2,113 | 2,944 | n/a | 1,213 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| face-crying.svg | 2,083 | 1,356 | n/a | 755 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| beat-hazard-2.svg | 2,079 | 3,585 | n/a | 1,181 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| kxstitch.svg | 2,079 | 3,242 | n/a | 955 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| rto-proxy.svg | 2,069 | 2,708 | 731 | 753 | 453 | 407 | 94 | 4.5% |  |
| x-tile.svg | 2,056 | 3,104 | 967 | 1,008 | 451 | 437 | 396 | 19.3% |  |
| i2pd.svg | 2,040 | 3,169 | 718 | 728 | 437 | 427 | 140 | 6.9% |  |
| netradiant.svg | 2,033 | 3,114 | n/a | 967 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| mx-conky.svg | 2,023 | 1,479 | 830 | 1,315 | 415 | 367 | 317 | 15.7% |  |
| org.gnode.NixView.svg | 2,017 | 3,033 | n/a | 765 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| vim.svg | 2,008 | 2,436 | 811 | 822 | 481 | 453 | 163 | 8.1% |  |
| security-medium.svg | 1,999 | 3,603 | n/a | 782 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| blender.svg | 1,992 | 2,905 | 913 | 786 | 528 | 525 | 294 | 14.8% |  |
| audacious.svg | 1,989 | 2,287 | 716 | 717 | 451 | 415 | 277 | 13.9% |  |
| org.gnome.PasswordSafe.svg | 1,973 | 1,996 | n/a | 1,187 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| jred.svg | 1,957 | 2,920 | n/a | 648 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| jyellow.svg | 1,957 | 2,920 | n/a | 648 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| hipchat.svg | 1,953 | 2,967 | n/a | 789 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| nomacs.svg | 1,946 | 3,219 | 1,078 | 1,091 | 512 | 450 | 451 | 23.2% |  |
| taskbar.svg | 1,943 | 3,370 | 1,272 | 1,290 | 524 | 419 | 488 | 25.1% |  |
| xcom-enemy-unknown.svg | 1,943 | 2,320 | 731 | 752 | 382 | 359 | 250 | 12.9% |  |
| musescore.svg | 1,932 | 3,282 | n/a | 979 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| crayon-physics-deluxe.svg | 1,925 | 2,443 | n/a | 691 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| unison-gtk.svg | 1,924 | 3,895 | n/a | 823 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| wine.svg | 1,908 | 2,575 | n/a | 653 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| muse-dash.svg | 1,895 | 3,220 | n/a | 950 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-magenta-owncloud.svg | 1,893 | 3,472 | n/a | 752 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-orange-owncloud.svg | 1,893 | 3,472 | n/a | 752 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-violet-owncloud.svg | 1,893 | 3,472 | n/a | 752 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| jellyfin.svg | 1,883 | 2,581 | n/a | 755 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| screencloud.svg | 1,881 | 2,355 | n/a | 958 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| wpscrackgui.svg | 1,881 | 3,196 | n/a | 708 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| mps.svg | 1,866 | 3,000 | n/a | 659 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| mpc-qt.svg | 1,856 | 2,943 | n/a | 924 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| folder-bluegrey-games.svg | 1,843 | 2,200 | n/a | 927 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-brown-games.svg | 1,843 | 2,200 | n/a | 927 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-cyan-games.svg | 1,843 | 2,200 | n/a | 927 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-darkcyan-games.svg | 1,843 | 2,200 | n/a | 927 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-grey-games.svg | 1,843 | 2,200 | n/a | 927 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-nordic-games.svg | 1,843 | 2,200 | n/a | 927 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-paleorange-games.svg | 1,843 | 2,200 | n/a | 927 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-violet-games.svg | 1,843 | 2,200 | n/a | 927 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-yaru-games.svg | 1,843 | 2,200 | n/a | 927 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| smilla.svg | 1,840 | 2,862 | 901 | 905 | 388 | 331 | 119 | 6.5% |  |
| application-x-font-ttf.svg | 1,818 | 2,164 | 684 | 699 | 473 | 446 | 300 | 16.5% |  |
| vmware-player.svg | 1,816 | 3,423 | 1,056 | 1,091 | 591 | 559 | 490 | 27.0% |  |
| text-x-erlang.svg | 1,812 | 2,608 | n/a | 738 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| ophcrack.svg | 1,810 | 1,903 | n/a | 1,086 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| jetbrains-toolbox.svg | 1,796 | 2,688 | n/a | 677 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| gcolor3.svg | 1,790 | 2,801 | 692 | 695 | 419 | 395 | 351 | 19.6% |  |
| jupyter.svg | 1,788 | 5,694 | n/a | 750 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| menulibre.svg | 1,788 | 3,059 | n/a | 805 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| applications-education.svg | 1,784 | 2,821 | 695 | 706 | 429 | 418 | 83 | 4.7% |  |
| banshee.svg | 1,769 | n/a | n/a | 828 | n/a | n/a | n/a | n/a | no_source |
| android-sdk.svg | 1,765 | 3,087 | n/a | 847 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| application-x-nes-rom.svg | 1,758 | 2,510 | 822 | 822 | 527 | 494 | 61 | 3.5% |  |
| weather-few-clouds.svg | 1,752 | 1,561 | n/a | 996 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| com.github.artemanufrij.graphui.svg | 1,750 | 2,924 | n/a | 860 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| openarena.svg | 1,748 | 2,379 | n/a | 703 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| mx-select-sound.svg | 1,742 | 2,955 | 900 | 896 | 487 | 451 | 35 | 2.0% |  |
| com.github.padjis.ghistory.svg | 1,741 | 2,433 | n/a | 765 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| chrome-app-list.svg | 1,739 | 2,284 | 1,576 | 1,541 | 454 | 410 | 135 | 7.8% |  |
| bloomrpc.svg | 1,735 | 2,888 | 608 | 572 | 550 | 545 | 533 | 30.7% |  |
| folder-custom-kde.svg | 1,731 | n/a | n/a | 918 | n/a | n/a | n/a | n/a | no_source |
| sparkleshare.svg | 1,730 | 3,234 | n/a | 881 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-bluegrey-kde.svg | 1,722 | 2,541 | 902 | 918 | 665 | 635 | 38 | 2.2% |  |
| folder-green-kde.svg | 1,722 | 2,541 | 902 | 918 | 665 | 635 | 38 | 2.2% |  |
| folder-magenta-kde.svg | 1,722 | 2,541 | 902 | 918 | 666 | 638 | 48 | 2.8% |  |
| folder-red-kde.svg | 1,722 | 2,541 | 902 | 918 | 665 | 638 | 38 | 2.2% |  |
| folder-yellow-kde.svg | 1,722 | 2,541 | 902 | 918 | 665 | 635 | 48 | 2.8% |  |
| postal-2.svg | 1,717 | 2,187 | n/a | 1,047 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| kali-undercover.svg | 1,713 | 1,632 | 761 | 773 | 418 | 374 | 151 | 8.8% |  |
| ryujinx.svg | 1,706 | 2,892 | 801 | 834 | 516 | 487 | 183 | 10.7% |  |
| cpod.svg | 1,701 | 3,367 | n/a | 898 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| YACReader.svg | 1,692 | 2,355 | n/a | 548 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| fontforge.svg | 1,687 | 1,835 | 536 | 667 | 349 | 322 | 220 | 13.0% |  |
| soundkonverter.svg | 1,685 | 3,345 | n/a | 744 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| alien-swarm-reactive-drop.svg | 1,684 | 1,596 | 762 | 750 | 438 | 397 | 291 | 17.3% |  |
| laigter.svg | 1,684 | 2,586 | n/a | 672 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| Zoom.svg | 1,672 | 2,381 | 704 | 710 | 465 | 425 | 333 | 19.9% |  |
| world-of-tanks.svg | 1,661 | 3,175 | n/a | 790 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| alienfx.svg | 1,657 | 2,385 | 576 | 583 | 382 | 345 | 369 | 22.3% |  |
| rstudio.svg | 1,654 | 3,263 | 884 | 676 | 447 | 421 | 406 | 24.5% |  |
| org.gnome.GTG.svg | 1,649 | 2,771 | n/a | 770 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| babe.svg | 1,645 | 5,520 | 1,118 | 1,229 | 426 | 353 | 230 | 14.0% |  |
| luminance-hdr.svg | 1,644 | 1,834 | n/a | 995 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-cyan-github.svg | 1,637 | 2,161 | 833 | 836 | 622 | 601 | 38 | 2.3% |  |
| folder-deeporange-github.svg | 1,637 | 2,161 | 833 | 836 | 622 | 598 | 38 | 2.3% |  |
| folder-green-github.svg | 1,637 | 2,161 | 833 | 836 | 624 | 593 | 38 | 2.3% |  |
| folder-grey-github.svg | 1,637 | 2,161 | 833 | 836 | 624 | 586 | 38 | 2.3% |  |
| folder-indigo-github.svg | 1,637 | 2,161 | 833 | 836 | 623 | 597 | 38 | 2.3% |  |
| folder-nordic-github.svg | 1,637 | 2,161 | 833 | 836 | 626 | 604 | 38 | 2.3% |  |
| com.github.aleksandar-stefanovic.urmsimulator | 1,632 | 1,865 | n/a | 508 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| application-x-aoi.svg | 1,619 | 2,332 | 750 | 760 | 439 | 406 | 377 | 23.3% |  |
| preferences-desktop-font.svg | 1,612 | 1,891 | 660 | 665 | 436 | 409 | 311 | 19.3% |  |
| application-x-blender.svg | 1,610 | 2,324 | n/a | 769 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| distributor-logo-steamos.svg | 1,602 | 2,334 | n/a | 883 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| org.gnome.NetworkDisplays.svg | 1,598 | 2,483 | n/a | 802 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| face-angry.svg | 1,592 | 961 | 234 | 617 | 222 | 204 | 165 | 10.4% |  |
| git.svg | 1,589 | 2,614 | n/a | 720 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| scid.svg | 1,587 | 2,323 | 951 | 1,033 | 417 | 381 | 106 | 6.7% |  |
| wicd.svg | 1,567 | 2,602 | 512 | 508 | 372 | 362 | 203 | 13.0% |  |
| texmaker.svg | 1,561 | 2,639 | 961 | 933 | 424 | 381 | 149 | 9.5% |  |
| civilization5.svg | 1,534 | 2,206 | n/a | 558 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| dotcover.svg | 1,532 | 2,457 | n/a | 564 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| eqonomize.svg | 1,531 | 2,354 | 663 | 703 | 511 | 494 | 440 | 28.7% |  |
| vidcutter.svg | 1,521 | 2,574 | n/a | 944 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| preferences-desktop-notification-bell.svg | 1,516 | 2,886 | n/a | 630 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| image-x-svg+xml.svg | 1,515 | 2,002 | 957 | 987 | 547 | 513 | 532 | 35.1% |  |
| ms-onenote.svg | 1,511 | 2,411 | 618 | 633 | 406 | 401 | 72 | 4.8% |  |
| calibre-viewer.svg | 1,507 | 2,109 | n/a | 662 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-black-image-people.svg | 1,507 | 1,852 | n/a | 793 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-bluegrey-image-people.svg | 1,507 | 1,852 | n/a | 793 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-bluegrey-publicshare-open.svg | 1,507 | 1,641 | n/a | 793 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-brown-image-people.svg | 1,507 | 1,852 | n/a | 793 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-deeporange-image-people.svg | 1,507 | 1,852 | n/a | 793 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-green-publicshare-open.svg | 1,507 | 1,641 | n/a | 793 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-red-publicshare-open.svg | 1,507 | 1,641 | n/a | 793 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-violet-image-people.svg | 1,507 | 1,852 | n/a | 793 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| yubikey-personalization-gui.svg | 1,507 | 1,924 | n/a | 592 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| audio-speaker-mono.svg | 1,503 | 2,201 | n/a | 636 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| com.github.kmal-kenneth.monilet.svg | 1,497 | 1,872 | n/a | 538 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| dotmemory.svg | 1,496 | 2,241 | n/a | 512 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| slingscold.svg | 1,495 | 1,607 | n/a | 615 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| singular.svg | 1,491 | 1,976 | 496 | 510 | 290 | 269 | 27 | 1.8% |  |
| custom-toolbox.svg | 1,485 | 1,718 | 708 | 716 | 455 | 439 | 303 | 20.4% |  |
| bridge-constructor-stunts.svg | 1,475 | 2,108 | n/a | 817 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| dosbox.svg | 1,473 | 1,423 | 1,227 | 1,303 | 526 | 454 | 205 | 13.9% |  |
| glyphr-studio-desktop.svg | 1,469 | 2,104 | n/a | 672 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-custom-gnome.svg | 1,457 | n/a | n/a | 774 | n/a | n/a | n/a | n/a | no_source |
| kipi-panorama.svg | 1,452 | 2,008 | 676 | 622 | 510 | 471 | 123 | 8.5% |  |
| catia.svg | 1,448 | 1,939 | 564 | 571 | 319 | 310 | 114 | 7.9% |  |
| folder-breeze-gnome.svg | 1,448 | 1,747 | n/a | 774 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-brown-gnome.svg | 1,448 | 1,747 | n/a | 774 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-nordic-gnome.svg | 1,448 | 1,747 | n/a | 774 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-palebrown-gnome.svg | 1,448 | 1,747 | n/a | 774 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-yaru-gnome.svg | 1,448 | 1,747 | n/a | 774 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| inode-symlink.svg | 1,442 | 2,028 | 560 | 560 | 393 | 364 | 248 | 17.2% |  |
| bzflag.svg | 1,431 | 1,975 | 993 | 1,000 | 555 | 511 | 395 | 27.6% |  |
| owncloud.svg | 1,428 | 1,526 | 483 | 487 | 259 | 236 | 138 | 9.7% |  |
| accessories-notes.svg | 1,424 | 2,469 | n/a | 799 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| ao-app.svg | 1,424 | 4,164 | 929 | 524 | 492 | 478 | 171 | 12.0% |  |
| kubeplayer.svg | 1,423 | 1,973 | 622 | 676 | 398 | 388 | 186 | 13.1% |  |
| magnatune.svg | 1,418 | 2,811 | n/a | 769 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| QOwnNotes.svg | 1,416 | 3,137 | n/a | 756 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| dottrace.svg | 1,412 | 2,145 | n/a | 482 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| mx-snapshot.svg | 1,411 | 1,499 | n/a | 821 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| phantompeer.svg | 1,409 | 2,081 | 904 | 909 | 540 | 515 | 247 | 17.5% |  |
| day-of-the-tentacle-remastered.svg | 1,403 | 1,887 | 572 | 574 | 377 | 357 | 325 | 23.2% |  |
| openage.svg | 1,401 | 1,810 | 600 | 624 | 395 | 342 | 259 | 18.5% |  |
| tilix.svg | 1,399 | 1,774 | 388 | 393 | 222 | 200 | 121 | 8.6% |  |
| application-dart.svg | 1,388 | 2,019 | n/a | 512 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-blue-apple.svg | 1,388 | 1,633 | n/a | 747 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-bluegrey-apple.svg | 1,388 | 1,633 | n/a | 747 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-cyan-apple.svg | 1,388 | 1,633 | n/a | 747 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-grey-apple.svg | 1,388 | 1,633 | n/a | 747 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-magenta-apple.svg | 1,388 | 1,633 | n/a | 747 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-palebrown-apple.svg | 1,388 | 1,633 | n/a | 747 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-teal-apple.svg | 1,388 | 1,633 | n/a | 747 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| com.github.themix_project.Oomox.svg | 1,383 | 1,465 | 510 | 566 | 280 | 272 | 226 | 16.3% |  |
| utilities-system-monitor.svg | 1,382 | 2,123 | 677 | 693 | 445 | 440 | 292 | 21.1% |  |
| folder-black-java.svg | 1,379 | 1,751 | n/a | 793 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-indigo-java.svg | 1,379 | 1,751 | n/a | 793 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-magenta-java.svg | 1,379 | 1,751 | n/a | 793 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-red-java.svg | 1,379 | 1,751 | n/a | 793 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| intellij.svg | 1,372 | 2,095 | n/a | 472 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| sirikali.svg | 1,371 | 1,772 | n/a | 763 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| fs-uae-launcher.svg | 1,368 | 1,999 | n/a | 559 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| qasmixer.svg | 1,366 | 1,838 | 997 | 993 | 469 | 421 | 216 | 15.8% |  |
| chrome-fljalecfjciodhpcledpamjachpmelml-Defau | 1,365 | n/a | n/a | 584 | n/a | n/a | n/a | n/a | no_source |
| face-sick.svg | 1,362 | 775 | n/a | 580 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| fusion-icon.svg | 1,362 | 2,034 | n/a | 523 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| network-card.svg | 1,361 | 2,552 | 697 | 696 | 406 | 369 | 58 | 4.3% |  |
| pingus-icon.svg | 1,359 | 2,247 | 621 | 624 | 349 | 326 | 264 | 19.4% |  |
| lovely-planet-arcade.svg | 1,357 | 1,851 | n/a | 721 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| fceux.svg | 1,348 | 2,573 | 662 | 641 | 426 | 391 | 372 | 27.6% |  |
| face-cool.svg | 1,341 | 789 | 506 | 1,091 | 327 | 294 | 265 | 19.8% |  |
| ares.svg | 1,321 | 2,058 | n/a | 450 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| text-x-texmacs.svg | 1,321 | 2,173 | 556 | 552 | 343 | 304 | 37 | 2.8% |  |
| krusader_root.svg | 1,315 | 2,083 | 513 | 555 | 341 | 311 | 102 | 7.8% |  |
| redshift.svg | 1,315 | 2,428 | 567 | 578 | 454 | 424 | 39 | 3.0% |  |
| stock_xfburn-burn-cd.svg | 1,304 | 1,852 | n/a | 612 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| clockify.svg | 1,301 | 1,987 | n/a | 600 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| tizen-studio-dynamicanalyzer.svg | 1,301 | 1,787 | n/a | 661 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-custom-projects.svg | 1,296 | n/a | n/a | 792 | n/a | n/a | n/a | n/a | no_source |
| folder-bluegrey-applications.svg | 1,292 | 1,714 | 801 | 802 | 508 | 461 | 38 | 2.9% |  |
| folder-indigo-applications.svg | 1,292 | 1,714 | 801 | 802 | 509 | 463 | 38 | 2.9% |  |
| folder-pink-applications.svg | 1,292 | 1,714 | 801 | 802 | 508 | 462 | 38 | 2.9% |  |
| folder-red-applications.svg | 1,292 | 1,714 | 801 | 802 | 508 | 461 | 38 | 2.9% |  |
| folder-black-development.svg | 1,290 | 1,543 | 752 | 730 | 490 | 484 | 38 | 2.9% |  |
| folder-bluegrey-development.svg | 1,290 | 1,543 | 752 | 730 | 492 | 490 | 38 | 2.9% |  |
| folder-breeze-development.svg | 1,290 | 1,543 | 752 | 730 | 490 | 489 | 38 | 2.9% |  |
| folder-darkcyan-development.svg | 1,290 | 1,543 | 752 | 730 | 491 | 478 | 38 | 2.9% |  |
| folder-deeporange-development.svg | 1,290 | 1,543 | 752 | 730 | 488 | 473 | 38 | 2.9% |  |
| folder-green-development.svg | 1,290 | 1,543 | 752 | 730 | 492 | 489 | 38 | 2.9% |  |
| folder-red-development.svg | 1,290 | 1,543 | 752 | 730 | 490 | 476 | 38 | 2.9% |  |
| rsibreak.svg | 1,288 | 2,255 | 619 | 619 | 364 | 341 | 266 | 20.7% |  |
| folder-deeporange-projects.svg | 1,287 | 1,599 | n/a | 792 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-paleorange-projects.svg | 1,287 | 1,599 | n/a | 792 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| darwinia.svg | 1,285 | 1,679 | 794 | 824 | 331 | 301 | 43 | 3.3% |  |
| isomaster.svg | 1,284 | 1,835 | n/a | 612 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| k9-copy.svg | 1,283 | 1,778 | n/a | 650 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| multiwinia.svg | 1,282 | 1,962 | 798 | 825 | 335 | 307 | 58 | 4.5% |  |
| stock_xfburn-blank-cdrw.svg | 1,281 | 790 | n/a | 590 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| qtdbusviewer.svg | 1,280 | 3,815 | 908 | 727 | 605 | 587 | 294 | 23.0% |  |
| jazzradio.svg | 1,277 | 3,313 | n/a | 576 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| nextcloud.svg | 1,273 | 1,530 | n/a | 800 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| preferences-desktop-navigation.svg | 1,273 | 2,007 | 580 | 584 | 288 | 295 | 93 | 7.3% |  |
| model-stl.svg | 1,272 | 1,749 | 546 | 538 | 336 | 335 | 311 | 24.4% |  |
| dropbox.svg | 1,269 | 1,864 | 582 | 585 | 303 | 317 | 281 | 22.1% |  |
| freecad.svg | 1,262 | 3,410 | 760 | 614 | 558 | 522 | 508 | 40.3% |  |
| folder-black-onedrive.svg | 1,261 | 2,667 | n/a | 803 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-darkcyan-onedrive.svg | 1,261 | 2,667 | n/a | 803 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-deeporange-onedrive.svg | 1,261 | 2,667 | n/a | 803 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-grey-onedrive.svg | 1,261 | 2,667 | n/a | 803 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-palebrown-onedrive.svg | 1,261 | 2,667 | n/a | 803 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-violet-onedrive.svg | 1,261 | 2,667 | n/a | 803 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-yellow-onedrive.svg | 1,261 | 2,667 | n/a | 803 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-darkcyan-meocloud.svg | 1,259 | 1,695 | n/a | 748 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-nordic-meocloud.svg | 1,259 | 1,695 | n/a | 748 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-pink-meocloud.svg | 1,259 | 1,695 | n/a | 748 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-red-meocloud.svg | 1,259 | 1,695 | n/a | 748 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-yellow-meocloud.svg | 1,259 | 1,695 | n/a | 748 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-custom-pcloud.svg | 1,255 | n/a | n/a | 818 | n/a | n/a | n/a | n/a | no_source |
| folder-white-onedrive.svg | 1,255 | 2,667 | n/a | 803 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-breeze-backup.svg | 1,254 | 1,857 | n/a | 750 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-carmine-backup.svg | 1,254 | 1,857 | n/a | 750 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-cyan-backup.svg | 1,254 | 1,857 | n/a | 750 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-deeporange-backup.svg | 1,254 | 1,857 | n/a | 750 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-green-backup.svg | 1,254 | 1,857 | n/a | 750 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-grey-backup.svg | 1,254 | 1,857 | n/a | 750 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-indigo-backup.svg | 1,254 | 1,857 | n/a | 750 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-magenta-backup.svg | 1,254 | 1,857 | n/a | 750 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-yaru-backup.svg | 1,254 | 1,857 | n/a | 750 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-white-meocloud.svg | 1,253 | 1,695 | n/a | 748 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-white-backup.svg | 1,248 | 1,857 | n/a | 750 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-blue-pcloud.svg | 1,246 | 1,965 | n/a | 818 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-carmine-pcloud.svg | 1,246 | 1,965 | n/a | 818 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-indigo-pcloud.svg | 1,246 | 1,965 | n/a | 818 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-nordic-pcloud.svg | 1,246 | 1,965 | n/a | 818 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-red-pcloud.svg | 1,246 | 1,965 | n/a | 818 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-violet-pcloud.svg | 1,246 | 1,965 | n/a | 818 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| pushbullet-indicator.svg | 1,246 | 1,886 | n/a | 570 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-custom-git.svg | 1,245 | n/a | n/a | 729 | n/a | n/a | n/a | n/a | no_source |
| minetime.svg | 1,242 | 1,690 | 506 | 533 | 295 | 263 | 183 | 14.7% |  |
| folder-white-pcloud.svg | 1,240 | 1,965 | n/a | 818 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| application-x-asp.svg | 1,239 | 1,876 | 666 | 709 | 400 | 366 | 32 | 2.6% |  |
| folder-blue-git.svg | 1,236 | 1,543 | 725 | 729 | 443 | 423 | 39 | 3.2% |  |
| folder-magenta-git.svg | 1,236 | 1,543 | 725 | 729 | 442 | 420 | 48 | 3.9% |  |
| folder-red-git.svg | 1,236 | 1,543 | 725 | 729 | 440 | 441 | 39 | 3.2% |  |
| easystroke.svg | 1,235 | 1,515 | 415 | 449 | 269 | 252 | 190 | 15.4% |  |
| opengl.svg | 1,234 | 1,510 | 480 | 495 | 328 | 312 | 27 | 2.2% |  |
| entangle.svg | 1,230 | 1,370 | 450 | 451 | 250 | 242 | 233 | 18.9% |  |
| audio-speaker-center.svg | 1,227 | 702 | 79 | 580 | 76 | 68 | 70 | 5.7% |  |
| input-mouse.svg | 1,223 | 2,116 | 489 | 495 | 289 | 272 | 129 | 10.5% |  |
| beyondallreason.svg | 1,220 | 1,681 | 816 | 805 | 438 | 400 | 55 | 4.5% |  |
| transmageddon.svg | 1,218 | 2,435 | 817 | 735 | 392 | 358 | 162 | 13.3% |  |
| weather-hail.svg | 1,218 | 1,404 | n/a | 628 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| AdobePrelude.svg | 1,216 | 1,816 | 563 | 562 | 407 | 401 | 282 | 23.2% |  |
| application-x-sqlite2.svg | 1,212 | 1,430 | n/a | 495 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| audio-speaker-left-side-testing.svg | 1,209 | 1,764 | n/a | 536 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-darkcyan-tar.svg | 1,205 | 1,454 | n/a | 849 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-grey-tar.svg | 1,205 | 1,454 | n/a | 849 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-orange-tar.svg | 1,205 | 1,454 | n/a | 849 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-pink-tar.svg | 1,205 | 1,454 | n/a | 849 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| sm.puri.Chatty.svg | 1,196 | 1,573 | n/a | 582 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| cutter.svg | 1,195 | 1,885 | n/a | 571 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| colortone.svg | 1,194 | 2,578 | 627 | 639 | 403 | 376 | 276 | 23.1% |  |
| com.github.rickybas.date-countdown.svg | 1,194 | 916 | n/a | 475 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-brown-steam.svg | 1,194 | 1,777 | n/a | 750 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-darkcyan-steam.svg | 1,194 | 1,777 | n/a | 750 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-grey-steam.svg | 1,194 | 1,777 | n/a | 750 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| qtodotxt.svg | 1,193 | 2,255 | n/a | 574 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| application-vnd.stardivision.mail.svg | 1,175 | 1,702 | 518 | 528 | 333 | 317 | 186 | 15.8% |  |
| gnome-lockscreen.svg | 1,175 | 738 | n/a | 727 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| fluajho.svg | 1,174 | 1,820 | n/a | 636 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| stuntrally.svg | 1,174 | 1,456 | 472 | 470 | 315 | 290 | 175 | 14.9% |  |
| olivia.svg | 1,173 | 1,802 | n/a | 757 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| moe-era.svg | 1,172 | 1,273 | n/a | 737 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| 6180-the-moon.svg | 1,166 | 1,278 | 781 | 789 | 451 | 372 | 361 | 31.0% |  |
| eu.scarpetta.PDFMixTool.svg | 1,155 | 1,837 | 504 | 521 | 378 | 360 | 250 | 21.6% |  |
| infector.svg | 1,155 | 1,927 | 661 | 724 | 298 | 264 | 234 | 20.3% |  |
| media-optical-video-new.svg | 1,155 | 1,273 | n/a | 569 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| face-smile.svg | 1,153 | 730 | n/a | 577 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| com.github.alonsoenrique.quotes.svg | 1,152 | 1,924 | n/a | 425 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| folder-grey-nextcloud.svg | 1,152 | 1,384 | n/a | 836 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| folder-orange-nextcloud.svg | 1,152 | 1,384 | n/a | 836 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| folder-red-nextcloud.svg | 1,152 | 1,384 | n/a | 836 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| folder-white-nextcloud.svg | 1,146 | 1,384 | n/a | 836 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| text-x-lua.svg | 1,146 | 1,492 | n/a | 595 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| Nextcloud_sync_shared.svg | 1,144 | 1,558 | n/a | 508 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| guake.svg | 1,144 | 1,084 | n/a | 671 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| sqldeveloper.svg | 1,144 | 1,484 | 586 | 536 | 247 | 230 | 176 | 15.4% |  |
| y-ppa-manager.svg | 1,135 | n/a | n/a | 596 | n/a | n/a | n/a | n/a | no_source |
| eBook-speaker.svg | 1,132 | 1,431 | 778 | 784 | 395 | 349 | 294 | 26.0% |  |
| vibrantLinux.svg | 1,126 | 1,621 | 442 | 443 | 259 | 260 | 213 | 18.9% |  |
| wxglade.svg | 1,123 | 1,860 | 534 | 536 | 348 | 330 | 85 | 7.6% |  |
| application-epub+zip.svg | 1,118 | 1,752 | 490 | 490 | 299 | 283 | 147 | 13.1% |  |
| audiobook.svg | 1,118 | 1,490 | n/a | 549 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| tor-browser-nightly.svg | 1,116 | 1,669 | n/a | 559 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| text-x-makefile.svg | 1,114 | 1,707 | 507 | 519 | 352 | 328 | 183 | 16.4% |  |
| vmware-workstation.svg | 1,111 | 1,310 | n/a | 593 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| org.processing.processingide.svg | 1,108 | 1,307 | 470 | 487 | 285 | 293 | 143 | 12.9% |  |
| qnapi.svg | 1,107 | 1,687 | n/a | 589 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| com.moddb.TotalChaos.svg | 1,104 | 1,675 | 510 | 513 | 345 | 329 | 217 | 19.7% |  |
| folder-brown-gitlab.svg | 1,096 | 1,432 | n/a | 673 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-darkcyan-gitlab.svg | 1,096 | 1,432 | n/a | 673 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-grey-gitlab.svg | 1,096 | 1,432 | n/a | 673 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-indigo-gitlab.svg | 1,096 | 1,432 | n/a | 673 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-palebrown-gitlab.svg | 1,096 | 1,432 | n/a | 673 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| half-life.svg | 1,094 | 859 | n/a | 491 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-brown-script.svg | 1,091 | 1,504 | 713 | 717 | 478 | 453 | 48 | 4.4% |  |
| folder-carmine-script.svg | 1,091 | 1,504 | 713 | 717 | 471 | 442 | 39 | 3.6% |  |
| folder-green-script.svg | 1,091 | 1,504 | 713 | 717 | 479 | 452 | 39 | 3.6% |  |
| folder-paleorange-script.svg | 1,091 | 1,504 | 713 | 717 | 479 | 454 | 39 | 3.6% |  |
| folder-pink-script.svg | 1,091 | 1,504 | 713 | 717 | 476 | 451 | 39 | 3.6% |  |
| folder-violet-script.svg | 1,091 | 1,504 | 713 | 717 | 478 | 447 | 36 | 3.3% |  |
| folder-custom-syncthing.svg | 1,090 | n/a | n/a | 698 | n/a | n/a | n/a | n/a | no_source |
| preferences-desktop-emoticons.svg | 1,088 | 1,645 | 447 | 543 | 336 | 322 | 238 | 21.9% |  |
| little-inferno.svg | 1,086 | 1,214 | 589 | 593 | 353 | 326 | 62 | 5.7% |  |
| steadyflow.svg | 1,086 | 1,591 | 432 | 432 | 354 | 326 | 31 | 2.9% |  |
| fontypython.svg | 1,083 | 1,836 | 604 | 617 | 380 | 339 | 259 | 23.9% |  |
| folder-brown-syncthing.svg | 1,081 | 1,663 | n/a | 698 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-deeporange-syncthing.svg | 1,081 | 1,663 | n/a | 698 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-magenta-syncthing.svg | 1,081 | 1,663 | n/a | 698 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-palebrown-syncthing.svg | 1,081 | 1,663 | n/a | 698 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-paleorange-syncthing.svg | 1,081 | 1,663 | n/a | 698 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| jclicauthor.svg | 1,081 | 1,748 | 432 | 440 | 258 | 262 | 224 | 20.7% |  |
| application-bitwig-template.svg | 1,075 | 1,614 | 602 | 602 | 265 | 231 | 91 | 8.5% |  |
| kfourinline.svg | 1,074 | 1,317 | n/a | 648 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| apple-music.svg | 1,071 | 1,156 | 568 | 570 | 288 | 267 | 250 | 23.3% |  |
| com.gitlab.bitseater.meteo.svg | 1,070 | 1,209 | 530 | 623 | 362 | 361 | 348 | 32.5% |  |
| com.github.bluesabre.darkbar.svg | 1,069 | 1,770 | 530 | 616 | 315 | 285 | 263 | 24.6% |  |
| dvanalyzer.svg | 1,068 | 1,258 | n/a | 586 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| nicotine-plus.svg | 1,065 | 3,254 | 831 | 499 | 506 | 473 | 389 | 36.5% |  |
| plasma-search.svg | 1,065 | 1,983 | n/a | 561 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| openboard.svg | 1,059 | 1,575 | 400 | 405 | 270 | 255 | 236 | 22.3% |  |
| face-smile-big.svg | 1,056 | 498 | 165 | 470 | 128 | 129 | 64 | 6.1% |  |
| mkusb.svg | 1,055 | 1,603 | n/a | 402 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| openoffice4-draw.svg | 1,049 | 1,281 | 333 | 341 | 239 | 226 | 171 | 16.3% |  |
| image-svg+xml-compressed.svg | 1,047 | 1,422 | 602 | 636 | 385 | 354 | 357 | 34.1% |  |
| application-vnd.oasis.opendocument.formula.sv | 1,041 | 1,536 | 470 | 488 | 318 | 289 | 42 | 4.0% |  |
| edex-ui.svg | 1,038 | 1,068 | 351 | 427 | 196 | 187 | 127 | 12.2% |  |
| folder-custom-templates.svg | 1,038 | n/a | n/a | 785 | n/a | n/a | n/a | n/a | no_source |
| iortcw.svg | 1,034 | 1,636 | n/a | 586 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| application-x-designer.svg | 1,030 | 1,560 | 444 | 445 | 301 | 289 | 155 | 15.0% |  |
| folder-breeze-templates-open.svg | 1,029 | 1,546 | 871 | 785 | 475 | 424 | 47 | 4.6% |  |
| folder-darkcyan-templates.svg | 1,029 | 1,940 | 871 | 785 | 476 | 432 | 39 | 3.8% |  |
| folder-deeporange-templates.svg | 1,029 | 1,940 | 871 | 785 | 480 | 436 | 38 | 3.7% |  |
| folder-green-templates-open.svg | 1,029 | 1,546 | 871 | 785 | 476 | 427 | 47 | 4.6% |  |
| folder-indigo-templates.svg | 1,029 | 1,940 | 871 | 785 | 481 | 427 | 38 | 3.7% |  |
| folder-nordic-templates-open.svg | 1,029 | 1,546 | 871 | 785 | 478 | 428 | 47 | 4.6% |  |
| folder-orange-templates.svg | 1,029 | 1,940 | 871 | 785 | 480 | 435 | 39 | 3.8% |  |
| folder-paleorange-templates-open.svg | 1,029 | 1,546 | 871 | 785 | 478 | 431 | 47 | 4.6% |  |
| folder-paleorange-templates.svg | 1,029 | 1,940 | 871 | 785 | 483 | 437 | 38 | 3.7% |  |
| folder-red-templates.svg | 1,029 | 1,940 | 871 | 785 | 476 | 432 | 39 | 3.8% |  |
| folder-teal-templates.svg | 1,029 | 1,940 | 871 | 785 | 474 | 434 | 39 | 3.8% |  |
| folder-violet-templates.svg | 1,029 | 1,940 | 871 | 785 | 481 | 427 | 35 | 3.4% |  |
| folder-yaru-templates-open.svg | 1,029 | 1,546 | 871 | 785 | 472 | 427 | 47 | 4.6% |  |
| phoronix-test-suite.svg | 1,029 | 1,744 | 535 | 547 | 344 | 303 | 133 | 12.9% |  |
| dev.geopjr.Hashbrown.svg | 1,023 | n/a | n/a | 513 | n/a | n/a | n/a | n/a | no_source |
| io.github.OpenToonz.svg | 1,020 | 1,800 | n/a | 586 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| air.svg | 1,019 | 1,202 | n/a | 653 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| datovka.svg | 1,017 | 1,529 | 491 | 505 | 345 | 342 | 207 | 20.4% |  |
| zenkit.svg | 1,015 | 1,491 | n/a | 510 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| eureka.svg | 1,010 | 1,813 | 571 | 599 | 338 | 324 | 205 | 20.3% |  |
| folder-custom-visiting.svg | 1,004 | n/a | n/a | 650 | n/a | n/a | n/a | n/a | no_source |
| folder-black-books.svg | 1,003 | 1,140 | n/a | 768 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| folder-green-books.svg | 1,003 | 1,140 | n/a | 768 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| folder-indigo-books.svg | 1,003 | 1,140 | n/a | 768 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| folder-violet-books.svg | 1,003 | 1,140 | n/a | 768 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| kcmdf.svg | 1,002 | 1,234 | 637 | 640 | 358 | 324 | 122 | 12.2% |  |
| folder-black-sync.svg | 997 | 1,468 | n/a | 664 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-breeze-sync.svg | 997 | 1,468 | n/a | 664 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-indigo-sync.svg | 997 | 1,468 | n/a | 664 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-magenta-sync.svg | 997 | 1,468 | n/a | 664 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-teal-sync.svg | 997 | 1,468 | n/a | 664 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| quassel.svg | 996 | 1,795 | 526 | 529 | 282 | 271 | 154 | 15.5% |  |
| text-r.svg | 996 | 1,400 | 429 | 479 | 336 | 323 | 172 | 17.3% |  |
| folder-black-visiting.svg | 995 | 1,312 | 627 | 650 | 414 | 384 | 38 | 3.8% |  |
| folder-bluegrey-visiting.svg | 995 | 1,312 | 627 | 650 | 417 | 394 | 38 | 3.8% |  |
| folder-cyan-visiting.svg | 995 | 1,312 | 627 | 650 | 414 | 387 | 38 | 3.8% |  |
| folder-deeporange-visiting.svg | 995 | 1,312 | 627 | 650 | 415 | 396 | 38 | 3.8% |  |
| folder-grey-visiting.svg | 995 | 1,312 | 627 | 650 | 414 | 387 | 38 | 3.8% |  |
| face-raspberry.svg | 994 | 696 | 219 | 567 | 187 | 186 | 134 | 13.5% |  |
| kget.svg | 993 | 1,948 | 510 | 526 | 363 | 347 | 193 | 19.4% |  |
| wavebox.svg | 992 | 1,321 | 428 | 437 | 281 | 259 | 220 | 22.2% |  |
| ldview.svg | 991 | 1,978 | 447 | 528 | 276 | 264 | 253 | 25.5% |  |
| peerunity.svg | 991 | 1,319 | 328 | 386 | 229 | 212 | 156 | 15.7% |  |
| terminator.svg | 990 | 1,642 | 606 | 589 | 366 | 301 | 267 | 27.0% |  |
| yubikey-piv-manager.svg | 989 | 1,346 | n/a | 369 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| folder-black-locked.svg | 987 | 1,210 | n/a | 658 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-breeze-locked.svg | 987 | 1,210 | n/a | 658 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-carmine-locked.svg | 987 | 1,210 | n/a | 658 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-cyan-locked.svg | 987 | 1,210 | n/a | 658 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-nordic-locked.svg | 987 | 1,210 | n/a | 658 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-palebrown-locked.svg | 987 | 1,210 | n/a | 658 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-yaru-locked.svg | 987 | 1,210 | n/a | 658 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| org.kde.plasma.vault.svg | 987 | 1,133 | n/a | 658 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| org.gnome.IconPreview.svg | 985 | n/a | n/a | 442 | n/a | n/a | n/a | n/a | no_source |
| application-x-kodelife-project.svg | 984 | 1,492 | 470 | 487 | 303 | 260 | 146 | 14.8% |  |
| flareget.svg | 983 | 1,592 | 350 | 362 | 253 | 242 | 27 | 2.7% |  |
| folder-custom-unlocked.svg | 979 | n/a | n/a | 652 | n/a | n/a | n/a | n/a | no_source |
| i-nex.svg | 979 | 1,249 | 523 | 573 | 332 | 322 | 46 | 4.7% |  |
| folder-custom-torrent.svg | 978 | n/a | n/a | 688 | n/a | n/a | n/a | n/a | no_source |
| pulseview.svg | 978 | 1,406 | 534 | 537 | 336 | 309 | 314 | 32.1% |  |
| com.github.arshubham.cipher.svg | 977 | 1,437 | n/a | 527 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-bluegrey-mail.svg | 971 | 1,717 | n/a | 674 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-breeze-mail.svg | 971 | 1,717 | n/a | 674 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-cyan-mail.svg | 971 | 1,717 | n/a | 674 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-green-mail.svg | 971 | 1,717 | n/a | 674 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-grey-mail.svg | 971 | 1,717 | n/a | 674 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-paleorange-mail.svg | 971 | 1,717 | n/a | 674 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-teal-mail.svg | 971 | 1,717 | n/a | 674 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-yellow-mail.svg | 971 | 1,717 | n/a | 674 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-deeporange-unlocked.svg | 970 | 1,197 | 641 | 652 | 422 | 391 | 38 | 3.9% |  |
| folder-grey-unlocked.svg | 970 | 1,197 | 641 | 652 | 419 | 383 | 38 | 3.9% |  |
| folder-magenta-unlocked.svg | 970 | 1,197 | 641 | 652 | 427 | 394 | 48 | 4.9% |  |
| folder-teal-unlocked.svg | 970 | 1,197 | 641 | 652 | 421 | 392 | 38 | 3.9% |  |
| folder-violet-unlocked.svg | 970 | 1,197 | 641 | 652 | 425 | 393 | 35 | 3.6% |  |
| folder-brown-torrent.svg | 969 | 1,511 | n/a | 688 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-carmine-torrent.svg | 969 | 1,511 | n/a | 688 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-darkcyan-torrent.svg | 969 | 1,511 | n/a | 688 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-green-torrent.svg | 969 | 1,511 | n/a | 688 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| auryo.svg | 966 | 1,649 | n/a | 587 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| tamtam-app.svg | 966 | 1,553 | n/a | 528 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-white-mail.svg | 965 | 1,717 | n/a | 674 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-white-unlocked.svg | 964 | 1,197 | 641 | 652 | 418 | 378 | 38 | 3.9% |  |
| tipp10.svg | 961 | 1,243 | 888 | 891 | 354 | 297 | 236 | 24.6% |  |
| QMPlay2.svg | 945 | 1,485 | 342 | 354 | 240 | 235 | 212 | 22.4% |  |
| notification-network-ethernet-disconnected.sv | 942 | 1,226 | 506 | 520 | 292 | 277 | 260 | 27.6% |  |
| com.github.plugarut.pwned-checker.svg | 940 | 1,341 | n/a | 583 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| jango.svg | 939 | 1,337 | n/a | 567 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| folder-indigo-mail-cloud.svg | 938 | 1,371 | 640 | 650 | 456 | 435 | 38 | 4.1% |  |
| folder-magenta-mail-cloud.svg | 938 | 1,371 | 640 | 650 | 456 | 435 | 48 | 5.1% |  |
| folder-palebrown-mail-cloud.svg | 938 | 1,371 | 640 | 650 | 456 | 435 | 38 | 4.1% |  |
| folder-paleorange-mail-cloud.svg | 938 | 1,371 | 640 | 650 | 456 | 434 | 38 | 4.1% |  |
| folder-teal-mail-cloud.svg | 938 | 1,371 | 640 | 650 | 452 | 430 | 38 | 4.1% |  |
| workflowy.svg | 934 | 1,199 | 600 | 605 | 309 | 298 | 199 | 21.3% |  |
| flash.svg | 933 | 1,048 | 391 | 419 | 277 | 259 | 27 | 2.9% |  |
| face-uncertain.svg | 932 | 441 | 141 | 364 | 113 | 113 | 26 | 2.8% |  |
| museeq.svg | 930 | 1,641 | 491 | 493 | 295 | 296 | 287 | 30.9% |  |
| folder-breeze-code.svg | 927 | 1,141 | 585 | 602 | 393 | 373 | 38 | 4.1% |  |
| folder-red-code.svg | 927 | 1,141 | 585 | 602 | 393 | 372 | 38 | 4.1% |  |
| folder-yellow-code.svg | 927 | 1,141 | 585 | 602 | 392 | 372 | 48 | 5.2% |  |
| peek.svg | 922 | 1,395 | n/a | 581 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| folder-bluegrey-photo.svg | 918 | 1,204 | 644 | 624 | 417 | 394 | 38 | 4.1% |  |
| folder-carmine-photo.svg | 918 | 1,204 | 644 | 624 | 407 | 384 | 39 | 4.2% |  |
| folder-grey-photo.svg | 918 | 1,204 | 644 | 624 | 412 | 384 | 38 | 4.1% |  |
| folder-palebrown-photo.svg | 918 | 1,204 | 644 | 624 | 418 | 391 | 38 | 4.1% |  |
| folder-paleorange-photo.svg | 918 | 1,204 | 644 | 624 | 420 | 397 | 38 | 4.1% |  |
| folder-red-photo.svg | 918 | 1,204 | 644 | 624 | 416 | 390 | 39 | 4.2% |  |
| folder-teal-photo.svg | 918 | 1,204 | 644 | 624 | 416 | 388 | 39 | 4.2% |  |
| folder-violet-photo.svg | 918 | 1,204 | 644 | 624 | 417 | 387 | 35 | 3.8% |  |
| folder-custom-copy-cloud.svg | 915 | n/a | n/a | 605 | n/a | n/a | n/a | n/a | no_source |
| folder-white-photo.svg | 912 | 1,204 | 644 | 624 | 410 | 377 | 38 | 4.2% |  |
| cantata.svg | 911 | 1,709 | 443 | 429 | 320 | 306 | 42 | 4.6% |  |
| playlist.svg | 911 | 1,360 | 404 | 412 | 251 | 255 | 102 | 11.2% |  |
| 8bitmmo.svg | 908 | 881 | 584 | 631 | 319 | 268 | 250 | 27.5% |  |
| folder-breeze-copy-cloud.svg | 906 | n/a | n/a | 605 | n/a | n/a | n/a | n/a | no_source |
| folder-brown-copy-cloud.svg | 906 | n/a | n/a | 605 | n/a | n/a | n/a | n/a | no_source |
| folder-carmine-copy-cloud.svg | 906 | n/a | n/a | 605 | n/a | n/a | n/a | n/a | no_source |
| folder-paleorange-copy-cloud.svg | 906 | n/a | n/a | 605 | n/a | n/a | n/a | n/a | no_source |
| half-life-deathmatch.svg | 906 | 930 | n/a | 440 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| kbreakout.svg | 902 | 1,925 | 514 | 523 | 320 | 284 | 255 | 28.3% |  |
| folder-custom-private.svg | 901 | n/a | n/a | 605 | n/a | n/a | n/a | n/a | no_source |
| org.kde.kontrast.svg | 901 | 1,230 | 368 | 388 | 239 | 239 | 179 | 19.9% |  |
| folder-custom-music.svg | 897 | n/a | n/a | 606 | n/a | n/a | n/a | n/a | no_source |
| libreoffice-calc.svg | 895 | 1,867 | 966 | 536 | 449 | 403 | 202 | 22.6% |  |
| folder-custom-dropbox.svg | 894 | n/a | n/a | 630 | n/a | n/a | n/a | n/a | no_source |
| folder-carmine-private.svg | 892 | 1,213 | n/a | 605 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-darkcyan-private.svg | 892 | 1,213 | n/a | 605 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-grey-private.svg | 892 | 1,213 | n/a | 605 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-red-private.svg | 892 | 1,213 | n/a | 605 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-violet-private.svg | 892 | 1,213 | n/a | 605 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-cyan-recent.svg | 891 | 1,158 | n/a | 641 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-green-recent.svg | 891 | 1,158 | n/a | 641 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-grey-recent.svg | 891 | 1,158 | n/a | 641 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-orange-recent.svg | 891 | 1,158 | n/a | 641 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-palebrown-recent.svg | 891 | 1,158 | n/a | 641 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-pink-recent.svg | 891 | 1,158 | n/a | 641 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-yaru-recent.svg | 891 | 1,158 | n/a | 641 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-yellow-recent.svg | 891 | 1,158 | n/a | 641 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| your-freedom.svg | 891 | 1,394 | 315 | 350 | 241 | 227 | 207 | 23.2% |  |
| folder-black-music.svg | 888 | 1,153 | 632 | 606 | 403 | 357 | 38 | 4.3% |  |
| folder-breeze-music-open.svg | 888 | 1,153 | 632 | 606 | 400 | 364 | 94 | 10.6% |  |
| folder-breeze-music.svg | 888 | 1,153 | 632 | 606 | 406 | 363 | 38 | 4.3% |  |
| folder-carmine-music.svg | 888 | 1,153 | 632 | 606 | 398 | 360 | 38 | 4.3% |  |
| folder-pink-music-open.svg | 888 | 1,153 | 632 | 606 | 399 | 370 | 94 | 10.6% |  |
| folder-pink-music.svg | 888 | 1,153 | 632 | 606 | 405 | 370 | 38 | 4.3% |  |
| folder-red-music-open.svg | 888 | 1,153 | 632 | 606 | 399 | 373 | 94 | 10.6% |  |
| folder-red-music.svg | 888 | 1,153 | 632 | 606 | 405 | 362 | 38 | 4.3% |  |
| folder-teal-music-open.svg | 888 | 1,153 | 632 | 606 | 399 | 367 | 94 | 10.6% |  |
| kontena-lens.svg | 888 | 1,249 | 468 | 498 | 302 | 285 | 172 | 19.4% |  |
| mintsources-additional.svg | 888 | 1,086 | 397 | 431 | 211 | 214 | 105 | 11.8% |  |
| folder-white-recent.svg | 885 | 1,158 | n/a | 641 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-yaru-dropbox.svg | 885 | 1,160 | 626 | 630 | 399 | 385 | 38 | 4.3% |  |
| com.github.davidmhewitt.clipped.svg | 882 | 1,218 | 472 | 532 | 284 | 254 | 242 | 27.4% |  |
| folder-white-music.svg | 882 | 1,153 | 632 | 606 | 400 | 355 | 38 | 4.3% |  |
| webby.svg | 882 | 1,192 | 297 | 395 | 222 | 219 | 32 | 3.6% |  |
| folder-black-google-drive.svg | 880 | 1,034 | 567 | 571 | 371 | 339 | 38 | 4.3% |  |
| folder-breeze-google-drive.svg | 880 | 1,034 | 567 | 571 | 372 | 344 | 38 | 4.3% |  |
| folder-nordic-google-drive.svg | 880 | 1,034 | 567 | 571 | 376 | 345 | 38 | 4.3% |  |
| folder-white-dropbox.svg | 879 | 1,160 | 626 | 630 | 394 | 369 | 38 | 4.3% |  |
| com.github.alainm23.byte.svg | 877 | 956 | 457 | 443 | 263 | 236 | 187 | 21.3% |  |
| text-x-copying.svg | 876 | 1,259 | n/a | 493 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-bluegrey-print.svg | 875 | 1,163 | 617 | 621 | 411 | 380 | 38 | 4.3% |  |
| folder-grey-print.svg | 875 | 1,163 | 617 | 621 | 408 | 375 | 38 | 4.3% |  |
| folder-red-print.svg | 875 | 1,163 | 617 | 621 | 411 | 376 | 38 | 4.3% |  |
| folder-violet-print.svg | 875 | 1,163 | 617 | 621 | 412 | 377 | 34 | 3.9% |  |
| folder-yellow-print.svg | 875 | 1,163 | 617 | 621 | 411 | 381 | 48 | 5.5% |  |
| folder-green-video.svg | 874 | 1,142 | 589 | 601 | 392 | 362 | 38 | 4.3% |  |
| folder-orange-video.svg | 874 | 1,142 | 589 | 601 | 391 | 361 | 38 | 4.3% |  |
| folder-paleorange-video.svg | 874 | 1,142 | 589 | 601 | 393 | 366 | 38 | 4.3% |  |
| folder-white-google-drive.svg | 874 | 1,034 | 567 | 571 | 367 | 335 | 38 | 4.3% |  |
| application-x-atari-lynx-rom.svg | 871 | 1,052 | 475 | 506 | 300 | 263 | 143 | 16.4% |  |
| cutemaze.svg | 868 | 1,636 | 530 | 546 | 334 | 311 | 267 | 30.8% |  |
| otter-browser.svg | 867 | 979 | 344 | 374 | 192 | 177 | 108 | 12.5% |  |
| financial-schedule.svg | 866 | 1,374 | 616 | 619 | 352 | 312 | 62 | 7.2% |  |
| folder-blue-videos-open.svg | 865 | 1,103 | 589 | 593 | 394 | 368 | 53 | 6.1% |  |
| folder-bluegrey-videos-open.svg | 865 | 1,103 | 589 | 593 | 393 | 370 | 53 | 6.1% |  |
| folder-brown-videos-open.svg | 865 | 1,103 | 589 | 593 | 393 | 368 | 63 | 7.3% |  |
| folder-carmine-videos-open.svg | 865 | 1,103 | 589 | 593 | 386 | 363 | 53 | 6.1% |  |
| folder-nordic-videos-open.svg | 865 | 1,103 | 589 | 593 | 395 | 371 | 53 | 6.1% |  |
| folder-violet-videos-open.svg | 865 | 1,103 | 589 | 593 | 393 | 366 | 50 | 5.8% |  |
| com.bixense.PasswordCalculator.svg | 860 | 1,141 | 384 | 400 | 235 | 244 | 198 | 23.0% |  |
| folder-black-remote-open.svg | 858 | 1,121 | 592 | 593 | 397 | 360 | 43 | 5.0% |  |
| folder-brown-remote-open.svg | 858 | 1,121 | 592 | 593 | 400 | 377 | 53 | 6.2% |  |
| folder-grey-remote-open.svg | 858 | 1,121 | 592 | 593 | 397 | 367 | 43 | 5.0% |  |
| folder-grey-remote.svg | 858 | 1,121 | 592 | 593 | 399 | 366 | 38 | 4.4% |  |
| folder-nordic-remote.svg | 858 | 1,121 | 592 | 593 | 405 | 373 | 38 | 4.4% |  |
| folder-paleorange-remote-open.svg | 858 | 1,121 | 592 | 593 | 403 | 376 | 43 | 5.0% |  |
| folder-violet-remote-open.svg | 858 | 1,121 | 592 | 593 | 400 | 367 | 40 | 4.7% |  |
| folder-yaru-remote-open.svg | 858 | 1,121 | 592 | 593 | 399 | 365 | 43 | 5.0% |  |
| folder-yaru-remote.svg | 858 | 1,121 | 592 | 593 | 402 | 366 | 38 | 4.4% |  |
| text-x-kotlin.svg | 856 | 1,067 | 311 | 398 | 203 | 194 | 148 | 17.3% |  |
| bootstrap-studio.svg | 855 | 1,443 | 654 | 675 | 341 | 292 | 321 | 37.5% |  |
| folder-white-remote-open.svg | 852 | 1,121 | 592 | 593 | 395 | 361 | 43 | 5.0% |  |
| folder-blue-pictures.svg | 850 | 1,166 | 605 | 609 | 401 | 369 | 38 | 4.5% |  |
| folder-breeze-pictures.svg | 850 | 1,166 | 605 | 609 | 401 | 370 | 38 | 4.5% |  |
| folder-brown-pictures-open.svg | 850 | 1,124 | 605 | 609 | 401 | 371 | 53 | 6.2% |  |
| folder-deeporange-pictures-open.svg | 850 | 1,124 | 605 | 609 | 402 | 370 | 43 | 5.1% |  |
| folder-deeporange-pictures.svg | 850 | 1,166 | 605 | 609 | 401 | 376 | 38 | 4.5% |  |
| folder-paleorange-pictures.svg | 850 | 1,166 | 605 | 609 | 401 | 374 | 38 | 4.5% |  |
| folder-yaru-pictures.svg | 850 | 1,166 | 605 | 609 | 401 | 367 | 38 | 4.5% |  |
| folder-yellow-pictures-open.svg | 850 | 1,124 | 605 | 609 | 401 | 371 | 53 | 6.2% |  |
| piwigo.svg | 847 | 1,033 | 436 | 436 | 240 | 209 | 169 | 20.0% |  |
| VCVRack.svg | 844 | 1,063 | 294 | 295 | 168 | 158 | 92 | 10.9% |  |
| com.github.artemanufrij.hashit.svg | 843 | 1,135 | 459 | 457 | 314 | 290 | 180 | 21.4% |  |
| mouse-touchpad-gestures.svg | 841 | 1,106 | 624 | 503 | 306 | 256 | 281 | 33.4% |  |
| folder-bluegrey-wine.svg | 840 | 1,152 | 585 | 592 | 386 | 357 | 38 | 4.5% |  |
| folder-paleorange-wine.svg | 840 | 1,152 | 585 | 592 | 388 | 357 | 38 | 4.5% |  |
| folder-red-wine.svg | 840 | 1,152 | 585 | 592 | 384 | 354 | 38 | 4.5% |  |
| folder-yellow-wine.svg | 840 | 1,152 | 585 | 592 | 386 | 357 | 47 | 5.6% |  |
| zeal.svg | 839 | 1,355 | 303 | 309 | 207 | 201 | 179 | 21.3% |  |
| folder-black-activities.svg | 838 | 1,070 | 577 | 581 | 353 | 315 | 62 | 7.4% |  |
| folder-black-favorites.svg | 838 | 1,023 | 555 | 563 | 368 | 345 | 37 | 4.4% |  |
| folder-blue-favorites.svg | 838 | 1,023 | 555 | 563 | 372 | 351 | 37 | 4.4% |  |
| folder-brown-favorites.svg | 838 | 1,023 | 555 | 563 | 373 | 349 | 47 | 5.6% |  |
| folder-green-favorites.svg | 838 | 1,023 | 555 | 563 | 372 | 354 | 37 | 4.4% |  |
| folder-grey-favorites.svg | 838 | 1,023 | 555 | 563 | 365 | 346 | 37 | 4.4% |  |
| folder-orange-favorites.svg | 838 | 1,023 | 555 | 563 | 370 | 355 | 37 | 4.4% |  |
| folder-palebrown-activities.svg | 838 | 1,070 | 577 | 581 | 357 | 322 | 62 | 7.4% |  |
| folder-paleorange-activities.svg | 838 | 1,070 | 577 | 581 | 358 | 328 | 62 | 7.4% |  |
| folder-pink-favorites.svg | 838 | 1,023 | 555 | 563 | 370 | 357 | 37 | 4.4% |  |
| folder-red-activities.svg | 838 | 1,070 | 577 | 581 | 356 | 322 | 62 | 7.4% |  |
| folder-red-favorites.svg | 838 | 1,023 | 555 | 563 | 370 | 355 | 37 | 4.4% |  |
| folder-violet-favorites.svg | 838 | 1,023 | 555 | 563 | 371 | 353 | 34 | 4.1% |  |
| folder-yaru-favorites.svg | 838 | 1,023 | 555 | 563 | 370 | 351 | 37 | 4.4% |  |
| exaile.svg | 837 | 1,337 | n/a | 368 | n/a | n/a | n/a | n/a | tvg-text:syntax |
| org.kde.plasma.systemmonitor.cpucore.svg | 836 | 1,203 | 521 | 545 | 293 | 261 | 268 | 32.1% |  |
| folder-white-wine.svg | 834 | 1,152 | 585 | 592 | 378 | 342 | 38 | 4.6% |  |
| folder-bluegrey-documents.svg | 830 | 1,076 | 567 | 574 | 378 | 349 | 38 | 4.6% |  |
| folder-brown-documents.svg | 830 | 1,076 | 567 | 574 | 378 | 349 | 48 | 5.8% |  |
| folder-deeporange-documents.svg | 830 | 1,076 | 567 | 574 | 378 | 350 | 38 | 4.6% |  |
| folder-grey-documents.svg | 830 | 1,076 | 567 | 574 | 374 | 340 | 38 | 4.6% |  |
| folder-orange-documents.svg | 830 | 1,076 | 567 | 574 | 376 | 352 | 38 | 4.6% |  |
| folder-yaru-documents.svg | 830 | 1,076 | 567 | 574 | 376 | 344 | 38 | 4.6% |  |
| distributor-logo-devuan.svg | 829 | 1,355 | 349 | 335 | 207 | 198 | 186 | 22.4% |  |
| folder-black-documents-open.svg | 827 | 1,057 | 567 | 571 | 374 | 339 | 43 | 5.2% |  |
| folder-breeze-documents-open.svg | 827 | 1,057 | 567 | 571 | 376 | 351 | 43 | 5.2% |  |
| folder-custom-mega.svg | 827 | n/a | n/a | 589 | n/a | n/a | n/a | n/a | no_source |
| folder-darkcyan-documents-open.svg | 827 | 1,057 | 567 | 571 | 375 | 346 | 43 | 5.2% |  |
| folder-nordic-documents-open.svg | 827 | 1,057 | 567 | 571 | 378 | 354 | 43 | 5.2% |  |
| folder-palebrown-documents-open.svg | 827 | 1,057 | 567 | 571 | 377 | 350 | 43 | 5.2% |  |
| folder-violet-documents-open.svg | 827 | 1,057 | 567 | 571 | 377 | 344 | 40 | 4.8% |  |
| folder-nordic-vbox.svg | 826 | 1,039 | 546 | 550 | 363 | 337 | 38 | 4.6% |  |
| folder-palebrown-vbox.svg | 826 | 1,039 | 546 | 550 | 361 | 334 | 38 | 4.6% |  |
| folder-paleorange-vbox.svg | 826 | 1,039 | 546 | 550 | 362 | 337 | 38 | 4.6% |  |
| folder-pink-vbox.svg | 826 | 1,039 | 546 | 550 | 360 | 338 | 38 | 4.6% |  |
| folder-red-vbox.svg | 826 | 1,039 | 546 | 550 | 361 | 336 | 38 | 4.6% |  |
| folder-violet-vbox.svg | 826 | 1,039 | 546 | 550 | 361 | 331 | 34 | 4.1% |  |
| semaphor.svg | 825 | 1,036 | 344 | 356 | 187 | 181 | 28 | 3.4% |  |
| org.emilien.Password.svg | 824 | 1,135 | n/a | 533 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| xfce4-systray.svg | 823 | 1,406 | 406 | 405 | 234 | 216 | 173 | 21.0% |  |
| com.github.treagod.spectator.svg | 821 | 856 | n/a | 485 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-bluegrey-important.svg | 821 | 1,214 | n/a | 587 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-cyan-important.svg | 821 | 1,214 | n/a | 587 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-grey-important.svg | 821 | 1,214 | n/a | 587 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-paleorange-important.svg | 821 | 1,214 | n/a | 587 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-white-documents-open.svg | 821 | 1,057 | 567 | 571 | 370 | 337 | 43 | 5.2% |  |
| system-suspend.svg | 821 | 965 | n/a | 443 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-orange-mega.svg | 818 | 1,122 | n/a | 589 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| folder-paleorange-mega.svg | 818 | 1,122 | n/a | 589 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| folder-violet-mega.svg | 818 | 1,122 | n/a | 589 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| folder-custom-wifi.svg | 815 | n/a | n/a | 554 | n/a | n/a | n/a | n/a | no_source |
| folder-white-important.svg | 815 | 1,214 | n/a | 587 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| folder-white-mega.svg | 812 | 1,122 | n/a | 589 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| AdobeLightroomClassic.svg | 810 | 979 | 380 | 386 | 267 | 255 | 130 | 16.0% |  |
| application-x-vmware-vmfoundry.svg | 810 | 1,372 | 582 | 603 | 336 | 285 | 47 | 5.8% |  |
| ar.xjuan.Cambalache.svg | 808 | 1,339 | 495 | 493 | 302 | 290 | 251 | 31.1% |  |
| folder-blue-wifi.svg | 806 | 1,012 | 549 | 554 | 366 | 336 | 38 | 4.7% |  |
| folder-orange-wifi.svg | 806 | 1,012 | 549 | 554 | 362 | 340 | 38 | 4.7% |  |
| folder-palebrown-wifi.svg | 806 | 1,012 | 549 | 554 | 365 | 336 | 38 | 4.7% |  |
| folder-paleorange-wifi.svg | 806 | 1,012 | 549 | 554 | 366 | 340 | 38 | 4.7% |  |
| folder-pink-wifi.svg | 806 | 1,012 | 549 | 554 | 364 | 339 | 38 | 4.7% |  |
| com.github.allen-b1.news.svg | 805 | 867 | 433 | 411 | 301 | 284 | 170 | 21.1% |  |
| battery-caution-charging.svg | 804 | 596 | 98 | 452 | 91 | 85 | 76 | 9.5% |  |
| folder-white-wifi.svg | 800 | 1,012 | 549 | 554 | 359 | 326 | 38 | 4.8% |  |
| folder-black-snap.svg | 799 | 991 | 568 | 572 | 368 | 335 | 74 | 9.3% |  |
| folder-pink-snap.svg | 799 | 991 | 568 | 572 | 372 | 348 | 74 | 9.3% |  |
| laverna.svg | 799 | 984 | 349 | 351 | 213 | 203 | 90 | 11.3% |  |
| AdobeDimension.svg | 798 | 1,121 | 535 | 540 | 332 | 299 | 186 | 23.3% |  |
| pspp.svg | 797 | 1,052 | 317 | 323 | 209 | 205 | 178 | 22.3% |  |
| com.szibele.e-juice-calc.svg | 794 | 1,183 | 419 | 425 | 283 | 271 | 245 | 30.9% |  |
| folder-black-cd.svg | 792 | 1,016 | 553 | 557 | 349 | 314 | 56 | 7.1% |  |
| folder-carmine-cd.svg | 792 | 1,016 | 553 | 557 | 341 | 317 | 57 | 7.2% |  |
| folder-cyan-cd.svg | 792 | 1,016 | 553 | 557 | 347 | 325 | 56 | 7.1% |  |
| mini-calendar-widget.svg | 789 | 1,044 | 400 | 401 | 233 | 205 | 124 | 15.7% |  |
| beholder.svg | 788 | 958 | n/a | 520 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| gnome-subtitles.svg | 788 | 1,593 | 404 | 407 | 288 | 256 | 261 | 33.1% |  |
| folder-white-cd.svg | 786 | 1,016 | 553 | 557 | 346 | 313 | 56 | 7.1% |  |
| terratech.svg | 785 | 806 | 466 | 470 | 262 | 249 | 39 | 5.0% |  |
| video-x-generic.svg | 785 | 1,167 | 415 | 416 | 274 | 255 | 168 | 21.4% |  |
| user-custom-home-open.svg | 782 | n/a | n/a | 550 | n/a | n/a | n/a | n/a | no_source |
| kwordquiz.svg | 781 | 1,502 | n/a | 393 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| battery-missing.svg | 780 | 861 | n/a | 422 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| text-x-po.svg | 779 | 1,271 | 409 | 420 | 288 | 254 | 128 | 16.4% |  |
| folder-black-download.svg | 778 | 997 | 551 | 555 | 359 | 325 | 38 | 4.9% |  |
| folder-bluegrey-download.svg | 778 | 997 | 551 | 555 | 361 | 334 | 38 | 4.9% |  |
| folder-breeze-download-open.svg | 778 | 997 | 551 | 555 | 359 | 329 | 43 | 5.5% |  |
| folder-cyan-download.svg | 778 | 997 | 551 | 555 | 359 | 330 | 38 | 4.9% |  |
| folder-darkcyan-download.svg | 778 | 997 | 551 | 555 | 360 | 329 | 38 | 4.9% |  |
| folder-grey-download-open.svg | 778 | 997 | 551 | 555 | 357 | 325 | 43 | 5.5% |  |
| folder-indigo-download.svg | 778 | 997 | 551 | 555 | 361 | 334 | 38 | 4.9% |  |
| folder-magenta-download-open.svg | 778 | 997 | 551 | 555 | 360 | 329 | 53 | 6.8% |  |
| folder-magenta-download.svg | 778 | 997 | 551 | 555 | 363 | 333 | 47 | 6.0% |  |
| folder-orange-download.svg | 778 | 997 | 551 | 555 | 359 | 334 | 38 | 4.9% |  |
| folder-red-download.svg | 778 | 997 | 551 | 555 | 361 | 331 | 38 | 4.9% |  |
| folder-teal-download-open.svg | 778 | 997 | 551 | 555 | 357 | 328 | 43 | 5.5% |  |
| dissenter-browser.svg | 776 | 1,274 | n/a | 374 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| gnumeric.svg | 774 | 989 | 456 | 458 | 247 | 209 | 123 | 15.9% |  |
| preferences-desktop-personal.svg | 773 | 1,128 | n/a | 410 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| user-blue-home-open.svg | 773 | 993 | 546 | 550 | 358 | 325 | 40 | 5.2% |  |
| user-bluegrey-home.svg | 773 | 991 | 546 | 550 | 356 | 324 | 38 | 4.9% |  |
| user-breeze-home.svg | 773 | 991 | 546 | 550 | 357 | 329 | 38 | 4.9% |  |
| user-carmine-home.svg | 773 | 991 | 546 | 550 | 349 | 316 | 38 | 4.9% |  |
| user-darkcyan-home-open.svg | 773 | 993 | 546 | 550 | 356 | 321 | 40 | 5.2% |  |
| user-green-home.svg | 773 | 991 | 546 | 550 | 357 | 323 | 38 | 4.9% |  |
| user-indigo-home-open.svg | 773 | 993 | 546 | 550 | 358 | 324 | 40 | 5.2% |  |
| user-orange-home.svg | 773 | 991 | 546 | 550 | 355 | 324 | 38 | 4.9% |  |
| user-palebrown-home-open.svg | 773 | 993 | 546 | 550 | 358 | 324 | 40 | 5.2% |  |
| user-paleorange-home.svg | 773 | 991 | 546 | 550 | 357 | 329 | 38 | 4.9% |  |
| user-red-home-open.svg | 773 | 993 | 546 | 550 | 356 | 322 | 40 | 5.2% |  |
| user-yaru-home.svg | 773 | 991 | 546 | 550 | 357 | 321 | 38 | 4.9% |  |
| folder-white-download.svg | 772 | 997 | 551 | 555 | 355 | 320 | 38 | 4.9% |  |
| avatar-default.svg | 770 | 592 | n/a | 406 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| gksu.svg | 770 | 1,141 | n/a | 406 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| system-users.svg | 770 | 1,141 | n/a | 406 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| user-white-home-open.svg | 767 | 993 | 546 | 550 | 351 | 312 | 40 | 5.2% |  |
| AdobeFresco.svg | 766 | 1,033 | 420 | 420 | 294 | 278 | 146 | 19.1% |  |
| kawaii-player.svg | 765 | 1,098 | n/a | 384 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| tweet-tray.svg | 765 | 1,247 | 316 | 303 | 180 | 193 | 179 | 23.4% |  |
| retext.svg | 763 | 1,477 | 428 | 433 | 265 | 242 | 39 | 5.1% |  |
| application-x-virtualbox-hdd.svg | 762 | 1,184 | 410 | 421 | 269 | 260 | 41 | 5.4% |  |
| application-x-virtualbox-ova.svg | 762 | 1,184 | 410 | 421 | 269 | 244 | 41 | 5.4% |  |
| application-x-virtualbox-vhd.svg | 762 | 1,184 | 410 | 421 | 269 | 267 | 41 | 5.4% |  |
| mx-welcome.svg | 762 | 752 | n/a | 504 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| jubler.svg | 754 | 1,203 | n/a | 446 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| kbruch.svg | 751 | 1,380 | 416 | 434 | 264 | 253 | 33 | 4.4% |  |
| emily-is-away.svg | 750 | 1,179 | 427 | 392 | 289 | 289 | 203 | 27.1% |  |
| nasc.svg | 749 | 887 | 396 | 425 | 268 | 228 | 119 | 15.9% |  |
| bookworm.svg | 748 | 704 | 329 | 368 | 201 | 171 | 32 | 4.3% |  |
| WickrMe.svg | 736 | 962 | 300 | 300 | 181 | 177 | 65 | 8.8% |  |
| muon.svg | 736 | 1,060 | 377 | 382 | 265 | 267 | 174 | 23.6% |  |
| org.gnome.Firmware.svg | 725 | 2,760 | n/a | 526 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| io.gitlab.leesonwai.Sums.svg | 724 | 1,320 | 461 | 475 | 263 | 240 | 50 | 6.9% |  |
| mate-panel-separator.svg | 724 | 972 | 504 | 515 | 305 | 271 | 174 | 24.0% |  |
| pomodoneapp.svg | 718 | 755 | 431 | 465 | 224 | 218 | 164 | 22.8% |  |
| postr.svg | 718 | 956 | 429 | 434 | 258 | 247 | 30 | 4.2% |  |
| abbaye.svg | 717 | 743 | 514 | 529 | 271 | 242 | 198 | 27.6% |  |
| notification-audio-volume-medium.svg | 713 | 832 | n/a | 314 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| kube.svg | 703 | 966 | 425 | 408 | 261 | 245 | 137 | 19.5% |  |
| devdocs.svg | 702 | 1,329 | 369 | 370 | 219 | 212 | 123 | 17.5% |  |
| marknoto.svg | 701 | 828 | 378 | 370 | 229 | 215 | 28 | 4.0% |  |
| folder-black-open.svg | 700 | 894 | 501 | 505 | 320 | 288 | 43 | 6.1% |  |
| folder-blue.svg | 700 | 894 | 501 | 505 | 326 | 290 | 38 | 5.4% |  |
| folder-bluegrey.svg | 700 | 894 | 501 | 505 | 326 | 291 | 38 | 5.4% |  |
| folder-cyan-open.svg | 700 | 894 | 501 | 505 | 322 | 292 | 43 | 6.1% |  |
| folder-yellow.svg | 700 | 894 | 501 | 505 | 325 | 294 | 45 | 6.4% |  |
| application-x-codeblocks-workspace.svg | 699 | 853 | 340 | 344 | 209 | 194 | 27 | 3.9% |  |
| freeoffice-textmaker.svg | 698 | 795 | 351 | 359 | 215 | 204 | 170 | 24.4% |  |
| ibus-bopomofo.svg | 698 | 1,397 | 476 | 306 | 394 | 359 | 240 | 34.4% |  |
| text-x-install.svg | 697 | 1,003 | 323 | 334 | 232 | 223 | 75 | 10.8% |  |
| uget.svg | 697 | 968 | 513 | 519 | 302 | 268 | 251 | 36.0% |  |
| tomb-raider.svg | 695 | 844 | 478 | 479 | 272 | 250 | 27 | 3.9% |  |
| application-pgp-keys.svg | 690 | 1,222 | 361 | 373 | 237 | 224 | 38 | 5.5% |  |
| com.github.lainsce.yishu.svg | 685 | 827 | 338 | 339 | 236 | 224 | 37 | 5.4% |  |
| kig.svg | 680 | 831 | n/a | 403 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| granule.svg | 679 | 1,101 | 428 | 459 | 310 | 286 | 228 | 33.6% |  |
| half-life-alyx.svg | 678 | 807 | 356 | 359 | 237 | 229 | 112 | 16.5% |  |
| Encryptr.svg | 672 | 1,353 | 356 | 386 | 242 | 239 | 106 | 15.8% |  |
| cdbaby.svg | 672 | 1,519 | 388 | 421 | 271 | 243 | 118 | 17.6% |  |
| com.github.bharatkalluri.easypass.svg | 672 | n/a | n/a | 344 | n/a | n/a | n/a | n/a | no_source |
| password-manager.svg | 672 | 1,352 | 360 | 344 | 199 | 192 | 27 | 4.0% |  |
| application-x-srt.svg | 663 | 1,020 | 366 | 368 | 240 | 206 | 27 | 4.1% |  |
| io.ark.Desktop.svg | 654 | 1,038 | 400 | 402 | 254 | 246 | 131 | 20.0% |  |
| redirection.svg | 654 | 1,101 | 413 | 416 | 249 | 235 | 114 | 17.4% |  |
| ksnakeduel.svg | 651 | 1,613 | 362 | 299 | 239 | 230 | 118 | 18.1% |  |
| text-x-log.svg | 650 | 924 | 297 | 292 | 204 | 181 | 54 | 8.3% |  |
| folder-custom-drag-accept.svg | 637 | n/a | n/a | 429 | n/a | n/a | n/a | n/a | no_source |
| shadowsocks-qt5.svg | 637 | 831 | 274 | 275 | 191 | 169 | 115 | 18.1% |  |
| foursquare.svg | 633 | 763 | 315 | 315 | 199 | 191 | 80 | 12.6% |  |
| kbibtex.svg | 632 | 900 | 387 | 396 | 253 | 236 | 191 | 30.2% |  |
| text-x-generic.svg | 630 | 908 | 329 | 340 | 222 | 197 | 67 | 10.6% |  |
| libreoffice-main.svg | 629 | 1,080 | 414 | 331 | 271 | 249 | 172 | 27.3% |  |
| folder-bluegrey-drag-accept.svg | 628 | 810 | 425 | 429 | 268 | 251 | 40 | 6.4% |  |
| folder-breeze-drag-accept.svg | 628 | 810 | 425 | 429 | 267 | 249 | 40 | 6.4% |  |
| folder-darkcyan-drag-accept.svg | 628 | 810 | 425 | 429 | 267 | 247 | 40 | 6.4% |  |
| folder-deeporange-drag-accept.svg | 628 | 810 | 425 | 429 | 266 | 248 | 40 | 6.4% |  |
| folder-paleorange-drag-accept.svg | 628 | 810 | 425 | 429 | 268 | 250 | 40 | 6.4% |  |
| folder-red-drag-accept.svg | 628 | 810 | 425 | 429 | 267 | 243 | 40 | 6.4% |  |
| folder-violet-drag-accept.svg | 628 | 810 | 425 | 429 | 267 | 245 | 38 | 6.1% |  |
| folder-yellow-drag-accept.svg | 628 | 810 | 425 | 429 | 267 | 245 | 44 | 7.0% |  |
| preferences-desktop-thunderbolt.svg | 609 | 811 | 257 | 265 | 180 | 171 | 102 | 16.7% |  |
| compiz.svg | 607 | 1,127 | 304 | 315 | 219 | 216 | 27 | 4.4% |  |
| touchpad-indicator.svg | 602 | 982 | 476 | 480 | 280 | 282 | 257 | 42.7% |  |
| ease.svg | 599 | 939 | 309 | 311 | 222 | 206 | 136 | 22.7% |  |
| distributor-logo-manjaro.svg | 595 | 911 | 332 | 352 | 191 | 166 | 118 | 19.8% |  |
| downline.svg | 594 | 889 | 332 | 330 | 218 | 206 | 97 | 16.3% |  |
| no-mans-sky.svg | 594 | 691 | 246 | 280 | 173 | 165 | 67 | 11.3% |  |
| lightsoff.svg | 591 | 757 | 289 | 293 | 177 | 174 | 55 | 9.3% |  |
| nvim.svg | 588 | 748 | 287 | 275 | 219 | 208 | 200 | 34.0% |  |
| brackets-electron.svg | 584 | 757 | 445 | 454 | 258 | 215 | 151 | 25.9% |  |
| notification-network-ethernet-connected.svg | 583 | 549 | 358 | 362 | 209 | 196 | 187 | 32.1% |  |
| notification-gsm-connected.svg | 580 | 714 | 317 | 320 | 210 | 197 | 187 | 32.2% |  |
| narcissu-1st-2nd.svg | 569 | 778 | 400 | 407 | 231 | 212 | 31 | 5.4% |  |
| gitter.svg | 568 | 1,330 | 368 | 367 | 219 | 206 | 80 | 14.1% |  |
| xfe.svg | 567 | 1,185 | 384 | 387 | 250 | 249 | 170 | 30.0% |  |
| lightzone.svg | 566 | 796 | 284 | 287 | 193 | 197 | 170 | 30.0% |  |
| emblem-syncthing-offline.svg | 552 | 825 | n/a | 279 | n/a | n/a | n/a | n/a | svg2tvgt:path_parse |
| org.homelinuxserver.vance.biblereader-symboli | 545 | 788 | 365 | 374 | 218 | 201 | 129 | 23.7% |  |
| microsoft.svg | 544 | 665 | 300 | 300 | 190 | 183 | 129 | 23.7% |  |
| org.gnome.Pinpoint.svg | 541 | 795 | 307 | 319 | 205 | 205 | 28 | 5.2% |  |
| com.endlessnetwork.fablemaker.svg | 539 | 600 | 338 | 338 | 206 | 194 | 95 | 17.6% |  |
| mpv.svg | 535 | 724 | 254 | 262 | 170 | 159 | 100 | 18.7% |  |
| notification-audio-volume-low.svg | 531 | 555 | 213 | 221 | 181 | 182 | 162 | 30.5% |  |
| liteupgrade.svg | 525 | 712 | 356 | 359 | 221 | 201 | 97 | 18.5% |  |
| user-custom-desktop.svg | 522 | n/a | n/a | 297 | n/a | n/a | n/a | n/a | no_source |
| user-carmine-desktop.svg | 517 | 691 | 305 | 297 | 204 | 197 | 37 | 7.2% |  |
| user-cyan-desktop.svg | 517 | 691 | 305 | 297 | 206 | 203 | 37 | 7.2% |  |
| user-teal-desktop.svg | 517 | 691 | 305 | 297 | 207 | 202 | 27 | 5.2% |  |
| user-white-desktop.svg | 517 | 691 | 305 | 297 | 207 | 202 | 34 | 6.6% |  |
| openoffice4-writer.svg | 513 | 717 | 273 | 281 | 171 | 154 | 70 | 13.6% |  |
| xnoise.svg | 494 | 612 | n/a | 307 | n/a | n/a | n/a | n/a | svg2tvgt:moveto_bug |
| emblem-favorite.svg | 485 | 656 | 180 | 181 | 171 | 169 | 134 | 27.6% |  |
| battery-empty.svg | 470 | 692 | 110 | 298 | 103 | 97 | 85 | 18.1% |  |
| battery-low.svg | 470 | 720 | 118 | 298 | 90 | 87 | 77 | 16.4% |  |
| emblem-dropbox-app.svg | 459 | 592 | 226 | 219 | 201 | 201 | 199 | 43.4% |  |
| nightsky.svg | 458 | 534 | 223 | 231 | 137 | 133 | 72 | 15.7% |  |
| emblem-unlocked.svg | 428 | 639 | 178 | 179 | 162 | 163 | 134 | 31.3% |  |
| mame.svg | 378 | 448 | 159 | 159 | 117 | 107 | 98 | 25.9% |  |
| emblem-photos.svg | 321 | 562 | 157 | 158 | 137 | 128 | 99 | 30.8% |  |
| vcs-conflicting.svg | 245 | 331 | 78 | 106 | 86 | 83 | 66 | 26.9% |  |
| emblem-default.svg | 240 | 301 | 81 | 86 | 94 | 86 | 26 | 10.8% |  |
| emblem-important.svg | 219 | 262 | 84 | 84 | 78 | 76 | 48 | 21.9% |  |
| emblem-new.svg | 196 | 288 | 78 | 78 | 78 | 77 | 52 | 26.5% |  |
| Nextcloud_ok.svg | 189 | 249 | 76 | 76 | 89 | 81 | 26 | 13.8% |  |
| emblem-downloads.svg | 187 | 294 | 91 | 88 | 84 | 84 | 56 | 29.9% |  |
| emblem-remove.svg | 156 | 225 | 60 | 60 | 69 | 65 | 41 | 26.3% |  |

### freesvg (5 files)

| File | ref_svg | cur_svg | TVG | ref_tvg | zstd | brotli | zstd+dict | dict/SVG | notes |
|------|---------|---------|-----|---------|------|--------|-----------|----------|-------|
| woman-in-blue-bikini.svg | 158,938 | n/a | n/a | 47,225 | n/a | n/a | n/a | n/a | no_source |
| reddresslady-1919-remix.svg | 29,820 | n/a | n/a | 8,509 | n/a | n/a | n/a | n/a | no_source |
| spatula.svg | 10,911 | n/a | n/a | 3,682 | n/a | n/a | n/a | n/a | no_source |
| chip.svg | 5,641 | n/a | n/a | 1,555 | n/a | n/a | n/a | n/a | no_source |
| 1638862592editor FreeSVG updated Vector Broke | 1,868 | n/a | n/a | 607 | n/a | n/a | n/a | n/a | no_source |

## Top 20 Best Compression Ratios (zstd+dict as % of SVG)

| File | Group | SVG | TVG | zstd+dict | % of SVG |
|------|-------|-----|-----|-----------|----------|
| singular.svg | papirus | 1,491 | 496 | 27 | 1.8% |
| mx-select-sound.svg | papirus | 1,742 | 900 | 35 | 2.0% |
| opengl.svg | papirus | 1,234 | 480 | 27 | 2.2% |
| folder-bluegrey-kde.svg | papirus | 1,722 | 902 | 38 | 2.2% |
| folder-green-kde.svg | papirus | 1,722 | 902 | 38 | 2.2% |
| folder-red-kde.svg | papirus | 1,722 | 902 | 38 | 2.2% |
| penrose-staircase.svg | w3c | 3,231 | 649 | 74 | 2.3% |
| folder-cyan-github.svg | papirus | 1,637 | 833 | 38 | 2.3% |
| folder-deeporange-github.svg | papirus | 1,637 | 833 | 38 | 2.3% |
| folder-green-github.svg | papirus | 1,637 | 833 | 38 | 2.3% |
| folder-grey-github.svg | papirus | 1,637 | 833 | 38 | 2.3% |
| folder-indigo-github.svg | papirus | 1,637 | 833 | 38 | 2.3% |
| folder-nordic-github.svg | papirus | 1,637 | 833 | 38 | 2.3% |
| application-x-asp.svg | papirus | 1,239 | 666 | 32 | 2.6% |
| flareget.svg | papirus | 983 | 350 | 27 | 2.7% |
| folder-magenta-kde.svg | papirus | 1,722 | 902 | 48 | 2.8% |
| folder-yellow-kde.svg | papirus | 1,722 | 902 | 48 | 2.8% |
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
