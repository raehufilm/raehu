# Clip extraction scripts

Two command-line tools that automate the clip extraction workflow described in [clip-extraction.md](clip-extraction.md). They live at `~/bin/` and are available in any terminal window.

- **`generate-candidates`** — detects shots in a video, generates preview thumbnails, opens the folder for review
- **`extract-clips`** — extracts the shots you approved as web-ready MP4 clips, then scores them

These map directly to the two-phase workflow: detect and preview first, extract and score second.

---

## Prerequisites

FFmpeg must be installed:
```
brew install ffmpeg
```

---

## generate-candidates

Scans the source video for shot boundaries and creates one preview thumbnail per shot. Opens the thumbnail folder automatically when done.

### Usage

```
generate-candidates <source-video> <project> [options]
```

| Argument | What it is |
|---|---|
| `<source-video>` | Full path to the video file |
| `<project>` | Short name you choose — becomes the folder name (e.g. `vans`, `gugu`) |

| Option | Default | What it does |
|---|---|---|
| `--threshold N` | `0.2` | How sensitive shot detection is. Lower = more shots. Try `0.3` for fast-cut commercials. |
| `--output DIR` | `video_clip_seed/previews/<project>/` in the site repo | Save thumbnails somewhere else |
| `--help` | — | Print usage |

### What it prints

When it runs, it prints the input and output paths before doing anything:

```
==================================================
  generate-candidates
==================================================

  Input  : /Users/rae/Documents/Works & SHOWREEL/VANS_0812_DIR.mp4
  Output : /Users/rae/Documents/Rae/website 2026 /raehu/video_clip_seed/previews/vans
  Threshold: 0.2

  (Using default output root. Override with --output <dir>)

  Source duration: 107.4s

  Detecting shots — this may take a minute for longer files...
```

Then a table of every shot found:

```
--------------------------------------------------
  Shot                  Start       End         Duration
--------------------------------------------------
  shot00_0m00s          0.00s       3.64s       3.64s
  shot01_0m03s          3.64s       7.12s       3.48s
  shot02_0m07s          7.12s       8.52s       1.40s
  ...
  shot77_1m40s          100.64s     103.24s     2.60s
  shot78_1m43s          103.24s     107.44s     4.20s
--------------------------------------------------
  Total shots: 79
```

Then thumbnails are generated in parallel and the preview folder opens automatically.

At the end, it prints an `extract-clips` example command pre-filled with the first two shots from this video, so you have a template to copy.

### Real example

```
generate-candidates \
  "/Users/rae/Documents/Works & SHOWREEL/VANS_0812_DIR.mp4" \
  vans
```

Thumbnails land at:
```
video_clip_seed/previews/vans/
  shot00_0m00s.jpg
  shot01_0m03s.jpg
  shot02_0m07s.jpg
  ...
```

---

## extract-clips

Takes one or more time ranges, extracts each as a silent H.264 MP4, then scores every clip in the project folder by KB/s to flag any that look like logos, fades, or static frames.

### Usage

```
extract-clips <source-video> <project> <start:end> [<start:end> ...] [options]
```

| Argument | What it is |
|---|---|
| `<source-video>` | Full path to the video file (same one used in generate-candidates) |
| `<project>` | Same short name used in generate-candidates |
| `<start:end>` | Time range in seconds. Copy start and end from the shot table. |

You can pass as many `<start:end>` ranges as you want — they all extract in parallel.

| Option | Default | What it does |
|---|---|---|
| `--output DIR` | `video_clip_seed/clips/<project>/` in the site repo | Save clips somewhere else |
| `--threshold N` | `100` | KB/s value below which a clip gets flagged. Lower = fewer flags. |
| `--help` | — | Print usage |

### What it prints

Input, output, and what's about to happen — before it starts:

```
==================================================
  extract-clips
==================================================

  Input  : /Users/rae/Documents/Works & SHOWREEL/VANS_0812_DIR.mp4
  Output : /Users/rae/Documents/Rae/website 2026 /raehu/video_clip_seed/clips/vans
  Clips  : 3
  KB/s flag threshold: 100

  (Using default output root. Override with --output <dir>)
```

Then a score report for every clip in the folder:

```
--------------------------------------------------
  Scoring all clips in: .../video_clip_seed/clips/vans
  (Flag threshold: 100 KB/s)
--------------------------------------------------

  File                                  KB/s       Status
  ------------------------------------------------------------------
  clip01_0m21s.mp4                      4304 KB/s  ok
  clip02_0m53s.mp4                      6036 KB/s  ok
  clip03_1m10s.mp4                      7115 KB/s  ok

  All 3 clip(s) passed the content check.
```

If a clip scores under 100 KB/s it gets flagged:

```
  clip02_0m29s.mp4                        14 KB/s  FLAGGED — likely logo, fade, or static
```

Flagged clips are not deleted. Review them before using on the site.

### Output file format

| Setting | Value |
|---|---|
| Container | MP4 |
| Video | H.264, CRF 23, fast preset |
| Audio | None — clips are always silent |
| Compatibility | `yuv420p` pixel format (required for Safari), `+faststart` (plays before full download) |

### Real example — VANS

After reviewing the thumbnails from `generate-candidates`, shots 20, 40, and 54 look good:

```
  shot20_0m21s   21.28s → 25.48s   (4.20s)
  shot40_0m53s   53.16s → 56.92s   (3.76s)
  shot54_1m10s   70.36s → 75.52s   (5.16s)
```

Extract them:

```
extract-clips \
  "/Users/rae/Documents/Works & SHOWREEL/VANS_0812_DIR.mp4" \
  vans \
  21.28:25.48 53.16:56.92 70.36:75.52
```

Output:
```
video_clip_seed/clips/vans/
  clip01_0m21s.mp4    (4.2s)
  clip02_0m53s.mp4    (3.8s)
  clip03_1m10s.mp4    (5.2s)
```

### Another real example — Gugu

We've already extracted clips from this file. To add one more shot (e.g. 23:39 to 24:39):

```
extract-clips \
  "/Users/rae/Documents/Strange Fruit/Gugu/Gugu 奇怪的果 small size.mp4" \
  gugu \
  1419:1479
```

(23 minutes 39 seconds = 1419s; 24 minutes 39 seconds = 1479s)

---

## Full workflow — step by step

**Step 1 — Detect shots and generate thumbnails**

```
generate-candidates \
  "/Users/rae/Documents/Works & SHOWREEL/VANS_0812_DIR.mp4" \
  vans
```

The thumbnail folder opens. Review the images and note the shot names and times from the table printed in the terminal.

**Step 2 — Extract the shots you want**

```
extract-clips \
  "/Users/rae/Documents/Works & SHOWREEL/VANS_0812_DIR.mp4" \
  vans \
  21.28:25.48 53.16:56.92 70.36:75.52
```

Review the score report. Any clip flagged under 100 KB/s is worth a second look before using on the site.

**Step 3 — Move approved clips into the site**

Clips live at `video_clip_seed/clips/<project>/` (not committed to the repo — too large). Once you're happy with a clip, move or copy it to wherever it's needed on the site.

---

## Tips

- **Fast-cut content** (commercials with many 1–2 second cuts): raise `--threshold` to `0.3` to avoid detecting every single frame as a new shot.
- **Time ranges are in seconds.** To convert from minutes: multiply minutes by 60 and add seconds. Example: 2:04 = 124s.
- **You can run extract-clips multiple times** on the same project. The score report always covers every clip in the folder, not just the ones just extracted.
- **Flagged clips are not deleted** — the flag is a prompt to review, not an automatic rejection. A legitimately dark or slow cinematic shot may score low and still be usable.
