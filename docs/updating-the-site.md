# Updating raehu.com

How this site gets changed — what Rae asks for, what Claude does, and how the change shows up online.

## The simple version

The site is a folder of files stored on GitHub. When something needs to change, Rae tells Claude. Claude edits the files and sends them to GitHub. Usually within a minute, the change is live at https://raehu.com.

No apps to install, no commands to run, no code to read.

---

## For Rae (the owner)

### How to ask for a change

Just describe it. Examples that work:

- "Add a new project. Title is X, year is 2026, here are the images."
- "Change the bio paragraph in the About section to say X."
- "Replace the hero illustration with this file."
- "Remove the McDonald's card from the landing page."
- "Move Strange Fruit to the top of the Works section."

If the request isn't clear, Claude will ask before doing anything.

### How long the change takes to appear

Usually within a minute after Claude pushes. GitHub (where the site is hosted) takes ~30 seconds to rebuild it after each change.

### If you don't see your change

Three things to try, in order:

1. **Wait another minute** — the build might still be running.
2. **Hard refresh.** Your browser keeps a local copy of pages so they load fast next time, but that copy can be stale.
   - **Mac:** press `Cmd + Shift + R`, or hold Shift and click the reload button.
   - **Windows:** press `Ctrl + F5`, or hold Ctrl and click the reload button.
3. **Open the page in a private / incognito window** — bypasses the cache entirely.

If you've tried all three and the old version is still showing, tell Claude. Builds can occasionally fail (a typo in the code, a missing image, etc.) and Claude will investigate.

### What you'll never need to do

Install software. Open a terminal. Edit code. Learn what "Git" or "DNS" or "GitHub" actually means. None of that is on you.

---

## For Claude (the assistant)

The operational workflow for any owner-requested change. The architecture rules in `CLAUDE.md` apply throughout — this doc is the operational layer on top.

### Steps

Before you start, run `git status` to see the working tree. If files you're about to modify have unstaged user changes, follow the "Commit hygiene" rule in `CLAUDE.md` before doing your own edit — usually that means committing the user's prior work first as its own commit.

1. **Read** the relevant file(s) to confirm current state before editing.
2. **Edit** with the Edit tool, preserving the architecture rules in `CLAUDE.md` (no build step, no package manager, no frameworks, no JS-rendered data files).
3. **Preview locally** when the change is visual:
   - `open /Users/mabunday/Desktop/rae/raehu/<file>` for instant `file://` preview in the owner's default browser.
   - `python3 -m http.server` from the repo root if the change needs real HTTP (cross-page links from non-root paths, fetch, etc.).
4. **Commit:**
   ```
   git -C /Users/mabunday/Desktop/rae/raehu add <files>
   git -C /Users/mabunday/Desktop/rae/raehu commit -m "<concise imperative message>"
   ```
   The pre-commit hook verifies local git identity. If it fails, fix the local config (see `CLAUDE.md`) — never bypass with `--no-verify`.
5. **Push:**
   ```
   git -C /Users/mabunday/Desktop/rae/raehu push origin main
   ```
   The CI author check runs on every push. Branch protection blocks force-pushes and deletions to `main`. Work with these layers, never around them.
6. **Verify the deploy:**
   ```
   gh api repos/raehufilm/raehu/pages/builds/latest --jq '{status, error_message: .error.message, commit}'
   ```
   Expect `status: "built"`, `error_message: null`, and `commit` matching your push. Build typically completes within 30 seconds.
7. **Confirm with the owner.** Tell them the change is live. If they don't see it, walk them through hard refresh (see the "For Rae" section above).

### When the owner reports the site looks wrong

1. Check the latest build first (step 6 above). If it failed, fix the underlying issue and re-push.
2. Curl the live site: `curl -sI https://raehu.com/`. Check `age` (how cached the response is at GitHub's CDN) and `last-modified`.
3. If the build is good and the live site reflects the change but the owner still doesn't see it: hard refresh on their end.
4. If anything else is off, surface it to the owner in plain English. No jargon.

### Never

- Install anything to the repo (`npm install`, `pip install`, etc.) — violates the architecture rules in `CLAUDE.md`.
- Commit video files. Link to Vimeo (https://vimeo.com/raehu) instead.
- Bypass the pre-commit hook with `--no-verify`.
- Force-push to `main`. Branch protection blocks it and that's intentional.
- Use absolute paths or other machine-specific values in committed files.

### Commit message style

Imperative, present tense, one line, concise. Match what's already in the repo's git log. Examples:

- `Update bio copy in About section`
- `Add Gucci Dreamscraper to landing page works`
- `Replace hero illustration with cover SVG`
- `Fix typo in contact email`

Include the `Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>` trailer on Claude-authored commits.
