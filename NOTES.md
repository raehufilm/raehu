# raehu — working notes

Running state for the raehu.com portfolio site. **Read `CLAUDE.md` first for the rules**, then `docs/updating-the-site.md` for the operational workflow when making changes. This file is the running state: what's done, what's not, design context, open work.

## At a glance

- **Live site:** https://raehu.com (HTTPS-enforced, GitHub Pages via custom workflow)
- **Repo:** https://github.com/raehufilm/raehu
- **Owner:** Rae Hu — director and filmmaker, Shanghai
- **Video host:** https://vimeo.com/raehu for trailers/longform; approved WebP/MP4 media can be committed for generated work pages
- **Domain registrar:** Namecheap (DNS = 4 A records on `@` + 1 CNAME on `www`)
- **Source of truth for visual design:** the 2026 portfolio PDF the owner shared (not committed; lives outside the repo in the owner's working directory)

## Current state of the site

`index.html` is a single-file scrolling landing page derived from the owner's 2026 portfolio deck. The visual system is locked in (palette, typography, section structure, hover/scroll behavior). Most content is still placeholder.

### What's real
- Bio copy (about section)
- Brand/client list (28 entries, matching PDF exactly)
- Pull quote
- Contact email (`raehufilm@gmail.com`) and Vimeo link
- Location ("Shanghai · Mexico City")
- Works list aligned with PDF (Rooftop and McDonald's removed)
- Hero illustration with subtle ink texture; hero background updated to `#E8B949`
- Generated per-project proof-of-concept pages for Strange Fruit and Champion
- `pages/works/` source-content skeleton and generator for trailer, note, highlight, and BTS sections
- Deployment pipeline (DNS, HTTPS, custom GitHub Pages publish workflow, three-layer author enforcement)

### What's placeholder or wrong
- **Every project card** is a CSS gradient with a "Still from X" text label. No real images yet.
- **About portrait** and **quote portrait** are gradient placeholders.
- **Generated Strange Fruit and Champion pages** are still proof-of-concept pages, not final editorial/design sign-off.

## Design system (from the deck)

- Black `#0a0a0a` / warm white `#f4f1ec`
- Amber `#c8943a` (cover background, accents) / light amber `#e8b86d`
- Red dot `#c0392b` (label indicator), neutral gray `#888`
- Serif: EB Garamond — titles, body, italics
- Sans: Syne — uppercase labels, tags, page chrome
- **Convention:** every section label is `[red-dot] + ALL-CAPS TEXT`, mirroring the deck

## Content structure (deck → site)

The deck uses a 3-beat per-work template: **title spread → director's note → stills grids**. On the landing page, each work collapses to a card (title + meta tags + 1-line subtitle). The generated per-project proof of concept currently expands that into trailer, director's note, highlight grid, and BTS sections.

## Open work

- [ ] Reconcile the landing page works list against the deck's actual works
- [ ] Add real images: hero, about portrait, every project card
- [ ] Continue hardening the generated per-project detail page template and expand it to the deck works
- [ ] Clean up brand grid duplicates
- [ ] Decide whether to self-host fonts (currently CDN; the only thing that softens the "zip and email" self-test in CLAUDE.md)

## Iteration log

- **2026-05-12** — Initial pass on the 2026 PDF (pages 1–31). Identified the per-work template. Reviewed first draft of `index.html`. Set up the repo, custom domain, GitHub Pages, HTTPS enforcement, three-layer author enforcement (pre-commit hook + CI + branch protection). Migrated notes from the owner's working directory into the repo and tightened the architecture rules in CLAUDE.md.
- **2026-05-12** — Added `docs/updating-the-site.md` documenting the update workflow for both audiences. Added `README.md` at repo root as the public index / site map. Added a "Documentation maintenance" hard constraint to CLAUDE.md requiring docs to be updated in the same commit as any change to repo behavior, structure, or workflow.
- **2026-05-12** — Replaced the placeholder hero illustration with the real cover art from page 9 of the 2026 portfolio PDF. The vector lines now come from `images/illustration.svg` (31 paths, `currentColor`-driven so any consumer can theme it, reusable as a brand asset), inlined into the hero and sized to fill the frame rather than sitting as a small centered crop. Line color is `#6C1B0F` (the PDF's authentic dark red) on the existing `#c8943a` amber. Also added an "Iteration log" rule to `CLAUDE.md` requiring every commit that ships a substantive change to append a plain-English dated entry here — this log is the owner's changelog, since they don't read `git log`.
- **2026-05-12** — Added a "Commit hygiene" hard constraint to `CLAUDE.md` requiring Claude to check `git status` / `git diff` before any edit, and to commit the owner's unstaged work first as its own commit rather than mixing it under Claude's message. The trigger was an earlier commit that quietly rolled a hero SVG swap into a domain-fix message. The new rule plus its cross-reference in `docs/updating-the-site.md` should make that kind of muddied history harder to produce by accident.
- **2026-05-12** — Consolidated 樂瑞 into the main "rae hu" headline in the hero so the English and Chinese names sit on one line in the same big serif, matching how the nav logo already pairs them. Removed the smaller standalone 樂瑞 that previously sat under the name (now redundant) and dropped the unused `.hero-chinese` CSS class.
- **2026-05-12** — Made the red indicator dots pulse with a 1.6s opacity loop (100% → 20% → 100%) as a subtle "REC light" cue, applied site-wide via the shared `.red-dot` class; respects `prefers-reduced-motion: reduce` for users who opt out of animation. Also added `docs/portfolio-reference.md` — a design vocabulary, voice, and project catalog distilled from the 2026 portfolio PDF, intended as the canonical reference when handling design requests.
- **2026-05-12** — Added a "Stay in sync with the remote" hard constraint to `CLAUDE.md`: before any edit session and before any commit, Claude must `git fetch` and check whether `origin/main` has commits this clone doesn't, and pull before editing if so. The rule protects the owner's option to work on the site from multiple machines — without the fetch-first habit, work from one machine can silently overwrite or conflict with work from another.
- **2026-05-12** — Formalized "Preview before deploy" as a hard constraint in `CLAUDE.md` and integrated it as step 3 of the workflow in `docs/updating-the-site.md`. Every user-visible change must now be opened in the local browser preview and described to the owner in plain English — with the `file://` URL, a refresh note, where to look, a numbered list of what changed, and an explicit ask before deploying — and Claude waits for confirmation before committing or pushing. Docs / hooks / CI / infra changes are exempt.
- **2026-05-25** — Added the portfolio grid layout system: `js/portfolio-grid.js` is a reusable irregular-grid engine that arranges landscape stills and video clips in gapless rows with varying column widths. Row heights are computed automatically so every cell stays landscape; images fill cells via `object-fit: cover` (CSS cropping, no resized source files needed). Layout patterns are specified as a compact `data-layout` attribute in HTML (e.g., `"7-5, 3-5-4, 5-7, 4-8"`). Algorithm is adapted from the Knuth-Plass line-breaking approach used by Google Photos. Documented in `docs/portfolio-grid.md`.
- **2026-05-25** — Added `docs/clip-extraction.md` — FFmpeg workflow for pulling highlight clips from source video. Two-step process: shot detection → preview thumbnails for owner approval → web-ready H.264 MP4 extraction (silent, faststart, yuv420p). Added `video_clip_seed/` and `.claude/` to `.gitignore`.
- **2026-06-01** — Started the `works/strange-fruit/` portfolio-page proof of concept with three formal content sections: trailer, note, and highlight. Added a fixed left-side section tracker that uses the shared red-dot motif, highlights the current section while scrolling, and supports smooth jumps to each section. The page still depends on local raw media assets and is not deployment-ready until those assets are compressed and the video policy is resolved.
- **2026-06-01** — Continued the `works/strange-fruit/` proof of concept with a fixed black project header using EB Garamond links (`works`, `about`, `contact`) and added a fourth `bts` section to the left-side tracker. The BTS section is a mixed image/text page with a 70/30 slideshow-and-copy layout, using five local stills for the temporary proof of concept.
- **2026-06-01** — Centralized the Strange Fruit page inset spacing behind a shared `data-page-padding` section attribute and inherited CSS variables. Trailer, note, highlight, and BTS now pull their horizontal/inner spacing from the same page padding value instead of duplicating hard-coded `3rem` rules.
- **2026-06-01** — Simplified the Strange Fruit BTS text column to a single right-aligned body copy block containing the current film credits.
- **2026-06-01** — Added hover-revealed previous/next arrow controls to the Strange Fruit BTS slideshow and shared the manual controls with the existing autoplay state.
- **2026-06-01** — Reduced the Strange Fruit BTS credits body size and set the credits to preserve one line per credit so they do not wrap in the right text column.
- **2026-06-01** — Simplified the Strange Fruit BTS slideshow controls to bare hover-revealed arrows and top-aligned the right-side credits block.
- **2026-06-01** — Tuned the Strange Fruit note typography down to a quieter scale: the main note headline is now `2rem` and the supporting note copy is now `1.2rem`.
- **2026-06-01** — Started the non-technical content source structure under `pages/works/strange-fruit/bts/` with `text.md` for BTS copy and `media/` for ordered slideshow assets. Media ordering is represented by a leading `NUMBER_` filename prefix so assets can be rearranged by renaming.
- **2026-06-01** — Added `PAGES.md` at the repo root as the running specification for the developing non-technical `pages/` content workflow. The document records the current work/section folder schema, `text.md` Markdown rules, `media/` ordering by `NUMBER_` prefix, current BTS template behavior, and open decisions for the eventual templating step.
- **2026-06-01** — Added `pages/works/strange-fruit/highlight/media/` and copied the five current highlight proof-of-concept media items into it with `NUMBER_` prefixes that preserve the existing grid order. Updated `PAGES.md` with the current highlight mixed-media grid rules.
- **2026-06-01** — Added `pages/works/strange-fruit/note/text.md` and `pages/works/strange-fruit/note/media/1_hero.png` for the note section source-content skeleton. The note text uses Markdown heading/body conventions, while static section chrome such as `Director's note` remains a template responsibility.
- **2026-06-01** — Added `pages/works/strange-fruit/trailer/trailer_link.md` with the user-facing Vimeo URL for the Strange Fruit trailer. Updated `PAGES.md` to specify whitespace-tolerant trailer link parsing and Vimeo URL-to-embed translation.
- **2026-06-01** — Added the first dependency-free `pages/works` generator: `scripts/generate_pages.py` reads valid work folders, renders `templates/work-page.html`, and writes static `works/<slug>/index.html` output. Added unit tests, a GitHub Actions check for generated-page drift, and updated the docs to clarify that this is a local/CI maintenance step rather than a deploy-time build.
- **2026-06-01** — Extended the generator media pipeline so ffmpeg converts source images in `pages/works/**/media/` to WebP, skips conversion when the WebP is already up to date, and generated HTML references the WebP assets. Raw image drops are ignored by Git; WebP and MP4 remain commit candidates.
- **2026-06-01** — Added a double-clickable root `generate_website` publishing script and a custom `Publish website` GitHub Actions workflow. The script generates and tests pages locally, enforces that publishable work-page media is only WebP/MP4 and stays under 800 MB, pushes approved changes, switches GitHub Pages from legacy branch publishing to workflow publishing, and waits for the deployment to finish.
