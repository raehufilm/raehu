import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import generate_pages


class GeneratePagesTests(unittest.TestCase):
    def sample_about_content(self):
        return generate_pages.AboutContent(
            title_html="about",
            body_html="<p>About body.</p>",
            contact_html='<span class="about-location"><span>Shanghai · Mexico City</span></span>',
            title_html_chinese="about",
            body_html_chinese="<p>About body.</p>",
            contact_html_chinese='<span class="about-location"><span>Shanghai · Mexico City</span></span>',
            title_html_spanish="about",
            body_html_spanish="<p>About body.</p>",
            contact_html_spanish='<span class="about-location"><span>Shanghai · Mexico City</span></span>',
            image_html="",
            quote_html='"Quote."',
        )

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

    def test_load_about_content_uses_numbered_about_image(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            about_dir = root / "editable-content" / "about"
            about_dir.mkdir(parents=True)
            text_path = about_dir / "text.md"
            quote_path = about_dir / "quote.md"
            text_path.write_text(
                "# about\n\n"
                "About body.\n\n"
                "Email: raehufilm@gmail.com\n",
                encoding="utf-8",
            )
            quote_path.write_text("> Quote line.\n", encoding="utf-8")
            (about_dir / "1_image.webp").write_text("webp", encoding="utf-8")

            about = generate_pages.load_about_content(
                text_path=text_path,
                quote_path=quote_path,
                about_dir=about_dir,
                output_html=root / "generated-website" / "index.html",
            )

        self.assertIn('class="about-image"', about.image_html)
        self.assertIn("../editable-content/about/1_image.webp", about.image_html)
        self.assertEqual(about.title_html_chinese, about.title_html)
        self.assertEqual(about.body_html_chinese, about.body_html)
        self.assertEqual(about.contact_html_chinese, about.contact_html)
        self.assertEqual(about.title_html_spanish, about.title_html)
        self.assertEqual(about.body_html_spanish, about.body_html)
        self.assertEqual(about.contact_html_spanish, about.contact_html)

    def test_load_about_content_uses_chinese_text_when_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            about_dir = root / "editable-content" / "about"
            about_dir.mkdir(parents=True)
            text_path = about_dir / "text.md"
            quote_path = about_dir / "quote.md"
            text_path.write_text(
                "# about\n\n"
                "English body.\n\n"
                "Email: raehufilm@gmail.com\n",
                encoding="utf-8",
            )
            (about_dir / "text_chinese.md").write_text(
                "# 关于\n\n"
                "中文正文。\n\n"
                "Email: raehufilm@gmail.com\n",
                encoding="utf-8",
            )
            quote_path.write_text("> Quote line.\n", encoding="utf-8")

            about = generate_pages.load_about_content(
                text_path=text_path,
                quote_path=quote_path,
                about_dir=about_dir,
                output_html=root / "generated-website" / "index.html",
            )

        self.assertEqual(about.title_html_chinese, "关于")
        self.assertIn("中文正文。", about.body_html_chinese)

    def test_load_about_content_uses_spanish_text_when_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            about_dir = root / "editable-content" / "about"
            about_dir.mkdir(parents=True)
            text_path = about_dir / "text.md"
            quote_path = about_dir / "quote.md"
            text_path.write_text(
                "# about\n\n"
                "English body.\n\n"
                "Email: raehufilm@gmail.com\n",
                encoding="utf-8",
            )
            (about_dir / "text_spanish.md").write_text(
                "# sobre\n\n"
                "Texto en español.\n\n"
                "Email: raehufilm@gmail.com\n",
                encoding="utf-8",
            )
            quote_path.write_text("> Quote line.\n", encoding="utf-8")

            about = generate_pages.load_about_content(
                text_path=text_path,
                quote_path=quote_path,
                about_dir=about_dir,
                output_html=root / "generated-website" / "index.html",
            )

        self.assertEqual(about.title_html_spanish, "sobre")
        self.assertIn("Texto en español.", about.body_html_spanish)

    def test_alternate_language_path_adds_language_before_suffix(self):
        path = Path("editable-content/about/text.md")

        self.assertEqual(
            generate_pages.alternate_language_path(path, "chinese"),
            Path("editable-content/about/text_chinese.md"),
        )
        self.assertEqual(
            generate_pages.alternate_language_path(path, "spanish"),
            Path("editable-content/about/text_spanish.md"),
        )

    def test_load_localized_markdown_lines_defaults_to_english_without_alternate(self):
        with tempfile.TemporaryDirectory() as tmp:
            text_path = Path(tmp) / "text.md"
            text_path.write_text("English body.", encoding="utf-8")

            (
                english_html,
                chinese_html,
                spanish_html,
            ) = generate_pages.load_localized_markdown_lines(text_path)

        self.assertEqual(english_html, "English body.")
        self.assertEqual(chinese_html, "English body.")
        self.assertEqual(spanish_html, "English body.")

    def test_about_quote_rejects_section_divider_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            quote_path = Path(tmp) / "quote.md"
            quote_path.write_text("> Quote line.\n\nAnd... action!\n", encoding="utf-8")

            with self.assertRaises(generate_pages.PageGenerationError) as context:
                generate_pages.parse_about_quote(quote_path)

        self.assertIn("Section divider text is built into the website template", str(context.exception))

    def test_home_template_uses_paused_ellipsis_dividers(self):
        template = generate_pages.read_text(generate_pages.HOME_TEMPLATE)

        self.assertIn('aria-label="And... action!"', template)
        self.assertIn('aria-label="...AND CUT!"', template)
        self.assertIn('aria-label="Camera, rolling!"', template)
        self.assertIn("--section-divider-ellipsis-pause-duration", template)
        self.assertIn("--section-divider-camera-pause-duration", template)
        self.assertIn('section-divider-segment--ellipsis" aria-hidden="true">...</span>', template)
        self.assertIn(
            'section-divider-segment--camera-prefix" aria-hidden="true">Camera,</span>',
            template,
        )
        self.assertIn(
            'section-divider-segment--camera-suffix" aria-hidden="true">&nbsp;rolling!</span>',
            template,
        )
        self.assertIn(
            'section-divider-segment--suffix" aria-hidden="true">&nbsp;action!</span>',
            template,
        )
        self.assertIn(
            "--section-divider-dot-delay: calc(\n        "
            "var(--section-divider-camera-suffix-delay) + var(--section-divider-camera-suffix-duration)\n      );",
            template,
        )
        self.assertIn(
            "--section-divider-dot-delay: calc(\n        "
            "var(--section-divider-reveal-duration) + var(--section-divider-reveal-delay)\n      );",
            template,
        )
        self.assertIn("--section-divider-dot-cycle-duration: 1.6s;", template)
        self.assertIn(
            "animation: pulse var(--section-divider-dot-cycle-duration) ease-in-out forwards;",
            template,
        )
        self.assertNotIn("section-divider-dot-fade-out", template)
        self.assertNotIn("......", template)

    def test_load_about_image_requires_numbered_prefix(self):
        with tempfile.TemporaryDirectory() as tmp:
            about_dir = Path(tmp) / "editable-content" / "about"
            about_dir.mkdir(parents=True)
            (about_dir / "image.webp").write_text("webp", encoding="utf-8")

            with self.assertRaises(generate_pages.PageGenerationError) as context:
                generate_pages.load_about_image(about_dir)

        self.assertIn("must start with NUMBER_", str(context.exception))

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
            output_html = root / "generated-website" / "work" / "sample" / "index.html"
            media = (
                root
                / "editable-content"
                / "work"
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

    def test_render_commercial_primary_section_is_film(self):
        work = generate_pages.WorkContent(
            slug="sample-ad",
            title="Sample Ad",
            trailer_embed_url="https://player.vimeo.com/video/123",
            trailer_poster_url="https://i.vimeocdn.com/video/example_1280",
            note=generate_pages.NoteContent(title_html="Title", body_html="Body"),
            note_media=generate_pages.MediaItem(1, Path("note.webp"), "image"),
            highlight_media=(),
            bts_text_html="Credits",
            bts_media=(),
            category="commercials",
        )

        html = generate_pages.render_trailer_section(work, Path("index.html"))

        self.assertIn('id="film"', html)
        self.assertIn('data-section-page="film"', html)
        self.assertIn('data-section-title="Film"', html)
        self.assertIn('aria-label="Play film"', html)

    def test_render_primary_links_below_primary_media(self):
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
            primary_links=(
                generate_pages.PrimaryLink("view full film", "https://vimeo.com/123"),
                generate_pages.PrimaryLink("second link", "https://example.com"),
            ),
        )

        html = generate_pages.render_trailer_section(work, Path("index.html"))

        self.assertIn("primary-section-layout--has-links", html)
        self.assertIn('class="primary-section-links"', html)
        self.assertIn('class="primary-section-link-chevron"', html)
        self.assertIn("interactive-chevron--right", html)
        self.assertIn('href="https://vimeo.com/123"', html)
        self.assertIn(">view full film</span>", html)
        self.assertGreater(html.index("trailer-wrap"), html.index("primary-section-layout"))
        self.assertGreater(html.index("primary-section-links"), html.index("trailer-wrap"))

    def test_load_primary_links_rejects_invalid_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "additional_links.md"
            path.write_text("[good](https://example.com)\nnot a link\n", encoding="utf-8")

            with self.assertRaises(generate_pages.PageGenerationError) as context:
                generate_pages.load_primary_links(path)

        message = str(context.exception)
        self.assertIn("additional_links.md line 2", message)
        self.assertIn("[view full film](https://vimeo.com/123456789)", message)

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

    def test_load_note_content_uses_chinese_companion_without_counting_it_as_extra_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            note_dir = Path(tmp)
            (note_dir / "2_text.md").write_text(
                "# English Title\n\nEnglish body.",
                encoding="utf-8",
            )
            (note_dir / "2_text_chinese.md").write_text(
                "# 中文标题\n\n中文正文。",
                encoding="utf-8",
            )

            note = generate_pages.load_note_content(note_dir)

        self.assertEqual(note.index, 2)
        self.assertEqual(note.title_html_chinese, "中文标题")
        self.assertEqual(note.body_html_chinese, "中文正文。")

    def test_load_note_content_uses_spanish_companion_without_counting_it_as_extra_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            note_dir = Path(tmp)
            (note_dir / "2_text.md").write_text(
                "# English Title\n\nEnglish body.",
                encoding="utf-8",
            )
            (note_dir / "2_text_spanish.md").write_text(
                "# Título en español\n\nTexto en español.",
                encoding="utf-8",
            )

            note = generate_pages.load_note_content(note_dir)

        self.assertEqual(note.index, 2)
        self.assertEqual(note.title_html_spanish, "Título en español")
        self.assertEqual(note.body_html_spanish, "Texto en español.")

    def test_render_note_orders_media_before_text_when_media_is_position_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output_html = root / "generated-website" / "work" / "sample" / "index.html"
            media = (
                root
                / "editable-content"
                / "work"
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
        self.assertIn('data-language-content="en"', rendered)
        self.assertIn('data-language-content="cn"', rendered)
        self.assertIn('data-language-content="es"', rendered)

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
            output_html = root / "generated-website" / "work" / "sample-work" / "index.html"
            media_path = (
                root
                / "editable-content"
                / "work"
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
            editable_work = Path(tmp) / "editable-content" / "work"
            commercial = editable_work / "commercials" / "sample-ad"
            film = editable_work / "films" / "sample-film"
            (commercial / "film").mkdir(parents=True)
            (film / "trailer").mkdir(parents=True)
            (commercial / "film" / "film_link.md").write_text(
                "https://vimeo.com/1",
                encoding="utf-8",
            )
            (film / "trailer" / "trailer_link.md").write_text(
                "https://vimeo.com/2",
                encoding="utf-8",
            )

            work_dirs = generate_pages.discover_work_dirs(editable_work)

        self.assertEqual(
            [path.relative_to(editable_work).as_posix() for path in work_dirs],
            ["films/sample-film", "commercials/sample-ad"],
        )

    def test_discover_work_dirs_rejects_duplicate_slugs_across_categories(self):
        with tempfile.TemporaryDirectory() as tmp:
            editable_work = Path(tmp) / "editable-content" / "work"
            commercial = editable_work / "commercials" / "same-slug"
            film = editable_work / "films" / "same-slug"
            (commercial / "film").mkdir(parents=True)
            (film / "trailer").mkdir(parents=True)
            (commercial / "film" / "film_link.md").write_text(
                "https://vimeo.com/1",
                encoding="utf-8",
            )
            (film / "trailer" / "trailer_link.md").write_text(
                "https://vimeo.com/2",
                encoding="utf-8",
            )

            with self.assertRaises(generate_pages.PageGenerationError):
                generate_pages.discover_work_dirs(editable_work)

    def test_generate_writes_category_source_to_public_work_page(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "editable-content" / "work" / "films" / "sample-work"
            generated_site = root / "generated-website"
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
                "{{WORK_CATEGORY_LABEL}}"
                "{{WORK_CATEGORY_LABEL_HTML}}"
                "{{WORK_CATEGORY_URL}}"
                "{{ROOT_INDEX_URL}}"
                "{{SITE_HEADER_CSS_URL}}"
                "{{SHARED_EFFECTS_CSS_URL}}"
                "{{PORTFOLIO_GRID_JS_URL}}"
                "{{LOCAL_PREVIEW_LINKS_JS_URL}}"
                "{{PREFERENCES_JS_URL}}"
                "{{LANGUAGE_INIT_JS_URL}}"
                "{{LANGUAGE_TOGGLE_JS_URL}}"
                "{{WORK_SECTIONS}}",
                encoding="utf-8",
            )
            (source_assets / "css").mkdir(parents=True)
            (source_assets / "js").mkdir(parents=True)
            (source_assets / "css" / "shared-effects.css").write_text("", encoding="utf-8")
            (source_assets / "js" / "portfolio-grid.js").write_text("", encoding="utf-8")
            (source_assets / "js" / "local-preview-links.js").write_text("", encoding="utf-8")

            with (
                contextlib.redirect_stdout(io.StringIO()),
                mock.patch.object(generate_pages, "REPO_ROOT", root),
                mock.patch.object(generate_pages, "EDITABLE_WORK_DIR", source.parent.parent),
                mock.patch.object(generate_pages, "GENERATED_WEBSITE_DIR", generated_site),
                mock.patch.object(generate_pages, "WORK_PAGE_TEMPLATE", template),
                mock.patch.object(generate_pages, "SITE_SOURCE_ASSETS_DIR", source_assets),
                mock.patch.object(generate_pages, "vimeo_thumbnail_url", return_value=None),
            ):
                failures = generate_pages.generate(selected_slug="sample-work")

            output_html = generated_site / "films" / "sample-work" / "index.html"
            old_works_output_html = generated_site / "work" / "sample-work" / "index.html"

            self.assertEqual(failures, 0)
            self.assertTrue(output_html.exists())
            self.assertFalse(old_works_output_html.exists())
            generated = output_html.read_text(encoding="utf-8")
            self.assertIn("films", generated)
            self.assertIn('<span data-language-content="cn">电影</span>', generated)
            self.assertIn('<span data-language-content="es">películas</span>', generated)
            self.assertNotIn("{{WORK_CATEGORY_LABEL_HTML}}", generated)
            self.assertIn("../../", generated)
            self.assertIn("../../#films", generated)
            self.assertIn("../../css/site-header.css", generated)
            self.assertIn("../../css/shared-effects.css", generated)
            self.assertIn("../../js/portfolio-grid.js", generated)
            self.assertIn("../../js/local-preview-links.js", generated)
            self.assertIn("../../js/preferences.js", generated)
            self.assertIn("../../js/language-init.js", generated)
            self.assertIn("../../js/language-toggle.js", generated)

    def test_commercial_loads_film_folder_and_renders_film_tracker(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "editable-content" / "work" / "commercials" / "sample-ad"
            output_html = root / "generated-website" / "commercials" / "sample-ad" / "index.html"

            (source / "film").mkdir(parents=True)
            (source / "film" / "film_link.md").write_text(
                "https://vimeo.com/123456789",
                encoding="utf-8",
            )
            (source / "film" / "additional_links.md").write_text(
                "[view full film](https://vimeo.com/123456789)\n",
                encoding="utf-8",
            )
            (source / "note").mkdir(parents=True)
            (source / "note" / "1_text.md").write_text(
                "# Sample Ad\n\nA sample note.",
                encoding="utf-8",
            )
            (source / "note" / "2_note.webp").write_text("webp", encoding="utf-8")
            (source / "highlight").mkdir(parents=True)
            (source / "highlight" / "1_highlight.webp").write_text(
                "webp",
                encoding="utf-8",
            )
            (source / "bts").mkdir(parents=True)
            (source / "bts" / "text.md").write_text("Credits", encoding="utf-8")
            (source / "bts" / "1_bts.webp").write_text("webp", encoding="utf-8")

            with mock.patch.object(generate_pages, "vimeo_thumbnail_url", return_value=None):
                work = generate_pages.load_work(source)
            rendered = generate_pages.render_work(
                work,
                "{{SECTION_TRACKER_LINKS}}{{WORK_SECTIONS}}",
                output_html,
            )

        self.assertIn('<span data-language-content="en">film</span>', rendered)
        self.assertIn('<span data-language-content="cn">影片</span>', rendered)
        self.assertIn('<span data-language-content="es">cine</span>', rendered)
        self.assertNotIn("<span>trailer</span>", rendered)
        self.assertIn('id="film"', rendered)
        self.assertIn('data-section-title="Film"', rendered)
        self.assertIn('href="https://vimeo.com/123456789"', rendered)
        self.assertIn(">view full film</span>", rendered)

    def test_load_work_rejects_multiple_trailer_sources_with_actionable_message(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "editable-content" / "work" / "films" / "sample-work"

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
            source = root / "editable-content" / "work" / "films" / "sample-work"

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
                / "work"
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

    def test_works_index_grid_uses_optional_grid_preview_before_primary_preview(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output_html = root / "generated-website" / "index.html"
            primary_media = (
                root
                / "editable-content"
                / "work"
                / "commercials"
                / "sample-work"
                / "film"
                / "1_film.mp4"
            )
            grid_preview_media = (
                root
                / "editable-content"
                / "work"
                / "commercials"
                / "sample-work"
                / "grid_preview"
                / "1_preview.webp"
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
                category="commercials",
                trailer_media=generate_pages.MediaItem(1, primary_media, "video"),
                grid_preview_media=generate_pages.MediaItem(1, grid_preview_media, "image"),
            )

            rendered = generate_pages.render_works_index_grid_item(work, output_html)

        self.assertIn("<img", rendered)
        self.assertIn("grid_preview/1_preview.webp", rendered)
        self.assertNotIn("film/1_film.mp4", rendered)

    def test_load_work_rejects_multiple_grid_preview_media(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "editable-content" / "work" / "films" / "sample-work"

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
            (source / "note" / "2_note.webp").write_text("webp", encoding="utf-8")
            (source / "highlight").mkdir(parents=True)
            (source / "highlight" / "1_highlight.webp").write_text("webp", encoding="utf-8")
            (source / "bts").mkdir(parents=True)
            (source / "bts" / "text.md").write_text("Credits", encoding="utf-8")
            (source / "bts" / "1_bts.webp").write_text("webp", encoding="utf-8")
            (source / "grid_preview").mkdir()
            (source / "grid_preview" / "1_preview.webp").write_text("webp", encoding="utf-8")
            (source / "grid_preview" / "2_preview.webp").write_text("webp", encoding="utf-8")

            with self.assertRaises(generate_pages.PageGenerationError) as context:
                generate_pages.load_work(source)

        message = str(context.exception)
        self.assertIn("multiple grid preview media files", message)
        self.assertIn("Keep exactly one", message)

    def test_render_home_uses_category_sections_and_trailer_posters(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            generated_site = root / "generated-website"
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
                    root / "editable-content" / "work" / "films" / "sample-film" / "note" / "2_note.webp",
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
                    root / "editable-content" / "work" / "commercials" / "sample-ad" / "note" / "2_note.webp",
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
                "{{SITE_HEADER_CSS_URL}}"
                "{{SHARED_EFFECTS_CSS_URL}}"
                "{{PORTFOLIO_GRID_JS_URL}}"
                "{{LOCAL_PREVIEW_LINKS_JS_URL}}"
                "{{PREFERENCES_JS_URL}}"
                "{{LANGUAGE_INIT_JS_URL}}"
                "{{LANGUAGE_TOGGLE_JS_URL}}"
                "{{THEME_TOGGLE_JS_URL}}"
                "{{SITE_HEADER_ACTIONS}}"
                "{{ABOUT_TITLE_CHINESE}}"
                "{{ABOUT_BODY_HTML_CHINESE}}"
                "{{ABOUT_CONTACT_HTML_CHINESE}}"
                "{{ABOUT_TITLE_SPANISH}}"
                "{{ABOUT_BODY_HTML_SPANISH}}"
                "{{ABOUT_CONTACT_HTML_SPANISH}}"
                "{{FAVICON_URL}}"
                "{{HERO_ILLUSTRATION_SVG}}"
            )

            with (
                mock.patch.object(generate_pages, "REPO_ROOT", root),
                mock.patch.object(generate_pages, "GENERATED_WEBSITE_DIR", generated_site),
                mock.patch.object(generate_pages, "HERO_ILLUSTRATION", illustration),
            ):
                rendered = generate_pages.render_home(
                    (commercial, film),
                    self.sample_about_content(),
                    template,
                    output_html,
                )

        films_index = rendered.index('id="films"')
        commercials_index = rendered.index('id="commercials"')

        self.assertLess(films_index, commercials_index)
        self.assertIn('data-work-category-link="films"', rendered)
        self.assertIn('data-work-category-link="commercials"', rendered)
        self.assertIn('<span data-language-content="en">work</span>', rendered)
        self.assertIn('<span data-language-content="cn">作品</span>', rendered)
        self.assertIn('<span data-language-content="es">obra</span>', rendered)
        self.assertIn('<span data-language-content="en">films</span>', rendered)
        self.assertIn('<span data-language-content="cn">电影</span>', rendered)
        self.assertIn('<span data-language-content="es">películas</span>', rendered)
        self.assertIn('<span data-language-content="en">commercials</span>', rendered)
        self.assertIn('<span data-language-content="cn">广告</span>', rendered)
        self.assertIn('<span data-language-content="es">anuncios</span>', rendered)
        self.assertIn('data-work-category-section="films"', rendered)
        self.assertIn('data-work-category-section="commercials"', rendered)
        self.assertIn('href="films/sample-film/"', rendered)
        self.assertIn('href="commercials/sample-ad/"', rendered)
        self.assertIn("works-grid-title-chevron", rendered)
        self.assertIn("interactive-chevron--right", rendered)
        self.assertIn("css/site-header.css", rendered)
        self.assertIn("css/shared-effects.css", rendered)
        self.assertIn("js/preferences.js", rendered)
        self.assertIn("js/language-init.js", rendered)
        self.assertIn("js/language-toggle.js", rendered)
        self.assertIn("js/theme-toggle.js", rendered)
        self.assertIn("data-language-menu", rendered)
        self.assertIn("data-language-option=\"cn\"", rendered)
        self.assertIn("data-language-option=\"es\"", rendered)
        self.assertIn("<p>About body.</p>", rendered)
        self.assertIn("images/favicon.svg", rendered)
        self.assertIn('src="https://i.vimeocdn.com/video/film_1280"', rendered)
        self.assertIn('src="https://i.vimeocdn.com/video/ad_1280"', rendered)
        self.assertIn("js/portfolio-grid.js", rendered)
        self.assertIn("js/local-preview-links.js", rendered)
        self.assertIn("<svg></svg>", rendered)

if __name__ == "__main__":
    unittest.main()
