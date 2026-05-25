# Portfolio grid system

A reusable irregular-grid layout engine for displaying landscape stills and video clips across portfolio pages. Lives at `js/portfolio-grid.js` — a single vanilla JS file with no dependencies.

## How it works

The grid takes a container of images (or videos) and arranges them in rows with **varying column widths**. Row heights are computed automatically so that every cell stays landscape — wider than tall. Images fill their cells via CSS `object-fit: cover`, cropping as needed without resizing the source file.

### The algorithm

Based on the [Knuth-Plass line-breaking algorithm](https://blog.vjeux.com/2014/image/google-plus-layout-find-best-breaks.html) adapted for image grids (the same approach used by Google Photos and Flickr). For this site's use case — a small number of hand-curated items — we skip the dynamic-programming row-breaking step and specify the layout pattern directly. The engine handles the height math and placement.

**Per row, given column spans `[s1, s2, …]` summing to `S`:**

1. Narrowest cell width = `(min(spans) / S) × container_width`
2. Row height = `narrowest_cell_width / min_aspect_ratio`
3. Every cell in the row gets this height; wider cells have even higher aspect ratios
4. The **landscape constraint** is guaranteed: `cell_width / cell_height ≥ min_aspect_ratio > 1`

### Key design rule

**All source content is roughly 16:9 landscape.** The grid cells don't need to match 16:9 exactly — CSS `object-fit: cover` handles the cropping at render time. No resized or specially-cropped image variants are needed. The same source image works in any cell width.

Cropping anchor defaults to `center center`. For shots where the subject is off-center, override per-item with inline `style="object-position: left center"` (or `right`, `top`, etc.).

## Usage

### HTML

```html
<div class="portfolio-grid" data-layout="7-5, 3-5-4, 5-7, 4-8">
  <img src="images/project/still-01.webp" alt="Description">
  <img src="images/project/still-02.webp" alt="Description">
  <!-- one child per cell; count must match the layout pattern -->
</div>
<script src="/js/portfolio-grid.js"></script>
```

### Required CSS

```css
.portfolio-grid { width: 100%; }
.portfolio-grid > * {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
```

### The `data-layout` attribute

Comma-separated rows. Each row is dash-separated column spans on a 12-column grid.

| Pattern | Meaning |
|---|---|
| `7-5` | 2 items: 58% and 42% wide |
| `3-5-4` | 3 items: 25%, 42%, 33% wide |
| `4-4-4` | 3 items: equal thirds |
| `8-4` | 2 items: 67% and 33% wide |

Spans in a row should sum to 12 (the default grid column count). The engine is flexible — any total works, but 12 gives a good range of proportions.

**Irregularity comes from two things:**
1. Rows have different numbers of items (2 vs. 3)
2. Column break-points don't align between rows

For maximum irregularity, avoid repeating the same break-point in adjacent rows.

### Optional attributes

| Attribute | Default | Purpose |
|---|---|---|
| `data-min-ar` | `1.35` | Minimum aspect ratio for the narrowest cell. Lower = taller rows, more cropping. Higher = shorter rows, less cropping. Must be > 1. |
| `data-cols` | `12` | Base column count for the grid. |

### Video support

Works identically with `<video>` elements:

```html
<video src="clips/clip-01.mp4" muted playsinline poster="images/poster-01.webp"></video>
```

`object-fit: cover` applies to video the same way. For Vimeo embeds, use the facade pattern (poster image + play button, swap iframe on click) per the site's performance rules.

## Tested layout presets

These patterns have been visually verified. Use as starting points and adjust as needed.

| Name | Pattern | Items | Character |
|---|---|---|---|
| A | `7-5, 3-5-4, 5-4-3, 4-8` | 10 | Bookended wide items, dense middle |
| B | `5-7, 4-4-4, 8-4` | 9 | Opens narrow, closes with hero |
| C | `7-5, 3-5-4, 5-7, 4-5-3, 3-4-5, 4-8, 6-6` | 17 | Full 7-row layout, strong rhythm |

## File locations

- **Engine:** `js/portfolio-grid.js`
- **Portfolio pages:** `works/<slug>/index.html`
- **Image assets:** `images/<slug>/` (WebP, committed to repo)
- **Source stills:** `website_stills/` (PNGs, not committed — convert to WebP before use)

## Creating a new portfolio page

1. Create `works/<slug>/index.html`
2. Add images as `<img>` tags inside a `.portfolio-grid` container
3. Choose or design a `data-layout` pattern
4. Link `../../js/portfolio-grid.js` at the bottom of `<body>`
5. Include the base CSS (inline or linked)
6. Preview locally, then commit and push
