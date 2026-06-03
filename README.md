# raehu.com

Portfolio site for filmmaker Rae Hu (樂瑞).

Live site: **https://raehu.com**

## For Rae: How to Update Site Content

You only need this folder:

```text
editable-content/
```

### About Page

Edit the about page text here:

```text
editable-content/about/text.md
```

Edit the quote underneath the about text here:

```text
editable-content/about/quote.md
```

Put the about image next to those files. It must start with a number and underscore:

```text
editable-content/about/1_image.jpg
```

The generator will convert the image to WebP for the website.

The about text file uses this shape:

```text
# about

Main paragraph text goes here.

Email: raehufilm@gmail.com
Vimeo: vimeo.com/raehu
Instagram: instagram.com/raehufilm
Location: Shanghai · Mexico City
```

Optional translated about text goes next to it:

```text
editable-content/about/text_chinese.md
editable-content/about/text_spanish.md
```

Use the same shape as `text.md`. If a translated file is missing, that language option will show the English text.

The quote file uses this shape:

```text
> quote line one
> quote line two
```

The divider labels like `Camera, rolling!`, `And... action!`, and `...AND CUT!` are built into the website. Do not put them in these markdown files.

### Work Pages

Create and edit work pages only inside:

The website has two work categories:

```text
editable-content/work/films/
editable-content/work/commercials/
```

Do not create work folders in `generated-website/`, `generator-templates/`, or `site-source-assets/`.

Each work gets its own folder. The folder name becomes the page address, so keep it short, lowercase, and use hyphens instead of spaces.
Do not use the same folder name twice, even if one is a film and one is a commercial.

Example:

```text
editable-content/work/films/strange-fruit/
```

becomes:

```text
https://raehu.com/films/strange-fruit/
```

### Folder Example

Films use this shape:

```text
editable-content/work/films/my-film/
  trailer/
    trailer_link.md
    additional_links.md
    # or 1_trailer.jpg
    # or 1_trailer.mp4
  grid_preview/
    1_preview.jpg
  note/
    1_text.md
    2_note-image.jpg
  highlight/
    1_opening.jpg
    2_close-up.png
    3_scene.mp4
  bts/
    text.md
    1_rehearsal.jpg
    2_location.png
    3_crew.jpg
```

Commercials use `film/` instead of `trailer/`:

```text
editable-content/work/commercials/my-commercial/
  film/
    film_link.md
    additional_links.md
    # or 1_film.jpg
    # or 1_film.mp4
  grid_preview/
    1_preview.jpg
  note/
    1_text.md
    2_note-image.jpg
  highlight/
    1_opening.jpg
    2_close-up.png
    3_scene.mp4
  bts/
    text.md
    1_rehearsal.jpg
    2_location.png
    3_crew.jpg
```

A new film needs `trailer`, `note`, `highlight`, and `bts`.
A new commercial needs `film`, `note`, `highlight`, and `bts`.
Empty draft folders are ignored until they have the required files.

### Trailer Or Film

Choose exactly one source for the first section.

For a film, put one normal Vimeo link in `trailer/trailer_link.md`.
For a commercial, put one normal Vimeo link in `film/film_link.md`.

```text
https://vimeo.com/1119717934
```

It is okay if there are blank spaces or blank lines around the link. The website generator will clean that up.

Or put one image in the first section folder.

```text
trailer/
  1_trailer.jpg

film/
  1_film.jpg
```

Or put one MP4 video in the first section folder.

```text
trailer/
  1_trailer.mp4

film/
  1_film.mp4
```

Do not mix these options. If the generator finds more than one first-section source, it will stop and tell you which extra source to remove.

Optional: add links below the first video/image by creating `additional_links.md` in the same folder.
Put one Markdown link on each line.

```text
[view full film](https://vimeo.com/1119717934)
[second link](https://example.com)
```

### Grid Preview

Optional: create `grid_preview/` when you want the homepage work grid to use a different image or video than the first section.

Put exactly one numbered image or MP4 in the folder.

```text
grid_preview/
  1_preview.jpg
```

If you do not create `grid_preview/`, the website automatically uses the `trailer/` or `film/` media. If the first section is a Vimeo link, it uses the Vimeo preview image.

### Note

Put the page title and note text in one numbered Markdown file.

Example:

```text
# Strange Fruit

A short director's note or project description goes here.
```

The `#` line becomes the title. The text below it becomes the body.

The note section needs exactly one text file and exactly one image or video file.
Use `1_` for the left column and `2_` for the right column.

Text on the left, image on the right:

```text
note/
  1_text.md
  2_note-image.jpg
```

Image on the left, text on the right:

```text
note/
  1_note-image.jpg
  2_text.md
```

### Highlight

Put highlight images or short clips in `highlight/`.

Example:

```text
highlight/
  1_opening.jpg
  2_detail.png
  3_motion.mp4
  4_wide-shot.jpg
```

The website automatically builds the irregular image grid from however many items are in this folder.

### BTS

Put behind-the-scenes text in `bts/text.md`.

Example:

```text
A film by *Cindy Tran* & *Xiao Han*

Written by Cindy Tran
Directed by Xiao Han
Produced by Cindy Tran
```

You can use simple Markdown formatting:

```text
*italic text*
**bold text**
```

Put BTS slideshow media in `bts/` beside `text.md`.

### Media Naming

