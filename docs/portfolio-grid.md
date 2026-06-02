# Portfolio grid system

A reusable irregular-grid layout engine for displaying landscape stills and video clips across portfolio pages. Lives at `js/portfolio-grid.js` — a single vanilla JS file with no dependencies.

## How it works

The grid takes a container of images (or videos) and arranges them in rows with **varying column widths**. Row heights are computed automatically so that every cell stays landscape — wider than tall. Images fill their cells via CSS `object-fit: cover`, cropping as needed without resizing the source file.

### Two modes

1. **Auto-layout (recommended):** Drop images into a `.portfolio-grid` container — the engine counts the children and generates a valid layout automatically. Use `data-seed` to get different arrangements for the same item count.

2. **Manual override:** Set `data-layout` to specify exact column spans per row. The item count must match the pattern exactly — if it doesn't, the engine falls back to auto-layout and logs a warning.

### The algorithm

Based on the [Knuth-Plass line-breaking algorithm](https://blog.vjeux.com/2014/image/google-plus-layout-find-best-breaks.html) adapted for image grids (the same approach used by Google Photos and Flickr).

**Layout generation (auto mode):**

1. Count N children in the container.
2. Partition N into rows of 2 or 3 items. The partitioner ensures no row of 1 item is created (e.g., 4 → 2+2, not 3+1).
3. Assign column span patterns to each row from preset pools, avoiding adjacent-row repeats. Spans are irregular (e.g., `[7,5]`, `[3,5,4]`) and always sum to 12.
4. The `data-seed` attribute controls which patterns are selected — same seed + same N = identical layout every time.

**Row height computation (both modes):**

For each row with spans `[s1, s2, …]` summing to `S`:

1. Narrowest cell width = `(min(spans) / S) × container_width`
2. Row height = `narrowest_cell_width / min_aspect_ratio`
3. Every cell in the row gets this height; wider cells have even higher aspect ratios
4. The **landscape constraint** is guaranteed: `cell_width / cell_height ≥ min_aspect_ratio > 1`

### Key design rule

**All source content is roughly 16:9 landscape.** The grid cells don't need to match 16:9 exactly — CSS `object-fit: cover` handles the cropping at render time. No resized or specially-cropped image variants are needed. The same source image works in any cell width.

Cropping anchor defaults to `center center`. For shots where the subject is off-center, override per-item with inline `style="object-position: left center"` (or `right`, `top`, etc.).

## Usage

### Auto-layout (no pattern needed)

```html
<div class="portfolio-grid">
  <img src="images/project/still-01.webp" alt="...">
  <img src="images/project/still-02.webp" alt="...">
  <img src="images/project/still-03.webp" alt="...">
  <!-- any number of children — layout is generated from the count -->
</div>
<script src="/js/portfolio-grid.js"></script>
```

### Auto-layout with seed (for reproducible variants)

```html
<!-- Same 17 images, three different layouts -->
<div class="portfolio-grid" data-seed="0">  <!-- variant A -->
<div class="portfolio-grid" data-seed="42"> <!-- variant B -->
<div class="portfolio-grid" data-seed="99"> <!-- variant C -->
```

The seed is an integer passed to a deterministic PRNG (mulberry32). **Same seed + same item count = same layout every time**, across browsers and page loads. To explore different arrangements, just try different seed values.

### Manual override

```html
<div class="portfolio-grid" data-layout="7-5, 3-5-4, 5-7, 4-8">
  <img src="..."> <!-- 10 items must match 2+3+2+2=9... wait -->
  <!-- item count MUST match the pattern total -->
</div>
```

If the item count doesn't match the pattern, the engine logs a console warning and falls back to auto-layout.

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

### The `data-layout` attribute (manual mode)

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

### All attributes

| Attribute | Default | Purpose |
|---|---|---|
| `data-seed` | `0` | Integer seed for the auto-layout generator. Different seeds produce different arrangements for the same item count. Deterministic — same seed always gives the same layout. |
| `data-layout` | *(auto)* | Manual layout override. Comma-separated rows of dash-separated column spans. If set, item count must match. |
| `data-min-ar` | `1.35` | Minimum aspect ratio for the narrowest cell. Lower = taller rows, more cropping. Higher = shorter rows, less cropping. Must be > 1. |
| `data-cols` | `12` | Base column count for the grid. |

### Video support

Works identically with `<video>` elements:

```html
<video src="clips/clip-01.mp4" muted playsinline poster="images/poster-01.webp"></video>
```

`object-fit: cover` applies to video the same way. For Vimeo embeds, use the facade pattern (poster image + play button, swap iframe on click) per the site's performance rules.

## Span presets (used by the auto-layout generator)

The generator picks from these pools. All sum to 12.

**2-item rows:**
- `[7, 5]`, `[5, 7]`, `[8, 4]`, `[4, 8]`

**3-item rows:**
- `[3, 5, 4]`, `[4, 5, 3]`, `[5, 4, 3]`, `[3, 4, 5]`, `[4, 3, 5]`, `[5, 3, 4]`

The generator never repeats the same span pattern in adjacent rows.

## Tested layout seeds

These seed + item count combinations have been visually verified with real stills during local development.

| Items | Seed | Rows | Character |
|---|---|---|---|
| 17 | `0` | 8 | Mixed 2- and 3-item rows, opens with a wide pair |
| 17 | `42` | 7 | Starts with a 3-item row, alternating rhythm |
| 17 | `99` | 7 | Different row partition, different span selection |

To reproduce: put 17 `<img>` children in a `.portfolio-grid` container with `data-seed="0"` (or `42`, `99`). The layout will be identical regardless of which images are used — only the count and seed matter.

## File locations

- **Engine:** `js/portfolio-grid.js`
- **Root works grids:** `index.html#works`
- **Portfolio pages:** `works/<slug>/index.html`
- **Image assets:** `images/<slug>/` (WebP, committed to repo)
- **Source stills:** `website_stills/` (PNGs, not committed — convert to WebP before use)

## Creating a new portfolio page

1. Add source content under `pages/works/films/<slug>/` or `pages/works/commercials/<slug>/`.
2. Put ordered media inside the section `media/` folders using the `NUMBER_` filename prefix.
3. Run `python3 scripts/generate_pages.py` so the root works grids and the detail page are regenerated.
4. Preview locally, then commit and push through the normal generated-site workflow.
