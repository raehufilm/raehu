#!/usr/bin/env python3
"""Generate static pages from the editable-content source tree.

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
from typing import Callable, Iterable, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, quote, urlencode, urlparse
from urllib.request import Request, urlopen


REPO_ROOT = Path(__file__).resolve().parents[1]
EDITABLE_CONTENT_DIR = REPO_ROOT / "editable-content"
EDITABLE_ABOUT_DIR = EDITABLE_CONTENT_DIR / "about"
EDITABLE_ABOUT_TEXT = EDITABLE_ABOUT_DIR / "text.md"
EDITABLE_ABOUT_QUOTE = EDITABLE_ABOUT_DIR / "quote.md"
EDITABLE_WORK_DIR = EDITABLE_CONTENT_DIR / "work"
GENERATED_WEBSITE_DIR = REPO_ROOT / "generated-website"
HOME_OUTPUT_HTML = GENERATED_WEBSITE_DIR / "index.html"
GENERATOR_TEMPLATES_DIR = REPO_ROOT / "generator-templates"
WORK_PAGE_TEMPLATE = GENERATOR_TEMPLATES_DIR / "work-page.html"
HOME_TEMPLATE = GENERATOR_TEMPLATES_DIR / "index.html"
SITE_SOURCE_ASSETS_DIR = REPO_ROOT / "site-source-assets"
HERO_ILLUSTRATION = SITE_SOURCE_ASSETS_DIR / "images" / "illustration-tight.svg"
FAVICON = SITE_SOURCE_ASSETS_DIR / "images" / "favicon.svg"
VIMEO_THUMBNAIL_CACHE = REPO_ROOT / "vimeo-thumbnails.json"

WORK_CATEGORIES = ("films", "commercials")
ROOT_WORK_SECTION = "work"
ROOT_SECTION_ORDER = ("about", ROOT_WORK_SECTION)
PRIMARY_SECTION_BY_CATEGORY = {
    "films": "trailer",
    "commercials": "film",
}
PRIMARY_LINK_FILE_BY_SECTION = {
    "trailer": "trailer_link.md",
    "film": "film_link.md",
}
COMMON_WORK_SECTION_ORDER = ("note", "highlight", "bts")
STATIC_ASSET_DIRS = ("css", "images", "js")
IGNORED_NAMES = {".DS_Store"}
IMAGE_EXTENSIONS = {".avif", ".gif", ".heic", ".jpeg", ".jpg", ".png", ".webp"}
VIDEO_EXTENSIONS = {".mp4"}
WEB_IMAGE_EXTENSION = ".webp"
RESPONSIVE_IMAGE_WIDTHS = (480, 960, 1440, 1920)
GRID_PREVIEW_VIDEO_EXTENSION = ".mp4"
GRID_PREVIEW_VIDEO_VERSION = "v3"
GRID_PREVIEW_VIDEO_DURATION_SECONDS = 6
GRID_PREVIEW_VIDEO_MAX_WIDTH = 720
GRID_PREVIEW_VIDEO_BITRATE = "1200k"
GRID_PREVIEW_VIDEO_MAXRATE = "1400k"
GRID_PREVIEW_VIDEO_BUFSIZE = "2400k"
HIGHLIGHT_TILE_VIDEO_EXTENSION = ".mp4"
HIGHLIGHT_TILE_VIDEO_VERSION = "v1"
HIGHLIGHT_TILE_VIDEO_WIDTHS = (480, 720)
HIGHLIGHT_TILE_VIDEO_BITRATES = {
    480: "700k",
    720: "1400k",
}
HIGHLIGHT_TILE_VIDEO_MAXRATES = {
    480: "900k",
    720: "1800k",
}
HIGHLIGHT_TILE_VIDEO_BUFSIZES = {
    480: "1400k",
    720: "2800k",
}
GRID_SPANS_BY_ROW_SIZE = {
    1: ((12,),),
    2: ((7, 5), (5, 7), (8, 4), (4, 8)),
    3: ((3, 5, 4), (4, 5, 3), (5, 4, 3), (3, 4, 5), (4, 3, 5), (5, 3, 4)),
}
CHINESE_NAV_LABELS = {
    "about": "关于",
    "work": "作品",
    "films": "电影",
    "commercials": "广告",
    "film": "影片",
    "trailer": "预告片",
    "note": "手记",
    "highlight": "精选",
    "bts": "幕后",
}
SPANISH_NAV_LABELS = {
    "about": "sobre",
    "work": "obra",
    "films": "películas",
    "commercials": "anuncios",
    "film": "cine",
    "trailer": "trailer",
    "note": "apuntes",
    "highlight": "destacados",
    "bts": "bts",
}
TRANSLATED_LANGUAGE_SUFFIXES = {
    "cn": "chinese",
    "es": "spanish",
}


class PageGenerationError(Exception):
    """Raised when source content cannot be converted into a page."""


@dataclass(frozen=True)
class MediaItem:
    index: int
    path: Path
    kind: str
    width: int | None = None
    height: int | None = None


@dataclass(frozen=True)
class PrimaryLink:
    label: str
    href: str


@dataclass(frozen=True)
class NoteContent:
    title_html: str
    body_html: str
    index: int = 1
    title_html_chinese: str | None = None
    body_html_chinese: str | None = None
    title_html_spanish: str | None = None
    body_html_spanish: str | None = None


@dataclass(frozen=True)
class WorkContent:
    slug: str
    title: str
    trailer_embed_url: str | None
    trailer_poster_url: str | None
    note: NoteContent | None
    note_media: MediaItem | None
    highlight_media: tuple[MediaItem, ...]
    bts_text_html: str | None
    bts_media: tuple[MediaItem, ...]
    category: str = ""
    trailer_media: MediaItem | None = None
    grid_preview_media: MediaItem | None = None
    grid_display_media: MediaItem | None = None
    primary_links: tuple[PrimaryLink, ...] = ()
    bts_text_html_chinese: str | None = None
    bts_text_html_spanish: str | None = None


@dataclass(frozen=True)
class AboutContent:
    title_html: str
    body_html: str
    contact_html: str
    title_html_chinese: str
    body_html_chinese: str
    contact_html_chinese: str
    title_html_spanish: str
    body_html_spanish: str
    contact_html_spanish: str
    image_html: str
    quote_html: str


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


def read_optional_first_non_empty_line(path: Path) -> str | None:
    if not path.exists():
        return None
    lines = non_empty_lines(read_text(path))
    return lines[0] if lines else None


def alternate_language_path(path: Path, language: str) -> Path:
    return path.with_name(f"{path.stem}_{language}{path.suffix}")


def is_alternate_language_path(path: Path) -> bool:
    return any(
        path.stem.endswith(f"_{suffix}")
        for suffix in TRANSLATED_LANGUAGE_SUFFIXES.values()
    )


def primary_section_for_category(category: str) -> str:
    return PRIMARY_SECTION_BY_CATEGORY.get(category, "trailer")


def primary_link_file_for_section(section_name: str) -> str:
    return PRIMARY_LINK_FILE_BY_SECTION.get(section_name, f"{section_name}_link.md")


def has_note_section(work: WorkContent) -> bool:
    return work.note is not None or work.note_media is not None


def has_bts_section(work: WorkContent) -> bool:
    return work.bts_text_html is not None or len(work.bts_media) > 0


def work_section_order(work: WorkContent) -> tuple[str, ...]:
    sections = [primary_section_for_category(work.category)]
    if has_note_section(work):
        sections.append("note")
    sections.append("highlight")
    if has_bts_section(work):
        sections.append("bts")
    return tuple(sections)


def load_primary_links(path: Path) -> tuple[PrimaryLink, ...]:
    if not path.exists():
        return ()

    links: list[PrimaryLink] = []
    for line_number, raw_line in enumerate(read_text(path).splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        match = re.fullmatch(r"\[([^\]\n]+)\]\(([^)\n]+)\)", line)
        if not match:
            raise PageGenerationError(
                f"{path} line {line_number} must use Markdown link format like "
                "[view full film](https://vimeo.com/123456789)."
            )
        label = match.group(1).strip()
        href = match.group(2).strip()
        if not label or not href:
            raise PageGenerationError(
                f"{path} line {line_number} must include both link text and a URL."
            )
        links.append(PrimaryLink(label=label, href=href))
    return tuple(links)


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


def render_markdown_paragraphs(lines: Iterable[str]) -> str:
    paragraphs: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        if line.strip():
            current.append(line)
            continue
        if current:
            paragraphs.append(current)
            current = []
    if current:
        paragraphs.append(current)
    return "\n".join(f"            <p>{render_markdown_lines(paragraph)}</p>" for paragraph in paragraphs)


def contact_icon_svg(kind: str) -> str:
    if kind == "email":
        return """<svg class="about-contact-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false">
                  <path d="M4.75 6.75h14.5v10.5H4.75z" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"/>
                  <path d="m5.25 7.25 6.75 5.4 6.75-5.4" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>"""
    if kind == "vimeo":
        return """<svg class="about-contact-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false">
                  <path d="M4.25 8.25c1.25-1.05 2.25-1.57 3-1.57 1.15 0 1.9 0.72 2.25 2.16l1.25 5.18c0.22 0.86 0.53 1.29 0.94 1.29 0.48 0 1.12-0.58 1.93-1.74 0.8-1.16 1.23-2.08 1.29-2.78 0.07-0.78-0.23-1.17-0.88-1.17-0.4 0-0.87 0.1-1.41 0.31 0.95-2.83 2.59-4.2 4.92-4.1 1.72 0.06 2.5 1.16 2.34 3.31-0.16 2.03-1.64 4.72-4.45 8.08-1.96 2.34-3.64 3.51-5.03 3.51-1.29 0-2.2-1.18-2.72-3.55L6.43 11.8c-0.22-0.94-0.55-1.41-0.98-1.41-0.26 0-0.78 0.31-1.56 0.93L3 9.98l1.25-1.73Z" fill="currentColor"/>
                </svg>"""
    if kind == "instagram":
        return """<svg class="about-contact-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false">
                  <rect x="5" y="5" width="14" height="14" rx="4" fill="none" stroke="currentColor" stroke-width="1.7"/>
                  <circle cx="12" cy="12" r="3.2" fill="none" stroke="currentColor" stroke-width="1.7"/>
                  <circle cx="16.25" cy="7.75" r="0.95" fill="currentColor"/>
                </svg>"""
    if kind == "location":
        return """<svg class="about-contact-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false">
                  <path d="M12 20.25s6-5.63 6-10.25a6 6 0 0 0-12 0c0 4.62 6 10.25 6 10.25Z" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"/>
                  <circle cx="12" cy="10" r="2" fill="none" stroke="currentColor" stroke-width="1.7"/>
                </svg>"""
    raise PageGenerationError(f"Unsupported about contact kind: {kind}")


def contact_href(kind: str, value: str) -> str | None:
    if kind == "email":
        return f"mailto:{value}"
    if kind == "vimeo":
        return value if value.startswith(("http://", "https://")) else f"https://{value}"
    if kind == "instagram":
        return value if value.startswith(("http://", "https://")) else f"https://{value}"
    return None


def parse_note_text(path: Path, index: int = 1) -> NoteContent:
    lines = read_text(path).splitlines()

    title_index = None
    title = None
    for line_index, line in enumerate(lines):
        if line.strip().startswith("# "):
            title_index = line_index
            title = line.strip()[2:].strip()
            break

    if title_index is None or not title:
        raise PageGenerationError(f"{path} must start its title with '# '")

    body_lines = lines[title_index + 1 :]
    body_html = render_markdown_lines(body_lines)

    return NoteContent(
        title_html=render_markdown_lines([title]),
        body_html=body_html or "",
        index=index,
    )


def render_about_contact_line(kind: str, value: str) -> str:
    value_html = html_escape(value)
    icon = contact_icon_svg(kind)
    href = contact_href(kind, value)
    if href:
        target = ' target="_blank" rel="noreferrer"' if kind in {"vimeo", "instagram"} else ""
        return f"""              <div class="about-contact-item" role="listitem">
                <a href="{html_escape(href)}"{target} class="about-contact-link">
                  {icon}
                  <span>{value_html}</span>
                </a>
              </div>"""

    return f"""              <div class="about-contact-item" role="listitem">
                <span class="about-location">
                  {icon}
                  <span>{value_html}</span>
                </span>
              </div>"""


def parse_about_text(path: Path) -> tuple[str, str, str]:
    lines = read_text(path).splitlines()
    title = None
    body_start_index = None

    for line_index, line in enumerate(lines):
        stripped = line.strip()
        if title is None and stripped.startswith("# "):
            title = stripped[2:].strip()
            body_start_index = line_index + 1
            break

    if not title:
        raise PageGenerationError(f"{path} must include an about title starting with '# '")
    if body_start_index is None:
        raise PageGenerationError(f"{path} must include body paragraphs after the about title")

    body_lines: list[str] = []
    contact_rows: list[tuple[str, str]] = []
    contact_labels = {
        "Email": "email",
        "Vimeo": "vimeo",
        "Instagram": "instagram",
        "Location": "location",
    }

    for line in lines[body_start_index:]:
        stripped = line.strip()
        matched_contact = False
        for label, kind in contact_labels.items():
            prefix = f"{label}:"
            if stripped.startswith(prefix):
                value = stripped[len(prefix) :].strip()
                if not value:
                    raise PageGenerationError(f"{path} has an empty {label} contact line")
                contact_rows.append((kind, value))
                matched_contact = True
                break
        if not matched_contact:
            body_lines.append(line)

    body_html = render_markdown_paragraphs(body_lines)
    if not body_html:
        raise PageGenerationError(f"{path} must include body paragraphs after the about title")
    if not contact_rows:
        raise PageGenerationError(f"{path} must include Email, Vimeo, Instagram, or Location lines")

    contact_html = "\n".join(render_about_contact_line(kind, value) for kind, value in contact_rows)
    return (
        render_markdown_lines([title]),
        body_html,
        contact_html,
    )


def parse_about_quote(path: Path) -> str:
    quote_lines: list[str] = []
    for line in read_text(path).splitlines():
        stripped = line.strip()
        if stripped.startswith(">"):
            quote_lines.append(stripped[1:].strip())
        elif stripped:
            raise PageGenerationError(
                f"{path} should only include quote lines starting with '>'. "
                "Section divider text is built into the website template."
            )

    quote_html = render_markdown_lines(quote_lines)
    if not quote_html:
        raise PageGenerationError(f"{path} must include quote lines starting with '>'")

    return f'"{quote_html}"'


def render_about_image(item: MediaItem | None, output_html: Path) -> str:
    if item is None:
        return ""

    image_html = image_tag(
        item,
        output_html,
        "Rae Hu",
        class_name="about-image",
        loading="lazy",
        sizes="(max-width: 900px) 100vw, 42vw",
    )
    return f"""        <figure class="about-image-wrap fade-up">
          {image_html}
        </figure>"""


def load_about_image(
    about_dir: Path = EDITABLE_ABOUT_DIR,
    write_assets: bool = False,
    check_generated_assets: bool = False,
    resolve_assets: bool = True,
) -> MediaItem | None:
    media = ordered_media(
        about_dir,
        write_assets=write_assets,
        require_media=False,
        check_generated_assets=check_generated_assets,
        resolve_assets=resolve_assets,
    )
    if not media:
        return None
    if len(media) > 1:
        raise PageGenerationError(
            f"{about_dir} has multiple about media files. Keep exactly one numbered image, "
            "for example 1_image.jpg."
        )

    item = media[0]
    if item.kind != "image":
        raise PageGenerationError(f"{item.path} is not supported for the about page. Use an image.")
    return item


def load_about_content(
    text_path: Path = EDITABLE_ABOUT_TEXT,
    quote_path: Path = EDITABLE_ABOUT_QUOTE,
    about_dir: Path = EDITABLE_ABOUT_DIR,
    output_html: Path = HOME_OUTPUT_HTML,
    write_assets: bool = False,
    check_generated_assets: bool = False,
    resolve_assets: bool = True,
) -> AboutContent:
    title_html, body_html, contact_html = parse_about_text(text_path)
    chinese_text_path = alternate_language_path(text_path, "chinese")
    if chinese_text_path.exists():
        title_html_chinese, body_html_chinese, contact_html_chinese = parse_about_text(
            chinese_text_path
        )
    else:
        title_html_chinese = title_html
        body_html_chinese = body_html
        contact_html_chinese = contact_html
    spanish_text_path = alternate_language_path(text_path, "spanish")
    if spanish_text_path.exists():
        title_html_spanish, body_html_spanish, contact_html_spanish = parse_about_text(
            spanish_text_path
        )
    else:
        title_html_spanish = title_html
        body_html_spanish = body_html
        contact_html_spanish = contact_html
    quote_html = parse_about_quote(quote_path)
    image = load_about_image(
        about_dir,
        write_assets=write_assets,
        check_generated_assets=check_generated_assets,
        resolve_assets=resolve_assets,
    )
    return AboutContent(
        title_html=title_html,
        body_html=body_html,
        contact_html=contact_html,
        title_html_chinese=title_html_chinese,
        body_html_chinese=body_html_chinese,
        contact_html_chinese=contact_html_chinese,
        title_html_spanish=title_html_spanish,
        body_html_spanish=body_html_spanish,
        contact_html_spanish=contact_html_spanish,
        image_html=render_about_image(image, output_html),
        quote_html=quote_html,
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


def is_media_path(path: Path) -> bool:
    return path.suffix.lower() in IMAGE_EXTENSIONS | VIDEO_EXTENSIONS


def media_dimensions(path: Path) -> tuple[int, int] | tuple[None, None]:
    suffix = path.suffix.lower()
    try:
        data = path.read_bytes()
    except OSError:
        return (None, None)

    if suffix == ".png":
        return png_dimensions(data)
    if suffix == ".webp":
        return webp_dimensions(data)
    if suffix in {".jpg", ".jpeg"}:
        return jpeg_dimensions(data)
    return (None, None)


def png_dimensions(data: bytes) -> tuple[int, int] | tuple[None, None]:
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        return (None, None)
    return (
        int.from_bytes(data[16:20], "big"),
        int.from_bytes(data[20:24], "big"),
    )


def webp_dimensions(data: bytes) -> tuple[int, int] | tuple[None, None]:
    if len(data) < 30 or data[:4] != b"RIFF" or data[8:12] != b"WEBP":
        return (None, None)

    offset = 12
    while offset + 8 <= len(data):
        chunk_type = data[offset : offset + 4]
        chunk_size = int.from_bytes(data[offset + 4 : offset + 8], "little")
        payload = offset + 8

        if chunk_type == b"VP8X" and payload + 10 <= len(data):
            width = 1 + int.from_bytes(data[payload + 4 : payload + 7], "little")
            height = 1 + int.from_bytes(data[payload + 7 : payload + 10], "little")
            return (width, height)

        if chunk_type == b"VP8 " and payload + 10 <= len(data):
            if data[payload + 3 : payload + 6] != b"\x9d\x01\x2a":
                return (None, None)
            width = int.from_bytes(data[payload + 6 : payload + 8], "little") & 0x3FFF
            height = int.from_bytes(data[payload + 8 : payload + 10], "little") & 0x3FFF
            return (width, height)

        if chunk_type == b"VP8L" and payload + 5 <= len(data) and data[payload] == 0x2F:
            b0, b1, b2, b3 = data[payload + 1 : payload + 5]
            width = 1 + (((b1 & 0x3F) << 8) | b0)
            height = 1 + (((b3 & 0x0F) << 10) | (b2 << 2) | ((b1 & 0xC0) >> 6))
            return (width, height)

        offset = payload + chunk_size + (chunk_size % 2)

    return (None, None)


def jpeg_dimensions(data: bytes) -> tuple[int, int] | tuple[None, None]:
    if len(data) < 4 or data[:2] != b"\xff\xd8":
        return (None, None)

    offset = 2
    while offset + 9 <= len(data):
        if data[offset] != 0xFF:
            offset += 1
            continue
        marker = data[offset + 1]
        offset += 2
        if marker in {0xD8, 0xD9}:
            continue
        if offset + 2 > len(data):
            break
        segment_length = int.from_bytes(data[offset : offset + 2], "big")
        if segment_length < 2 or offset + segment_length > len(data):
            break
        if marker in {
            0xC0,
            0xC1,
            0xC2,
            0xC3,
            0xC5,
            0xC6,
            0xC7,
            0xC9,
            0xCA,
            0xCB,
            0xCD,
            0xCE,
            0xCF,
        }:
            height = int.from_bytes(data[offset + 3 : offset + 5], "big")
            width = int.from_bytes(data[offset + 5 : offset + 7], "big")
            return (width, height)
        offset += segment_length

    return (None, None)


def converted_image_path(path: Path) -> Path:
    return path.with_suffix(WEB_IMAGE_EXTENSION)


_current_hash_memo: dict[Path, str] = {}


def source_content_hash(path: Path) -> str:
    resolved = path.resolve()
    cached = _current_hash_memo.get(resolved)
    if cached is not None:
        return cached
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    digest = h.hexdigest()
    _current_hash_memo[resolved] = digest
    return digest


_source_hash_cache: dict[Path, str] = {}


def _source_hash_cache_path() -> Path:
    return responsive_media_dir() / ".source-hashes.json"


def source_hash_cache_key(path: Path) -> Path:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve())
    except ValueError:
        return path.resolve()


def normalize_source_hash_cache_key(raw_key: str) -> Path:
    path = Path(raw_key)
    if not path.is_absolute():
        return path

    try:
        return path.resolve().relative_to(REPO_ROOT.resolve())
    except ValueError:
        pass

    parts = path.parts
    for anchor in ("editable-content", "site-source-assets"):
        if anchor in parts:
            return Path(*parts[parts.index(anchor) :])
    return path


def load_source_hash_cache() -> None:
    _source_hash_cache.clear()
    _current_hash_memo.clear()
    cache_path = _source_hash_cache_path()
    if cache_path.exists():
        try:
            data = json.loads(cache_path.read_text(encoding="utf-8"))
            _source_hash_cache.update(
                {normalize_source_hash_cache_key(k): v for k, v in data.items()}
            )
        except (json.JSONDecodeError, OSError):
            pass


def save_source_hash_cache() -> None:
    cache_path = _source_hash_cache_path()
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    data = {str(k): v for k, v in sorted(_source_hash_cache.items())}
    cache_path.write_text(
        json.dumps(data, indent=2) + "\n",
        encoding="utf-8",
    )


def needs_conversion(source: Path, target: Path) -> bool:
    if not target.exists():
        return True
    current_hash = source_content_hash(source)
    cache_key = source_hash_cache_key(source)
    cached_hash = _source_hash_cache.get(cache_key)
    if cached_hash is None:
        cached_hash = _source_hash_cache.get(source)
    return current_hash != cached_hash


def record_conversion(source: Path) -> None:
    _source_hash_cache[source_hash_cache_key(source)] = source_content_hash(source)


def convert_image_to_webp(
    source: Path,
    target: Path,
    max_width: int = 1920,
    quality: int = 82,
) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise PageGenerationError(
            "ffmpeg is required to convert source images to WebP. "
            "Install ffmpeg or provide .webp files directly."
        )

    target.parent.mkdir(parents=True, exist_ok=True)
    filter_spec = f"scale=w=min({max_width}\\,iw):h=-2"
    if source.suffix.lower() == ".heic":
        filter_option = ["-filter_complex", filter_spec]
    else:
        filter_option = ["-vf", filter_spec]
    command = [
        ffmpeg,
        "-y",
        "-loglevel",
        "error",
        "-i",
        str(source),
        *filter_option,
        "-c:v",
        "libwebp",
        "-quality",
        str(quality),
        "-compression_level",
        "6",
        str(target),
    ]
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as exc:
        raise PageGenerationError(f"ffmpeg failed to convert {source} to {target}") from exc


def require_ffmpeg() -> str:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise PageGenerationError(
            "ffmpeg is required to optimize media. Install ffmpeg and rerun generate_website."
        )
    return ffmpeg


def responsive_media_dir() -> Path:
    return GENERATED_WEBSITE_DIR / "media"


def responsive_image_variant_path(source: Path, width: int) -> Path:
    try:
        relative_source = source.relative_to(REPO_ROOT)
    except ValueError:
        digest = hashlib.sha1(str(source).encode("utf-8")).hexdigest()[:12]
        relative_source = Path("external") / digest / source.name

    return (
        responsive_media_dir()
        / relative_source.parent
        / f"{relative_source.stem}-{width}{WEB_IMAGE_EXTENSION}"
    )


def responsive_image_variant_paths(source: Path) -> tuple[Path, ...]:
    return tuple(responsive_image_variant_path(source, width) for width in RESPONSIVE_IMAGE_WIDTHS)


def generated_media_path(source: Path, filename: str) -> Path:
    try:
        relative_source = source.relative_to(REPO_ROOT)
    except ValueError:
        digest = hashlib.sha1(str(source).encode("utf-8")).hexdigest()[:12]
        relative_source = Path("external") / digest / source.name

    return responsive_media_dir() / relative_source.parent / filename


def is_repo_content_path(source: Path) -> bool:
    try:
        source.relative_to(REPO_ROOT)
    except ValueError:
        return False
    return True


def ensure_responsive_image_variants(
    source: Path,
    write_assets: bool,
    check_generated_assets: bool = False,
) -> None:
    if not write_assets and not check_generated_assets:
        return
    if not is_repo_content_path(source):
        return

    targets = list(zip(RESPONSIVE_IMAGE_WIDTHS, responsive_image_variant_paths(source)))
    if check_generated_assets:
        for _width, target in targets:
            if not target.exists():
                raise PageGenerationError(
                    f"Responsive image variant is missing for {source}: {target}. "
                    "Run python3 scripts/generate_pages.py."
                )
        return

    stale = needs_conversion(source, targets[0][1])
    for width, target in targets:
        if stale or not target.exists():
            convert_image_to_webp(source, target, max_width=width, quality=78)
    record_conversion(source)


def optimized_grid_preview_video_path(source: Path) -> Path:
    filename = (
        f"{source.stem}-grid-preview-{GRID_PREVIEW_VIDEO_MAX_WIDTH}p-"
        f"{GRID_PREVIEW_VIDEO_VERSION}{GRID_PREVIEW_VIDEO_EXTENSION}"
    )
    return generated_media_path(source, filename)


def transcode_grid_preview_video(source: Path, target: Path) -> None:
    ffmpeg = require_ffmpeg()
    target.parent.mkdir(parents=True, exist_ok=True)
    command = [
        ffmpeg,
        "-y",
        "-loglevel",
        "error",
        "-i",
        str(source),
        "-map",
        "0:v:0",
        "-t",
        str(GRID_PREVIEW_VIDEO_DURATION_SECONDS),
        "-vf",
        f"scale=w=min({GRID_PREVIEW_VIDEO_MAX_WIDTH}\\,iw):h=-2",
        "-an",
        "-dn",
        "-map_metadata",
        "-1",
        "-map_chapters",
        "-1",
        "-c:v",
        "libx264",
        "-profile:v",
        "main",
        "-pix_fmt",
        "yuv420p",
        "-preset",
        "medium",
        "-b:v",
        GRID_PREVIEW_VIDEO_BITRATE,
        "-maxrate",
        GRID_PREVIEW_VIDEO_MAXRATE,
        "-bufsize",
        GRID_PREVIEW_VIDEO_BUFSIZE,
        "-movflags",
        "+faststart",
        "-write_tmcd",
        "0",
        str(target),
    ]
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as exc:
        raise PageGenerationError(
            f"ffmpeg failed to optimize grid preview video {source} to {target}. "
            "Make sure ffmpeg includes the libx264 encoder."
        ) from exc


def ensure_optimized_grid_preview_video(
    source: Path,
    write_assets: bool,
    check_generated_assets: bool = False,
) -> Path:
    target = optimized_grid_preview_video_path(source)
    if not write_assets and not check_generated_assets:
        return target
    if not is_repo_content_path(source):
        return target
    if check_generated_assets:
        if not target.exists():
            raise PageGenerationError(
                f"Optimized grid preview video is missing for {source}: {target}. "
                "Run python3 scripts/generate_pages.py."
            )
        return target
    if not needs_conversion(source, target):
        return target
    transcode_grid_preview_video(source, target)
    record_conversion(source)
    return target


def highlight_tile_video_variant_path(source: Path, width: int) -> Path:
    filename = (
        f"{source.stem}-tile-{width}p-"
        f"{HIGHLIGHT_TILE_VIDEO_VERSION}{HIGHLIGHT_TILE_VIDEO_EXTENSION}"
    )
    return generated_media_path(source, filename)


def highlight_tile_video_variant_paths(source: Path) -> tuple[Path, ...]:
    return tuple(
        highlight_tile_video_variant_path(source, width)
        for width in HIGHLIGHT_TILE_VIDEO_WIDTHS
    )


def transcode_highlight_tile_video(source: Path, target: Path, width: int) -> None:
    ffmpeg = require_ffmpeg()
    target.parent.mkdir(parents=True, exist_ok=True)
    command = [
        ffmpeg,
        "-y",
        "-loglevel",
        "error",
        "-i",
        str(source),
        "-map",
        "0:v:0",
        "-vf",
        f"scale=w=min({width}\\,iw):h=-2",
        "-an",
        "-dn",
        "-map_metadata",
        "-1",
        "-map_chapters",
        "-1",
        "-c:v",
        "libx264",
        "-profile:v",
        "main",
        "-pix_fmt",
        "yuv420p",
        "-preset",
        "medium",
        "-b:v",
        HIGHLIGHT_TILE_VIDEO_BITRATES[width],
        "-maxrate",
        HIGHLIGHT_TILE_VIDEO_MAXRATES[width],
        "-bufsize",
        HIGHLIGHT_TILE_VIDEO_BUFSIZES[width],
        "-movflags",
        "+faststart",
        "-write_tmcd",
        "0",
        str(target),
    ]
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as exc:
        raise PageGenerationError(
            f"ffmpeg failed to create highlight video tile variant {source} to {target}. "
            "Make sure ffmpeg includes the libx264 encoder."
        ) from exc


def ensure_highlight_tile_video_variants(
    source: Path,
    write_assets: bool,
    check_generated_assets: bool = False,
) -> tuple[Path, ...]:
    targets = list(
        zip(
            HIGHLIGHT_TILE_VIDEO_WIDTHS,
            highlight_tile_video_variant_paths(source),
        )
    )
    if not write_assets and not check_generated_assets:
        return tuple(target for _width, target in targets)
    if not is_repo_content_path(source):
        return tuple(target for _width, target in targets)

    if check_generated_assets:
        missing = [target for _width, target in targets if not target.exists()]
        if missing:
            missing_text = ", ".join(str(target) for target in missing)
            raise PageGenerationError(
                f"Responsive highlight video variant is missing for {source}: {missing_text}. "
                "Run python3 scripts/generate_pages.py."
            )
        return tuple(target for _width, target in targets)

    stale = needs_conversion(source, targets[0][1])
    for width, target in targets:
        if stale or not target.exists():
            transcode_highlight_tile_video(source, target, width)
    record_conversion(source)
    return tuple(target for _width, target in targets)


def ensure_highlight_video_outputs(
    media: tuple[MediaItem, ...],
    write_assets: bool,
    check_generated_assets: bool = False,
) -> None:
    for item in media:
        if item.kind == "video":
            ensure_highlight_tile_video_variants(
                item.path,
                write_assets=write_assets,
                check_generated_assets=check_generated_assets,
            )


def grid_display_media_for(
    item: MediaItem | None,
    write_assets: bool,
    check_generated_assets: bool = False,
) -> MediaItem | None:
    if item is None:
        return None
    if item.kind != "video":
        return item
    return MediaItem(
        index=item.index,
        path=ensure_optimized_grid_preview_video(
            item.path,
            write_assets=write_assets,
            check_generated_assets=check_generated_assets,
        ),
        kind=item.kind,
        width=item.width,
        height=item.height,
    )


def canonical_media_path(
    path: Path,
    write_assets: bool,
    check_generated_assets: bool = False,
) -> Path:
    kind = media_kind(path)
    if kind != "image":
        return path

    target = converted_image_path(path)
    if path.suffix.lower() == WEB_IMAGE_EXTENSION:
        ensure_responsive_image_variants(
            path,
            write_assets=write_assets,
            check_generated_assets=check_generated_assets,
        )
        return path

    if not write_assets:
        if not target.exists():
            raise PageGenerationError(
                f"Converted WebP is missing for {path}. "
                "Run python3 scripts/generate_pages.py."
            )
    elif needs_conversion(path, target):
        convert_image_to_webp(path, target)
        record_conversion(path)
    ensure_responsive_image_variants(
        target,
        write_assets=write_assets,
        check_generated_assets=check_generated_assets,
    )
    return target


def content_index(path: Path, label: str) -> int:
    match = re.match(r"^(\d+)_", path.name)
    if not match:
        raise PageGenerationError(f"{label} must start with NUMBER_: {path}")
    return int(match.group(1))


def media_index(path: Path) -> int:
    return content_index(path, "Media file")


def note_text_files(note_dir: Path) -> tuple[Path, ...]:
    if not note_dir.is_dir():
        raise PageGenerationError(f"Missing required note folder: {note_dir}")
    return tuple(
        sorted(
            path
            for path in note_dir.iterdir()
            if path.is_file()
            and path.suffix.lower() == ".md"
            and path.name not in IGNORED_NAMES
            and not path.name.startswith(".")
            and not is_alternate_language_path(path)
        )
    )


def load_localized_note_content(path: Path, index: int) -> NoteContent:
    note = parse_note_text(path, index=index)
    chinese_path = alternate_language_path(path, "chinese")
    chinese_note = parse_note_text(chinese_path, index=index) if chinese_path.exists() else note
    spanish_path = alternate_language_path(path, "spanish")
    spanish_note = parse_note_text(spanish_path, index=index) if spanish_path.exists() else note
    return NoteContent(
        title_html=note.title_html,
        body_html=note.body_html,
        index=index,
        title_html_chinese=chinese_note.title_html,
        body_html_chinese=chinese_note.body_html,
        title_html_spanish=spanish_note.title_html,
        body_html_spanish=spanish_note.body_html,
    )


def load_note_content(note_dir: Path) -> NoteContent | None:
    paths = note_text_files(note_dir)
    if not paths:
        return None
    if len(paths) > 1:
        raise PageGenerationError(
            f"{note_dir} has multiple note text files: {', '.join(str(path) for path in paths)}. "
            "Keep exactly one: either 1_text.md or 2_text.md."
        )

    path = paths[0]
    index = content_index(path, "Note text file")
    if index not in {1, 2}:
        raise PageGenerationError(
            f"{path} uses position {index}. Note text must use 1_ for the left column "
            "or 2_ for the right column."
        )
    return load_localized_note_content(path, index=index)


def validate_note_content(
    note_dir: Path,
    note: NoteContent | None,
    note_media: tuple[MediaItem, ...],
) -> MediaItem | None:
    if len(note_media) > 1:
        raise PageGenerationError(
            f"{note_dir} has multiple note media files. Keep exactly one numbered image/video file."
        )

    if not note_media:
        return None

    media = note_media[0]
    if note is not None:
        if media.index not in {1, 2}:
            raise PageGenerationError(
                f"{media.path} uses position {media.index}. Note media must use 1_ for the left column "
                "or 2_ for the right column."
            )
        if media.index == note.index:
            raise PageGenerationError(
                f"{note_dir} has note text and media both using {note.index}_. "
                "Use 1_ for the left column and 2_ for the right column so each position is used once."
            )
    return media


def ordered_media(
    section_dir: Path,
    write_assets: bool = False,
    require_media: bool = True,
    check_generated_assets: bool = False,
    resolve_assets: bool = True,
) -> tuple[MediaItem, ...]:
    if not section_dir.is_dir():
        raise PageGenerationError(f"Missing required section folder: {section_dir}")

    sources_by_index: dict[int, list[Path]] = {}
    first_source_by_canonical_path: dict[Path, Path] = {}
    used_indexes: set[int] = set()
    for path in sorted(section_dir.iterdir()):
        if path.name in IGNORED_NAMES or path.name.startswith("."):
            continue
        if not path.is_file():
            continue
        if not is_media_path(path):
            continue
        index = media_index(path)
        used_indexes.add(index)
        canonical_path = media_canonical_identity_path(path)
        if canonical_path in first_source_by_canonical_path:
            continue
        first_source_by_canonical_path[canonical_path] = path
        sources_by_index.setdefault(index, []).append(path)

    duplicate_indexes = {
        index: tuple(paths)
        for index, paths in sources_by_index.items()
        if len(paths) > 1
    }
    if duplicate_indexes:
        raise PageGenerationError(
            duplicate_media_numbers_message(
                section_dir,
                duplicate_indexes,
                used_indexes,
            )
        )

    media: list[MediaItem] = []
    for index, source_path in sorted(
        (
            (index, paths[0])
            for index, paths in sources_by_index.items()
        ),
        key=lambda item: item[0],
    ):
        if resolve_assets:
            canonical_path = canonical_media_path(
                source_path,
                write_assets=write_assets,
                check_generated_assets=check_generated_assets,
            )
            dimension_path = canonical_path
        else:
            canonical_path = media_canonical_identity_path(source_path)
            dimension_path = source_path
        width, height = media_dimensions(dimension_path)
        media.append(
            MediaItem(
                index=index,
                path=canonical_path,
                kind=media_kind(canonical_path),
                width=width,
                height=height,
            )
        )

    if require_media and not media:
        raise PageGenerationError(f"No media found in: {section_dir}")

    return tuple(sorted(media, key=lambda item: item.index))


def media_canonical_identity_path(path: Path) -> Path:
    if media_kind(path) == "image":
        return converted_image_path(path)
    return path


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def filename_with_replaced_index(filename: str, index: int) -> str:
    return re.sub(r"^\d+_", f"{index}_", filename, count=1)


def duplicate_media_numbers_message(
    section_dir: Path,
    duplicate_indexes: Mapping[int, tuple[Path, ...]],
    used_indexes: Iterable[int],
) -> str:
    used = set(used_indexes)
    example_index = (max(used) + 1) if used else 1
    first_duplicate_index = min(duplicate_indexes)
    example_source = sorted(
        duplicate_indexes[first_duplicate_index],
        key=lambda path: path.name,
    )[-1]
    example_target = filename_with_replaced_index(example_source.name, example_index)

    conflict_lines: list[str] = []
    for index in sorted(duplicate_indexes):
        conflict_lines.append(f"Number {index}:")
        conflict_lines.extend(
            f"  {path.name}"
            for path in sorted(duplicate_indexes[index], key=lambda item: item.name)
        )
        conflict_lines.append("")

    return (
        "STOP: Two or more files in the same section use the same order number.\n"
        "\n"
        "Folder:\n"
        f"{display_path(section_dir)}\n"
        "\n"
        "The website uses the number at the start of each filename to decide the display order.\n"
        "Each number can only be used once in the same folder.\n"
        "\n"
        "Conflicts found:\n"
        "\n"
        f"{chr(10).join(conflict_lines).rstrip()}\n"
        "\n"
        "What to do:\n"
        "\n"
        "If you want ALL of these files to appear on the website:\n"
        "  Rename files so each one starts with a different unused number.\n"
        f"  Example: {example_source.name} -> {example_target}\n"
        "\n"
        "If one file replaced another and only ONE should appear:\n"
        "  Delete the file you no longer want.\n"
        "\n"
        "Then run generate_website again.\n"
        "\n"
        "No commit, push, or publish was performed."
    )


def output_relative_url(output_html: Path, target: Path) -> str:
    relative_path = os.path.relpath(target, start=output_html.parent)
    return "/".join(quote(part) for part in Path(relative_path).parts)


def generated_site_relative_url(output_html: Path, *parts: str) -> str:
    return output_relative_url(output_html, GENERATED_WEBSITE_DIR.joinpath(*parts))


def responsive_image_srcset(source: Path, output_html: Path) -> str:
    return ", ".join(
        f"{output_relative_url(output_html, responsive_image_variant_path(source, width))} {width}w"
        for width in RESPONSIVE_IMAGE_WIDTHS
    )


def media_dimension_attrs(item: MediaItem) -> str:
    if not item.width or not item.height:
        return ""
    aspect_ratio = item.width / item.height
    return (
        f' width="{item.width}" height="{item.height}"'
        f' data-aspect-ratio="{aspect_ratio:.6f}"'
    )


def image_tag(
    item: MediaItem,
    output_html: Path,
    alt: str,
    class_name: str | None = None,
    loading: str = "lazy",
    sizes: str = "100vw",
    fetchpriority: str | None = None,
) -> str:
    src = output_relative_url(output_html, item.path)
    class_attr = f' class="{class_name}"' if class_name else ""
    fetchpriority_attr = f' fetchpriority="{fetchpriority}"' if fetchpriority else ""
    dimension_attrs = media_dimension_attrs(item)
    return (
        f'<img{class_attr}{dimension_attrs} src="{src}" '
        f'srcset="{responsive_image_srcset(item.path, output_html)}" '
        f'sizes="{html_escape(sizes)}" alt="{html_escape(alt)}" '
        f'loading="{html_escape(loading)}" decoding="async"{fetchpriority_attr}>'
    )


def video_tag(
    item: MediaItem,
    output_html: Path,
    label: str,
    class_name: str | None = None,
    autoplay: bool = True,
    controls: bool = False,
    lazy: bool = True,
    preload: str = "none",
    muted: bool = True,
) -> str:
    src = output_relative_url(output_html, item.path)
    class_attr = f' class="{class_name}"' if class_name else ""
    dimension_attrs = media_dimension_attrs(item)
    controls_attr = " controls" if controls else ""
    muted_attr = " muted" if muted else ""
    autoplay_attr = " autoplay" if autoplay and not lazy else ""
    src_attr = f' data-src="{src}" data-lazy-video' if lazy else f' src="{src}"'
    return (
        f'<video{class_attr}{dimension_attrs}{src_attr}{muted_attr} playsinline{autoplay_attr} loop{controls_attr} '
        f'preload="{html_escape(preload)}" '
        f'aria-label="{html_escape(label)}"></video>'
    )


def work_output_html(work: WorkContent) -> Path:
    return GENERATED_WEBSITE_DIR / work.category / work.slug / "index.html"


def work_public_url_from(output_html: Path, work: WorkContent) -> str:
    href = output_relative_url(output_html, work_output_html(work).parent)
    return href if href.endswith("/") else f"{href}/"


def root_index_url_from(output_html: Path) -> str:
    href = output_relative_url(output_html, GENERATED_WEBSITE_DIR)
    if href in {"", "."}:
        return "./"
    return href if href.endswith("/") else f"{href}/"


def root_category_url_from(output_html: Path, category: str) -> str:
    return root_index_url_from(output_html) + f"#{category}"


def media_tag(
    item: MediaItem,
    output_html: Path,
    alt: str,
    class_name: str | None = None,
    active: bool = False,
    image_loading: str = "lazy",
    video_lazy: bool = True,
    video_preload: str = "none",
    video_controls: bool = False,
) -> str:
    class_attr = ""
    if class_name:
        classes = class_name + (" is-active" if active else "")
    else:
        classes = ""

    if item.kind == "image":
        return image_tag(
            item,
            output_html,
            alt,
            class_name=classes or None,
            loading=image_loading,
        )
    return video_tag(
        item,
        output_html,
        alt,
        class_name=classes or None,
        autoplay=True,
        lazy=video_lazy,
        preload=video_preload,
        controls=video_controls,
    )


def has_primary_source(work_dir: Path) -> bool:
    primary_section = primary_section_for_category(work_dir.parent.name)
    primary_dir = work_dir / primary_section
    if not primary_dir.is_dir():
        return False

    link_path = primary_dir / primary_link_file_for_section(primary_section)
    if read_optional_first_non_empty_line(link_path):
        return True

    for path in primary_dir.iterdir():
        if path.name in IGNORED_NAMES or path.name.startswith("."):
            continue
        if path.is_file() and is_media_path(path):
            return True
    return False


def has_publishable_content(work_dir: Path) -> bool:
    for path in work_dir.rglob("*"):
        if path.name in IGNORED_NAMES or path.name.startswith("."):
            continue
        if path.is_file():
            return True
    return False


def primary_source_count(work_dir: Path) -> int:
    primary_section = primary_section_for_category(work_dir.parent.name)
    primary_dir = work_dir / primary_section
    if not primary_dir.is_dir():
        return 0

    sources = 0
    link_path = primary_dir / primary_link_file_for_section(primary_section)
    if read_optional_first_non_empty_line(link_path):
        sources += 1

    seen_media: set[Path] = set()
    for path in primary_dir.iterdir():
        if path.name in IGNORED_NAMES or path.name.startswith("."):
            continue
        if not path.is_file() or not is_media_path(path):
            continue
        canonical_path = media_canonical_identity_path(path)
        if canonical_path in seen_media:
            continue
        seen_media.add(canonical_path)
        sources += 1
    return sources


def has_section_media(section_dir: Path) -> bool:
    if not section_dir.is_dir():
        return False
    for path in section_dir.iterdir():
        if path.name in IGNORED_NAMES or path.name.startswith("."):
            continue
        if path.is_file() and is_media_path(path):
            return True
    return False


def valid_started_work(work_dir: Path) -> bool:
    return has_primary_source(work_dir) and has_section_media(work_dir / "highlight")


def work_completion_issues(work_dir: Path) -> tuple[str, ...]:
    issues: list[str] = []
    primary_section = primary_section_for_category(work_dir.parent.name)
    primary_dir = work_dir / primary_section
    primary_link_file = primary_link_file_for_section(primary_section)

    if not primary_dir.is_dir():
        issues.append(
            f"Missing {primary_section}/. Add {primary_section}/{primary_link_file} "
            f"with one Vimeo URL, or add exactly one numbered image or MP4 in {primary_section}/."
        )
    elif primary_source_count(work_dir) == 0:
        issues.append(
            f"Missing {primary_section} source. Add {primary_section}/{primary_link_file} "
            f"with one Vimeo URL, or add exactly one numbered image or MP4 in {primary_section}/."
        )

    highlight_dir = work_dir / "highlight"
    if not highlight_dir.is_dir():
        issues.append(
            "Missing highlight/. Add at least one numbered image or MP4 in highlight/."
        )
    elif not has_section_media(highlight_dir):
        issues.append(
            "Missing highlight media. Add at least one numbered image or MP4 in highlight/."
        )

    return tuple(issues)


def warn_incomplete_work(work_dir: Path, issues: tuple[str, ...]) -> None:
    if not issues:
        return

    primary_section = primary_section_for_category(work_dir.parent.name)
    primary_link_file = primary_link_file_for_section(primary_section)
    issue_lines = "\n".join(f"  - {issue}" for issue in issues)
    print(
        "WARNING: A work folder was skipped because it is not ready to publish.\n"
        "\n"
        "Folder:\n"
        f"{display_path(work_dir)}\n"
        "\n"
        "Missing required pieces:\n"
        f"{issue_lines}\n"
        "\n"
        "For the generator to publish this page, the folder needs:\n"
        f"  - Exactly one {primary_section} source in {primary_section}/: "
        f"either {primary_link_file} with one Vimeo URL, or one numbered image or MP4.\n"
        "  - At least one numbered image or MP4 in highlight/.\n"
        "\n"
        "This draft was skipped. Complete the missing pieces when you want it to appear on the website.",
        file=sys.stderr,
    )


def load_primary_media_source(
    source_dir: Path,
    section_name: str,
    link_file_name: str,
    write_assets: bool = False,
    check_generated_assets: bool = False,
    vimeo_thumbnail_cache: dict[str, str] | None = None,
    fetch_vimeo_thumbnails: bool = True,
    resolve_assets: bool = True,
) -> tuple[str | None, str | None, MediaItem | None]:
    if not source_dir.is_dir():
        raise PageGenerationError(f"Missing required {section_name} folder: {source_dir}")

    link_path = source_dir / link_file_name
    source_link = read_optional_first_non_empty_line(link_path)
    source_media = ordered_media(
        source_dir,
        write_assets=write_assets,
        require_media=False,
        check_generated_assets=check_generated_assets,
        resolve_assets=resolve_assets,
    )

    sources = []
    if source_link:
        sources.append(str(link_path))
    sources.extend(str(item.path) for item in source_media)

    if len(sources) != 1:
        if not sources:
            raise PageGenerationError(
                f"{source_dir} must contain exactly one {section_name} source. "
                f"Add either {link_file_name} with one Vimeo URL, or one numbered "
                f"media file such as 1_{section_name}.webp or 1_{section_name}.mp4."
            )
        raise PageGenerationError(
            f"{source_dir} has multiple {section_name} sources: {', '.join(sources)}. "
            f"Keep exactly one source: either {link_file_name} with one Vimeo URL, "
            f"or one numbered .webp/.mp4 {section_name} media file. Remove the extra source(s)."
        )

    if source_link:
        return (
            vimeo_embed_url(source_link),
            vimeo_thumbnail_url(
                source_link,
                cache=vimeo_thumbnail_cache,
                allow_fetch=fetch_vimeo_thumbnails,
            ),
            None,
        )

    return None, None, source_media[0]


def render_required_markdown_lines(path: Path) -> str:
    rendered = render_markdown_lines(read_text(path).splitlines())
    if not rendered:
        raise PageGenerationError(f"{path} must not be empty")
    return rendered


def load_localized_markdown_lines(path: Path) -> tuple[str, str, str]:
    english_html = render_required_markdown_lines(path)
    chinese_path = alternate_language_path(path, "chinese")
    chinese_html = (
        render_required_markdown_lines(chinese_path)
        if chinese_path.exists()
        else english_html
    )
    spanish_path = alternate_language_path(path, "spanish")
    spanish_html = (
        render_required_markdown_lines(spanish_path)
        if spanish_path.exists()
        else english_html
    )
    return english_html, chinese_html, spanish_html


def load_optional_grid_preview_media(
    work_dir: Path,
    write_assets: bool = False,
    check_generated_assets: bool = False,
    resolve_assets: bool = True,
) -> MediaItem | None:
    preview_dir = work_dir / "grid_preview"
    if not preview_dir.exists():
        return None
    if not preview_dir.is_dir():
        raise PageGenerationError(
            f"{preview_dir} must be a folder. "
            "Create grid_preview/ with one numbered image or MP4, or remove it."
        )

    preview_media = ordered_media(
        preview_dir,
        write_assets=write_assets,
        require_media=False,
        check_generated_assets=check_generated_assets,
        resolve_assets=resolve_assets,
    )
    if len(preview_media) != 1:
        if not preview_media:
            raise PageGenerationError(
                f"{preview_dir} must contain exactly one grid preview media file. "
                "Add one numbered image or MP4 such as 1_preview.jpg, or remove grid_preview/ "
                "to use the film/trailer preview automatically."
            )
        raise PageGenerationError(
            f"{preview_dir} has multiple grid preview media files. "
            "Keep exactly one numbered image or MP4, such as 1_preview.jpg."
        )
    return preview_media[0]


def load_work(
    work_dir: Path,
    write_assets: bool = False,
    check_generated_assets: bool = False,
    vimeo_thumbnail_cache: dict[str, str] | None = None,
    fetch_vimeo_thumbnails: bool = True,
    resolve_assets: bool = True,
) -> WorkContent:
    slug = work_dir.name
    category = work_dir.parent.name
    primary_section = primary_section_for_category(category)
    primary_dir = work_dir / primary_section
    trailer_embed_url, trailer_poster_url, trailer_media = load_primary_media_source(
        primary_dir,
        primary_section,
        primary_link_file_for_section(primary_section),
        write_assets=write_assets,
        check_generated_assets=check_generated_assets,
        vimeo_thumbnail_cache=vimeo_thumbnail_cache,
        fetch_vimeo_thumbnails=fetch_vimeo_thumbnails,
        resolve_assets=resolve_assets,
    )
    primary_links = load_primary_links(primary_dir / "additional_links.md")
    note_dir = work_dir / "note"
    note: NoteContent | None = None
    note_media_item: MediaItem | None = None
    if note_dir.is_dir():
        note = load_note_content(note_dir)
        note_media = ordered_media(
            note_dir,
            write_assets=write_assets,
            require_media=False,
            check_generated_assets=check_generated_assets,
            resolve_assets=resolve_assets,
        )
        note_media_item = validate_note_content(note_dir, note, note_media)
    highlight_media = ordered_media(
        work_dir / "highlight",
        write_assets=write_assets,
        check_generated_assets=check_generated_assets,
        resolve_assets=resolve_assets,
    )
    ensure_highlight_video_outputs(
        highlight_media,
        write_assets=write_assets,
        check_generated_assets=check_generated_assets,
    )
    grid_preview_media = load_optional_grid_preview_media(
        work_dir,
        write_assets=write_assets,
        check_generated_assets=check_generated_assets,
        resolve_assets=resolve_assets,
    )
    bts_dir = work_dir / "bts"
    bts_text_html: str | None = None
    bts_text_html_chinese: str | None = None
    bts_text_html_spanish: str | None = None
    bts_media: tuple[MediaItem, ...] = ()
    if bts_dir.is_dir():
        bts_text_path = bts_dir / "text.md"
        if bts_text_path.exists():
            bts_text_html, bts_text_html_chinese, bts_text_html_spanish = load_localized_markdown_lines(
                bts_text_path
            )
        bts_media = ordered_media(
            bts_dir,
            write_assets=write_assets,
            require_media=False,
            check_generated_assets=check_generated_assets,
            resolve_assets=resolve_assets,
        )
    grid_display_media = grid_display_media_for(
        grid_preview_media or trailer_media,
        write_assets=write_assets,
        check_generated_assets=check_generated_assets,
    )

    return WorkContent(
        slug=slug,
        title=title_from_slug(slug),
        trailer_embed_url=trailer_embed_url,
        trailer_poster_url=trailer_poster_url,
        note=note,
        note_media=note_media_item,
        highlight_media=highlight_media,
        bts_text_html=bts_text_html,
        bts_media=bts_media,
        bts_text_html_chinese=bts_text_html_chinese,
        bts_text_html_spanish=bts_text_html_spanish,
        category=category,
        trailer_media=trailer_media,
        grid_preview_media=grid_preview_media,
        grid_display_media=grid_display_media,
        primary_links=primary_links,
    )


def render_tracker_links(sections: Iterable[str]) -> str:
    lines: list[str] = []
    for index, section in enumerate(sections):
        current = ' aria-current="true"' if index == 0 else ""
        lines.append(
            f'    <a href="#{section}" data-section-link="{section}"{current}>\n'
            '      <span class="red-dot section-tracker-dot" aria-hidden="true"></span>\n'
            f"      {render_nav_label(section)}\n"
            "    </a>"
        )
    return "\n".join(lines)


def render_nav_label(label: str) -> str:
    chinese_label = CHINESE_NAV_LABELS.get(label, label)
    spanish_label = SPANISH_NAV_LABELS.get(label, label)
    return (
        f'<span data-language-content="en">{html_escape(label)}</span>'
        f'<span data-language-content="cn">{html_escape(chinese_label)}</span>'
        f'<span data-language-content="es">{html_escape(spanish_label)}</span>'
    )


def render_work_category_links(categories: Iterable[str]) -> str:
    lines: list[str] = []
    for category in categories:
        lines.append(
            f'        <a href="#{category}" data-work-category-link="{category}">\n'
            '          <span class="red-dot section-tracker-dot" aria-hidden="true"></span>\n'
            f"          {render_nav_label(category)}\n"
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


def render_trailer_media(
    item: MediaItem,
    output_html: Path,
    title: str,
    section_name: str,
) -> str:
    if item.kind == "image":
        return image_tag(
            item,
            output_html,
            f"{title} {section_name}",
            class_name="trailer-poster",
            loading="eager",
            sizes="100vw",
            fetchpriority="high",
        )
    return video_tag(
        item,
        output_html,
        f"{title} {section_name}",
        class_name="trailer-poster trailer-video",
        autoplay=False,
        controls=True,
        lazy=False,
        preload="metadata",
        muted=False,
    )


def render_primary_links(links: tuple[PrimaryLink, ...]) -> str:
    if not links:
        return ""

    link_lines = [
        "        "
        + (
            f'<a class="primary-section-link" href="{html_escape(link.href)}" '
            f'target="_blank" rel="noreferrer">'
            f'<span class="primary-section-link-text">{html_escape(link.label)}</span>'
            '<svg class="primary-section-link-chevron" viewBox="0 0 24 24" '
            'aria-hidden="true" focusable="false">'
            '<path class="interactive-chevron interactive-chevron--right" d="M9 6l6 6-6 6"></path>'
            "</svg>"
            "</a>"
        )
        for link in links
    ]
    return (
        '      <nav class="primary-section-links" aria-label="Project links">\n'
        + "\n".join(link_lines)
        + "\n      </nav>"
    )


def render_trailer_section(work: WorkContent, output_html: Path) -> str:
    section_name = primary_section_for_category(work.category)
    section_title = section_name.title()
    section_class = f"work-page--{section_name}"
    escaped_section = html_escape(section_name)
    escaped_title = html_escape(section_title)
    links_html = render_primary_links(work.primary_links)
    layout_class = "primary-section-layout"
    if work.primary_links:
        layout_class += " primary-section-layout--has-links"
    escaped_layout_class = html_escape(layout_class)

    if work.trailer_media:
        media_html = render_trailer_media(
            work.trailer_media,
            output_html,
            work.title,
            section_name,
        )
        return f"""    <section class="work-page {html_escape(section_class)}"
             id="{escaped_section}"
             data-section-page="{escaped_section}"
             data-section-title="{escaped_title}"
             data-page-padding
             aria-label="{escaped_title}">
      <div class="{escaped_layout_class}">
        <div class="trailer-wrap trailer-wrap--media">
          {media_html}
        </div>
{links_html}
      </div>
    </section>"""

    if work.trailer_poster_url:
        poster_html = (
            f'<img class="trailer-poster" '
            f'src="{html_escape(work.trailer_poster_url)}" '
            f'alt="{html_escape(work.title)} {escaped_section}" '
            'loading="eager" decoding="async" fetchpriority="high">'
        )
    else:
        poster_html = '<div class="trailer-poster trailer-poster--placeholder" aria-hidden="true"></div>'

    return f"""    <section class="work-page {html_escape(section_class)}"
             id="{escaped_section}"
             data-section-page="{escaped_section}"
             data-section-title="{escaped_title}"
             data-page-padding
             aria-label="{escaped_title}">
      <div class="{escaped_layout_class}">
        <div class="trailer-wrap"
             data-vimeo-embed="{html_escape(work.trailer_embed_url or '')}">
          {poster_html}
          <button class="trailer-play" aria-label="Play {escaped_section}">
            <svg viewBox="0 0 68 48" width="68" height="48"><path d="M66.5 7.7c-.8-2.9-2.5-5.4-5.4-6.2C55.8.1 34 0 34 0S12.2.1 6.9 1.5c-2.9.8-4.6 3.3-5.4 6.2C.1 13 0 24 0 24s.1 11 1.5 16.3c.8 2.9 2.5 5.4 5.4 6.2C12.2 47.9 34 48 34 48s21.8-.1 27.1-1.5c2.9-.8 4.6-3.3 5.4-6.2C67.9 35 68 24 68 24s-.1-11-1.5-16.3z" fill="rgba(255,255,255,0.85)"/><path d="M45 24L27 14v20z" fill="#0a0a0a"/></svg>
          </button>
        </div>
{links_html}
      </div>
    </section>"""


def _note_body_tag(body_html: str) -> str:
    if not body_html:
        return ""
    return f'\n          <p class="work-subtext">{body_html}</p>'


def render_note_text_block(note: NoteContent) -> str:
    note_title_chinese = note.title_html_chinese or note.title_html
    note_body_chinese = note.body_html_chinese or note.body_html
    note_title_spanish = note.title_html_spanish or note.title_html
    note_body_spanish = note.body_html_spanish or note.body_html
    return f"""        <div class="work-header-text" data-language-content="en">
          <h1 class="work-title">{note.title_html}</h1>{_note_body_tag(note.body_html)}
          <div class="work-label"><div class="red-dot"></div> Director's note</div>
        </div>
        <div class="work-header-text" data-language-content="cn">
          <h1 class="work-title">{note_title_chinese}</h1>{_note_body_tag(note_body_chinese)}
          <div class="work-label"><div class="red-dot"></div> Director's note</div>
        </div>
        <div class="work-header-text" data-language-content="es">
          <h1 class="work-title">{note_title_spanish}</h1>{_note_body_tag(note_body_spanish)}
          <div class="work-label"><div class="red-dot"></div> Director's note</div>
        </div>"""


def render_note_section(work: WorkContent, output_html: Path) -> str:
    has_text = work.note is not None
    has_media = work.note_media is not None
    empty_column = '        <div class="work-header-spacer"></div>'

    if has_text and has_media:
        media_html = media_tag(work.note_media, output_html, work.title, class_name="work-header-image", video_controls=True)
        media_position = "left" if work.note_media.index == 1 else "right"
        text_html = render_note_text_block(work.note)
        media_block_html = f"""        <div class="work-header-image-wrap work-header-piece--{media_position}">
          {media_html}
        </div>"""
        note_columns = "\n".join(
            html_block
            for _, html_block in sorted(
                (
                    (work.note.index, text_html),
                    (work.note_media.index, media_block_html),
                ),
                key=lambda item: item[0],
            )
        )
    elif has_text:
        text_position = work.note.index
        if text_position == 1:
            note_columns = render_note_text_block(work.note) + "\n" + empty_column
        else:
            note_columns = empty_column + "\n" + render_note_text_block(work.note)
    else:
        media_html = media_tag(work.note_media, output_html, work.title, class_name="work-header-image", video_controls=True)
        media_block_html = f"""        <div class="work-header-image-wrap">
          {media_html}
        </div>"""
        if work.note_media.index == 1:
            note_columns = media_block_html + "\n" + empty_column
        else:
            note_columns = empty_column + "\n" + media_block_html

    return f"""    <section class="work-page work-page--note content-visibility-auto"
             id="note"
             data-section-page="note"
             data-section-title="Note"
             data-page-padding
             aria-label="Director's note">
      <div class="work-header">
{note_columns}
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
    return f"""    <section class="work-page work-page--highlight content-visibility-auto"
             id="highlight"
             data-section-page="highlight"
             data-section-title="Highlight"
             data-page-padding
             aria-label="Highlight">
      <div class="grid-wrapper">
        <div class="portfolio-grid"
             data-grid-mode="justify"
             data-layout="{html_escape(layout)}"
             data-justify-max-items="3"
             data-justify-mobile-max-items="2">
{media_html}
        </div>
      </div>
    </section>"""


