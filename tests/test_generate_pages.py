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

        html = generate_pages.render_trailer_section(work)

        self.assertIn('class="trailer-poster"', html)
        self.assertIn('src="https://i.vimeocdn.com/video/example_1280"', html)
        self.assertNotIn("trailer-poster--placeholder", html)

    def test_ordered_media_sorts_by_numeric_prefix(self):
        with tempfile.TemporaryDirectory() as tmp:
            media_dir = Path(tmp)
            (media_dir / "10_late.webp").write_text("", encoding="utf-8")
            (media_dir / "2_middle.mp4").write_text("", encoding="utf-8")
            (media_dir / "1_first.webp").write_text("", encoding="utf-8")
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
            note_file = Path(tmp) / "text.md"
            note_file.write_text(
                "# A title with *emphasis*\n\n"
                "First body line.\n"
                "Second body line.",
                encoding="utf-8",
            )

            note = generate_pages.parse_note_text(note_file)

        self.assertEqual(note.title_html, "A title with <em>emphasis</em>")
        self.assertEqual(note.body_html, "First body line.<br>Second body line.")

    def test_default_layout_preserves_current_five_item_highlight_shape(self):
        self.assertEqual(generate_pages.default_grid_layout(5), "7-5, 4-5-3")

    def test_discover_work_dirs_traverses_commercials_and_films(self):
        with tempfile.TemporaryDirectory() as tmp:
            pages_works = Path(tmp) / "pages" / "works"
            commercial = pages_works / "commercials" / "sample-ad"
            film = pages_works / "films" / "sample-film"
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

            work_dirs = generate_pages.discover_work_dirs(pages_works)

        self.assertEqual(
            [path.relative_to(pages_works).as_posix() for path in work_dirs],
            ["films/sample-film", "commercials/sample-ad"],
        )

    def test_discover_work_dirs_rejects_duplicate_slugs_across_categories(self):
        with tempfile.TemporaryDirectory() as tmp:
            pages_works = Path(tmp) / "pages" / "works"
            commercial = pages_works / "commercials" / "same-slug"
            film = pages_works / "films" / "same-slug"
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
                generate_pages.discover_work_dirs(pages_works)

    def test_generate_writes_category_source_to_public_work_page(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "pages" / "works" / "films" / "sample-work"
            output = root / "works"
            template = root / "templates" / "work-page.html"

            (source / "trailer").mkdir(parents=True)
            (source / "trailer" / "trailer_link.md").write_text(
                "https://vimeo.com/123456789",
                encoding="utf-8",
            )
            (source / "note" / "media").mkdir(parents=True)
            (source / "note" / "text.md").write_text(
                "# Sample Work\n\nA sample note.",
                encoding="utf-8",
            )
            (source / "note" / "media" / "1_note.webp").write_text(
                "webp",
                encoding="utf-8",
            )
            (source / "highlight" / "media").mkdir(parents=True)
            (source / "highlight" / "media" / "1_highlight.webp").write_text(
                "webp",
                encoding="utf-8",
            )
            (source / "bts" / "media").mkdir(parents=True)
            (source / "bts" / "text.md").write_text("Credits", encoding="utf-8")
            (source / "bts" / "media" / "1_bts.webp").write_text(
                "webp",
                encoding="utf-8",
            )
            template.parent.mkdir()
            template.write_text(
                "<title>{{DOCUMENT_TITLE}}</title>"
                "{{WORK_CATEGORY}}"
                "{{ROOT_INDEX_URL}}"
                "{{PORTFOLIO_GRID_JS_URL}}"
                "{{WORK_SECTIONS}}",
                encoding="utf-8",
            )

            with (
                contextlib.redirect_stdout(io.StringIO()),
                mock.patch.object(generate_pages, "REPO_ROOT", root),
                mock.patch.object(generate_pages, "PAGES_WORKS_DIR", source.parent.parent),
                mock.patch.object(generate_pages, "WORKS_OUTPUT_DIR", output),
                mock.patch.object(generate_pages, "WORK_PAGE_TEMPLATE", template),
                mock.patch.object(generate_pages, "vimeo_thumbnail_url", return_value=None),
            ):
                failures = generate_pages.generate(selected_slug="sample-work")

            output_html = output / "sample-work" / "index.html"
            subpages_output_html = root / "works" / "subpages" / "sample-work" / "index.html"

            self.assertEqual(failures, 0)
            self.assertTrue(output_html.exists())
            self.assertFalse(subpages_output_html.exists())
            generated = output_html.read_text(encoding="utf-8")
            self.assertIn("films", generated)
            self.assertIn("../../index.html", generated)
            self.assertIn("../../js/portfolio-grid.js", generated)

    def test_render_works_index_uses_category_sections_and_trailer_posters(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            works_output = root / "works"
            output_html = works_output / "index.html"
            film = generate_pages.WorkContent(
                slug="sample-film",
                title="Sample Film",
                trailer_embed_url="https://player.vimeo.com/video/1",
                trailer_poster_url="https://i.vimeocdn.com/video/film_1280",
                note=generate_pages.NoteContent(title_html="Film", body_html="Body"),
                note_media=generate_pages.MediaItem(
                    1,
                    root / "pages" / "works" / "films" / "sample-film" / "note" / "media" / "1_note.webp",
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
                    1,
                    root / "pages" / "works" / "commercials" / "sample-ad" / "note" / "media" / "1_note.webp",
                    "image",
                ),
                highlight_media=(),
                bts_text_html="Credits",
                bts_media=(),
                category="commercials",
            )
            template = (
                "{{SECTION_TRACKER_LINKS}}"
                "{{WORKS_INDEX_SECTIONS}}"
                "{{ROOT_INDEX_URL}}"
                "{{PORTFOLIO_GRID_JS_URL}}"
            )

            with (
                mock.patch.object(generate_pages, "REPO_ROOT", root),
                mock.patch.object(generate_pages, "WORKS_OUTPUT_DIR", works_output),
            ):
                rendered = generate_pages.render_works_index(
                    (commercial, film),
                    template,
                    output_html,
                )

        films_index = rendered.index('id="films"')
        commercials_index = rendered.index('id="commercials"')

        self.assertLess(films_index, commercials_index)
        self.assertIn('href="sample-film/"', rendered)
        self.assertIn('href="sample-ad/"', rendered)
        self.assertIn('src="https://i.vimeocdn.com/video/film_1280"', rendered)
        self.assertIn('src="https://i.vimeocdn.com/video/ad_1280"', rendered)
        self.assertIn("../index.html", rendered)
        self.assertIn("../js/portfolio-grid.js", rendered)


if __name__ == "__main__":
    unittest.main()
