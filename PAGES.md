# pages/ content process

This document describes the editable content structure we are developing under `pages/`.
Keep it updated whenever the folder schema, naming rules, supported media types, or template behavior changes.

## Goal

`pages/` is the source-content area for a non-technical workflow. The owner should be able to create and rearrange project content by working with plain folders, Markdown text files, and media files.

The public website output still lives in the normal static site paths, such as:

```text
index.html
works/index.html
works/<work-slug>/index.html
```

`scripts/generate_pages.py` reads valid work folders under `pages/works/commercials/` and `pages/works/films/` and writes the static HTML output for the root landing page, the `/works/` redirect, and the per-work pages. The owner should not need to understand code; Claude/Codex runs it after content changes and commits the generated HTML. On this Mac, the root `generate_website` script is also available as a double-clickable publish path.

## Current Structure

The working content skeleton is:

```text
pages/
  works/
    commercials/
      champion/
        trailer/
          trailer_link.md
        note/
          text.md
          media/
            1_note.webp
        highlight/
          media/
            1_highlight.webp
            2_highlight.webp
            3_highlight.webp
        bts/
          text.md
          media/
            1_bts.webp
            2_bts.webp
    films/
      strange-fruit/
        trailer/
          trailer_link.md
        note/
          text.md
          media/
            1_hero.webp
        highlight/
          media/
            1_still-01.webp
            2_still-02.webp
            3_shot39_7m09s.mp4
        bts/
          text.md
          media/
            1_bts.webp
            2_bts.webp
```

The current `trailer`, `note`, `highlight`, and `bts` sections are the first sections being formalized.

## General Rules

- `pages/works/commercials/<work-slug>/` maps to `works/<work-slug>/index.html` and one grid item in `index.html#works`.
- `pages/works/films/<work-slug>/` maps to `works/<work-slug>/index.html` and one grid item in `index.html#works`.
- Both categories are traversed for valid started work folders.
- Work slugs must be unique across `commercials` and `films`, because both categories share the public `/works/<slug>/` URL space.
- Each child folder under a work represents a page section.
- Section folder names should match the site section IDs and tracker labels where practical: `trailer`, `note`, `highlight`, `bts`.
- Empty folders are useful locally, but Git does not preserve empty directories. A folder needs real content or a placeholder file before it can be committed.
- The generated/static HTML remains the deployable website output. `pages/` is the editable content source, not a runtime JavaScript data store.
- Generated files such as `works/<work-slug>/index.html` should not be edited directly once a work is managed by `pages/`; update `pages/works/commercials/` or `pages/works/films/` and rerun the generator instead.
- The generator currently treats a work as a candidate only when the work folder contains real source files. Empty draft folders are ignored.
- A started work folder must be valid before it can generate: missing required files, unsupported media types, duplicate media numbers, or invalid Vimeo links are errors.

## Generator

The generator is dependency-free Python:

```text
scripts/generate_pages.py
```

Local write command:

```sh
python3 scripts/generate_pages.py
```

Local check command:

```sh
python3 scripts/generate_pages.py --check
```

Unit tests:

```sh
python3 -m unittest discover -s tests
```

CI runs the same tests and `--check` via `.github/workflows/check-generated-pages.yml`.

Owner/Claude publish command:

```sh
./generate_website
```

That wrapper runs generation, tests, the generated-page check, the media policy check, commits/pushes approved site changes, switches GitHub Pages to workflow publishing if needed, dispatches `.github/workflows/publish-website.yml`, and waits for deployment.

Generator rules:

- It uses only the Python standard library; do not add package-manager dependencies.
- `--check` fails if committed HTML differs from generated HTML.
- The root landing-page wrapper lives at `templates/index.html`.
- The shared work-page wrapper lives at `templates/work-page.html`.
- The `/works/` redirect wrapper lives at `templates/works-redirect.html`.
- The root landing-page output is `index.html`.
- The `/works/` redirect output is `works/index.html`.
- The generated work-page output is `works/<work-slug>/index.html`.
- The current work title is derived from the folder slug, such as `strange-fruit` → `Strange Fruit`. A richer work-title metadata rule is still open.
- Image inputs in `media/` are converted to WebP with ffmpeg.
- WebP conversion is skipped on rerun when the matching `.webp` file already exists and is newer than the source image.
- Publishable work-page media is limited to `.webp` and `.mp4`.
- The combined size of publishable work-page media under `pages/works/**/media/` must stay under 800 MB.

