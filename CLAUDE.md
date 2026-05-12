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

## Previewing locally

The site owner does not have npm/node and will not run a dev server. Previews are run by Claude, not the owner:
- Simplest: `open index.html` (opens via `file://` in the default browser)
- If HTTP is needed (real fetch calls, absolute asset paths): `python3 -m http.server` from repo root — Python is preinstalled on macOS

## Deployment

Push to `main` → GitHub Pages rebuilds in ~30 sec. No PR / staging flow; iteration happens locally and we push when ready. Custom domain + HTTPS are already configured at the DNS level (4 A records + 1 CNAME at Namecheap).