Media order is controlled by the number at the start of the filename.

```text
1_first-image.jpg
2_second-image.png
3_third-image.mp4
```

To rearrange the order, rename the numbers.

Use normal image files or MP4 video files:

```text
.jpg
.png
.mp4
```

The generator automatically creates web-ready image copies when needed. The original raw image files stay local and are not pushed to the website.

### Running the Website Generator

To publish the site from this Mac:

1. Double-click `generate_website` in the repo folder.
2. Wait for the Terminal window to finish.
3. When it finishes successfully, the site is published to https://raehu.com.

To test locally without publishing:

```sh
./generate_website --dry-run
```

To preview the generated site on this Mac, open:

```text
generated-website/index.html
```

The generator updates:

```text
https://raehu.com/
https://raehu.com/#work
https://raehu.com/films/<work-folder-name>/
https://raehu.com/commercials/<work-folder-name>/
```

Do not edit generated HTML files directly. Edit the folders under `editable-content/work/`, then run `generate_website`.

### What the Other Folders Mean

```text
editable-content/       You edit this.
generated-website/      Generated output. Do not edit by hand.
generator-templates/    Layout templates. Agents edit this when changing page structure.
site-source-assets/     CSS, JavaScript, and site artwork. Agents edit this.
```

## For Agents: Rules to Maintain

This is the single root-level source of truth for repo rules. Do not recreate separate root docs like `CLAUDE.md`, `NOTES.md`, or `PAGES.md` unless the owner asks for them.

Hard requirements:

- Use only the GitHub/Git identity `raehufilm <283902148+raehufilm@users.noreply.github.com>` for this repo.
- Preserve user-created local files and uncommitted work. Check `git status` before editing or committing.
- Keep the site static: no npm, no package manager, no framework, no deploy-time build.
- `scripts/generate_pages.py` must stay Python-standard-library only.
- `ffmpeg` is the local image conversion tool for raw image media.
- Generated HTML is committed output. Source content lives in `editable-content/about/` and `editable-content/work/`.
- Optional translated Markdown files use the normal filename plus `_chinese` or `_spanish` before `.md`, for example `text.md`, `text_chinese.md`, and `text_spanish.md`. Missing translated files must fall back to English content.
- About media is discovered from `editable-content/about/` by the same `NUMBER_` prefix convention as work media. Do not add special-case filenames like `image.jpg`.
- Work slugs must stay unique across `films` and `commercials` so generated links and tooling remain unambiguous.
- Do not edit generated `generated-website/index.html`, `generated-website/films/<slug>/index.html`, or `generated-website/commercials/<slug>/index.html` directly. Edit source folders, templates, source assets, or generator code, then regenerate.
- Highlight grids use deterministic slug-based layouts. Keep media ordered by the `NUMBER_` filename prefix, and vary only the generated grid pattern so users can rearrange media by renaming files.

Generated-site mechanism:

- `generator-templates/index.html` generates the root page.
- `generator-templates/work-page.html` generates individual work pages.
- `site-source-assets/` contains source CSS, JS, and site artwork copied into generated output.
- Shared header styling lives in `site-source-assets/css/site-header.css`, and shared header action markup is produced by `render_site_header_actions()` in `scripts/generate_pages.py`. Do not duplicate that header CSS or action markup in templates.
- `generated-website/index.html` serves the landing page, about section, and `#work` section.
- `generated-website/films/<slug>/index.html` and `generated-website/commercials/<slug>/index.html` serve generated work pages.
- `vimeo-thumbnails.json` is the committed Vimeo poster cache. Check mode must not depend on live Vimeo availability.

Media rules:

- Committed media under `editable-content/about/` and `editable-content/work/` must be `.webp` or `.mp4`.
- Raw `.jpg`, `.jpeg`, `.png`, and similar source drops are ignored by Git.
- Media order is numeric by `NUMBER_` prefix.
- Duplicate media numbers in one section folder are invalid.
- Films use `trailer/` as the first section and it must contain exactly one source: either a non-empty `trailer_link.md`, one numbered image, or one numbered `.mp4`.
- Commercials use `film/` as the first section and it must contain exactly one source: either a non-empty `film_link.md`, one numbered image, or one numbered `.mp4`.
- The first section may also contain optional `additional_links.md`. It does not count as the first-section source and must contain one Markdown link per non-empty line.
- `grid_preview/` is optional. If present, it must contain exactly one numbered image or `.mp4` and it overrides the homepage work-grid preview. If missing, the work grid falls back to the first-section media or Vimeo thumbnail.
- `note/` must contain exactly one numbered Markdown file and exactly one numbered media item. Together they must use positions `1_` and `2_` exactly once so the user can swap left/right layout by renaming files.
- Total publishable work media must stay under 800 MB.

Validation and publishing:

```sh
python3 -m unittest discover -s tests
python3 scripts/generate_pages.py --check
```

Use `./generate_website --message "<commit message>" --no-pause` for normal publishing. It generates pages, runs tests, checks generated HTML, enforces media policy, commits, pushes, switches GitHub Pages to workflow publishing if needed, dispatches `.github/workflows/publish-website.yml`, and waits for deployment.

Before pushing user-visible changes, preview locally and get explicit owner confirmation. Docs, hooks, CI, and internal maintenance changes do not need a visual preview.

Useful technical references live under `docs/`.
