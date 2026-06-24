# Updating raehu.com

How this site gets changed — what Rae asks for, what an agent does, and how the change shows up online.

## The simple version

The site is a folder of files stored on GitHub. When something needs to change, Rae tells an agent. The agent edits the files, sends them to GitHub, and runs the publication workflow. Usually within a minute, the change is live at https://raehu.com.

No apps to install, no code to read. There is also a double-clickable `generate_website` file at the repo root for the rare case where Rae wants to publish approved local content directly from this Mac.

---

## For Rae (the owner)

### How to ask for a change

Just describe it. Examples that work:

- "Add a new project. Title is X, year is 2026, here are the images."
- "Change the bio paragraph in the About section to say X."
- "Replace the hero illustration with this file."
- "Remove the McDonald's card from the landing page."
- "Move Strange Fruit to the top of the Works section."

If the request isn't clear, the agent will ask before doing anything.

### How long the change takes to appear

Usually within a minute after the agent publishes. GitHub (where the site is hosted) takes ~30 seconds to deploy the site after the publish workflow starts.

### If you don't see your change

Three things to try, in order:

1. **Wait another minute** — the build might still be running.
2. **Hard refresh.** Your browser keeps a local copy of pages so they load fast next time, but that copy can be stale.
   - **Mac:** press `Cmd + Shift + R`, or hold Shift and click the reload button.
   - **Windows:** press `Ctrl + F5`, or hold Ctrl and click the reload button.
3. **Open the page in a private / incognito window** — bypasses the cache entirely.

If you've tried all three and the old version is still showing, tell the agent. Builds can occasionally fail (a typo in the code, a missing image, etc.) and the agent will investigate.

### What you'll never need to do

Install software. Open a terminal. Edit code. Learn what "Git" or "DNS" or "GitHub" actually means. None of that is on you.

---

## For agents

The operational workflow for any owner-requested change. The repo rules in `README.md` apply throughout — this doc is the operational layer on top.

### Steps

Before you start, run `git status` to see the working tree. If files you're about to modify have unstaged user changes, preserve that work and keep it separate from your own changes.

1. **Read** the relevant file(s) to confirm current state before editing.
2. **Edit** with the appropriate edit tool, preserving the architecture rules in `README.md` (no deploy-time build step, no package manager, no frameworks, no JS-rendered data files).
   - For generated site pages, edit the source content under `editable-content/works/commercials/<slug>/` or `editable-content/works/films/<slug>/`, then run `python3 scripts/generate_pages.py` so `generated-website/index.html`, `generated-website/works/index.html`, and `generated-website/works/<slug>/index.html` are regenerated from the templates.
   - Before committing generated site pages, run `python3 -m unittest discover -s tests` and `python3 scripts/generate_pages.py --verify-generated`.
3. **Preview, describe, and wait for confirmation (REQUIRED for any user-visible change).** Skip only for non-visible changes: docs, hooks, CI, `.gitignore`, infra.

   - **Preview locally:**
     - `open generated-website/index.html` from the repo root for the generated homepage.
     - `open generated-website/works/<slug>/index.html` from the repo root for a generated work page.
     - `python3 -m http.server` from the repo root if the change needs real HTTP (cross-page links from non-root paths, fetch, etc.).
   - **Show the owner the change** clearly:
     - The `file://` URL (always include, even after `open`).
     - A refresh note (in case they already have a stale preview tab open).
     - Where to look on the page, in plain language (no CSS selectors, no line numbers).
     - A numbered list of what changed — what it used to look like, what it looks like now. No code, no class names.
     - What's unchanged (when relevant), as reassurance.
     - An explicit ask for confirmation: *"Ready to push to the live site? (Say 'go' or push back if anything needs tweaking.)"*
   - **Wait for explicit confirmation** ("go", "yes", "looks good", "push", etc.) before continuing to step 4. Do not stage, commit, or push without it.

4. **Commit and publish.** Prefer the root wrapper when publishing generated project pages or any normal site update:
   ```
   ./generate_website --message "<concise imperative message>" --no-pause
   ```
   The script runs the generator, tests, generated-HTML drift check, media policy check, commit, push, GitHub Pages workflow-mode configuration, workflow dispatch, and deployment watch.

   Manual commit/push is still acceptable for narrow maintenance work:
   ```
   git add <files>
   git commit -m "<concise imperative message>"
   ```
   The pre-commit hook verifies local git identity. If it fails, fix the local config (see `README.md`) — never bypass with `--no-verify`.
5. **Push manually only if you did not use `generate_website`:**
   ```
   git push origin main
   ```
   The CI author check runs on every push. Branch protection blocks force-pushes and deletions to `main`. Work with these layers, never around them.
6. **Verify the deploy.** If you used `generate_website`, it already watches the `Publish website` workflow. For manual checks:
   ```
   gh run list --workflow publish-website.yml --branch main --limit 1
   gh api repos/raehufilm/raehu/pages --jq '{html_url, build_type, status, cname}'
   ```
   Expect `build_type: "workflow"` and a successful latest `Publish website` run. Deployment typically completes within 30 seconds.
7. **Confirm with the owner.** Tell them the change is live. If they don't see it, walk them through hard refresh (see the "For Rae" section above).

### When the owner reports the site looks wrong

1. Check the latest build first (step 6 above). If it failed, fix the underlying issue and re-push.
2. Curl the live site: `curl -sI https://raehu.com/`. Check `age` (how cached the response is at GitHub's CDN) and `last-modified`.
3. If the build is good and the live site reflects the change but the owner still doesn't see it: hard refresh on their end.
4. If anything else is off, surface it to the owner in plain English. No jargon.

### Never

- Install anything to the repo (`npm install`, `pip install`, etc.) — violates the architecture rules in `README.md`.
- Edit a generated `generated-website/works/<slug>/index.html` directly when that work is managed by `editable-content/works/commercials/<slug>/` or `editable-content/works/films/<slug>/`; edit the source folder and rerun `scripts/generate_pages.py`.
- Commit raw video files. Link trailers and longform videos to Vimeo (https://vimeo.com/raehu). Approved short MP4 clips are allowed only as ordered work-page media under `editable-content/works/**/media/`.
- Bypass the pre-commit hook with `--no-verify`.
- Force-push to `main`. Branch protection blocks it and that's intentional.
- Use absolute paths or other machine-specific values in committed files.

### Commit message style

Imperative, present tense, one line, concise. Match what's already in the repo's git log. Examples:

- `Update bio copy in About section`
- `Add Gucci Dreamscraper to landing page works`
- `Replace hero illustration with cover SVG`
- `Fix typo in contact email`

Do not add co-author trailers unless the owner explicitly requests them.
