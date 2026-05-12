# CLAUDE.md

Static portfolio site for filmmaker Rae Hu — deployed at https://raehu.com via GitHub Pages from this repo's `main` branch root.

## Commit author identity (REQUIRED)

All commits MUST be authored by `raehufilm`:
- `user.name`: `raehufilm`
- `user.email`: `283902148+raehufilm@users.noreply.github.com`

If local git config in this repo is unset or different, fix it (do **not** use `--global`):
```
git config user.name "raehufilm"
git config user.email "283902148+raehufilm@users.noreply.github.com"
```

Push from a `gh` session with `raehufilm` as the active account. Switch if needed:
```
gh auth switch --user raehufilm
```

**Enforcement (three layers):**
1. **Local pre-commit hook** at `.githooks/pre-commit` — blocks `git commit` itself if `user.name` / `user.email` don't match. Requires `git config core.hooksPath .githooks` to be set in each clone (see below).
2. **CI workflow** at `.github/workflows/check-author.yml` — fails the build on any push or PR with a commit whose author email is not raehufilm's noreply address. Catches anything the local hook missed (e.g. fresh clone where `core.hooksPath` isn't set yet).
3. **Branch protection on `main`** — blocks force-pushes and deletions. `enforce_admins: false`, so raehufilm can still override in a genuine emergency.

If there is ever a legitimate reason for a different author (e.g. accepting an outside contribution), update the workflow, the hook, and this file in the same change. Do not work around the checks.

## One-time setup per clone

After cloning this repo, run once:
```
git config user.name "raehufilm"
git config user.email "283902148+raehufilm@users.noreply.github.com"
git config core.hooksPath .githooks
```

The first two lines set the author identity locally (without `--global`). The third tells git to look for hooks in the committed `.githooks/` directory instead of the local `.git/hooks/`. Without it, the pre-commit check won't run.

## Stay in sync with the remote (hard constraint)

The site owner may work on raehu from multiple machines, and commits can land on `origin/main` between your sessions. **Before any edit session — and again before any commit — fetch and check whether the local branch is up to date with `origin/main`.**

The check:
```
git fetch origin
git status
```

If `git status` reports `Your branch is behind 'origin/main' by N commits`, **stop and `git pull` before editing.** Building on a stale tree either silently overwrites the owner's recent work from another machine or creates a confusing merge you may not know how to resolve cleanly.

If both sides have diverged (local is ahead AND behind), do not auto-resolve — surface it to the owner. They may have intentional in-progress work on the other machine that should land first.

The cost of `git fetch` is near-zero; the cost of overwriting the owner's other-machine work is high.

## Commit hygiene (hard constraint)

**Before making any edit, run `git status` and `git diff` to check the working tree for unstaged user changes.** If files you're about to modify already have uncommitted edits the user made:

1. **Never silently pull those edits into your commit.** Mixing them under your own commit message muddies the history and misrepresents what landed.
2. **Pick one of two paths:**
   - **Commit the user's prior work first** as a separate commit with a faithful message describing their changes (use `git diff` to read what they did). Then make your own edit as a separate commit.
   - **Or stage only your hunks** with `git add -p` and tell the user their other changes remain unstaged.

   Default to the first path — it surfaces the user's work in its own commit instead of burying it under yours.

This applies to every commit, regardless of size. A two-line typo fix that quietly drags an unrelated change under it is still bad history.

## Architecture (hard constraints)

**The site owner is non-technical and may work from any machine. They do not run dev tools. They update the site by telling Claude what to change.** This sets every rule below — they are constraints, not preferences. Do not relax them without explicit user permission.

### Hard rules

1. **No build step.** Files on disk are exactly what gets served. No bundler, transpiler, static-site generator, or preprocessor.
2. **No package manager.** No `package.json`, no `node_modules`, no `requirements.txt`, no installable dependencies of any kind. If a feature needs a library, link it from a stable public CDN inline — but prefer writing it yourself in vanilla JS.
3. **No frameworks.** No React, Vue, Svelte, Alpine, htmx. Just HTML + CSS + browser JS.
4. **No CSS preprocessors.** No Sass, Less, Tailwind, postcss. Plain CSS, in `<style>` tags or `.css` files.
5. **No data files rendered by JS.** Content lives in HTML where the owner can see and point at it. JSON/YAML "content" with a JS renderer is a build step in disguise — don't introduce it.
6. **No machine-specific paths or assumptions.** Everything in this repo must work on any clone on any OS. No absolute paths, no user-specific config in committed files.
7. **External dependencies allow-list:** GitHub Pages (hosting), Vimeo (video embeds), Google Fonts CDN (typography). That's it. Anything else, ask.

### Conventions

