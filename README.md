# raehu.com

Portfolio site for filmmaker Rae Hu (樂瑞).

Live site: **https://raehu.com**

## For Rae: How to Add or Update Work Pages

You only need this folder:

```text
editable-content/
```

Create and edit work pages only inside:

The website has two work categories:

```text
editable-content/works/films/
editable-content/works/commercials/
```

Do not create work folders in `generated-website/`, `generator-templates/`, or `site-source-assets/`.

Each work gets its own folder. The folder name becomes the page address, so keep it short, lowercase, and use hyphens instead of spaces.
Do not use the same folder name twice, even if one is a film and one is a commercial.

Example:

```text
editable-content/works/films/strange-fruit/
```

becomes:

```text
https://raehu.com/works/strange-fruit/
```

### Folder Example

Use this shape for each work:

```text
editable-content/works/films/my-film/
  trailer/
    trailer_link.md
    # or 1_trailer.jpg
    # or 1_trailer.mp4
  note/
    text.md
    1_note-image.jpg
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

For a commercial, use the same shape under `editable-content/works/commercials/`:

```text
editable-content/works/commercials/my-commercial/
```

A new work needs all four sections: `trailer`, `note`, `highlight`, and `bts`. Empty draft folders are ignored until they have the required files.

### Trailer

Choose exactly one trailer source.

Option 1: put one normal Vimeo link in `trailer/trailer_link.md`.

```text
https://vimeo.com/1119717934
```

It is okay if there are blank spaces or blank lines around the link. The website generator will clean that up.

Option 2: put one image in `trailer/`.

```text
trailer/
  1_trailer.jpg
```

Option 3: put one MP4 video in `trailer/`.

```text
trailer/
  1_trailer.mp4
```

Do not mix these options. If the generator finds more than one trailer source, it will stop and tell you which extra source to remove.

### Note

Put the page title and note text in `note/text.md`.

Example:

```text
# Strange Fruit

A short director's note or project description goes here.
```

The `#` line becomes the title. The text below it becomes the body.

The note section needs exactly one media file:

```text
note/
  text.md
  1_note-image.jpg
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
https://raehu.com/#works
https://raehu.com/works/<work-folder-name>/
```

Do not edit generated HTML files directly. Edit the folders under `editable-content/works/`, then run `generate_website`.

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
- Generated HTML is committed output. Source content lives in `editable-content/works/films/` and `editable-content/works/commercials/`.
- Work slugs must be unique across `films` and `commercials`, because both publish to `works/<slug>/`.
- Do not edit generated `generated-website/index.html`, `generated-website/works/index.html`, or `generated-website/works/<slug>/index.html` directly. Edit source folders, templates, source assets, or generator code, then regenerate.
- Highlight grids use deterministic slug-based layouts. Keep media ordered by the `NUMBER_` filename prefix, and vary only the generated grid pattern so users can rearrange media by renaming files.

Generated-site mechanism:

- `generator-templates/index.html` generates the root page.
- `generator-templates/work-page.html` generates individual work pages.
- `generator-templates/works-redirect.html` generates the `/works/` redirect.
- `site-source-assets/` contains source CSS, JS, and site artwork copied into generated output.
- `generated-website/index.html` serves the landing page and `#works` section.
- `generated-website/works/index.html` redirects old `/works/` traffic to `/#works`.
- `generated-website/works/<slug>/index.html` serves each generated work page.
- `vimeo-thumbnails.json` is the committed Vimeo poster cache. Check mode must not depend on live Vimeo availability.

Media rules:

- Committed work media under `editable-content/works/` must be `.webp` or `.mp4`.
- Raw `.jpg`, `.jpeg`, `.png`, and similar source drops are ignored by Git.
- Media order is numeric by `NUMBER_` prefix.
- Duplicate media numbers in one section folder are invalid.
- `trailer/` must contain exactly one source: either a non-empty `trailer_link.md`, one numbered image, or one numbered `.mp4`.
- `note/` must contain exactly one media item, alongside `text.md`.
- Total publishable work media must stay under 800 MB.

Validation and publishing:

```sh
python3 -m unittest discover -s tests
python3 scripts/generate_pages.py --check
```

Use `./generate_website --message "<commit message>" --no-pause` for normal publishing. It generates pages, runs tests, checks generated HTML, enforces media policy, commits, pushes, switches GitHub Pages to workflow publishing if needed, dispatches `.github/workflows/publish-website.yml`, and waits for deployment.

Before pushing user-visible changes, preview locally and get explicit owner confirmation. Docs, hooks, CI, and internal maintenance changes do not need a visual preview.

Useful technical references live under `docs/`.
