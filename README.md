# raehu.com

The portfolio site for filmmaker Rae Hu (樂瑞) — director, Shanghai.

Live at **https://raehu.com**.

---

## Where to find things

### For the owner

- **[docs/updating-the-site.md](docs/updating-the-site.md)** — how to update the site, how long changes take to appear, what to do if you don't see a change.
- **[NOTES.md](NOTES.md)** — the current state of the site: what's done, what's still placeholder, what's next.

### For Claude (the assistant)

- **[CLAUDE.md](CLAUDE.md)** — rules and hard constraints (author identity, architecture, performance, conventions, doc maintenance).
- **[docs/updating-the-site.md](docs/updating-the-site.md)** — the operational workflow when handling owner-requested changes.
- **[docs/portfolio-reference.md](docs/portfolio-reference.md)** — design vocabulary, voice, and project catalog extracted from the 2026 portfolio PDF; canonical reference for design requests.
- **[NOTES.md](NOTES.md)** — running state and open work.

---

## File layout

```
.
├── index.html                  # landing page (CSS + JS inline)
├── CNAME                       # custom domain config
├── README.md                   # this file
├── CLAUDE.md                   # rules for Claude
├── NOTES.md                    # running state
├── docs/                       # operational guides + reference
│   ├── updating-the-site.md
│   └── portfolio-reference.md
├── images/                     # committed image assets
│   └── illustration.svg        # signature line-art portrait (brand asset)
├── .github/
│   └── workflows/
│       └── check-author.yml    # CI: enforces commit author
├── .githooks/
│   └── pre-commit              # local: blocks wrong-author commits
└── .gitignore
```

When per-project work is added, it will land at `works/<slug>/index.html` with images at `images/<slug>/`. See [CLAUDE.md](CLAUDE.md) for the conventions.

---

## Site at a glance

- **Hosting:** GitHub Pages, served from `main` branch root
- **Domain:** raehu.com (Namecheap; DNS = 4 A records on `@` + 1 CNAME on `www`)
- **Videos:** [Vimeo](https://vimeo.com/raehu), embedded by URL (never committed to the repo)
- **HTTPS:** enforced via GitHub Pages
- **Build:** none — pure static HTML/CSS/JS, served as-is

---

## Architecture in one line

Pure static HTML + CSS + JS. **No build step, no package manager, no frameworks.** See [CLAUDE.md](CLAUDE.md) for the full set of constraints and the reasoning.