## Text Files

Each section may contain a `text.md` file.

Rules for `text.md`:

- Use Markdown for user-authored text.
- Markdown formatting is allowed, including italics such as `*Cindy Tran*`, bold such as `**Title**`, and links if a template supports them.
- Normal line breaks in `text.md` should be preserved by the eventual template output when the section needs line-based text, such as credits.
- Blank lines may be used to separate groups of text.
- Avoid raw HTML in `text.md` unless we explicitly decide a section needs it.

For the current BTS proof of concept, `text.md` contains the credits block shown in the right column.

For the current Note proof of concept, `text.md` contains only the variable title/body copy. Static section chrome such as the `Director's note` label should stay in the HTML/template because it is consistent across pages of this type.

## Media Folders

Sections that use media should contain a `media/` folder.

Rules for `media/`:

- Media files are ordered by a leading `NUMBER_` filename prefix.
- Numbering is 1-indexed: `1_`, `2_`, `3_`, etc.
- Reordering media should be possible by renaming the numeric prefixes.
- The text after `NUMBER_` is only a human-readable label and does not control layout.
- Sort order should be numeric, not alphabetical, so `10_...` comes after `9_...`.
- Numbers should be unique within a `media/` folder.
- Gaps are allowed during drafting, but contiguous numbering is easier for the owner to audit.
- Prefer simple filenames after the prefix: lowercase letters, numbers, hyphens, and underscores.

Example:

```text
media/
  1_opening-still.webp
  2_rehearsal-clip.mp4
  3_portrait.webp
```

Media is intentionally named `media`, not `images` or `videos`, because future section layouts may mix image and video content in the same ordered sequence. The position in the sequence should be interchangeable regardless of media type.

## Current Trailer Template Rules

The current `trailer` section behavior is:

- Trailer video source comes from `trailer/trailer_link.md`.
- The file should contain the normal user-facing Vimeo URL, not the embed URL.
- The current Strange Fruit trailer URL is `https://vimeo.com/316363898`.
- The generation step should strip leading/trailing whitespace from the file contents.
- Blank lines before or after the URL should be ignored so copy/paste is forgiving.
- After trimming, the first non-empty line should be treated as the trailer URL.
- The template/generator should translate normal Vimeo URLs into Vimeo player embed URLs.
- The rendered page should keep using the Vimeo facade pattern: poster plus play button first, iframe only after click.
- The generator stores resolved Vimeo poster URLs in `vimeo-thumbnails.json`, keyed by normalized public Vimeo URL.
- Normal generation may fetch missing poster URLs from Vimeo's oEmbed endpoint and update the cache.
- Check mode reads only from the cache so local and GitHub CI runs do not drift when Vimeo is slow or temporarily unreachable.
- If no cached or fetched thumbnail is available, the trailer template falls back to a black placeholder.

Private or unlisted Vimeo links may include a hash path after the numeric ID, such as `https://vimeo.com/123456789/abcdef1234`; the generator should preserve that hash when creating the embed URL.

## Current BTS Template Rules

The current `bts` section behavior is:

- Left column: slideshow built from `bts/media/`.
- Right column: body text from `bts/text.md`.
- Layout ratio: approximately 70% media / 30% text, not counting page padding.
- BTS text is right-aligned and starts near the upper-right of the text column.
- Slideshow media is ordered by `NUMBER_`.
- Slideshow controls are previous/next arrows that appear only when hovering over the slideshow.

The generated HTML currently references media directly from `pages/works/<category>/<slug>/bts/media/`. This is acceptable for local proof-of-concept work, but final deployable assets still need an optimized media workflow.

## Current Note Template Rules

The current `note` section behavior is:

- Mixed text/media page similar in structure to BTS.
- Text comes from `note/text.md`.
- Media comes from `note/media/`.
- The current template accepts exactly one media item.
- The media item still uses the shared `NUMBER_` prefix rule, currently `1_hero.webp`.
- The title should use normal Markdown heading syntax, currently one `#` heading.
- Body text should be normal Markdown paragraph text after the heading.
- Static section chrome, including the `Director's note` label, should come from the HTML/template and should not be repeated in `text.md`.

The future generation step should validate that this section has exactly one media item. For now, the folder follows the same ordered media scheme as the other sections.

