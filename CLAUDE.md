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

**Enforcement:** `.github/workflows/check-author.yml` fails CI on any push or PR with a commit whose author email is not raehufilm's noreply address above. If there is ever a legitimate reason for a different author (e.g. accepting an outside contribution), update both the workflow and this file in the same change. Do not work around the check.

## Architecture

Pure static HTML / CSS / JS. **No build step. No npm. No node_modules. No bundler.**

- `index.html` — landing page (CSS + JS inline for now)
- `CNAME` — custom domain `raehu.com` for GitHub Pages
- `.github/workflows/check-author.yml` — author enforcement
- `images/<project-slug>/` — image assets per project (future)
- `works/<project-slug>/index.html` — per-project detail pages (future)
- Videos hosted on Vimeo (https://vimeo.com/raehu), embedded via URL — do not commit video files

If you find yourself wanting to add a framework or build tooling, stop and confirm with the user first. The non-technical site owner is a hard constraint, not a stylistic preference.

## Previewing locally

The site owner does not have npm/node and will not run a dev server. Previews are run by Claude, not the owner:
- Simplest: `open index.html` (opens via `file://` in the default browser)
- If HTTP is needed (real fetch calls, absolute asset paths): `python3 -m http.server` from repo root — Python is preinstalled on macOS

## Deployment

Push to `main` → GitHub Pages rebuilds in ~30 sec. No PR / staging flow; iteration happens locally and we push when ready. Custom domain + HTTPS are already configured at the DNS level (4 A records + 1 CNAME at Namecheap).
