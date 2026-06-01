# pages/ content process

This document describes the editable content structure we are developing under `pages/`.
Keep it updated whenever the folder schema, naming rules, supported media types, or template behavior changes.

## Goal

`pages/` is the source-content area for a non-technical workflow. The owner should be able to create and rearrange project content by working with plain folders, Markdown text files, and media files.

The public website output still lives in the normal static site paths, such as:

```text
works/<work-slug>/index.html
```

`scripts/generate_pages.py` reads valid work folders under `pages/works/` and writes the static HTML output. The owner should not need to run the script, install tools, or understand code; Claude/Codex runs it after content changes and commits the generated HTML.

## Current Structure

The working content skeleton is:

```text
pages/
  works/
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
          4_still-04.webp
          5_still-05.webp
      bts/
        text.md
        media/
          1_bts.webp
          2_bts.webp
          3_bts.webp
          4_bts.webp
          5_bts.webp
```

The current `trailer`, `note`, `highlight`, and `bts` sections are the first sections being formalized.

## General Rules

- `pages/works/<work-slug>/` maps to `works/<work-slug>/index.html`.
- Each child folder under a work represents a page section.
- Section folder names should match the site section IDs and tracker labels where practical: `trailer`, `note`, `highlight`, `bts`.
- Empty folders are useful locally, but Git does not preserve empty directories. A folder needs real content or a placeholder file before it can be committed.
- The generated/static HTML remains the deployable website output. `pages/` is the editable content source, not a runtime JavaScript data store.
- Generated files such as `works/<work-slug>/index.html` should not be edited directly once a work is managed by `pages/`; update `pages/` and rerun the generator instead.
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

Generator rules:

- It uses only the Python standard library; do not add package-manager dependencies.
- `--check` fails if committed HTML differs from generated HTML.
- The shared HTML wrapper lives at `templates/work-page.html`.
- The current generated page output is `works/<work-slug>/index.html`.
- The current work title is derived from the folder slug, such as `strange-fruit` → `Strange Fruit`. A richer work-title metadata rule is still open.
- Image inputs in `media/` are converted to WebP with ffmpeg.
- WebP conversion is skipped on rerun when the matching `.webp` file already exists and is newer than the source image.

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
- The rendered page should keep using the Vimeo facade pattern: poster or placeholder plus play button first, iframe only after click.
- The current source schema has no trailer poster field, so generated trailer facades use a black placeholder behind the play button. A poster-source rule is still open.

Private or unlisted Vimeo links may include a hash path after the numeric ID, such as `https://vimeo.com/123456789/abcdef1234`; the generator should preserve that hash when creating the embed URL.

## Current BTS Template Rules

The current `bts` section behavior is:

- Left column: slideshow built from `bts/media/`.
- Right column: body text from `bts/text.md`.
- Layout ratio: approximately 70% media / 30% text, not counting page padding.
- BTS text is right-aligned and starts near the upper-right of the text column.
- Slideshow media is ordered by `NUMBER_`.
- Slideshow controls are previous/next arrows that appear only when hovering over the slideshow.

The generated HTML currently references media directly from `pages/works/strange-fruit/bts/media/`. This is acceptable for local proof-of-concept work, but final deployable assets still need an optimized media workflow.

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
- The current proof-of-concept grid uses five positions.
- Position 3 is currently a muted looping video clip.
- The rendered HTML currently uses a manual `data-layout` value of `7-5, 4-5-3` for the five-item grid.

The generated HTML currently references media directly from `pages/works/strange-fruit/highlight/media/`. This preserves the source-content order while the optimized media workflow is still being decided.

## Deployment And Media Quality

This repo is a static GitHub Pages site. Before content is deployed:

- Generated HTML should use repo-relative paths only.
- Images should be optimized for the web, preferably WebP or AVIF where practical.
- Raw full-size PNG/JPG files are acceptable while drafting locally, but should not be treated as final deployable assets.
- Raw videos should not be committed as final site assets. Use Vimeo embeds or approved optimized clips according to the repo media rules.
- The current `pages/works/strange-fruit/` media files are raw proof-of-concept assets. Before deployment, replace them with optimized committed assets or add an explicit generation step that writes optimized assets to the final asset location.

## Open Decisions

- Whether work-level metadata should use a file such as `title.md` to preserve titles that cannot be derived from the slug.
- How trailer poster images should be supplied.
- Whether generated pages should reference `pages/` media directly or copy optimized assets into `images/<work-slug>/`.
- Whether empty section folders should be preserved in Git with placeholder files.
- The final optimized media output location for generated website assets.
