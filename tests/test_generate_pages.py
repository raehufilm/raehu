import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import generate_pages


class GeneratePagesTests(unittest.TestCase):
    def test_vimeo_embed_url_accepts_user_facing_link_and_strips_hash(self):
        embed_url = generate_pages.vimeo_embed_url(
            "  https://vimeo.com/123456789/abcdef1234  "
        )

        self.assertEqual(
            embed_url,
            "https://player.vimeo.com/video/123456789?h=abcdef1234&autoplay=1&badge=0&autopause=0&player_id=0&app_id=58479",
        )

    def test_vimeo_public_url_normalizes_manage_links(self):
        public_url = generate_pages.vimeo_public_url(
            "https://vimeo.com/manage/videos/1119717934"
        )

        self.assertEqual(public_url, "https://vimeo.com/1119717934")

    def test_vimeo_thumbnail_url_uses_cached_public_url(self):
        cache = {
            "https://vimeo.com/123456789": "https://i.vimeocdn.com/video/example_1280",
        }

        with mock.patch.object(generate_pages, "fetch_vimeo_thumbnail_url") as fetch:
            thumbnail_url = generate_pages.vimeo_thumbnail_url(
                "https://vimeo.com/manage/videos/123456789",
                cache=cache,
                allow_fetch=False,
            )

        self.assertEqual(thumbnail_url, "https://i.vimeocdn.com/video/example_1280")
        fetch.assert_not_called()

    def test_vimeo_thumbnail_url_updates_cache_after_fetch(self):
        cache = {}

        with mock.patch.object(
            generate_pages,
            "fetch_vimeo_thumbnail_url",
            return_value="https://i.vimeocdn.com/video/example_1280",
        ):
            thumbnail_url = generate_pages.vimeo_thumbnail_url(
                "https://vimeo.com/123456789",
                cache=cache,
            )

        self.assertEqual(thumbnail_url, "https://i.vimeocdn.com/video/example_1280")
        self.assertEqual(
            cache,
            {
                "https://vimeo.com/123456789": "https://i.vimeocdn.com/video/example_1280",
            },
        )

    def test_vimeo_thumbnail_cache_round_trips_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache_path = Path(tmp) / "vimeo-thumbnails.json"

            with contextlib.redirect_stdout(io.StringIO()):
                generate_pages.write_vimeo_thumbnail_cache(
                    {
                        "https://vimeo.com/2": "https://i.vimeocdn.com/video/two_1280",
                        "https://vimeo.com/1": "https://i.vimeocdn.com/video/one_1280",
                    },
                    cache_path,
                )
            cache = generate_pages.read_vimeo_thumbnail_cache(cache_path)

        self.assertEqual(
            cache,
            {
                "https://vimeo.com/1": "https://i.vimeocdn.com/video/one_1280",
                "https://vimeo.com/2": "https://i.vimeocdn.com/video/two_1280",
            },
        )

    def test_render_trailer_uses_thumbnail_when_available(self):
        work = generate_pages.WorkContent(
            slug="sample",
            title="Sample",
            trailer_embed_url="https://player.vimeo.com/video/123",
            trailer_poster_url="https://i.vimeocdn.com/video/example_1280",
            note=generate_pages.NoteContent(title_html="Title", body_html="Body"),
            note_media=generate_pages.MediaItem(1, Path("note.webp"), "image"),
            highlight_media=(),
            bts_text_html="Credits",
            bts_media=(),
        )

        html = generate_pages.render_trailer_section(work, Path("index.html"))

        self.assertIn('class="trailer-poster"', html)
        self.assertIn('src="https://i.vimeocdn.com/video/example_1280"', html)
        self.assertNotIn("trailer-poster--placeholder", html)

    def test_render_trailer_accepts_local_image_media(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output_html = root / "generated-website" / "works" / "sample" / "index.html"
            media = (
                root
                / "editable-content"
                / "works"
                / "films"
                / "sample"
                / "trailer"
                / "1_trailer.webp"
            )
            work = generate_pages.WorkContent(
                slug="sample",
                title="Sample",
                trailer_embed_url=None,
                trailer_poster_url=None,
                note=generate_pages.NoteContent(title_html="Title", body_html="Body"),
                note_media=generate_pages.MediaItem(1, Path("note.webp"), "image"),
                highlight_media=(),
                bts_text_html="Credits",
                bts_media=(),
                trailer_media=generate_pages.MediaItem(1, media, "image"),
            )

            html = generate_pages.render_trailer_section(work, output_html)

        self.assertIn('class="trailer-wrap trailer-wrap--media"', html)
        self.assertIn("trailer/1_trailer.webp", html)
        self.assertNotIn("data-vimeo-embed", html)

    def test_ordered_media_sorts_by_numeric_prefix(self):
        with tempfile.TemporaryDirectory() as tmp:
            media_dir = Path(tmp)
            (media_dir / "10_late.webp").write_text("", encoding="utf-8")
            (media_dir / "2_middle.mp4").write_text("", encoding="utf-8")
            (media_dir / "1_first.webp").write_text("", encoding="utf-8")
            (media_dir / "text.md").write_text("Section copy", encoding="utf-8")
            (media_dir / ".DS_Store").write_text("", encoding="utf-8")

            media = generate_pages.ordered_media(media_dir)

        self.assertEqual([item.path.name for item in media], [
            "1_first.webp",
            "2_middle.mp4",
            "10_late.webp",
        ])

    def test_ordered_media_rejects_duplicate_prefixes(self):
        with tempfile.TemporaryDirectory() as tmp:
            media_dir = Path(tmp)
            (media_dir / "1_first.png").write_text("", encoding="utf-8")
            (media_dir / "1_second.png").write_text("", encoding="utf-8")

            with self.assertRaises(generate_pages.PageGenerationError):
                generate_pages.ordered_media(media_dir)

    def test_ordered_media_accepts_raw_image_when_matching_webp_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            media_dir = Path(tmp)
            (media_dir / "1_first.png").write_text("raw", encoding="utf-8")
            (media_dir / "1_first.webp").write_text("web", encoding="utf-8")

            media = generate_pages.ordered_media(media_dir)

        self.assertEqual(len(media), 1)
        self.assertEqual(media[0].path.name, "1_first.webp")
        self.assertEqual(media[0].kind, "image")

    def test_ordered_media_check_mode_requires_converted_webp_for_raw_image(self):
        with tempfile.TemporaryDirectory() as tmp:
            media_dir = Path(tmp)
            (media_dir / "1_first.png").write_text("raw", encoding="utf-8")

            with self.assertRaises(generate_pages.PageGenerationError):
                generate_pages.ordered_media(media_dir)

    def test_ordered_media_write_mode_skips_up_to_date_webp_conversion(self):
        with tempfile.TemporaryDirectory() as tmp:
            media_dir = Path(tmp)
            raw = media_dir / "1_first.png"
            webp = media_dir / "1_first.webp"
            raw.write_text("raw", encoding="utf-8")
            webp.write_text("web", encoding="utf-8")

            newer_time = raw.stat().st_mtime + 10
            webp.touch()
            import os
            os.utime(webp, (newer_time, newer_time))

            with mock.patch.object(generate_pages, "convert_image_to_webp") as convert:
                media = generate_pages.ordered_media(media_dir, write_assets=True)

        convert.assert_not_called()
        self.assertEqual(len(media), 1)
        self.assertEqual(media[0].path.name, "1_first.webp")

    def test_note_markdown_uses_heading_for_title_and_body_for_copy(self):
        with tempfile.TemporaryDirectory() as tmp:
            note_file = Path(tmp) / "1_text.md"
            note_file.write_text(
                "# A title with *emphasis*\n\n"
                "First body line.\n"
                "Second body line.",
                encoding="utf-8",
            )

            note = generate_pages.parse_note_text(note_file)

        self.assertEqual(note.title_html, "A title with <em>emphasis</em>")
        self.assertEqual(note.body_html, "First body line.<br>Second body line.")
        self.assertEqual(note.index, 1)

    def test_load_note_content_uses_numbered_position(self):
        with tempfile.TemporaryDirectory() as tmp:
            note_dir = Path(tmp)
            (note_dir / "2_text.md").write_text(
                "# Right Text\n\nBody copy.",
                encoding="utf-8",
            )

            note = generate_pages.load_note_content(note_dir)

        self.assertEqual(note.index, 2)

    def test_render_note_orders_media_before_text_when_media_is_position_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output_html = root / "generated-website" / "works" / "sample" / "index.html"
            media = (
                root
                / "editable-content"
                / "works"
                / "films"
                / "sample"
                / "note"
                / "1_note.webp"
            )
            work = generate_pages.WorkContent(
                slug="sample",
                title="Sample",
                trailer_embed_url="https://player.vimeo.com/video/123",
                trailer_poster_url=None,
                note=generate_pages.NoteContent(
                    title_html="Title",
                    body_html="Body",
                    index=2,
                ),
                note_media=generate_pages.MediaItem(1, media, "image"),
                highlight_media=(),
                bts_text_html="Credits",
                bts_media=(),
            )

            rendered = generate_pages.render_note_section(work, output_html)

        self.assertLess(
            rendered.index("work-header-image-wrap"),
            rendered.index("work-header-text"),
        )
        self.assertIn("work-header-piece--left", rendered)

    def test_highlight_grid_layout_is_deterministic_for_work_key(self):
        first = generate_pages.highlight_grid_layout(7, "commercials/champion")
        second = generate_pages.highlight_grid_layout(7, "commercials/champion")

        self.assertEqual(first, second)
        self.assertEqual(sum(len(row.split("-")) for row in first.split(", ")), 7)

    def test_highlight_grid_layout_varies_between_work_keys(self):
        first = generate_pages.highlight_grid_layout(8, "commercials/bose-global")
        second = generate_pages.highlight_grid_layout(
            8,
            "commercials/coach-unbox-your-joy",
        )

        self.assertNotEqual(first, second)

    def test_render_highlight_wraps_media_with_expand_controls(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output_html = root / "generated-website" / "works" / "sample-work" / "index.html"
            media_path = (
                root
                / "editable-content"
                / "works"
                / "films"
                / "sample-work"
                / "highlight"
                / "1_highlight.webp"
            )
            work = generate_pages.WorkContent(
                slug="sample-work",
                title="Sample Work",
                trailer_embed_url="https://player.vimeo.com/video/123",
                trailer_poster_url=None,
                note=generate_pages.NoteContent(title_html="Title", body_html="Body"),
                note_media=generate_pages.MediaItem(1, Path("note.webp"), "image"),
                highlight_media=(
                    generate_pages.MediaItem(1, media_path, "image"),
                ),
                bts_text_html="Credits",
                bts_media=(),
            )

            rendered = generate_pages.render_highlight_section(work, output_html)

        self.assertIn('class="highlight-tile media-hover-zoom" data-highlight-tile', rendered)
        self.assertIn('class="highlight-media media-hover-zoom-target"', rendered)
        self.assertIn("interactive-chevron--expand-ne", rendered)
        self.assertIn("interactive-chevron--expand-sw", rendered)
        self.assertIn("data-highlight-expand", rendered)
        self.assertIn("Expand highlight media", rendered)

    def test_discover_work_dirs_traverses_commercials_and_films(self):
        with tempfile.TemporaryDirectory() as tmp:
            editable_works = Path(tmp) / "editable-content" / "works"
            commercial = editable_works / "commercials" / "sample-ad"
            film = editable_works / "films" / "sample-film"
            (commercial / "trailer").mkdir(parents=True)
            (film / "trailer").mkdir(parents=True)
            (commercial / "trailer" / "trailer_link.md").write_text(
                "https://vimeo.com/1",
                encoding="utf-8",
            )
            (film / "trailer" / "trailer_link.md").write_text(
                "https://vimeo.com/2",
                encoding="utf-8",
            )

            work_dirs = generate_pages.discover_work_dirs(editable_works)

        self.assertEqual(
            [path.relative_to(editable_works).as_posix() for path in work_dirs],
            ["films/sample-film", "commercials/sample-ad"],
        )

    def test_discover_work_dirs_rejects_duplicate_slugs_across_categories(self):
        with tempfile.TemporaryDirectory() as tmp:
            editable_works = Path(tmp) / "editable-content" / "works"
            commercial = editable_works / "commercials" / "same-slug"
            film = editable_works / "films" / "same-slug"
            (commercial / "trailer").mkdir(parents=True)
            (film / "trailer").mkdir(parents=True)
            (commercial / "trailer" / "trailer_link.md").write_text(
                "https://vimeo.com/1",
                encoding="utf-8",
            )
            (film / "trailer" / "trailer_link.md").write_text(
                "https://vimeo.com/2",
                encoding="utf-8",
            )

            with self.assertRaises(generate_pages.PageGenerationError):
                generate_pages.discover_work_dirs(editable_works)

    def test_generate_writes_category_source_to_public_work_page(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "editable-content" / "works" / "films" / "sample-work"
            generated_site = root / "generated-website"
            output = generated_site / "works"
            template = root / "generator-templates" / "work-page.html"
            source_assets = root / "site-source-assets"

            (source / "trailer").mkdir(parents=True)
            (source / "trailer" / "trailer_link.md").write_text(
                "https://vimeo.com/123456789",
                encoding="utf-8",
            )
            (source / "note").mkdir(parents=True)
            (source / "note" / "1_text.md").write_text(
                "# Sample Work\n\nA sample note.",
                encoding="utf-8",
            )
            (source / "note" / "2_note.webp").write_text(
                "webp",
                encoding="utf-8",
            )
            (source / "highlight").mkdir(parents=True)
            (source / "highlight" / "1_highlight.webp").write_text(
                "webp",
                encoding="utf-8",
            )
            (source / "bts").mkdir(parents=True)
            (source / "bts" / "text.md").write_text("Credits", encoding="utf-8")
            (source / "bts" / "1_bts.webp").write_text(
                "webp",
                encoding="utf-8",
            )
            template.parent.mkdir()
            template.write_text(
                "<title>{{DOCUMENT_TITLE}}</title>"
                "{{WORK_CATEGORY}}"
                "{{ROOT_INDEX_URL}}"
                "{{WORKS_INDEX_URL}}"
                "{{SHARED_EFFECTS_CSS_URL}}"
                "{{PORTFOLIO_GRID_JS_URL}}"
                "{{WORK_SECTIONS}}",
                encoding="utf-8",
            )
            (source_assets / "css").mkdir(parents=True)
            (source_assets / "js").mkdir(parents=True)
            (source_assets / "css" / "shared-effects.css").write_text("", encoding="utf-8")
            (source_assets / "js" / "portfolio-grid.js").write_text("", encoding="utf-8")

            with (
                contextlib.redirect_stdout(io.StringIO()),
                mock.patch.object(generate_pages, "REPO_ROOT", root),
                mock.patch.object(generate_pages, "EDITABLE_WORKS_DIR", source.parent.parent),
                mock.patch.object(generate_pages, "GENERATED_WEBSITE_DIR", generated_site),
                mock.patch.object(generate_pages, "WORKS_OUTPUT_DIR", output),
                mock.patch.object(generate_pages, "WORK_PAGE_TEMPLATE", template),
                mock.patch.object(generate_pages, "SITE_SOURCE_ASSETS_DIR", source_assets),
                mock.patch.object(generate_pages, "vimeo_thumbnail_url", return_value=None),
            ):
                failures = generate_pages.generate(selected_slug="sample-work")

            output_html = output / "sample-work" / "index.html"
            subpages_output_html = (
                generated_site / "works" / "subpages" / "sample-work" / "index.html"
            )

            self.assertEqual(failures, 0)
            self.assertTrue(output_html.exists())
            self.assertFalse(subpages_output_html.exists())
            generated = output_html.read_text(encoding="utf-8")
            self.assertIn("films", generated)
            self.assertIn("../../", generated)
            self.assertIn("../../#works", generated)
            self.assertIn("../../css/shared-effects.css", generated)
            self.assertIn("../../js/portfolio-grid.js", generated)

    def test_load_work_rejects_multiple_trailer_sources_with_actionable_message(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "editable-content" / "works" / "films" / "sample-work"

            (source / "trailer").mkdir(parents=True)
            (source / "trailer" / "trailer_link.md").write_text(
                "https://vimeo.com/123456789",
                encoding="utf-8",
            )
            (source / "trailer" / "1_trailer.webp").write_text(
                "webp",
                encoding="utf-8",
            )

            with self.assertRaises(generate_pages.PageGenerationError) as context:
                generate_pages.load_work(source)

        message = str(context.exception)
        self.assertIn("multiple trailer sources", message)
        self.assertIn("Keep exactly one source", message)
        self.assertIn("Remove the extra source", message)

    def test_load_work_rejects_note_text_and_media_same_position(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "editable-content" / "works" / "films" / "sample-work"

            (source / "trailer").mkdir(parents=True)
            (source / "trailer" / "trailer_link.md").write_text(
                "https://vimeo.com/123456789",
                encoding="utf-8",
            )
            (source / "note").mkdir(parents=True)
            (source / "note" / "1_text.md").write_text(
                "# Sample Work\n\nA sample note.",
                encoding="utf-8",
            )
            (source / "note" / "1_note.webp").write_text(
                "webp",
                encoding="utf-8",
            )
            (source / "highlight").mkdir(parents=True)
            (source / "highlight" / "1_highlight.webp").write_text(
                "webp",
                encoding="utf-8",
            )
            (source / "bts").mkdir(parents=True)
            (source / "bts" / "text.md").write_text("Credits", encoding="utf-8")
            (source / "bts" / "1_bts.webp").write_text(
                "webp",
                encoding="utf-8",
            )

            with self.assertRaises(generate_pages.PageGenerationError) as context:
                generate_pages.load_work(source)

        message = str(context.exception)
        self.assertIn("both using 1_", message)
        self.assertIn("Use 1_ for the left column and 2_ for the right column", message)

    def test_works_index_grid_uses_local_video_trailer_preview(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output_html = root / "generated-website" / "index.html"
            media = (
                root
                / "editable-content"
                / "works"
                / "films"
                / "sample-work"
                / "trailer"
                / "1_trailer.mp4"
            )
            work = generate_pages.WorkContent(
                slug="sample-work",
                title="Sample Work",
                trailer_embed_url=None,
                trailer_poster_url=None,
                note=generate_pages.NoteContent(title_html="Title", body_html="Body"),
                note_media=generate_pages.MediaItem(1, Path("note.webp"), "image"),
                highlight_media=(),
                bts_text_html="Credits",
                bts_media=(),
                category="films",
                trailer_media=generate_pages.MediaItem(1, media, "video"),
            )

            rendered = generate_pages.render_works_index_grid_item(work, output_html)

        self.assertIn("<video", rendered)
        self.assertIn("trailer/1_trailer.mp4", rendered)
        self.assertIn("muted playsinline autoplay loop", rendered)

    def test_render_home_uses_category_sections_and_trailer_posters(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            generated_site = root / "generated-website"
            works_output = generated_site / "works"
            output_html = generated_site / "index.html"
            illustration = root / "site-source-assets" / "images" / "illustration-tight.svg"
            illustration.parent.mkdir(parents=True)
            illustration.write_text(
                '<?xml version="1.0" encoding="UTF-8"?><svg></svg>',
                encoding="utf-8",
            )
            film = generate_pages.WorkContent(
                slug="sample-film",
                title="Sample Film",
                trailer_embed_url="https://player.vimeo.com/video/1",
                trailer_poster_url="https://i.vimeocdn.com/video/film_1280",
                note=generate_pages.NoteContent(title_html="Film", body_html="Body"),
                note_media=generate_pages.MediaItem(
                    2,
                    root / "editable-content" / "works" / "films" / "sample-film" / "note" / "2_note.webp",
                    "image",
                ),
                highlight_media=(),
                bts_text_html="Credits",
                bts_media=(),
                category="films",
            )
            commercial = generate_pages.WorkContent(
                slug="sample-ad",
                title="Sample Ad",
                trailer_embed_url="https://player.vimeo.com/video/2",
                trailer_poster_url="https://i.vimeocdn.com/video/ad_1280",
                note=generate_pages.NoteContent(title_html="Ad", body_html="Body"),
                note_media=generate_pages.MediaItem(
                    2,
                    root / "editable-content" / "works" / "commercials" / "sample-ad" / "note" / "2_note.webp",
                    "image",
                ),
                highlight_media=(),
                bts_text_html="Credits",
                bts_media=(),
                category="commercials",
            )
            template = (
                "{{ROOT_SECTION_TRACKER_LINKS}}"
                "{{WORK_CATEGORY_TRACKER_LINKS}}"
                "{{WORKS_INDEX_SECTIONS}}"
                "{{SHARED_EFFECTS_CSS_URL}}"
                "{{PORTFOLIO_GRID_JS_URL}}"
                "{{HERO_ILLUSTRATION_SVG}}"
            )

            with (
                mock.patch.object(generate_pages, "REPO_ROOT", root),
                mock.patch.object(generate_pages, "GENERATED_WEBSITE_DIR", generated_site),
                mock.patch.object(generate_pages, "WORKS_OUTPUT_DIR", works_output),
                mock.patch.object(generate_pages, "HERO_ILLUSTRATION", illustration),
            ):
                rendered = generate_pages.render_home(
                    (commercial, film),
                    template,
                    output_html,
                )

        films_index = rendered.index('id="films"')
        commercials_index = rendered.index('id="commercials"')

        self.assertLess(films_index, commercials_index)
        self.assertIn('data-work-category-link="films"', rendered)
        self.assertIn('data-work-category-link="commercials"', rendered)
        self.assertIn('<span>films</span>', rendered)
        self.assertIn('<span>commercials</span>', rendered)
        self.assertIn('data-work-category-section="films"', rendered)
        self.assertIn('data-work-category-section="commercials"', rendered)
        self.assertIn('href="works/sample-film/"', rendered)
        self.assertIn('href="works/sample-ad/"', rendered)
        self.assertIn("works-grid-title-chevron", rendered)
        self.assertIn("interactive-chevron--right", rendered)
        self.assertIn("css/shared-effects.css", rendered)
        self.assertIn('src="https://i.vimeocdn.com/video/film_1280"', rendered)
        self.assertIn('src="https://i.vimeocdn.com/video/ad_1280"', rendered)
        self.assertIn("js/portfolio-grid.js", rendered)
        self.assertIn("<svg></svg>", rendered)

    def test_render_works_redirect_points_to_root_works_anchor(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            generated_site = root / "generated-website"
            output_html = generated_site / "works" / "index.html"
            template = "{{ROOT_WORKS_URL}}"

            with (
                mock.patch.object(generate_pages, "REPO_ROOT", root),
                mock.patch.object(generate_pages, "GENERATED_WEBSITE_DIR", generated_site),
            ):
                rendered = generate_pages.render_works_redirect(template, output_html)

        self.assertEqual(rendered, "../#works")


if __name__ == "__main__":
    unittest.main()