- `index.html` — landing page (CSS + JS inline)
- `works/<slug>/index.html` — per-project detail pages
- `images/<slug>/` — image assets per project, committed to the repo
- `CNAME` — custom domain
- Videos hosted on Vimeo (https://vimeo.com/raehu), embedded via URL. **Never commit video files.**

### Self-test before any change

Ask yourself: "If I zipped this repo and emailed it to the owner, could they unzip it, double-click `index.html`, and see what's on raehu.com?"

If yes, you're good. If no, you have broken the architecture — revert and reconsider.

### The owner's update loop

For the owner, "update the site" means: tell Claude what to change → Claude edits a file → Claude commits and pushes. The owner runs no commands. Preserve this workflow with every change you make.

**For the operational workflow when handling owner-requested changes — read, edit, preview, commit, push, verify — follow `docs/updating-the-site.md`.** That file also has the owner-facing plain-English explanation of how changes propagate; refer the owner to it when they ask why a change isn't showing up.

**Before any change to look, voice, or copy, consult `docs/portfolio-reference.md`.** It's the design and content reference extracted from the owner's portfolio PDF (palette, typography, canonical bio and quote, voice patterns, full project catalog, sequencing). The PDF itself is not committed (~80 MB binary that lives outside the repo); this markdown is the authoritative substitute.

## Performance rules (hard constraints)

Static content should stay fast. The site owner cannot manually audit performance — Claude is the only check between an unintentional regression and shipped code. These rules exist to make perf failures impossible by default, not optional.

### Hard rules

1. **Never embed Vimeo iframes directly.** Each `<iframe src="https://player.vimeo.com/…">` ships ~600 KB of player JS on load — a works grid with N projects = N × 600 KB of unrequested JS. Use a facade: render a poster `<img>` + play button, and swap in the iframe only on click. Build this when the first real Vimeo embed lands; do not preemptively scaffold.

2. **Every `<img>` must have explicit `width` and `height` attributes** (prevents CLS / layout shift), plus `loading="lazy"` and `decoding="async"` — **except** the hero/LCP image, which must load eagerly and be preloaded in `<head>`:
   ```html
   <link rel="preload" as="image" href="images/hero/hero.webp">
   ```

3. **Serve images as WebP** (or AVIF + WebP fallback via `<picture>`). Never commit raw JPG/PNG when WebP will do. Size budgets after compression — if an image won't fit at acceptable quality, resize it down before committing:
   - Hero / LCP image: ≤ 250 KB
   - Project still / full-width image: ≤ 150 KB
   - Thumbnail: ≤ 50 KB

4. **Google Fonts hygiene.** Only request `font-weight` and `font-style` values the CSS actually references — never "in case we need it later." When adding a typeface, audit the CSS first, then update the URL. Both preconnects must be present in `<head>`:
   ```html
   <link rel="preconnect" href="https://fonts.googleapis.com">
   <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
   ```
   `googleapis` serves the CSS; `gstatic` serves the woff2 files. Missing the second preconnect costs a round-trip on every cold visit.

5. **Animations stay on the compositor.** In anything that fires per-event (`mousemove`, `scroll`, hover on many elements), animate only `transform` and `opacity`. Avoid `left`/`top`/`width`/`height` for movement, and avoid mutating `filter` / `box-shadow` / `mix-blend-mode` in tight loops. Wrap per-event style writes in `requestAnimationFrame`.

### Self-test before any change

After any change that adds an image, video, font, or animation, ask:
- Does this make first paint slower for a visitor on a 4G phone?
- Does it download bytes the visitor won't see?

If yes to either, fix it before committing.

## Documentation maintenance (hard constraint)

This repo has four docs that must stay in sync with reality. Keeping them current is not optional — stale docs are worse than missing docs, because they actively mislead the next reader (including the next Claude session).

### The docs

- **`README.md`** — the public index / site map at the repo root. The entry point on GitHub.
- **`CLAUDE.md`** (this file) — rules and hard constraints for Claude.
- **`NOTES.md`** — running state of the site (what's done, what's placeholder, open work).
- **`docs/`** — operational guides. Currently: `docs/updating-the-site.md` — the update workflow.

### The rule

**In every commit that changes the repo's behavior, structure, or workflow, update the affected doc(s) in the same commit.**

Concrete triggers:
- New file or directory at the repo root → update `README.md`'s file layout.
- New architecture rule, performance constraint, or convention → update `CLAUDE.md`.
- New workflow or change to the update process → update `docs/updating-the-site.md`.
- Project shipped, placeholder removed, TODO closed, or new open work identified → update `NOTES.md`.
- New file under `docs/` → link to it from `README.md` and (if it documents a workflow Claude must follow) from `CLAUDE.md`.
- **Any substantive change to the site or its rules → append a dated entry to `NOTES.md`'s "Iteration log" (see "The iteration log" below).**

If you find yourself making a substantive change without touching any doc, stop and ask whether that's right. Usually it isn't.

### The iteration log (the owner's changelog)

`NOTES.md` ends with an "Iteration log" — a dated, append-only list of substantive changes. **Every commit that ships a substantive change must append an entry here.** This exists because the site owner is non-technical: they don't read `git log`, and they don't read commit messages on GitHub. The iteration log is where they go to see what changed and when.

Format for each entry:
- Lead with `**YYYY-MM-DD** — `, using an absolute calendar date. Convert "today" / "this week" / any relative date in your working context to the actual date.
- One paragraph, 1–4 sentences. Plain English first, technical detail second. The owner should be able to read the entry and understand what happened to the site.
- One commit, one entry. Multiple changes in the same commit can share one entry.

When to skip: pure internal refactors with no behavior change, typo fixes, edits that don't affect a rule or a user-visible outcome.

The existing entries at the bottom of `NOTES.md` are the reference for tone and granularity. If a change is too small or too internal to deserve an entry there, it's probably also too small to need a commit of its own.

## Previewing locally

The site owner does not have npm/node and will not run a dev server. Previews are run by Claude, not the owner:
- Simplest: `open index.html` (opens via `file://` in the default browser)
- If HTTP is needed (real fetch calls, absolute asset paths): `python3 -m http.server` from repo root — Python is preinstalled on macOS

## Deployment

Push to `main` → GitHub Pages rebuilds in ~30 sec. No PR / staging flow; iteration happens locally and we push when ready. Custom domain + HTTPS are already configured at the DNS level (4 A records + 1 CNAME at Namecheap).
