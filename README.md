# raehu.com

The portfolio site for filmmaker Rae Hu (樂瑞) — director, Shanghai.

Live at **https://raehu.com**.

---

## Where to find things

### For the owner

- **[docs/updating-the-site.md](docs/updating-the-site.md)** — how to update the site, how long changes take to appear, what to do if you don't see a change.
- **[NOTES.md](NOTES.md)** — the current state of the site: what's done, what's still placeholder, what's next.
- **`generate_website`** — double-clickable macOS script for generating, testing, pushing, and publishing the site.

### For Claude (the assistant)

- **[CLAUDE.md](CLAUDE.md)** — rules and hard constraints (author identity, architecture, performance, conventions, doc maintenance).
- **[docs/updating-the-site.md](docs/updating-the-site.md)** — the operational workflow when handling owner-requested changes.
- **[docs/portfolio-reference.md](docs/portfolio-reference.md)** — design vocabulary, voice, and project catalog extracted from the 2026 portfolio PDF; canonical reference for design requests.
- **[docs/portfolio-grid.md](docs/portfolio-grid.md)** — how the irregular portfolio grid layout system works; algorithm, usage, tested presets.
- **[docs/clip-extraction.md](docs/clip-extraction.md)** — FFmpeg workflow for generating preview thumbnails and highlight clips from source video.
- **[docs/clip-scripts.md](docs/clip-scripts.md)** — `generate-candidates` and `extract-clips` scripts that automate the clip extraction workflow; usage, examples, and installation.
- **[PAGES.md](PAGES.md)** — content-folder schema and generation rules for project pages under `pages/works/`.
- **[NOTES.md](NOTES.md)** — running state and open work.

---

## File layout

```
.
├── index.html                  # landing page (CSS + JS inline)
├── CNAME                       # custom domain config
├── generate_website            # macOS-clickable generate/test/publish script
├── README.md                   # this file
├── CLAUDE.md                   # rules for Claude
├── NOTES.md                    # running state
├── PAGES.md                    # generated project-page content rules
├── docs/                       # operational guides + reference
│   ├── updating-the-site.md
│   ├── portfolio-reference.md
│   ├── portfolio-grid.md
│   ├── clip-extraction.md
│   └── clip-scripts.md
├── js/                         # shared scripts (no build, no npm)
│   └── portfolio-grid.js       # irregular grid layout engine
├── images/                     # committed image assets
│   └── illustration.svg        # signature line-art portrait (brand asset)
├── pages/                      # source content for generated project pages
│   └── works/
├── scripts/
│   └── generate_pages.py       # dependency-free page generator
├── templates/
│   └── work-page.html          # shared generated work-page template
├── tests/                      # generator tests
├── works/                      # generated project pages, served at /works/<slug>/
├── .github/
│   └── workflows/
│       ├── check-author.yml
│       ├── check-generated-pages.yml
│       └── publish-website.yml
├── .githooks/
│   └── pre-commit              # local: blocks wrong-author commits
└── .gitignore
```

Generated per-project pages live at `works/<slug>/index.html` and are served at `https://raehu.com/works/<slug>/`. Source content lives under `pages/works/<slug>/`. See [PAGES.md](PAGES.md) for the folder rules.

---

## Site at a glance

- **Hosting:** GitHub Pages, published by the custom `Publish website` GitHub Actions workflow
- **Domain:** raehu.com (Namecheap; DNS = 4 A records on `@` + 1 CNAME on `www`)
- **Videos:** [Vimeo](https://vimeo.com/raehu) for trailers/longform; optimized MP4 clips are allowed only under generated work-page media
- **HTTPS:** enforced via GitHub Pages
- **Build:** none — pure static HTML/CSS/JS, served as-is

---

## Architecture in one line

Pure static HTML + CSS + JS. **No build step, no package manager, no frameworks.** See [CLAUDE.md](CLAUDE.md) for the full set of constraints and the reasoning.
