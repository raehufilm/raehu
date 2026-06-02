#!/usr/bin/env python3
"""Generate static work pages from the editable-content/works source tree.

This script intentionally uses only the Python standard library so it can run
locally and in GitHub Actions without package installation.
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import html
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, quote, urlencode, urlparse
from urllib.request import Request, urlopen


REPO_ROOT = Path(__file__).resolve().parents[1]
EDITABLE_WORKS_DIR = REPO_ROOT / "editable-content" / "works"
GENERATED_WEBSITE_DIR = REPO_ROOT / "generated-website"
WORKS_OUTPUT_DIR = GENERATED_WEBSITE_DIR / "works"
HOME_OUTPUT_HTML = GENERATED_WEBSITE_DIR / "index.html"
GENERATOR_TEMPLATES_DIR = REPO_ROOT / "generator-templates"
WORK_PAGE_TEMPLATE = GENERATOR_TEMPLATES_DIR / "work-page.html"
HOME_TEMPLATE = GENERATOR_TEMPLATES_DIR / "index.html"
WORKS_REDIRECT_TEMPLATE = GENERATOR_TEMPLATES_DIR / "works-redirect.html"
SITE_SOURCE_ASSETS_DIR = REPO_ROOT / "site-source-assets"
HERO_ILLUSTRATION = SITE_SOURCE_ASSETS_DIR / "images" / "illustration-tight.svg"
VIMEO_THUMBNAIL_CACHE = REPO_ROOT / "vimeo-thumbnails.json"

WORK_CATEGORIES = ("films", "commercials")
ROOT_SECTION_ORDER = ("about", "works", "contact")
SECTION_ORDER = ("trailer", "note", "highlight", "bts")
STATIC_ASSET_DIRS = ("css", "images", "js")
IGNORED_NAMES = {".DS_Store"}
IMAGE_EXTENSIONS = {".avif", ".gif", ".jpeg", ".jpg", ".png", ".webp"}
VIDEO_EXTENSIONS = {".mp4"}
WEB_IMAGE_EXTENSION = ".webp"
GRID_SPANS_BY_ROW_SIZE = {
    1: ((12,),),
    2: ((7, 5), (5, 7), (8, 4), (4, 8)),
    3: ((3, 5, 4), (4, 5, 3), (5, 4, 3), (3, 4, 5), (4, 3, 5), (5, 3, 4)),
}


class PageGenerationError(Exception):
    """Raised when source content cannot be converted into a page."""


@dataclass(frozen=True)
class MediaItem:
    index: int
    path: Path
    kind: str


@dataclass(frozen=True)
class NoteContent:
    title_html: str
    body_html: str


@dataclass(frozen=True)
class WorkContent:
    slug: str
    title: str
    trailer_embed_url: str
    trailer_poster_url: str | None
    note: NoteContent
    note_media: MediaItem
    highlight_media: tuple[MediaItem, ...]
    bts_text_html: str
    bts_media: tuple[MediaItem, ...]
    category: str = ""


def html_escape(value: str) -> str:
    return html.escape(value, quote=True)


def title_from_slug(slug: str) -> str:
    return " ".join(part.capitalize() for part in slug.split("-") if part)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise PageGenerationError(f"Missing required file: {path}") from exc


def non_empty_lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def read_first_non_empty_line(path: Path) -> str:
    lines = non_empty_lines(read_text(path))
    if not lines:
        raise PageGenerationError(f"{path} must contain one non-empty line")
    return lines[0]


def read_inline_svg(path: Path) -> str:
    svg = read_text(path).strip()
    return re.sub(r"^<\?xml[^>]+\?>\s*", "", svg)


def apply_inline_markdown(value: str) -> str:
    """Apply the small Markdown subset supported by editable-content text files."""
    escaped = html_escape(value)

    def link_repl(match: re.Match[str]) -> str:
        label = match.group(1)
        url = match.group(2)
        return f'<a href="{url}">{label}</a>'

    escaped = re.sub(
        r"\[([^\]\n]+)\]\((https?://[^)\s]+)\)",
        link_repl,
        escaped,
    )
    escaped = re.sub(r"\*\*([^*\n]+)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<em>\1</em>", escaped)
    return escaped


def render_markdown_lines(lines: Iterable[str]) -> str:
    trimmed = list(lines)
    while trimmed and not trimmed[0].strip():
        trimmed.pop(0)
    while trimmed and not trimmed[-1].strip():
        trimmed.pop()
    return "<br>".join(apply_inline_markdown(line.strip()) for line in trimmed)


def parse_note_text(path: Path) -> NoteContent:
    lines = read_text(path).splitlines()

    title_index = None
    title = None
    for index, line in enumerate(lines):
        if line.strip().startswith("# "):
            title_index = index
            title = line.strip()[2:].strip()
            break

    if title_index is None or not title:
        raise PageGenerationError(f"{path} must start its title with '# '")

    body_lines = lines[title_index + 1 :]
    body_html = render_markdown_lines(body_lines)
    if not body_html:
        raise PageGenerationError(f"{path} must include body text after the heading")

    return NoteContent(
        title_html=render_markdown_lines([title]),
        body_html=body_html,
    )


def parse_vimeo_url(raw_url: str) -> tuple[str, str | None]:
    url = raw_url.strip()
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise PageGenerationError(f"Vimeo URL must start with http:// or https://: {raw_url}")

    host = parsed.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    if host not in {"vimeo.com", "player.vimeo.com"}:
        raise PageGenerationError(f"Unsupported Vimeo host in URL: {raw_url}")

    parts = [part for part in parsed.path.split("/") if part]
    video_id = None
    hash_value = None

    for index, part in enumerate(parts):
        if part.isdigit():
            video_id = part
            if index + 1 < len(parts):
                hash_value = parts[index + 1]
            break

    if not video_id:
        raise PageGenerationError(f"Could not find Vimeo numeric video ID in URL: {raw_url}")

    query_hash = parse_qs(parsed.query).get("h")
    if query_hash:
        hash_value = query_hash[0]

    return video_id, hash_value


def vimeo_public_url(raw_url: str) -> str:
    video_id, hash_value = parse_vimeo_url(raw_url)
    if hash_value:
        return f"https://vimeo.com/{video_id}/{hash_value}"
    return f"https://vimeo.com/{video_id}"


def vimeo_embed_url(raw_url: str) -> str:
    video_id, hash_value = parse_vimeo_url(raw_url)
    params = [
        ("autoplay", "1"),
        ("badge", "0"),
        ("autopause", "0"),
        ("player_id", "0"),
        ("app_id", "58479"),
    ]
    if hash_value:
        params.insert(0, ("h", hash_value))
    return f"https://player.vimeo.com/video/{video_id}?{urlencode(params)}"


def read_vimeo_thumbnail_cache(path: Path = VIMEO_THUMBNAIL_CACHE) -> dict[str, str]:
    if not path.exists():
        return {}

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PageGenerationError(f"Invalid Vimeo thumbnail cache JSON: {path}") from exc

    if not isinstance(payload, dict):
        raise PageGenerationError(f"Vimeo thumbnail cache must be a JSON object: {path}")

    cache: dict[str, str] = {}
    for key, value in payload.items():
        if not isinstance(key, str) or not isinstance(value, str) or not value.strip():
            raise PageGenerationError(
                f"Vimeo thumbnail cache entries must be non-empty strings: {path}"
            )
        cache[key] = value
    return cache


def write_vimeo_thumbnail_cache(
    cache: dict[str, str],
    path: Path = VIMEO_THUMBNAIL_CACHE,
) -> None:
    path.write_text(
        json.dumps(dict(sorted(cache.items())), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    try:
        display_path = path.relative_to(REPO_ROOT)
    except ValueError:
        display_path = path
    print(f"updated {display_path}")


def fetch_vimeo_thumbnail_url(public_url: str) -> str | None:
    endpoint = "https://vimeo.com/api/oembed.json?" + urlencode(
        {"url": public_url, "width": "1280"}
    )
    request = Request(endpoint, headers={"User-Agent": "raehu-page-generator/1.0"})

    try:
        with urlopen(request, timeout=10) as response:
            payload = response.read().decode("utf-8")
    except (HTTPError, URLError, TimeoutError, OSError):
        return None

    match = re.search(r'"thumbnail_url"\s*:\s*"([^"]+)"', payload)
    if not match:
        return None

    return match.group(1).replace("\\/", "/")


def vimeo_thumbnail_url(
    raw_url: str,
    cache: dict[str, str] | None = None,
    allow_fetch: bool = True,
) -> str | None:
    public_url = vimeo_public_url(raw_url)
    if cache is not None and public_url in cache:
        return cache[public_url]

    if not allow_fetch:
        return None

    thumbnail_url = fetch_vimeo_thumbnail_url(public_url)
    if thumbnail_url and cache is not None:
        cache[public_url] = thumbnail_url
    return thumbnail_url


def media_kind(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in IMAGE_EXTENSIONS:
        return "image"
    if suffix in VIDEO_EXTENSIONS:
        return "video"
    raise PageGenerationError(f"Unsupported media type: {path}")


def converted_image_path(path: Path) -> Path:
    return path.with_suffix(WEB_IMAGE_EXTENSION)


def needs_conversion(source: Path, target: Path) -> bool:
    if not target.exists():
        return True
    return source.stat().st_mtime_ns > target.stat().st_mtime_ns


def convert_image_to_webp(source: Path, target: Path) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise PageGenerationError(
            "ffmpeg is required to convert source images to WebP. "
            "Install ffmpeg or provide .webp files directly."
        )

    target.parent.mkdir(parents=True, exist_ok=True)
    command = [
        ffmpeg,
        "-y",
        "-loglevel",
        "error",
        "-i",
        str(source),
        "-vf",
        r"scale=w=min(1920\,iw):h=-2",
        "-c:v",
        "libwebp",
        "-quality",
        "82",
        "-compression_level",
        "6",
        str(target),
    ]
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as exc:
        raise PageGenerationError(f"ffmpeg failed to convert {source} to {target}") from exc


def canonical_media_path(path: Path, write_assets: bool) -> Path:
    kind = media_kind(path)
    if kind != "image":
        return path

    target = converted_image_path(path)
    if path.suffix.lower() == WEB_IMAGE_EXTENSION:
        return path

    if needs_conversion(path, target):
        if not write_assets:
            raise PageGenerationError(
                f"Converted WebP is missing or stale for {path}. "
                "Run python3 scripts/generate_pages.py."
            )
        convert_image_to_webp(path, target)
    return target


def media_index(path: Path) -> int:
    match = re.match(r"^(\d+)_", path.name)
    if not match:
        raise PageGenerationError(f"Media file must start with NUMBER_: {path}")
    return int(match.group(1))


def ordered_media(media_dir: Path, write_assets: bool = False) -> tuple[MediaItem, ...]:
    if not media_dir.is_dir():
        raise PageGenerationError(f"Missing required media folder: {media_dir}")

    media: list[MediaItem] = []
    seen_indexes: dict[int, Path] = {}
    seen_paths: set[Path] = set()
    for path in media_dir.iterdir():
        if path.name in IGNORED_NAMES or path.name.startswith("."):
            continue
        if not path.is_file():
            continue
        index = media_index(path)
        canonical_path = canonical_media_path(path, write_assets=write_assets)
        if canonical_path in seen_paths:
            continue
        if index in seen_indexes:
            raise PageGenerationError(
                f"Duplicate media number {index}: {seen_indexes[index]} and {canonical_path}"
            )
        seen_indexes[index] = canonical_path
        seen_paths.add(canonical_path)
        media.append(
            MediaItem(
                index=index,
                path=canonical_path,
                kind=media_kind(canonical_path),
            )
        )

    if not media:
        raise PageGenerationError(f"No media found in: {media_dir}")

    return tuple(sorted(media, key=lambda item: item.index))


def output_relative_url(output_html: Path, target: Path) -> str:
    relative_path = os.path.relpath(target, start=output_html.parent)
    return "/".join(quote(part) for part in Path(relative_path).parts)


def generated_site_relative_url(output_html: Path, *parts: str) -> str:
    return output_relative_url(output_html, GENERATED_WEBSITE_DIR.joinpath(*parts))


def work_output_html(work: WorkContent) -> Path:
    return WORKS_OUTPUT_DIR / work.slug / "index.html"


def work_public_url_from(output_html: Path, work: WorkContent) -> str:
    href = output_relative_url(output_html, work_output_html(work).parent)
    return href if href.endswith("/") else f"{href}/"


def root_index_url_from(output_html: Path) -> str:
    href = output_relative_url(output_html, GENERATED_WEBSITE_DIR)
    if href in {"", "."}:
        return "./"
    return href if href.endswith("/") else f"{href}/"


def root_works_url_from(output_html: Path) -> str:
    return root_index_url_from(output_html) + "#works"


def media_tag(
    item: MediaItem,
    output_html: Path,
    alt: str,
    class_name: str | None = None,
    active: bool = False,
) -> str:
    src = output_relative_url(output_html, item.path)
    class_attr = ""
    if class_name:
        classes = class_name + (" is-active" if active else "")
        class_attr = f' class="{classes}"'

    if item.kind == "image":
        return f'<img{class_attr} src="{src}" alt="{html_escape(alt)}">'
    return f'<video{class_attr} src="{src}" muted playsinline autoplay loop></video>'


def valid_started_work(work_dir: Path) -> bool:
    for path in work_dir.rglob("*"):
        if path.is_file() and path.name not in IGNORED_NAMES and not path.name.startswith("."):
            return True
    return False


def load_work(
    work_dir: Path,
    write_assets: bool = False,
    vimeo_thumbnail_cache: dict[str, str] | None = None,
    fetch_vimeo_thumbnails: bool = True,
) -> WorkContent:
    slug = work_dir.name
    trailer_link = read_first_non_empty_line(work_dir / "trailer" / "trailer_link.md")
    note = parse_note_text(work_dir / "note" / "text.md")
    note_media = ordered_media(work_dir / "note" / "media", write_assets=write_assets)
    highlight_media = ordered_media(work_dir / "highlight" / "media", write_assets=write_assets)
    bts_text = read_text(work_dir / "bts" / "text.md")
    bts_text_html = render_markdown_lines(bts_text.splitlines())
    bts_media = ordered_media(work_dir / "bts" / "media", write_assets=write_assets)

    if len(note_media) != 1:
        raise PageGenerationError(
            f"{work_dir / 'note' / 'media'} must contain exactly one media item"
        )
    if not bts_text_html:
        raise PageGenerationError(f"{work_dir / 'bts' / 'text.md'} must not be empty")

    return WorkContent(
        slug=slug,
        title=title_from_slug(slug),
        trailer_embed_url=vimeo_embed_url(trailer_link),
        trailer_poster_url=vimeo_thumbnail_url(
            trailer_link,
            cache=vimeo_thumbnail_cache,
            allow_fetch=fetch_vimeo_thumbnails,
        ),
        note=note,
        note_media=note_media[0],
        highlight_media=highlight_media,
        bts_text_html=bts_text_html,
        bts_media=bts_media,
        category=work_dir.parent.name,
    )


def render_tracker_links(sections: Iterable[str]) -> str:
    lines: list[str] = []
    for index, section in enumerate(sections):
        current = ' aria-current="true"' if index == 0 else ""
        lines.append(
            f'    <a href="#{section}" data-section-link="{section}"{current}>\n'
            '      <span class="red-dot section-tracker-dot" aria-hidden="true"></span>\n'
            f"      <span>{section}</span>\n"
            "    </a>"
        )
    return "\n".join(lines)


def render_work_category_links(categories: Iterable[str]) -> str:
    lines: list[str] = []
    for category in categories:
        lines.append(
            f'        <a href="#{category}" data-work-category-link="{category}">\n'
            '          <span class="red-dot section-tracker-dot" aria-hidden="true"></span>\n'
            f"          <span>{category}</span>\n"
            "        </a>"
        )
    return "\n".join(lines)


def category_label(category: str) -> str:
    return category.replace("-", " ")


class StableRng:
    """Small deterministic PRNG so grid layouts do not depend on Python random."""

    def __init__(self, seed: int) -> None:
        self.state = seed & 0xFFFFFFFF

    def random(self) -> float:
        self.state = (self.state + 0x6D2B79F5) & 0xFFFFFFFF
        value = self.state
        value = (value ^ (value >> 15)) * (1 | value)
        value &= 0xFFFFFFFF
        value ^= (value + ((value ^ (value >> 7)) * (61 | value))) & 0xFFFFFFFF
        value &= 0xFFFFFFFF
        return ((value ^ (value >> 14)) & 0xFFFFFFFF) / 4294967296

    def choice(self, values):
        if not values:
            raise ValueError("cannot choose from an empty tuple")
        return values[int(self.random() * len(values))]


def stable_seed(value: str) -> int:
    digest = hashlib.sha256(value.encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "big")


def row_size_patterns(count: int) -> tuple[tuple[int, ...], ...]:
    if count <= 0:
        return ()
    if count == 1:
        return ((1,),)

    patterns: list[tuple[int, ...]] = []

    def collect(remaining: int, rows: tuple[int, ...]) -> None:
        if remaining == 0:
            patterns.append(rows)
            return
        for row_size in (2, 3):
            if remaining >= row_size:
                collect(remaining - row_size, rows + (row_size,))

    collect(count, ())
    return tuple(patterns)


def highlight_grid_layout(count: int, layout_key: str) -> str:
    patterns = row_size_patterns(count)
    if not patterns:
        return ""

    rng = StableRng(stable_seed(f"highlight-grid:{layout_key}:{count}"))
    row_sizes = rng.choice(patterns)
    rows: list[tuple[int, ...]] = []
    previous: tuple[int, ...] | None = None

    for row_size in row_sizes:
        span_pool = GRID_SPANS_BY_ROW_SIZE[row_size]
        choices = tuple(spans for spans in span_pool if spans != previous) or span_pool
        spans = rng.choice(choices)
        rows.append(spans)
        previous = spans

    return ", ".join("-".join(str(span) for span in row) for row in rows)


def render_trailer_section(work: WorkContent) -> str:
    if work.trailer_poster_url:
        poster_html = (
            f'<img class="trailer-poster" '
            f'src="{html_escape(work.trailer_poster_url)}" '
            f'alt="{html_escape(work.title)} trailer">'
        )
    else:
        poster_html = '<div class="trailer-poster trailer-poster--placeholder" aria-hidden="true"></div>'

    return f"""    <section class="work-page work-page--trailer"
             id="trailer"
             data-section-page="trailer"
             data-section-title="Trailer"
             data-page-padding
             aria-label="Trailer">
      <div class="trailer-wrap"
           id="trailer-player"
           data-vimeo-embed="{html_escape(work.trailer_embed_url)}">
        {poster_html}
        <button class="trailer-play" aria-label="Play trailer">
          <svg viewBox="0 0 68 48" width="68" height="48"><path d="M66.5 7.7c-.8-2.9-2.5-5.4-5.4-6.2C55.8.1 34 0 34 0S12.2.1 6.9 1.5c-2.9.8-4.6 3.3-5.4 6.2C.1 13 0 24 0 24s.1 11 1.5 16.3c.8 2.9 2.5 5.4 5.4 6.2C12.2 47.9 34 48 34 48s21.8-.1 27.1-1.5c2.9-.8 4.6-3.3 5.4-6.2C67.9 35 68 24 68 24s-.1-11-1.5-16.3z" fill="rgba(255,255,255,0.85)"/><path d="M45 24L27 14v20z" fill="#0a0a0a"/></svg>
        </button>
      </div>
    </section>"""


def render_note_section(work: WorkContent, output_html: Path) -> str:
    media_html = media_tag(work.note_media, output_html, work.title, class_name="work-header-image")
    return f"""    <section class="work-page work-page--note"
             id="note"
             data-section-page="note"
             data-section-title="Note"
             data-page-padding
             aria-label="Director's note">
      <div class="work-header">
        <div class="work-header-text">
          <h1 class="work-title">{work.note.title_html}</h1>
          <p class="work-subtext">{work.note.body_html}</p>
          <div class="work-label"><div class="red-dot"></div> Director's note</div>
        </div>
        <div class="work-header-image-wrap">
          {media_html}
        </div>
      </div>
    </section>"""


def render_highlight_section(work: WorkContent, output_html: Path) -> str:
    media_lines = [
        "        " + render_highlight_tile(item, output_html, work.title)
        for item in work.highlight_media
    ]
    media_html = "\n".join(media_lines)
    layout = highlight_grid_layout(
        len(work.highlight_media),
        f"{work.category}/{work.slug}",
    )
    return f"""    <section class="work-page work-page--highlight"
             id="highlight"
             data-section-page="highlight"
             data-section-title="Highlight"
             data-page-padding
             aria-label="Highlight">
      <div class="grid-wrapper">
        <div class="portfolio-grid" data-layout="{html_escape(layout)}">
{media_html}
        </div>
      </div>
    </section>"""


def render_highlight_tile(item: MediaItem, output_html: Path, title: str) -> str:
    media_html = media_tag(
        item,
        output_html,
        f"{title} highlight",
        class_name="highlight-media media-hover-zoom-target",
    )
    return f"""<figure class="highlight-tile media-hover-zoom" data-highlight-tile>
          {media_html}
          <button class="highlight-expand-button"
                  type="button"
                  data-highlight-expand
                  aria-label="Expand highlight media">
            <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
              <path class="interactive-chevron interactive-chevron--expand-ne" d="M14 4h6v6"></path>
              <path class="interactive-chevron interactive-chevron--expand-sw" d="M10 20H4v-6"></path>
            </svg>
          </button>
        </figure>"""


def render_bts_section(work: WorkContent, output_html: Path) -> str:
    slide_lines = [
        "          "
        + media_tag(
            item,
            output_html,
            f"{work.title} behind the scenes",
            class_name="bts-slide",
            active=index == 0,
        )
        for index, item in enumerate(work.bts_media)
    ]
    controls = ""
    if len(work.bts_media) > 1:
        controls = """
          <button class="bts-slide-control bts-slide-control--prev"
                  type="button"
                  data-bts-slide-control="prev"
                  aria-label="Previous BTS image">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path class="interactive-chevron interactive-chevron--left" d="M15 18l-6-6 6-6"></path>
            </svg>
          </button>
          <button class="bts-slide-control bts-slide-control--next"
                  type="button"
                  data-bts-slide-control="next"
                  aria-label="Next BTS image">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path class="interactive-chevron interactive-chevron--right" d="M9 6l6 6-6 6"></path>
            </svg>
          </button>"""

    return f"""    <section class="work-page work-page--bts"
             id="bts"
             data-section-page="bts"
             data-section-title="BTS"
             data-page-padding
             aria-label="Behind the scenes">
      <div class="bts-layout">
        <div class="bts-slideshow" aria-label="Behind the scenes slideshow">
{chr(10).join(slide_lines)}{controls}
        </div>

        <div class="bts-copy">
          <p class="bts-text">{work.bts_text_html}</p>
        </div>
      </div>
    </section>"""


def render_work(work: WorkContent, template: str, output_html: Path) -> str:
    sections = [
        render_trailer_section(work),
        render_note_section(work, output_html),
        render_highlight_section(work, output_html),
        render_bts_section(work, output_html),
    ]

    replacements = {
        "{{DOCUMENT_TITLE}}": html_escape(work.title),
        "{{WORK_SLUG}}": html_escape(work.slug),
        "{{WORK_CATEGORY}}": html_escape(work.category),
        "{{ROOT_INDEX_URL}}": root_index_url_from(output_html),
        "{{WORKS_INDEX_URL}}": root_works_url_from(output_html),
        "{{SHARED_EFFECTS_CSS_URL}}": generated_site_relative_url(
            output_html,
            "css",
            "shared-effects.css",
        ),
        "{{PORTFOLIO_GRID_JS_URL}}": generated_site_relative_url(
            output_html,
            "js",
            "portfolio-grid.js",
        ),
        "{{SECTION_TRACKER_LINKS}}": render_tracker_links(SECTION_ORDER),
        "{{WORK_SECTIONS}}": "\n\n".join(sections),
    }

    rendered = template
    for placeholder, value in replacements.items():
        rendered = rendered.replace(placeholder, value)
    return rendered


def render_works_index_grid_item(work: WorkContent, output_html: Path) -> str:
    href = work_public_url_from(output_html, work)
    if work.trailer_poster_url:
        poster_src = html_escape(work.trailer_poster_url)
    else:
        poster_src = output_relative_url(output_html, work.note_media.path)

    title = html_escape(work.title)
    return f"""        <a class="works-grid-link media-hover-zoom" href="{href}" aria-label="{title}">
          <img class="media-hover-zoom-target" src="{poster_src}" alt="{title} trailer preview" loading="lazy" decoding="async">
          <span class="works-grid-title">
            <span class="works-grid-title-text">{title}</span>
            <span class="works-grid-title-chevron interactive-chevron interactive-chevron--right" aria-hidden="true">&gt;</span>
          </span>
        </a>"""


def render_works_index_section(
    category: str,
    works: tuple[WorkContent, ...],
    output_html: Path,
) -> str:
    grid_items = "\n".join(
        render_works_index_grid_item(work, output_html)
        for work in works
    )
    empty = ""
    if not grid_items:
        empty = '        <p class="works-index-empty">Coming soon.</p>'

    return f"""    <section class="works-index-page"
             id="{html_escape(category)}"
             data-work-category-section="{html_escape(category)}"
             data-section-title="{html_escape(category_label(category))}"
             aria-label="{html_escape(category_label(category))}">
      <div class="works-index-grid-wrap">
        <div class="portfolio-grid works-index-grid" data-seed="{len(category)}">
{grid_items or empty}
        </div>
      </div>
    </section>"""


def render_home(works: tuple[WorkContent, ...], template: str, output_html: Path) -> str:
    works_by_category = {
        category: tuple(work for work in works if work.category == category)
        for category in WORK_CATEGORIES
    }
    sections = [
        render_works_index_section(category, works_by_category[category], output_html)
        for category in WORK_CATEGORIES
    ]

    replacements = {
        "{{HERO_ILLUSTRATION_SVG}}": read_inline_svg(HERO_ILLUSTRATION),
        "{{SHARED_EFFECTS_CSS_URL}}": generated_site_relative_url(
            output_html,
            "css",
            "shared-effects.css",
        ),
        "{{PORTFOLIO_GRID_JS_URL}}": generated_site_relative_url(
            output_html,
            "js",
            "portfolio-grid.js",
        ),
        "{{ROOT_SECTION_TRACKER_LINKS}}": render_tracker_links(ROOT_SECTION_ORDER),
        "{{WORK_CATEGORY_TRACKER_LINKS}}": render_work_category_links(WORK_CATEGORIES),
        "{{WORKS_INDEX_SECTIONS}}": "\n\n".join(sections),
    }

    rendered = template
    for placeholder, value in replacements.items():
        rendered = rendered.replace(placeholder, value)
    return rendered


def render_works_redirect(template: str, output_html: Path) -> str:
    replacements = {
        "{{ROOT_WORKS_URL}}": root_works_url_from(output_html),
    }

    rendered = template
    for placeholder, value in replacements.items():
        rendered = rendered.replace(placeholder, value)
    return rendered


def write_or_check(output_html: Path, rendered: str, check: bool) -> int:
    if check:
        current = output_html.read_text(encoding="utf-8") if output_html.exists() else ""
        if current != rendered:
            diff = difflib.unified_diff(
                current.splitlines(),
                rendered.splitlines(),
                fromfile=str(output_html),
                tofile=f"generated:{output_html}",
                lineterm="",
            )
            print(
                f"Generated page is out of date: {output_html}",
                file=sys.stderr,
            )
            print("\n".join(diff), file=sys.stderr)
            return 1
        return 0

    output_html.parent.mkdir(parents=True, exist_ok=True)
    output_html.write_text(rendered, encoding="utf-8")
    print(f"generated {output_html.relative_to(REPO_ROOT)}")
    return 0


def visible_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file()
        and path.name not in IGNORED_NAMES
        and not path.name.startswith(".")
    )


def sync_static_assets(check: bool) -> int:
    failures = 0
    for dirname in STATIC_ASSET_DIRS:
        source_dir = SITE_SOURCE_ASSETS_DIR / dirname
        output_dir = GENERATED_WEBSITE_DIR / dirname

        if check:
            source_files = {
                path.relative_to(source_dir): path.read_bytes()
                for path in visible_files(source_dir)
            }
            output_files = {
                path.relative_to(output_dir): path.read_bytes()
                for path in visible_files(output_dir)
            }
            if source_files != output_files:
                print(
                    f"Generated static assets are out of date: {output_dir}",
                    file=sys.stderr,
                )
                failures += 1
            continue

        if output_dir.exists():
            shutil.rmtree(output_dir)
        if source_dir.exists():
            shutil.copytree(source_dir, output_dir)
            print(f"synced {output_dir.relative_to(REPO_ROOT)}")

    return failures


def discover_work_dirs(editable_works_dir: Path, selected_slug: str | None = None) -> list[Path]:
    if not editable_works_dir.is_dir():
        raise PageGenerationError(f"Missing editable works folder: {editable_works_dir}")

    work_dirs = []
    seen_slugs: dict[str, Path] = {}
    for category in WORK_CATEGORIES:
        category_dir = editable_works_dir / category
        if not category_dir.is_dir():
            continue
        for work_dir in sorted(path for path in category_dir.iterdir() if path.is_dir()):
            if work_dir.name.startswith("."):
                continue
            if selected_slug and work_dir.name != selected_slug:
                continue
            if not valid_started_work(work_dir):
                continue
            existing = seen_slugs.get(work_dir.name)
            if existing:
                raise PageGenerationError(
                    f"Duplicate work slug '{work_dir.name}' in {existing} and {work_dir}"
                )
            seen_slugs[work_dir.name] = work_dir
            work_dirs.append(work_dir)
    return work_dirs


def generate(check: bool = False, selected_slug: str | None = None) -> int:
    work_template = read_text(WORK_PAGE_TEMPLATE)
    work_dirs = discover_work_dirs(EDITABLE_WORKS_DIR, selected_slug)
    if selected_slug and not work_dirs:
        raise PageGenerationError(f"No valid started work found for slug: {selected_slug}")

    failures = sync_static_assets(check)
    works: list[WorkContent] = []
    vimeo_thumbnail_cache = read_vimeo_thumbnail_cache()
    original_vimeo_thumbnail_cache = dict(vimeo_thumbnail_cache)
    for work_dir in work_dirs:
        work = load_work(
            work_dir,
            write_assets=not check,
            vimeo_thumbnail_cache=vimeo_thumbnail_cache,
            fetch_vimeo_thumbnails=not check,
        )
        works.append(work)
        output_html = work_output_html(work)
        rendered = render_work(work, work_template, output_html)
        failures += write_or_check(output_html, rendered, check)

    if not selected_slug:
        home_template = read_text(HOME_TEMPLATE)
        home_rendered = render_home(tuple(works), home_template, HOME_OUTPUT_HTML)
        failures += write_or_check(HOME_OUTPUT_HTML, home_rendered, check)

        works_redirect_template = read_text(WORKS_REDIRECT_TEMPLATE)
        works_redirect_html = WORKS_OUTPUT_DIR / "index.html"
        works_redirect_rendered = render_works_redirect(
            works_redirect_template,
            works_redirect_html,
        )
        failures += write_or_check(works_redirect_html, works_redirect_rendered, check)

    if not check and vimeo_thumbnail_cache != original_vimeo_thumbnail_cache:
        write_vimeo_thumbnail_cache(vimeo_thumbnail_cache)

    return failures


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail if generated HTML differs from committed output",
    )
    parser.add_argument(
        "--work",
        metavar="SLUG",
        help="generate/check only one work slug",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        failures = generate(check=args.check, selected_slug=args.work)
    except PageGenerationError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
