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


if __name__ == "__main__":
    unittest.main()