def render_highlight_tile(item: MediaItem, output_html: Path, title: str) -> str:
    if item.kind == "video":
        media_html = highlight_video_tag(
            item,
            output_html,
            f"{title} highlight",
        )
    else:
        media_html = media_tag(
            item,
            output_html,
            f"{title} highlight",
            class_name="highlight-media media-hover-zoom-target",
            image_loading="eager",
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


def highlight_video_tag(item: MediaItem, output_html: Path, label: str) -> str:
    tile_src = output_relative_url(
        output_html,
        highlight_tile_video_variant_path(item.path, HIGHLIGHT_TILE_VIDEO_WIDTHS[-1]),
    )
    full_src = output_relative_url(output_html, item.path)
    dimension_attrs = media_dimension_attrs(item)
    return (
        f'<video class="highlight-media media-hover-zoom-target"{dimension_attrs} '
        f'src="{tile_src}" data-full-src="{full_src}" '
        'muted playsinline autoplay loop preload="metadata" '
        f'aria-label="{html_escape(label)}"></video>'
    )


def render_bts_slideshow(work: WorkContent, output_html: Path) -> str:
    slide_lines = [
        "          "
        + media_tag(
            item,
            output_html,
            f"{work.title} behind the scenes",
            class_name="bts-slide",
            active=index == 0,
            video_controls=True,
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
    return f"""        <div class="bts-slideshow" aria-label="Behind the scenes slideshow">
{chr(10).join(slide_lines)}{controls}
        </div>"""


def render_bts_copy(work: WorkContent) -> str:
    return f"""        <div class="bts-copy">
          <p class="bts-text" data-language-content="en">{work.bts_text_html}</p>
          <p class="bts-text" data-language-content="cn">{work.bts_text_html_chinese or work.bts_text_html}</p>
          <p class="bts-text" data-language-content="es">{work.bts_text_html_spanish or work.bts_text_html}</p>
        </div>"""


def render_bts_section(work: WorkContent, output_html: Path) -> str:
    has_media = len(work.bts_media) > 0
    has_text = work.bts_text_html is not None
    empty_column = '        <div class="bts-spacer"></div>'

    if has_media and has_text:
        layout_class = "bts-layout"
        inner = f"""{render_bts_slideshow(work, output_html)}

{render_bts_copy(work)}"""
    elif has_media:
        layout_class = "bts-layout"
        inner = f"""{render_bts_slideshow(work, output_html)}

{empty_column}"""
    else:
        layout_class = "bts-layout bts-layout--text-only"
        inner = f"""{empty_column}

{render_bts_copy(work)}"""

    return f"""    <section class="work-page work-page--bts content-visibility-auto"
             id="bts"
             data-section-page="bts"
             data-section-title="BTS"
             data-page-padding
             aria-label="Behind the scenes">
      <div class="{layout_class}">
{inner}
      </div>
    </section>"""


def render_site_header_actions() -> str:
    return """    <div class="site-header-actions">
      <nav class="site-header-socials" aria-label="Contact links">
        <a class="site-header-social-link" href="mailto:raehufilm@gmail.com" aria-label="Email Rae Hu">
          <svg class="site-header-social-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false">
            <path d="M4.75 6.75h14.5v10.5H4.75z" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"/>
            <path d="m5.25 7.25 6.75 5.4 6.75-5.4" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </a>
        <a class="site-header-social-link" href="https://vimeo.com/raehu" target="_blank" rel="noreferrer" aria-label="Rae Hu on Vimeo">
          <svg class="site-header-social-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false">
            <path d="M4.25 8.25c1.25-1.05 2.25-1.57 3-1.57 1.15 0 1.9 0.72 2.25 2.16l1.25 5.18c0.22 0.86 0.53 1.29 0.94 1.29 0.48 0 1.12-0.58 1.93-1.74 0.8-1.16 1.23-2.08 1.29-2.78 0.07-0.78-0.23-1.17-0.88-1.17-0.4 0-0.87 0.1-1.41 0.31 0.95-2.83 2.59-4.2 4.92-4.1 1.72 0.06 2.5 1.16 2.34 3.31-0.16 2.03-1.64 4.72-4.45 8.08-1.96 2.34-3.64 3.51-5.03 3.51-1.29 0-2.2-1.18-2.72-3.55L6.43 11.8c-0.22-0.94-0.55-1.41-0.98-1.41-0.26 0-0.78 0.31-1.56 0.93L3 9.98l1.25-1.73Z" fill="currentColor"/>
          </svg>
        </a>
        <a class="site-header-social-link" href="https://instagram.com/raehufilm" target="_blank" rel="noreferrer" aria-label="Rae Hu on Instagram">
          <svg class="site-header-social-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false">
            <rect x="5" y="5" width="14" height="14" rx="4" fill="none" stroke="currentColor" stroke-width="1.7"/>
            <circle cx="12" cy="12" r="3.2" fill="none" stroke="currentColor" stroke-width="1.7"/>
            <circle cx="16.25" cy="7.75" r="0.95" fill="currentColor"/>
          </svg>
        </a>
      </nav>
      <button class="theme-toggle"
              type="button"
              data-theme-toggle
              aria-label="Switch to light mode"
              aria-pressed="false">
        <svg class="theme-toggle-icon theme-toggle-icon--moon" viewBox="0 0 24 24" aria-hidden="true">
          <path d="M20.25 14.2A8.35 8.35 0 1 1 9.8 3.75 6.65 6.65 0 0 0 20.25 14.2Z"></path>
        </svg>
        <svg class="theme-toggle-icon theme-toggle-icon--sun" viewBox="0 0 24 24" aria-hidden="true">
          <circle cx="12" cy="12" r="3.75"></circle>
          <path d="M12 2.75V5M12 19v2.25M4.55 4.55l1.6 1.6M17.85 17.85l1.6 1.6M2.75 12H5M19 12h2.25M4.55 19.45l1.6-1.6M17.85 6.15l1.6-1.6"></path>
        </svg>
      </button>
      <div class="language-menu" data-language-menu>
        <button class="language-toggle"
                type="button"
                data-language-toggle
                aria-haspopup="listbox"
                aria-expanded="false"
                aria-label="Change language">
          <span data-language-current>EN</span>
          <svg class="language-toggle-chevron" viewBox="0 0 24 24" aria-hidden="true" focusable="false">
            <path d="M6 9l6 6 6-6"></path>
          </svg>
        </button>
        <div class="language-menu-list" role="listbox" aria-label="Language options">
          <button class="language-option" type="button" role="option" data-language-option="en" aria-selected="true">EN</button>
          <button class="language-option" type="button" role="option" data-language-option="cn" aria-selected="false">CN</button>
          <button class="language-option" type="button" role="option" data-language-option="es" aria-selected="false">ES</button>
        </div>
      </div>
    </div>"""


def apply_template_replacements(template: str, replacements: Mapping[str, str]) -> str:
    rendered = template
    for placeholder, value in sorted(
        replacements.items(),
        key=lambda item: len(item[0]),
        reverse=True,
    ):
        rendered = rendered.replace(placeholder, value)
    return rendered


def render_work(work: WorkContent, template: str, output_html: Path) -> str:
    sections = [render_trailer_section(work, output_html)]
    if has_note_section(work):
        sections.append(render_note_section(work, output_html))
    sections.append(render_highlight_section(work, output_html))
    if has_bts_section(work):
        sections.append(render_bts_section(work, output_html))

    replacements = {
        "{{DOCUMENT_TITLE}}": html_escape(work.title),
        "{{WORK_SLUG}}": html_escape(work.slug),
        "{{WORK_CATEGORY}}": html_escape(work.category),
        "{{WORK_CATEGORY_LABEL}}": html_escape(category_label(work.category)),
        "{{WORK_CATEGORY_LABEL_HTML}}": render_nav_label(work.category),
        "{{WORK_CATEGORY_URL}}": root_category_url_from(output_html, work.category),
        "{{ROOT_INDEX_URL}}": root_index_url_from(output_html),
        "{{FAVICON_URL}}": generated_site_relative_url(output_html, "images", "favicon.svg"),
        "{{SITE_HEADER_CSS_URL}}": generated_site_relative_url(
            output_html,
            "css",
            "site-header.css",
        ),
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
        "{{LOCAL_PREVIEW_LINKS_JS_URL}}": generated_site_relative_url(
            output_html,
            "js",
            "local-preview-links.js",
        ),
        "{{PREFERENCES_JS_URL}}": generated_site_relative_url(
            output_html,
            "js",
            "preferences.js",
        ),
        "{{THEME_INIT_JS_URL}}": generated_site_relative_url(
            output_html,
            "js",
            "theme-init.js",
        ),
        "{{LANGUAGE_INIT_JS_URL}}": generated_site_relative_url(
            output_html,
            "js",
            "language-init.js",
        ),
        "{{LANGUAGE_TOGGLE_JS_URL}}": generated_site_relative_url(
            output_html,
            "js",
            "language-toggle.js",
        ),
        "{{THEME_TOGGLE_JS_URL}}": generated_site_relative_url(
            output_html,
            "js",
            "theme-toggle.js",
        ),
        "{{LAZY_MEDIA_JS_URL}}": generated_site_relative_url(
            output_html,
            "js",
            "lazy-media.js",
        ),
        "{{SITE_HEADER_ACTIONS}}": render_site_header_actions(),
        "{{SECTION_TRACKER_LINKS}}": render_tracker_links(work_section_order(work)),
        "{{WORK_SECTIONS}}": "\n\n".join(sections),
    }

    return apply_template_replacements(template, replacements)


def render_works_index_grid_item(work: WorkContent, output_html: Path) -> str:
    href = work_public_url_from(output_html, work)
    title = html_escape(work.title)
    preview_media = work.grid_display_media or work.grid_preview_media or work.trailer_media
    if work.grid_preview_media:
        preview_label = html_escape("grid preview")
    else:
        preview_label = html_escape(f"{primary_section_for_category(work.category)} preview")
    if preview_media:
        if preview_media.kind == "video":
            preview_html = video_tag(
                preview_media,
                output_html,
                f"{work.title} {preview_label}",
                class_name="media-hover-zoom-target",
                autoplay=True,
                lazy=False,
                preload="metadata",
            )
        else:
            preview_html = image_tag(
                preview_media,
                output_html,
                f"{work.title} {preview_label}",
                class_name="media-hover-zoom-target",
                loading="eager",
                sizes="(max-width: 900px) 100vw, 33vw",
            )
    elif work.trailer_poster_url:
        preview_html = (
            f'<img class="media-hover-zoom-target" width="16" height="9" '
            f'data-aspect-ratio="1.777778" src="{html_escape(work.trailer_poster_url)}" '
            f'alt="{title} {preview_label}" loading="eager" decoding="async">'
        )
    else:
        preview_html = image_tag(
            work.note_media,
            output_html,
            f"{work.title} {preview_label}",
            class_name="media-hover-zoom-target",
            loading="eager",
            sizes="(max-width: 900px) 100vw, 33vw",
        )

    return f"""        <a class="works-grid-link media-hover-zoom" href="{href}" aria-label="{title}">
          {preview_html}
          <span class="works-grid-title">
            <span class="works-grid-title-text">{title}</span>
            <svg class="works-grid-title-chevron" viewBox="0 0 24 24" aria-hidden="true" focusable="false">
              <path class="interactive-chevron interactive-chevron--right" d="M9 6l6 6-6 6"></path>
            </svg>
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

    return f"""    <section class="works-index-page fade-up"
             id="{html_escape(category)}"
             data-work-category-section="{html_escape(category)}"
             data-section-title="{html_escape(category_label(category))}"
             aria-label="{html_escape(category_label(category))}">
      <div class="works-index-grid-wrap">
        <div class="portfolio-grid works-index-grid"
             data-grid-mode="justify"
             data-seed="{len(category)}"
             data-justify-max-items="3"
             data-justify-mobile-max-items="2">
{grid_items or empty}
        </div>
      </div>
    </section>"""


def render_home(
    works: tuple[WorkContent, ...],
    about: AboutContent,
    template: str,
    output_html: Path,
) -> str:
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
        "{{FAVICON_URL}}": generated_site_relative_url(output_html, "images", "favicon.svg"),
        "{{ABOUT_TITLE}}": about.title_html,
        "{{ABOUT_BODY_HTML}}": about.body_html,
        "{{ABOUT_CONTACT_HTML}}": about.contact_html,
        "{{ABOUT_TITLE_CHINESE}}": about.title_html_chinese,
        "{{ABOUT_BODY_HTML_CHINESE}}": about.body_html_chinese,
        "{{ABOUT_CONTACT_HTML_CHINESE}}": about.contact_html_chinese,
        "{{ABOUT_TITLE_SPANISH}}": about.title_html_spanish,
        "{{ABOUT_BODY_HTML_SPANISH}}": about.body_html_spanish,
        "{{ABOUT_CONTACT_HTML_SPANISH}}": about.contact_html_spanish,
        "{{ABOUT_IMAGE_HTML}}": about.image_html,
        "{{ABOUT_QUOTE_HTML}}": about.quote_html,
        "{{SITE_HEADER_CSS_URL}}": generated_site_relative_url(
            output_html,
            "css",
            "site-header.css",
        ),
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
        "{{LOCAL_PREVIEW_LINKS_JS_URL}}": generated_site_relative_url(
            output_html,
            "js",
            "local-preview-links.js",
        ),
        "{{PREFERENCES_JS_URL}}": generated_site_relative_url(
            output_html,
            "js",
            "preferences.js",
        ),
        "{{THEME_INIT_JS_URL}}": generated_site_relative_url(
            output_html,
            "js",
            "theme-init.js",
        ),
        "{{LANGUAGE_INIT_JS_URL}}": generated_site_relative_url(
            output_html,
            "js",
            "language-init.js",
        ),
        "{{LANGUAGE_TOGGLE_JS_URL}}": generated_site_relative_url(
            output_html,
            "js",
            "language-toggle.js",
        ),
        "{{THEME_TOGGLE_JS_URL}}": generated_site_relative_url(
            output_html,
            "js",
            "theme-toggle.js",
        ),
        "{{LAZY_MEDIA_JS_URL}}": generated_site_relative_url(
            output_html,
            "js",
            "lazy-media.js",
        ),
        "{{SITE_HEADER_ACTIONS}}": render_site_header_actions(),
        "{{ROOT_SECTION_TRACKER_LINKS}}": render_tracker_links(ROOT_SECTION_ORDER),
        "{{WORK_CATEGORY_TRACKER_LINKS}}": render_work_category_links(WORK_CATEGORIES),
        "{{WORKS_INDEX_SECTIONS}}": "\n\n".join(sections),
    }

    return apply_template_replacements(template, replacements)


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


def minify_svg_text(svg: str) -> str:
    svg = re.sub(r"<!--.*?-->", "", svg, flags=re.S)
    svg = re.sub(r">\s+<", "><", svg)
    svg = re.sub(r"\s{2,}", " ", svg)
    return svg.strip() + "\n"


def generated_static_asset_bytes(path: Path) -> bytes:
    if path.suffix.lower() == ".svg":
        return minify_svg_text(path.read_text(encoding="utf-8")).encode("utf-8")
    return path.read_bytes()


def sync_static_assets(check: bool) -> int:
    failures = 0
    for dirname in STATIC_ASSET_DIRS:
        source_dir = SITE_SOURCE_ASSETS_DIR / dirname
        output_dir = GENERATED_WEBSITE_DIR / dirname

        if check:
            source_files = {
                path.relative_to(source_dir): generated_static_asset_bytes(path)
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
            for source in visible_files(source_dir):
                destination = output_dir / source.relative_to(source_dir)
                destination.parent.mkdir(parents=True, exist_ok=True)
                if source.suffix.lower() == ".svg":
                    destination.write_bytes(generated_static_asset_bytes(source))
                else:
                    shutil.copy2(source, destination)
            print(f"synced {output_dir.relative_to(REPO_ROOT)}")

    return failures


def expected_generated_media(
    editable_content_dir: Path = EDITABLE_CONTENT_DIR,
    editable_work_dir: Path = EDITABLE_WORK_DIR,
    repo_root: Path = REPO_ROOT,
    generated_website_dir: Path = GENERATED_WEBSITE_DIR,
) -> set[Path]:
    expected: set[Path] = set()

    def add_image_outputs(source: Path) -> None:
        if source.suffix.lower() == WEB_IMAGE_EXTENSION:
            for width in RESPONSIVE_IMAGE_WIDTHS:
                expected.add(responsive_image_variant_path(source, width))
        else:
            webp = converted_image_path(source)
            for width in RESPONSIVE_IMAGE_WIDTHS:
                expected.add(responsive_image_variant_path(webp, width))

    def add_grid_preview_video_outputs(source: Path) -> None:
        expected.add(optimized_grid_preview_video_path(source))

    def add_highlight_video_outputs(source: Path) -> None:
        expected.update(highlight_tile_video_variant_paths(source))

    def scan_media_dir(
        section_dir: Path,
        video_outputs: Callable[[Path], None] | None = None,
    ) -> None:
        if not section_dir.is_dir():
            return
        for path in section_dir.iterdir():
            if path.name in IGNORED_NAMES or path.name.startswith("."):
                continue
            if not path.is_file() or not is_media_path(path):
                continue
            suffix = path.suffix.lower()
            if suffix in IMAGE_EXTENSIONS:
                add_image_outputs(path)
            elif suffix in VIDEO_EXTENSIONS and video_outputs is not None:
                video_outputs(path)

    about_dir = editable_content_dir / "about"
    scan_media_dir(about_dir)

    for category in WORK_CATEGORIES:
        category_dir = editable_work_dir / category
        if not category_dir.is_dir():
            continue
        for work_dir in sorted(
            path for path in category_dir.iterdir()
            if path.is_dir() and not path.name.startswith(".")
        ):
            if not valid_started_work(work_dir):
                continue
            primary_section = primary_section_for_category(category)
            grid_preview_dir = work_dir / "grid_preview"
            primary_video_outputs = None
            if not has_section_media(grid_preview_dir):
                primary_video_outputs = add_grid_preview_video_outputs
            scan_media_dir(work_dir / primary_section, primary_video_outputs)
            scan_media_dir(work_dir / "note")
            scan_media_dir(work_dir / "highlight", add_highlight_video_outputs)
            scan_media_dir(work_dir / "bts")
            scan_media_dir(grid_preview_dir, add_grid_preview_video_outputs)

    return expected


def prune_stale_generated_media(
    check: bool = False,
    editable_content_dir: Path = EDITABLE_CONTENT_DIR,
    editable_work_dir: Path = EDITABLE_WORK_DIR,
    repo_root: Path = REPO_ROOT,
    generated_website_dir: Path = GENERATED_WEBSITE_DIR,
) -> int:
    media_dir = generated_website_dir / "media"
    if not media_dir.exists():
        return 0

    expected = expected_generated_media(
        editable_content_dir=editable_content_dir,
        editable_work_dir=editable_work_dir,
        repo_root=repo_root,
        generated_website_dir=generated_website_dir,
    )

    actual = set(visible_files(media_dir))
    stale = actual - expected

    if not stale:
        return 0

    if check:
        print(
            f"Generated media directory has {len(stale)} stale file(s) "
            "from deleted or renamed source media:",
            file=sys.stderr,
        )
        for path in sorted(stale):
            print(f"  {path}", file=sys.stderr)
        return 1

    for path in sorted(stale):
        path.unlink()
        print(f"removed stale: {path}")

    for dirpath in sorted(media_dir.rglob("*"), reverse=True):
        if dirpath.is_dir() and not any(dirpath.iterdir()):
            dirpath.rmdir()

    return 0


def discover_work_dirs(editable_work_dir: Path, selected_slug: str | None = None) -> list[Path]:
    if not editable_work_dir.is_dir():
        raise PageGenerationError(f"Missing editable work folder: {editable_work_dir}")

    work_dirs = []
    seen_slugs: dict[str, Path] = {}
    for category in WORK_CATEGORIES:
        category_dir = editable_work_dir / category
        if not category_dir.is_dir():
            continue
        for work_dir in sorted(path for path in category_dir.iterdir() if path.is_dir()):
            if work_dir.name.startswith("."):
                continue
            if selected_slug and work_dir.name != selected_slug:
                continue
            if not valid_started_work(work_dir):
                if has_publishable_content(work_dir):
                    warn_incomplete_work(work_dir, work_completion_issues(work_dir))
                continue
            existing = seen_slugs.get(work_dir.name)
            if existing:
                raise PageGenerationError(
                    f"Duplicate work slug '{work_dir.name}' in {existing} and {work_dir}"
                )
            seen_slugs[work_dir.name] = work_dir
            work_dirs.append(work_dir)
    return work_dirs


def preflight_generation_inputs(work_dirs: Iterable[Path], include_home: bool) -> None:
    for work_dir in work_dirs:
        load_work(
            work_dir,
            write_assets=False,
            check_generated_assets=False,
            fetch_vimeo_thumbnails=False,
            resolve_assets=False,
        )

    if include_home:
        load_about_content(
            write_assets=False,
            check_generated_assets=False,
            resolve_assets=False,
        )


def generate(check: bool = False, selected_slug: str | None = None) -> int:
    work_template = read_text(WORK_PAGE_TEMPLATE)
    work_dirs = discover_work_dirs(EDITABLE_WORK_DIR, selected_slug)
    if selected_slug and not work_dirs:
        raise PageGenerationError(f"No valid started work found for slug: {selected_slug}")

    if not check:
        preflight_generation_inputs(work_dirs, include_home=not selected_slug)

    failures = sync_static_assets(check)
    load_source_hash_cache()
    if not selected_slug:
        failures += prune_stale_generated_media(check=check)
    works: list[WorkContent] = []
    vimeo_thumbnail_cache = read_vimeo_thumbnail_cache()
    original_vimeo_thumbnail_cache = dict(vimeo_thumbnail_cache)
    for work_dir in work_dirs:
        work = load_work(
            work_dir,
            write_assets=not check,
            check_generated_assets=check,
            vimeo_thumbnail_cache=vimeo_thumbnail_cache,
            fetch_vimeo_thumbnails=not check,
        )
        works.append(work)
        output_html = work_output_html(work)
        rendered = render_work(work, work_template, output_html)
        failures += write_or_check(output_html, rendered, check)

    if not selected_slug:
        home_template = read_text(HOME_TEMPLATE)
        about = load_about_content(
            write_assets=not check,
            check_generated_assets=check,
        )
        home_rendered = render_home(tuple(works), about, home_template, HOME_OUTPUT_HTML)
        failures += write_or_check(HOME_OUTPUT_HTML, home_rendered, check)

    if not check:
        save_source_hash_cache()
        if vimeo_thumbnail_cache != original_vimeo_thumbnail_cache:
            write_vimeo_thumbnail_cache(vimeo_thumbnail_cache)

    return failures


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--verify-generated",
        dest="verify_generated",
        action="store_true",
        help="verify generated output is already current without writing files",
    )
    parser.add_argument(
        "--work",
        metavar="SLUG",
        help="generate/verify only one work slug",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        failures = generate(check=args.verify_generated, selected_slug=args.work)
    except PageGenerationError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
