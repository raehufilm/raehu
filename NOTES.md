# raehu — working notes

Running state for the raehu.com portfolio site. **Read `CLAUDE.md` first for the rules**, then `docs/updating-the-site.md` for the operational workflow when making changes. This file is the running state: what's done, what's not, design context, open work.

## At a glance

- **Live site:** https://raehu.com (HTTPS-enforced, GitHub Pages from `main` root)
- **Repo:** https://github.com/raehufilm/raehu
- **Owner:** Rae Hu — director and filmmaker, Shanghai
- **Video host:** https://vimeo.com/raehu (embed by URL; never commit video files)
- **Domain registrar:** Namecheap (DNS = 4 A records on `@` + 1 CNAME on `www`)
- **Source of truth for visual design:** the 2026 portfolio PDF the owner shared (not committed; lives outside the repo in the owner's working directory)

## Current state of the site

`index.html` is a single-file scrolling landing page derived from the owner's 2026 portfolio deck. The visual system is locked in (palette, typography, section structure, hover/scroll behavior). Most content is still placeholder.

### What's real
- Bio copy (about section)
- Brand/client list (~30 entries as text)
- Pull quote
- Contact email and Vimeo link
- Deployment pipeline (DNS, HTTPS, GitHub Pages, three-layer author enforcement)

### What's placeholder or wrong
- **Hero illustration** at `index.html` lines 595–611 is a hand-coded SVG approximation of the deck's cover figure. Doesn't resemble the source. Needs either the original vector from the owner, an export from the PDF, or a faithful re-trace.
- **Every project card** is a CSS gradient with a "Still from X" text label. No real images yet.
- **About portrait** and **quote portrait** are gradient placeholders.
- **Project list mismatch vs. the deck:**
  - On the landing page but not in the deck: L'Oréal × Xiao Zhan, McDonald's × Wang Leehom, "Rooftop"
  - In the deck but missing from the landing page: Gucci Dreamscraper, Champion CNY, Under Armour, We Don't Dance For Nothing (possibly the unnamed "Rooftop" with a renamed card)
- **No per-project detail pages** exist yet (template TBD; would live at `works/<slug>/index.html`).
- **Brand grid duplicates:** Fendi and Lancôme appear twice.

## Design system (from the deck)

- Black `#0a0a0a` / warm white `#f4f1ec`
- Amber `#c8943a` (cover background, accents) / light amber `#e8b86d`
- Red dot `#c0392b` (label indicator), neutral gray `#888`
- Serif: EB Garamond — titles, body, italics
- Sans: Syne — uppercase labels, tags, page chrome
- **Convention:** every section label is `[red-dot] + ALL-CAPS TEXT`, mirroring the deck

## Content structure (deck → site)

The deck uses a 3-beat per-work template: **title spread → director's note → stills grids**. On the landing page, each work collapses to a card (title + meta tags + 1-line subtitle). The full 3-beat treatment is reserved for per-project detail pages — those don't exist yet, but should be the template when we build them.

## Open work

- [ ] Replace the hero illustration with the real cover art
- [ ] Reconcile the landing page works list against the deck's actual works
- [ ] Add real images: hero, about portrait, every project card
- [ ] Build the per-project detail page template, then per-work pages for the deck works
- [ ] Clean up brand grid duplicates
- [ ] Decide whether to self-host fonts (currently CDN; the only thing that softens the "zip and email" self-test in CLAUDE.md)

## Iteration log

- **2026-05-12** — Initial pass on the 2026 PDF (pages 1–31). Identified the per-work template. Reviewed first draft of `index.html`. Set up the repo, custom domain, GitHub Pages, HTTPS enforcement, three-layer author enforcement (pre-commit hook + CI + branch protection). Migrated notes from the owner's working directory into the repo and tightened the architecture rules in CLAUDE.md.
