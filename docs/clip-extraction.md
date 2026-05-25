# Clip extraction workflow

How to pull highlight clips from longer source video for use on the portfolio site. Requires **FFmpeg** (installed via Homebrew: `brew install ffmpeg`).

Source videos live in `video_clip_seed/`. Outputs go in subfolders within the same directory — never committed to the repo (too large; `video_clip_seed/` is in `.gitignore`).

---

## Step 1 — Inspect the source file

Get duration and confirm the file is readable:

```bash
ffprobe -v quiet -show_entries format=duration -of csv=p=0 "video_clip_seed/YourFile.mov"
```

---

## Step 2 — Detect shots and list candidates

Run scene detection to find all shot boundaries. Threshold `0.2` works well for typical narrative/commercial footage — raise it (e.g. `0.3`) if you get too many false positives in a high-motion piece.

```bash
ffmpeg -i "video_clip_seed/YourFile.mov" \
  -vf "select=gt(scene\,0.2),showinfo" -vsync vfr -f null - 2>&1 \
  | grep "pts_time" | grep -oP 'pts_time:\K[0-9.]+' \
  | awk -v total=<DURATION_IN_SECONDS> '
    BEGIN { prev=0; n=0 }
    {
      t = $1
      dur = t - prev
      printf "Shot %02d: %6.2fs → %6.2fs  (%.2fs)\n", n, prev, t, dur
      prev = t; n++
    }
    END {
      printf "Shot %02d: %6.2fs → %6.2fs  (%.2fs)\n", n, prev, total, total - prev
    }'
```

Replace `<DURATION_IN_SECONDS>` with the value from Step 1.

**Reading the output:** Each line is one shot — start time, end time, duration. Look for longer shots (2s+) as clip candidates. Skip anything under ~0.5s (flash cuts, transitions).

---

## Step 3 — Generate preview thumbnails

For each candidate shot, extract a single frame from its midpoint. This lets the owner approve moments before full clip generation.

```bash
mkdir -p "video_clip_seed/previews"

# One command per candidate — use the midpoint of each shot's time range.
# Example for a shot from 18.16s to 23.84s (midpoint = 21.0s):
ffmpeg -ss 21.0 -i "video_clip_seed/YourFile.mov" \
  -frames:v 1 "video_clip_seed/previews/shot13_18s-24s.jpg" -y

# Run multiple in parallel by appending & to each and then: wait
```

Open the folder and share the thumbnails with the owner for review:

```bash
open "video_clip_seed/previews/"
```

**Wait for approval before proceeding.** The owner picks which shots become clips.

---

## Step 4 — Extract approved clips

### Output spec (do not change without owner approval)

| Parameter | Value | Reason |
|---|---|---|
| Container | MP4 | Universal browser support |
| Video codec | H.264 (`libx264`) | Broadest compatibility; plays on every browser and device |
| Quality | CRF 23 | Good quality at reasonable file size; range is 0–51, lower = better |
| Encode speed | `fast` preset | Fine for portfolio use; `slow` gives marginally smaller files |
| Audio | **None** (`-an`) | Clips play silent on the site — audio is stripped entirely |
| Pixel format | `yuv420p` | Required for Safari compatibility; do not omit |
| Metadata placement | `+faststart` | Moves MP4 index to the front of the file so playback begins before full download |

These clips are silent by design. Every clip produced by this workflow should have no audio track.

### Commands

```bash
mkdir -p "video_clip_seed/clips"

# Replace -ss (start) and -t (duration) for each approved shot.
# Example for a shot from 18.16s, duration 5.68s:
ffmpeg -ss 18.16 -i "video_clip_seed/YourFile.mov" -t 5.68 \
  -c:v libx264 -crf 23 -preset fast \
  -an -movflags +faststart -pix_fmt yuv420p \
  "video_clip_seed/clips/shot13_18s-24s.mp4" -y

# Run multiple in parallel by appending & to each, then wait:
# ffmpeg ... "clip_a.mp4" -y &
# ffmpeg ... "clip_b.mp4" -y &
# wait
```

### Verify output

After extraction, confirm no audio track is present and the file is web-ready:

```bash
ffprobe -v quiet -show_streams "video_clip_seed/clips/shot13_18s-24s.mp4" \
  | grep codec_type
# Should output only: codec_type=video
# If codec_type=audio appears, re-run with -an
```

---

## Output structure

```
video_clip_seed/
├── YourFile.mov          # source (never committed)
├── previews/             # thumbnails for owner review (never committed)
│   └── shot13_18s-24s.jpg
└── clips/                # final clips ready for the site (never committed)
    └── shot13_18s-24s.mp4
```

Clips from `video_clip_seed/clips/` can be moved into the site as needed once approved.
