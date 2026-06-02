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
  note/
    text.md
    media/
      1_note-image.webp
  highlight/
    media/
      1_opening.webp
      2_close-up.webp
      3_scene.mp4
  bts/
    text.md
    media/
      1_rehearsal.webp
      2_location.webp
      3_crew.webp
```

For a commercial, use the same shape under `editable-content/works/commercials/`:

```text
editable-content/works/commercials/my-commercial/
```

A new work needs all four sections: `trailer`, `note`, `highlight`, and `bts`. Empty draft folders are ignored until they have the required files.

### Trailer

Put one normal Vimeo link in `trailer/trailer_link.md`.

Example:

```text
https://vimeo.com/1119717934
```

It is okay if there are blank spaces or blank lines around the link. The website generator will clean that up.

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
note/media/
  1_note-image.webp
```

### Highlight

Put highlight images or short clips in `highlight/media/`.

Example:

```text
highlight/media/
  1_opening.webp
  2_detail.webp
  3_motion.mp4
  4_wide-shot.webp
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

Put BTS slideshow media in `bts/media/`.

### Media Naming

Media order is controlled by the number at the start of the filename.

```text
1_first-image.webp
2_second-image.webp
3_third-image.mp4
```

To rearrange the order, rename the numbers.

Use:

```text
.webp
.mp4
```

If you drop in `.jpg`, `.jpeg`, or `.png` files locally, the generator can create `.webp` copies. The original raw files stay local and are not pushed to the website.

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

- Committed work media under `editable-content/works/**/media/` must be `.webp` or `.mp4`.
- Raw `.jpg`, `.jpeg`, `.png`, and similar source drops are ignored by Git.
- Media order is numeric by `NUMBER_` prefix.
- Duplicate media numbers in one `media/` folder are invalid.
- `note/media/` must contain exactly one media item.
- Total publishable work media must stay under 800 MB.

Validation and publishing:

```sh
python3 -m unittest discover -s tests
python3 scripts/generate_pages.py --check
```

Use `./generate_website --message "<commit message>" --no-pause` for normal publishing. It generates pages, runs tests, checks generated HTML, enforces media policy, commits, pushes, switches GitHub Pages to workflow publishing if needed, dispatches `.github/workflows/publish-website.yml`, and waits for deployment.

Before pushing user-visible changes, preview locally and get explicit owner confirmation. Docs, hooks, CI, and internal maintenance changes do not need a visual preview.

Useful technical references live under `docs/`.