## Current Highlight Template Rules

The current `highlight` section behavior is:

- Full-width irregular grid built from `highlight/media/`.
- Media can be images or video clips.
- Grid media is ordered by `NUMBER_`.
- The layout adapts to the number of media items. Five-item grids currently use `7-5, 4-5-3`; seven-item grids currently use `7-5, 4-4-4, 6-6`.
- Media items can be images or muted looping video clips.
- Each highlight tile includes a centered expand control, and clicking anywhere on the tile opens it.
- The expanded media opens in a dimmed overlay and animates from its grid tile to the width of the highlight grid.
- Clicking anywhere on the expanded overlay collapses it back; centered inward chevrons are shown as the visual cue.
- Highlight tiles use the shared `media-hover-zoom` effect from `css/shared-effects.css`, the same effect used by the root works grid.

The generated HTML currently references allowed media directly from `pages/works/<category>/<slug>/highlight/media/`. The publish workflow copies only `.webp` and `.mp4` files from those media folders into the Pages artifact.

## Current Root Template Rules

The current generated root `index.html` behavior is:

- It has one persistent left-side section tracker for `about`, `works`, and `contact`.
- The header is brand-only; `works`, `about`, and `contact` are no longer duplicated in the top-right header.
- The first `about` viewport uses the same left/right inset model as generated work-page trailers, with the line illustration placed where trailer media would normally sit. It starts at the top of the page underneath the transparent fixed header, without reserving a black header band.
- The first `about` viewport uses `images/illustration-tight.svg`, a tight-viewBox derivative of the reusable brand illustration. The SVG fits the visual area's height from the top-left corner, so left/top/bottom stay anchored and narrow screens may crop only the right side.
- The hero wordmark `rae hu 樂瑞` is overlaid separately with breakpoint-specific inset and font-size variables so it stays composed with the artwork on both wide and narrow screens.
- The opening visual has the `#home` anchor. The section tracker's `about` link targets the actual about copy at `#about`, not the hero visual.
- The quote `"nobody knows why and how creativity works...` and `And...action!` cue are part of the `about` section.
- It is generated from all valid work folders under `pages/works/films/` and `pages/works/commercials/`.
- The `works` section has two stacked category grids: `films`, then `commercials`.
- `films` and `commercials` appear as slightly indented sub-links underneath `works` in the left tracker while the `works` section is active.
- Each category section uses the shared irregular `.portfolio-grid` layout engine.
- Each grid entry links to the generated public work page at `works/<slug>/index.html`.
- Each grid entry uses the work's Vimeo trailer poster image when Vimeo returns one.
- If Vimeo does not return a trailer poster image, the generator falls back to the work's note media image.
- Grid entry titles include a right chevron after the work title because clicking opens the generated work subpage.
- Grid tiles use the shared `media-hover-zoom` effect from `css/shared-effects.css`, the same effect used by individual work-page highlight tiles.
- Interactive chevrons use the shared `interactive-chevron` motion classes from `css/shared-effects.css`; only the chevron mark moves, not the surrounding text or button.
- The grids are automatically sized by item count, so adding/removing valid work folders changes the rows/columns without hand-editing `index.html`.
- The old `works/index.html` path is now a generated redirect to `index.html#works`.

## Deployment And Media Quality

This repo is a static GitHub Pages site. Before content is deployed:

- Generated HTML should use repo-relative paths only.
- Images in work-page `media/` folders are generated/served as WebP.
- Short work-page clips may be served as optimized MP4.
- Raw full-size PNG/JPG files are acceptable while drafting locally, but they are ignored by Git and must not be pushed.
- Raw source videos such as `.mov` must not be committed as final site assets. Use Vimeo embeds for trailers/longform video or approved optimized MP4 clips for highlight grids.
- The root `generate_website` script and the publish workflow both enforce the `.webp`/`.mp4` media rule and the 800 MB publishable-media budget.
- GitHub Pages should be configured with `build_type=workflow`, not legacy branch publishing, so the custom publish workflow replaces `pages-build-deployment`.

## Open Decisions

- Whether work-level metadata should use a file such as `title.md` to preserve titles that cannot be derived from the slug.
- Whether generated pages should reference `pages/` media directly or copy optimized assets into `images/<work-slug>/`.
- Whether empty section folders should be preserved in Git with placeholder files.
