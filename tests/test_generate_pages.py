import contextlib
import html
import io
import itertools
import json
import re
import subprocess
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

    def test_parse_args_accepts_verify_generated_flag(self):
        args = generate_pages.parse_args(["--verify-generated"])

        self.assertTrue(args.verify_generated)

    def test_parse_args_rejects_old_check_flag(self):
        stderr = io.StringIO()

        with contextlib.redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as context:
                generate_pages.parse_args(["--check"])

        self.assertEqual(context.exception.code, 2)
        self.assertIn("unrecognized arguments: --check", stderr.getvalue())

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

    def test_home_template_divider_typewriter_steps_cover_every_character(self):
        template = generate_pages.read_text(generate_pages.HOME_TEMPLATE)
        step_rules = {
            f"section-divider-segment--{name}": int(steps)
            for name, steps in re.findall(
                r"\.section-divider-segment--([a-z-]+)\s*{[^}]*"
                r"--section-divider-segment-steps:\s*(\d+);",
                template,
                re.DOTALL,
            )
        }
        divider_blocks = re.findall(
            r'<div class="section-divider [^"]+">(?P<body>.*?)</div>',
            template,
            re.DOTALL,
        )

        self.assertEqual(len(divider_blocks), 3)
        for block_html in divider_blocks:
            aria_label_match = re.search(
                r'<span class="section-divider-text section-divider-text--segmented" aria-label="([^"]+)">',
                block_html,
            )
            self.assertIsNotNone(aria_label_match)
            aria_label = aria_label_match.group(1)
            segments = re.findall(
                r'<span class="section-divider-segment ([^"]+)" aria-hidden="true">'
                r"(.*?)</span>",
                block_html,
            )
            visible_parts = [
                html.unescape(raw_text).replace("\xa0", " ")
                for _, raw_text in segments
            ]

            self.assertTrue(segments)
            self.assertEqual("".join(visible_parts), aria_label)
            self.assertIn(aria_label[-1], {",", "!", "."})

            for (class_names, _), visible_text in zip(segments, visible_parts):
                segment_class = next(
                    name
                    for name in class_names.split()
                    if name.startswith("section-divider-segment--")
                )

                self.assertIn(segment_class, step_rules)
                self.assertGreaterEqual(
                    step_rules[segment_class],
                    len(visible_text),
                    f"{segment_class} should reveal all of {visible_text!r}",
                )

    def test_home_template_all_terminal_divider_punctuation_is_in_safe_suffix_spans(self):
        template = generate_pages.read_text(generate_pages.HOME_TEMPLATE)
        suffix_segments = re.findall(
            r'<span class="section-divider-segment ([^"]*section-divider-segment--(?:camera-suffix|suffix)[^"]*)" '
            r'aria-hidden="true">(.*?)</span>',
            template,
        )

        self.assertEqual(
            [
                html.unescape(text).replace("\xa0", " ")
                for _, text in suffix_segments
            ],
            [" rolling!", " action!", "AND CUT!"],
        )
        for class_names, raw_text in suffix_segments:
            visible_text = html.unescape(raw_text).replace("\xa0", " ")
            self.assertTrue(
                visible_text.endswith("!"),
                f"{class_names} should keep terminal punctuation inside the padded suffix span",
            )

    def test_home_template_divider_suffixes_have_layout_safe_clip_padding(self):
        template = generate_pages.read_text(generate_pages.HOME_TEMPLATE)
        suffix_rule = re.search(
            r"\.section-divider-segment--camera-suffix,\s*"
            r"\.section-divider-segment--suffix\s*{(?P<body>[^}]+)}",
            template,
            re.DOTALL,
        )
        segmented_rule = re.search(
            r"\.section-divider-text--segmented\s*{(?P<body>[^}]+)}",
            template,
            re.DOTALL,
        )
        inner_rule = re.search(
            r"\.section-divider-inner\s*{(?P<body>[^}]+)}",
            template,
            re.DOTALL,
        )

        self.assertIsNotNone(suffix_rule)
        self.assertIsNotNone(segmented_rule)
        self.assertIsNotNone(inner_rule)
        self.assertIn("--section-divider-suffix-reveal-padding: 0.45em;", template)
        self.assertIn(
            "padding-right: var(--section-divider-suffix-reveal-padding);",
            suffix_rule.group("body"),
        )
        self.assertNotIn("margin-right", suffix_rule.group("body"))
        self.assertIn("max-width: 100%;", segmented_rule.group("body"))
        self.assertIn("min-width: 0;", segmented_rule.group("body"))
        self.assertIn("max-width: 100%;", inner_rule.group("body"))
        self.assertIn("min-width: 0;", inner_rule.group("body"))

    def test_work_template_mobile_bts_stack_does_not_keep_desktop_min_height(self):
        template = generate_pages.read_text(generate_pages.WORK_PAGE_TEMPLATE)

        self.assertIn("@media (max-width: 700px)", template)
        self.assertIn(
            "      .work-page--bts {\n"
            "        --page-padding-top: 2rem;\n"
            "        min-height: 0;\n"
            "      }",
            template,
        )
        self.assertIn(
            "      .bts-slideshow {\n"
            "        width: 100%;\n"
            "        height: auto;\n"
            "        min-height: 0;\n"
            "        aspect-ratio: 16 / 9;\n"
            "      }",
            template,
        )

    def test_templates_keep_justified_grid_fill_black_in_light_mode(self):
        home_template = generate_pages.read_text(generate_pages.HOME_TEMPLATE)
        work_template = generate_pages.read_text(generate_pages.WORK_PAGE_TEMPLATE)

        self.assertIn("--grid-fill-bg: #000;", home_template)
        self.assertNotIn("--grid-fill-bg", home_template.split(':root[data-theme="light"]', 1)[1].split("}", 1)[0])
        self.assertIn(
            ".portfolio-grid[data-grid-mode=\"justify\"] {\n"
            "      align-items: flex-start;\n"
            "      background: var(--grid-fill-bg);\n"
            "    }",
            home_template,
        )
        self.assertIn(
            ".portfolio-grid[data-grid-mode=\"justify\"] > .portfolio-grid-row {\n"
            "      display: flex;\n"
            "      width: 100%;\n"
            "      align-items: flex-start;\n"
            "      background: var(--grid-fill-bg);\n"
            "    }",
            home_template,
        )
        self.assertIn(
            ".portfolio-grid[data-grid-mode=\"justify\"] .works-grid-link {\n"
            "      min-height: 0;\n"
            "      background: var(--grid-fill-bg);\n"
            "    }",
            home_template,
        )
        self.assertIn(
            ".portfolio-grid[data-grid-mode=\"justify\"] {\n"
            "      align-items: flex-start;\n"
            "      background: var(--media-bg);\n"
            "    }",
            work_template,
        )
        self.assertIn(
            ".portfolio-grid[data-grid-mode=\"justify\"] > .portfolio-grid-row > * {\n"
            "      min-height: 0;\n"
            "      margin: 0;\n"
            "      overflow: hidden;\n"
            "      background: var(--media-bg);\n"
            "    }",
            work_template,
        )

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
            (media_dir / "1_first.webp").write_text("", encoding="utf-8")
            (media_dir / "1_second.mp4").write_text("", encoding="utf-8")

            with self.assertRaises(generate_pages.PageGenerationError) as context:
                generate_pages.ordered_media(media_dir)

        message = str(context.exception)
        self.assertIn("STOP: Two or more files in the same section use the same order number.", message)
        self.assertIn("Folder:", message)
        self.assertIn(str(media_dir), message)
        self.assertIn("Number 1:", message)
        self.assertIn("  1_first.webp", message)
        self.assertIn("  1_second.mp4", message)
        self.assertIn("If you want ALL of these files to appear on the website:", message)
        self.assertIn("Rename files so each one starts with a different unused number.", message)
        self.assertIn("If one file replaced another and only ONE should appear:", message)
        self.assertIn("Delete the file you no longer want.", message)
        self.assertIn("Then run generate_website again.", message)
        self.assertIn("No commit, push, or publish was performed.", message)

    def test_ordered_media_reports_all_duplicate_prefixes_at_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            media_dir = Path(tmp)
            (media_dir / "1_ok.webp").write_text("", encoding="utf-8")
            (media_dir / "5_first.webp").write_text("", encoding="utf-8")
            (media_dir / "5_second.mp4").write_text("", encoding="utf-8")
            (media_dir / "5_third.webp").write_text("", encoding="utf-8")
            (media_dir / "8_fourth.mp4").write_text("", encoding="utf-8")
            (media_dir / "8_fifth.webp").write_text("", encoding="utf-8")

            with self.assertRaises(generate_pages.PageGenerationError) as context:
                generate_pages.ordered_media(media_dir)

        message = str(context.exception)
        self.assertIn("Number 5:", message)
        self.assertIn("  5_first.webp", message)
        self.assertIn("  5_second.mp4", message)
        self.assertIn("  5_third.webp", message)
        self.assertIn("Number 8:", message)
        self.assertIn("  8_fourth.mp4", message)
        self.assertIn("  8_fifth.webp", message)

    def test_ordered_media_check_mode_reports_duplicate_prefix_before_missing_webp(self):
        with tempfile.TemporaryDirectory() as tmp:
            media_dir = Path(tmp)
            (media_dir / "5_still.png").write_text("raw", encoding="utf-8")
            (media_dir / "5_clip.mp4").write_text("", encoding="utf-8")

            with self.assertRaises(generate_pages.PageGenerationError) as context:
                generate_pages.ordered_media(
                    media_dir,
                    check_generated_assets=True,
                )

        message = str(context.exception)
        self.assertIn("Number 5:", message)
        self.assertIn("  5_clip.mp4", message)
        self.assertIn("  5_still.png", message)
        self.assertNotIn("Converted WebP is missing", message)

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

            generate_pages._source_hash_cache[raw] = generate_pages.source_content_hash(raw)

            with mock.patch.object(generate_pages, "convert_image_to_webp") as convert:
                media = generate_pages.ordered_media(media_dir, write_assets=True)

            generate_pages._source_hash_cache.pop(raw, None)

        convert.assert_not_called()
        self.assertEqual(len(media), 1)
        self.assertEqual(media[0].path.name, "1_first.webp")

    def test_responsive_variants_skip_up_to_date_webp_conversion(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "editable-content" / "work" / "films" / "sample" / "highlight" / "1_first.webp"
            generated_site = root / "generated-website"
            source.parent.mkdir(parents=True)
            source.write_text("webp", encoding="utf-8")

            with (
                mock.patch.object(generate_pages, "REPO_ROOT", root),
                mock.patch.object(generate_pages, "GENERATED_WEBSITE_DIR", generated_site),
            ):
                for target in generate_pages.responsive_image_variant_paths(source):
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text("webp", encoding="utf-8")

                generate_pages._source_hash_cache[source] = generate_pages.source_content_hash(source)

                with mock.patch.object(generate_pages, "convert_image_to_webp") as convert:
                    generate_pages.ensure_responsive_image_variants(source, write_assets=True)

            generate_pages._source_hash_cache.pop(source, None)

        convert.assert_not_called()

    def test_grid_preview_video_transcode_skips_up_to_date_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = (
                root
                / "editable-content"
                / "work"
                / "commercials"
                / "sample"
                / "grid_preview"
                / "1_preview.mp4"
            )
            generated_site = root / "generated-website"
            source.parent.mkdir(parents=True)
            source.write_text("mp4", encoding="utf-8")

            with (
                mock.patch.object(generate_pages, "REPO_ROOT", root),
                mock.patch.object(generate_pages, "GENERATED_WEBSITE_DIR", generated_site),
            ):
                target = generate_pages.optimized_grid_preview_video_path(source)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("mp4", encoding="utf-8")

                generate_pages._source_hash_cache[source] = generate_pages.source_content_hash(source)

                with mock.patch.object(generate_pages, "transcode_grid_preview_video") as transcode:
                    optimized = generate_pages.ensure_optimized_grid_preview_video(
                        source,
                        write_assets=True,
                    )

            generate_pages._source_hash_cache.pop(source, None)

        transcode.assert_not_called()
        self.assertEqual(optimized.name, "1_preview-grid-preview-720p-v3.mp4")

    def test_responsive_variants_reconvert_when_source_content_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "editable-content" / "work" / "films" / "sample" / "highlight" / "1_first.webp"
            generated_site = root / "generated-website"
            source.parent.mkdir(parents=True)
            source.write_text("original content", encoding="utf-8")

            with (
                mock.patch.object(generate_pages, "REPO_ROOT", root),
                mock.patch.object(generate_pages, "GENERATED_WEBSITE_DIR", generated_site),
            ):
                for target in generate_pages.responsive_image_variant_paths(source):
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text("webp", encoding="utf-8")

                generate_pages._source_hash_cache[source] = "old_hash_from_different_content"

                with mock.patch.object(generate_pages, "convert_image_to_webp") as convert:
                    generate_pages.ensure_responsive_image_variants(source, write_assets=True)

            generate_pages._source_hash_cache.pop(source, None)
            generate_pages._current_hash_memo.clear()

        self.assertEqual(convert.call_count, len(generate_pages.RESPONSIVE_IMAGE_WIDTHS))

    def test_grid_preview_video_check_mode_requires_generated_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = (
                root
                / "editable-content"
                / "work"
                / "commercials"
                / "sample"
                / "grid_preview"
                / "1_preview.mp4"
            )
            source.parent.mkdir(parents=True)
            source.write_text("mp4", encoding="utf-8")

            with (
                mock.patch.object(generate_pages, "REPO_ROOT", root),
                mock.patch.object(generate_pages, "GENERATED_WEBSITE_DIR", root / "generated-website"),
                self.assertRaises(generate_pages.PageGenerationError) as context,
            ):
                generate_pages.ensure_optimized_grid_preview_video(
                    source,
                    write_assets=False,
                    check_generated_assets=True,
                )

        self.assertIn("Optimized grid preview video is missing", str(context.exception))

    def test_highlight_video_variants_skip_up_to_date_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = (
                root
                / "editable-content"
                / "work"
                / "commercials"
                / "sample"
                / "highlight"
                / "1_clip.mp4"
            )
            generated_site = root / "generated-website"
            source.parent.mkdir(parents=True)
            source.write_text("mp4", encoding="utf-8")

            with (
                mock.patch.object(generate_pages, "REPO_ROOT", root),
                mock.patch.object(generate_pages, "GENERATED_WEBSITE_DIR", generated_site),
            ):
                targets = generate_pages.highlight_tile_video_variant_paths(source)
                for target in targets:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text("mp4", encoding="utf-8")

                generate_pages._source_hash_cache[source] = generate_pages.source_content_hash(source)

                with mock.patch.object(generate_pages, "transcode_highlight_tile_video") as transcode:
                    variants = generate_pages.ensure_highlight_tile_video_variants(
                        source,
                        write_assets=True,
                    )

            generate_pages._source_hash_cache.pop(source, None)

        transcode.assert_not_called()
        self.assertEqual(
            [variant.name for variant in variants],
            ["1_clip-tile-480p-v1.mp4", "1_clip-tile-720p-v1.mp4"],
        )

    def test_highlight_video_variants_regenerate_when_source_content_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = (
                root
                / "editable-content"
                / "work"
                / "commercials"
                / "sample"
                / "highlight"
                / "1_clip.mp4"
            )
            generated_site = root / "generated-website"
            source.parent.mkdir(parents=True)
            source.write_text("new mp4", encoding="utf-8")

            def fake_transcode(_source_path, target_path, _width):
                target_path.parent.mkdir(parents=True, exist_ok=True)
                target_path.write_text("mp4", encoding="utf-8")

            with (
                mock.patch.object(generate_pages, "REPO_ROOT", root),
                mock.patch.object(generate_pages, "GENERATED_WEBSITE_DIR", generated_site),
            ):
                for target in generate_pages.highlight_tile_video_variant_paths(source):
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text("old mp4", encoding="utf-8")

                generate_pages._source_hash_cache[source] = "old_hash_from_different_content"

                with mock.patch.object(
                    generate_pages,
                    "transcode_highlight_tile_video",
                    side_effect=fake_transcode,
                ) as transcode:
                    generate_pages.ensure_highlight_tile_video_variants(
                        source,
                        write_assets=True,
                    )

            generate_pages._source_hash_cache.pop(source, None)
            generate_pages._current_hash_memo.clear()

        self.assertEqual(
            [call.args[2] for call in transcode.call_args_list],
            list(generate_pages.HIGHLIGHT_TILE_VIDEO_WIDTHS),
        )

    def test_highlight_video_check_mode_requires_generated_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = (
                root
                / "editable-content"
                / "work"
                / "commercials"
                / "sample"
                / "highlight"
                / "1_clip.mp4"
            )
            source.parent.mkdir(parents=True)
            source.write_text("mp4", encoding="utf-8")

            with (
                mock.patch.object(generate_pages, "REPO_ROOT", root),
                mock.patch.object(generate_pages, "GENERATED_WEBSITE_DIR", root / "generated-website"),
                self.assertRaises(generate_pages.PageGenerationError) as context,
            ):
                generate_pages.ensure_highlight_tile_video_variants(
                    source,
                    write_assets=False,
                    check_generated_assets=True,
                )

        message = str(context.exception)
        self.assertIn("Responsive highlight video variant is missing", message)
        self.assertIn("1_clip-tile-480p-v1.mp4", message)
        self.assertIn("1_clip-tile-720p-v1.mp4", message)

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
        self.assertIn('data-grid-mode="justify"', rendered)
        self.assertIn('data-justify-max-items="3"', rendered)
        self.assertIn('loading="eager"', rendered)
        self.assertNotIn("data-row-height", rendered)
        self.assertNotIn("data-mobile-row-height", rendered)
        self.assertIn("interactive-chevron--expand-ne", rendered)
        self.assertIn("interactive-chevron--expand-sw", rendered)
        self.assertIn("data-highlight-expand", rendered)
        self.assertIn("Expand highlight media", rendered)

    def test_render_highlight_video_uses_generated_tile_variants_and_original_full_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            generated_site = root / "generated-website"
            output_html = generated_site / "commercials" / "sample-work" / "index.html"
            media_path = (
                root
                / "editable-content"
                / "work"
                / "commercials"
                / "sample-work"
                / "highlight"
                / "1_clip.mp4"
            )
            work = generate_pages.WorkContent(
                slug="sample-work",
                title="Sample Work",
                trailer_embed_url="https://player.vimeo.com/video/123",
                trailer_poster_url=None,
                note=None,
                note_media=None,
                highlight_media=(
                    generate_pages.MediaItem(1, media_path, "video"),
                ),
                bts_text_html=None,
                bts_media=(),
                category="commercials",
            )

            with (
                mock.patch.object(generate_pages, "REPO_ROOT", root),
                mock.patch.object(generate_pages, "GENERATED_WEBSITE_DIR", generated_site),
            ):
                rendered = generate_pages.render_highlight_section(work, output_html)
                variant_480 = generate_pages.output_relative_url(
                    output_html,
                    generate_pages.highlight_tile_video_variant_path(media_path, 480),
                )
                variant_720 = generate_pages.output_relative_url(
                    output_html,
                    generate_pages.highlight_tile_video_variant_path(media_path, 720),
                )
                full_src = generate_pages.output_relative_url(output_html, media_path)

        self.assertIn('<video class="highlight-media media-hover-zoom-target"', rendered)
        self.assertIn("data-lazy-video", rendered)
        self.assertIn(f'data-src-480="{variant_480}"', rendered)
        self.assertIn(f'data-src-720="{variant_720}"', rendered)
        self.assertIn(f'data-full-src="{full_src}"', rendered)
        self.assertIn('preload="none"', rendered)
        self.assertNotIn(f' src="{full_src}"', rendered)

    def test_lazy_media_script_selects_responsive_video_sources(self):
        script = (
            Path(__file__).resolve().parents[1]
            / "site-source-assets"
            / "js"
            / "lazy-media.js"
        ).read_text(encoding="utf-8")

        self.assertIn("responsiveVideoSource", script)
        self.assertIn("data-src-(\\d+)", script)
        self.assertIn("devicePixelRatio", script)

    def test_highlight_lightbox_uses_original_video_source_when_expanded(self):
        template = (
            Path(__file__).resolve().parents[1]
            / "generator-templates"
            / "work-page.html"
        ).read_text(encoding="utf-8")

        self.assertIn("data-full-src", template)
        self.assertIn("clone.setAttribute('src', fullSource)", template)

    def test_portfolio_grid_justify_mode_uses_explicit_row_wrappers(self):
        script = (
            Path(__file__).resolve().parents[1]
            / "site-source-assets"
            / "js"
            / "portfolio-grid.js"
        ).read_text(encoding="utf-8")

        self.assertIn("portfolio-grid-row", script)
        self.assertIn("plannedJustifiedRowSizes", script)
        self.assertIn("rowSizesFromLayout", script)
        self.assertIn("mostlyPairRows", script)
        self.assertIn("bestScoredRowPlan", script)
        self.assertIn("scoreJustifiedRowPlan", script)
        self.assertIn("isUniformRowPlan", script)
        self.assertIn("nonUniformCandidatesOrOriginal", script)
        self.assertIn("document.createElement('div')", script)
        self.assertIn("rowEl.appendChild(child)", script)
        self.assertNotIn("container.style.flexWrap = 'wrap'", script)
        self.assertNotIn("currentDiff", script)
        self.assertNotIn("nextDiff", script)

    def test_portfolio_grid_justify_planner_scores_varied_row_rhythm(self):
        script_path = (
            Path(__file__).resolve().parents[1]
            / "site-source-assets"
            / "js"
            / "portfolio-grid.js"
        )
        node_script = f"""
const fs = require('fs');
global.window = {{ addEventListener() {{}}, setTimeout }};
global.document = {{
  readyState: 'loading',
  addEventListener() {{}},
  querySelectorAll() {{ return []; }}
}};
eval(fs.readFileSync({json.dumps(str(script_path))}, 'utf8'));
const ratios = [1.34, 1.78, 1.78, 1.78, 1.34, 1.6, 1.78, 1.78, 1.79];
const desktop = window.portfolioGrid.planJustifiedRows(
  9,
  101,
  3,
  false,
  '4-5-3, 7-5, 8-4, 7-5',
  ratios
);
const main = window.portfolioGrid.planJustifiedRows(
  13,
  202,
  3,
  false,
  '',
  Array(13).fill(16 / 9)
);
const mobile = window.portfolioGrid.planJustifiedRows(
  9,
  303,
  2,
  true,
  '',
  ratios
);
const desktopByCount = {{}};
const mobileByCount = {{}};
for (let count = 4; count <= 16; count += 1) {{
  desktopByCount[count] = window.portfolioGrid.planJustifiedRows(
    count,
    400 + count,
    3,
    false,
    '',
    Array(count).fill(16 / 9)
  );
  mobileByCount[count] = window.portfolioGrid.planJustifiedRows(
    count,
    800 + count,
    2,
    true,
    '',
    Array(count).fill(16 / 9)
  );
}}
console.log(JSON.stringify({{ desktop, main, mobile, desktopByCount, mobileByCount }}));
"""
        result = subprocess.run(
            ["node", "-e", node_script],
            check=True,
            capture_output=True,
            text=True,
        )
        plans = json.loads(result.stdout)

        self.assertEqual(sum(plans["desktop"]), 9)
        self.assertNotEqual(plans["desktop"], [3, 2, 2, 2])
        self.assertIn(3, plans["desktop"])
        self.assertIn(2, plans["desktop"])

        self.assertEqual(sum(plans["main"]), 13)
        self.assertGreaterEqual(plans["main"].count(3), 2)
        self.assertGreaterEqual(plans["main"].count(2), 2)
        self.assertLessEqual(
            max(
                len(list(group))
                for _, group in itertools.groupby(plans["main"])
            ),
            2,
        )

        self.assertEqual(sum(plans["mobile"]), 9)
        self.assertEqual(plans["mobile"].count(1), 1)
        self.assertEqual(plans["mobile"].count(2), 4)

        for count, plan in plans["desktopByCount"].items():
            self.assertEqual(sum(plan), int(count))
            if len(plan) > 1:
                self.assertGreater(
                    len(set(plan)),
                    1,
                    f"desktop count {count} should not use a uniform row plan: {plan}",
                )

        for count, plan in plans["mobileByCount"].items():
            self.assertEqual(sum(plan), int(count))
            if len(plan) > 1:
                self.assertGreater(
                    len(set(plan)),
                    1,
                    f"mobile count {count} should not use a uniform row plan: {plan}",
                )

    def test_current_site_justified_grids_use_non_uniform_row_counts(self):
        script_path = (
            Path(__file__).resolve().parents[1]
            / "site-source-assets"
            / "js"
            / "portfolio-grid.js"
        )
        works = tuple(
            generate_pages.load_work(
                work_dir,
                write_assets=False,
                fetch_vimeo_thumbnails=False,
            )
            for work_dir in generate_pages.discover_work_dirs(
                generate_pages.EDITABLE_WORK_DIR
            )
        )
        works_by_category = {
            category: tuple(work for work in works if work.category == category)
            for category in generate_pages.WORK_CATEGORIES
        }
        cases = [
            {
                "name": f"main/{category}",
                "count": len(works_by_category[category]),
                "seed": len(category),
                "layout": "",
                "ratios": [16 / 9] * len(works_by_category[category]),
            }
            for category in generate_pages.WORK_CATEGORIES
        ]
        cases.extend(
            {
                "name": f"{work.category}/{work.slug}/highlight",
                "count": len(work.highlight_media),
                "seed": generate_pages.stable_seed(
                    f"{work.category}/{work.slug}/highlight"
                ),
                "layout": generate_pages.highlight_grid_layout(
                    len(work.highlight_media),
                    f"{work.category}/{work.slug}",
                ),
                "ratios": [
                    (item.width / item.height)
                    if item.width and item.height
                    else 16 / 9
                    for item in work.highlight_media
                ],
            }
            for work in works
        )

        self.assertEqual(len(cases), len(works) + len(generate_pages.WORK_CATEGORIES))
        self.assertTrue(any(case["name"] == "main/films" for case in cases))
        self.assertTrue(any(case["name"] == "main/commercials" for case in cases))

        node_script = f"""
const fs = require('fs');
const cases = {json.dumps(cases)};
global.window = {{ addEventListener() {{}}, setTimeout }};
global.document = {{
  readyState: 'loading',
  addEventListener() {{}},
  querySelectorAll() {{ return []; }}
}};
eval(fs.readFileSync({json.dumps(str(script_path))}, 'utf8'));
const results = cases.map((testCase) => ({{
  name: testCase.name,
  count: testCase.count,
  desktop: window.portfolioGrid.planJustifiedRows(
    testCase.count,
    testCase.seed,
    3,
    false,
    testCase.layout,
    testCase.ratios
  ),
  mobile: window.portfolioGrid.planJustifiedRows(
    testCase.count,
    testCase.seed,
    2,
    true,
    testCase.layout,
    testCase.ratios
  )
}}));
console.log(JSON.stringify(results));
"""
        result = subprocess.run(
            ["node", "-e", node_script],
            check=True,
            capture_output=True,
            text=True,
        )
        results = json.loads(result.stdout)

        self.assertEqual(len(results), len(cases))
        for result in results:
            for viewport in ("desktop", "mobile"):
                plan = result[viewport]
                with self.subTest(grid=result["name"], viewport=viewport, plan=plan):
                    self.assertEqual(sum(plan), result["count"])
                    self.assertTrue(all(size > 0 for size in plan))
                    self.assertLessEqual(max(plan, default=0), 3 if viewport == "desktop" else 2)
                    if len(plan) > 1:
                        self.assertGreater(
                            len(set(plan)),
                            1,
                            f"{result['name']} {viewport} should not use one row size for every row: {plan}",
                        )

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
            (commercial / "highlight").mkdir(parents=True)
            (commercial / "highlight" / "1_img.jpg").write_bytes(b"\xff\xd8")
            (film / "trailer" / "trailer_link.md").write_text(
                "https://vimeo.com/2",
                encoding="utf-8",
            )
            (film / "highlight").mkdir(parents=True)
            (film / "highlight" / "1_img.jpg").write_bytes(b"\xff\xd8")

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
            (commercial / "highlight").mkdir(parents=True)
            (commercial / "highlight" / "1_img.jpg").write_bytes(b"\xff\xd8")
            (film / "trailer" / "trailer_link.md").write_text(
                "https://vimeo.com/2",
                encoding="utf-8",
            )
            (film / "highlight").mkdir(parents=True)
            (film / "highlight" / "1_img.jpg").write_bytes(b"\xff\xd8")

            with self.assertRaises(generate_pages.PageGenerationError):
                generate_pages.discover_work_dirs(editable_work)

    def test_discover_work_dirs_skips_draft_with_no_media(self):
        with tempfile.TemporaryDirectory() as tmp:
            editable_work = Path(tmp) / "editable-content" / "work"
            draft = editable_work / "films" / "draft-film"
            ready = editable_work / "films" / "ready-film"
            (draft / "note").mkdir(parents=True)
            (draft / "note" / "1_text.md").write_text("# Draft", encoding="utf-8")
            (draft / "highlight").mkdir(parents=True)
            (ready / "trailer").mkdir(parents=True)
            (ready / "trailer" / "trailer_link.md").write_text(
                "https://vimeo.com/1", encoding="utf-8"
            )
            (ready / "highlight").mkdir(parents=True)
            (ready / "highlight" / "1_img.jpg").write_bytes(b"\xff\xd8")

            warning = io.StringIO()
            with contextlib.redirect_stderr(warning):
                work_dirs = generate_pages.discover_work_dirs(editable_work)

            slugs = [d.name for d in work_dirs]
            self.assertNotIn("draft-film", slugs)
            self.assertIn("ready-film", slugs)
            warning_text = warning.getvalue()
            self.assertIn("WARNING: A work folder was skipped because it is not ready to publish.", warning_text)
            self.assertIn("editable-content/work/films/draft-film", warning_text)
            self.assertIn("Missing trailer/.", warning_text)
            self.assertIn("Missing highlight media.", warning_text)
            self.assertIn("Exactly one trailer source in trailer/", warning_text)
            self.assertIn("At least one numbered image or MP4 in highlight/.", warning_text)

    def test_discover_work_dirs_skips_draft_without_primary_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            editable_work = Path(tmp) / "editable-content" / "work"
            draft = editable_work / "commercials" / "draft-commercial"
            ready = editable_work / "commercials" / "ready-commercial"
            (draft / "highlight").mkdir(parents=True)
            (draft / "highlight" / "1_img.jpg").write_bytes(b"\xff\xd8")
            (ready / "film").mkdir(parents=True)
            (ready / "film" / "film_link.md").write_text(
                "https://vimeo.com/1", encoding="utf-8"
            )
            (ready / "highlight").mkdir(parents=True)
            (ready / "highlight" / "1_img.jpg").write_bytes(b"\xff\xd8")

            warning = io.StringIO()
            with contextlib.redirect_stderr(warning):
                work_dirs = generate_pages.discover_work_dirs(editable_work)

            slugs = [d.name for d in work_dirs]
            self.assertNotIn("draft-commercial", slugs)
            self.assertIn("ready-commercial", slugs)
            warning_text = warning.getvalue()
            self.assertIn("editable-content/work/commercials/draft-commercial", warning_text)
            self.assertIn("Missing film/.", warning_text)
            self.assertIn("Exactly one film source in film/", warning_text)
            self.assertNotIn("Missing highlight", warning_text)

    def test_discover_work_dirs_skips_draft_without_highlight_media(self):
        with tempfile.TemporaryDirectory() as tmp:
            editable_work = Path(tmp) / "editable-content" / "work"
            draft = editable_work / "films" / "draft-film"
            ready = editable_work / "films" / "ready-film"
            (draft / "trailer").mkdir(parents=True)
            (draft / "trailer" / "trailer_link.md").write_text(
                "https://vimeo.com/1", encoding="utf-8"
            )
            (ready / "trailer").mkdir(parents=True)
            (ready / "trailer" / "trailer_link.md").write_text(
                "https://vimeo.com/2", encoding="utf-8"
            )
            (ready / "highlight").mkdir(parents=True)
            (ready / "highlight" / "1_img.jpg").write_bytes(b"\xff\xd8")

            warning = io.StringIO()
            with contextlib.redirect_stderr(warning):
                work_dirs = generate_pages.discover_work_dirs(editable_work)

            slugs = [d.name for d in work_dirs]
            self.assertNotIn("draft-film", slugs)
            self.assertIn("ready-film", slugs)
            warning_text = warning.getvalue()
            self.assertIn("editable-content/work/films/draft-film", warning_text)
            self.assertIn("Missing highlight/.", warning_text)
            self.assertIn("Exactly one trailer source in trailer/", warning_text)
            self.assertNotIn("Missing trailer", warning_text)

    def test_discover_work_dirs_empty_placeholder_has_no_warning(self):
        with tempfile.TemporaryDirectory() as tmp:
            editable_work = Path(tmp) / "editable-content" / "work"
            draft = editable_work / "films" / "empty-draft"
            ready = editable_work / "films" / "ready-film"
            draft.mkdir(parents=True)
            (ready / "trailer").mkdir(parents=True)
            (ready / "trailer" / "trailer_link.md").write_text(
                "https://vimeo.com/1", encoding="utf-8"
            )
            (ready / "highlight").mkdir(parents=True)
            (ready / "highlight" / "1_img.jpg").write_bytes(b"\xff\xd8")

            warning = io.StringIO()
            with contextlib.redirect_stderr(warning):
                work_dirs = generate_pages.discover_work_dirs(editable_work)

            slugs = [d.name for d in work_dirs]
            self.assertNotIn("empty-draft", slugs)
            self.assertIn("ready-film", slugs)
            self.assertEqual(warning.getvalue(), "")

    def test_load_work_without_note_and_bts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "editable-content" / "work" / "films" / "minimal-work"
            output_html = root / "generated-website" / "films" / "minimal-work" / "index.html"

            (source / "trailer").mkdir(parents=True)
            (source / "trailer" / "trailer_link.md").write_text(
                "https://vimeo.com/123456789",
                encoding="utf-8",
            )
            (source / "highlight").mkdir(parents=True)
            (source / "highlight" / "1_highlight.webp").write_text(
                "webp",
                encoding="utf-8",
            )

            with mock.patch.object(generate_pages, "vimeo_thumbnail_url", return_value=None):
                work = generate_pages.load_work(source)
            rendered = generate_pages.render_work(
                work,
                "{{SECTION_TRACKER_LINKS}}{{WORK_SECTIONS}}",
                output_html,
            )

            self.assertIsNone(work.note)
            self.assertIsNone(work.note_media)
            self.assertIsNone(work.bts_text_html)
            self.assertEqual(work.bts_media, ())
            self.assertIn('id="trailer"', rendered)
            self.assertIn('id="highlight"', rendered)
            self.assertNotIn('id="note"', rendered)
            self.assertNotIn('id="bts"', rendered)
            self.assertNotIn('data-section-link="note"', rendered)
            self.assertNotIn('data-section-link="bts"', rendered)

    def test_note_text_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "editable-content" / "work" / "films" / "text-note"
            output_html = root / "generated-website" / "films" / "text-note" / "index.html"

            (source / "trailer").mkdir(parents=True)
            (source / "trailer" / "trailer_link.md").write_text(
                "https://vimeo.com/123456789", encoding="utf-8"
            )
            (source / "highlight").mkdir(parents=True)
            (source / "highlight" / "1_highlight.webp").write_text("webp", encoding="utf-8")
            (source / "note").mkdir(parents=True)
            (source / "note" / "1_text.md").write_text("# Title\n\nBody text.", encoding="utf-8")

            with mock.patch.object(generate_pages, "vimeo_thumbnail_url", return_value=None):
                work = generate_pages.load_work(source)
            rendered = generate_pages.render_work(
                work, "{{WORK_SECTIONS}}", output_html
            )

            self.assertIsNotNone(work.note)
            self.assertIsNone(work.note_media)
            self.assertIn('id="note"', rendered)
            self.assertIn("work-header-spacer", rendered)
            self.assertIn("Director's note", rendered)

    def test_note_media_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "editable-content" / "work" / "films" / "media-note"
            output_html = root / "generated-website" / "films" / "media-note" / "index.html"

            (source / "trailer").mkdir(parents=True)
            (source / "trailer" / "trailer_link.md").write_text(
                "https://vimeo.com/123456789", encoding="utf-8"
            )
            (source / "highlight").mkdir(parents=True)
            (source / "highlight" / "1_highlight.webp").write_text("webp", encoding="utf-8")
            (source / "note").mkdir(parents=True)
            (source / "note" / "1_image.webp").write_text("webp", encoding="utf-8")

            with mock.patch.object(generate_pages, "vimeo_thumbnail_url", return_value=None):
                work = generate_pages.load_work(source)
            rendered = generate_pages.render_work(
                work, "{{WORK_SECTIONS}}", output_html
            )

            self.assertIsNone(work.note)
            self.assertIsNotNone(work.note_media)
            self.assertIn('id="note"', rendered)
            self.assertIn("work-header-spacer", rendered)

    def test_bts_text_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "editable-content" / "work" / "films" / "text-bts"
            output_html = root / "generated-website" / "films" / "text-bts" / "index.html"

            (source / "trailer").mkdir(parents=True)
            (source / "trailer" / "trailer_link.md").write_text(
                "https://vimeo.com/123456789", encoding="utf-8"
            )
            (source / "highlight").mkdir(parents=True)
            (source / "highlight" / "1_highlight.webp").write_text("webp", encoding="utf-8")
            (source / "bts").mkdir(parents=True)
            (source / "bts" / "text.md").write_text("Credits here", encoding="utf-8")

            with mock.patch.object(generate_pages, "vimeo_thumbnail_url", return_value=None):
                work = generate_pages.load_work(source)
            rendered = generate_pages.render_work(
                work, "{{WORK_SECTIONS}}", output_html
            )

            self.assertIsNotNone(work.bts_text_html)
            self.assertEqual(work.bts_media, ())
            self.assertIn('id="bts"', rendered)
            self.assertIn("bts-layout--text-only", rendered)
            self.assertIn("bts-spacer", rendered)
            self.assertNotIn("bts-slideshow", rendered)

    def test_bts_media_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "editable-content" / "work" / "films" / "media-bts"
            output_html = root / "generated-website" / "films" / "media-bts" / "index.html"

            (source / "trailer").mkdir(parents=True)
            (source / "trailer" / "trailer_link.md").write_text(
                "https://vimeo.com/123456789", encoding="utf-8"
            )
            (source / "highlight").mkdir(parents=True)
            (source / "highlight" / "1_highlight.webp").write_text("webp", encoding="utf-8")
            (source / "bts").mkdir(parents=True)
            (source / "bts" / "1_bts.webp").write_text("webp", encoding="utf-8")

            with mock.patch.object(generate_pages, "vimeo_thumbnail_url", return_value=None):
                work = generate_pages.load_work(source)
            rendered = generate_pages.render_work(
                work, "{{WORK_SECTIONS}}", output_html
            )

            self.assertIsNone(work.bts_text_html)
            self.assertGreater(len(work.bts_media), 0)
            self.assertIn('id="bts"', rendered)
            self.assertIn("bts-spacer", rendered)
            self.assertIn("bts-slideshow", rendered)
            self.assertNotIn("bts-copy", rendered)

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
                "{{THEME_INIT_JS_URL}}"
                "{{LANGUAGE_INIT_JS_URL}}"
                "{{LANGUAGE_TOGGLE_JS_URL}}"
                "{{LAZY_MEDIA_JS_URL}}"
                "{{WORK_SECTIONS}}",
                encoding="utf-8",
            )
            (source_assets / "css").mkdir(parents=True)
            (source_assets / "js").mkdir(parents=True)
            (source_assets / "css" / "shared-effects.css").write_text("", encoding="utf-8")
            (source_assets / "js" / "portfolio-grid.js").write_text("", encoding="utf-8")
            (source_assets / "js" / "local-preview-links.js").write_text("", encoding="utf-8")

            def fake_convert_image_to_webp(source_path, target_path, **_kwargs):
                target_path.parent.mkdir(parents=True, exist_ok=True)
                target_path.write_text("webp", encoding="utf-8")

            with (
                contextlib.redirect_stdout(io.StringIO()),
                mock.patch.object(generate_pages, "REPO_ROOT", root),
                mock.patch.object(generate_pages, "EDITABLE_WORK_DIR", source.parent.parent),
                mock.patch.object(generate_pages, "GENERATED_WEBSITE_DIR", generated_site),
                mock.patch.object(generate_pages, "WORK_PAGE_TEMPLATE", template),
                mock.patch.object(generate_pages, "SITE_SOURCE_ASSETS_DIR", source_assets),
                mock.patch.object(generate_pages, "vimeo_thumbnail_url", return_value=None),
                mock.patch.object(
                    generate_pages,
                    "convert_image_to_webp",
                    side_effect=fake_convert_image_to_webp,
                ),
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
            self.assertIn("../../js/theme-init.js", generated)
            self.assertIn("../../js/language-init.js", generated)
            self.assertIn("../../js/language-toggle.js", generated)
            self.assertIn("../../js/lazy-media.js", generated)

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
        self.assertIn('src="../editable-content/work/films/sample-work/trailer/1_trailer.mp4"', rendered)
        self.assertIn('preload="metadata"', rendered)
        self.assertNotIn("data-lazy-video", rendered)

    def test_works_index_grid_uses_generated_video_preview_when_available(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output_html = root / "generated-website" / "index.html"
            source_media = (
                root
                / "editable-content"
                / "work"
                / "commercials"
                / "sample-work"
                / "grid_preview"
                / "1_preview.mp4"
            )
            generated_media = (
                root
                / "generated-website"
                / "media"
                / "editable-content"
                / "work"
                / "commercials"
                / "sample-work"
                / "grid_preview"
                / "1_preview-grid-preview-720p-v3.mp4"
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
                grid_preview_media=generate_pages.MediaItem(1, source_media, "video"),
                grid_display_media=generate_pages.MediaItem(1, generated_media, "video"),
            )

            rendered = generate_pages.render_works_index_grid_item(work, output_html)

        self.assertIn("media/editable-content/work/commercials/sample-work/grid_preview/1_preview-grid-preview-720p-v3.mp4", rendered)
        self.assertNotIn("../editable-content/work/commercials/sample-work/grid_preview/1_preview.mp4", rendered)

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
        self.assertIn("srcset=", rendered)
        self.assertIn("sizes=", rendered)
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

    def test_load_work_optimizes_video_grid_preview(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "editable-content" / "work" / "commercials" / "sample-work"
            generated_site = root / "generated-website"

            (source / "film").mkdir(parents=True)
            (source / "film" / "film_link.md").write_text(
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
            (source / "grid_preview" / "1_preview.mp4").write_text("mp4", encoding="utf-8")

            def fake_convert_image_to_webp(_source_path, target_path, **_kwargs):
                target_path.parent.mkdir(parents=True, exist_ok=True)
                target_path.write_text("webp", encoding="utf-8")

            def fake_transcode_grid_preview_video(_source_path, target_path):
                target_path.parent.mkdir(parents=True, exist_ok=True)
                target_path.write_text("mp4", encoding="utf-8")

            with (
                mock.patch.object(generate_pages, "REPO_ROOT", root),
                mock.patch.object(generate_pages, "GENERATED_WEBSITE_DIR", generated_site),
                mock.patch.object(generate_pages, "vimeo_thumbnail_url", return_value=None),
                mock.patch.object(
                    generate_pages,
                    "convert_image_to_webp",
                    side_effect=fake_convert_image_to_webp,
                ),
                mock.patch.object(
                    generate_pages,
                    "transcode_grid_preview_video",
                    side_effect=fake_transcode_grid_preview_video,
                ) as transcode,
            ):
                work = generate_pages.load_work(source, write_assets=True)

        transcode.assert_called_once()
        self.assertIsNotNone(work.grid_preview_media)
        self.assertIsNotNone(work.grid_display_media)
        self.assertEqual(work.grid_preview_media.path.name, "1_preview.mp4")
        self.assertEqual(work.grid_display_media.path.name, "1_preview-grid-preview-720p-v3.mp4")

    def test_load_work_generates_highlight_video_variants(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "editable-content" / "work" / "commercials" / "sample-work"
            highlight_video = source / "highlight" / "1_highlight.mp4"

            (source / "film").mkdir(parents=True)
            (source / "film" / "film_link.md").write_text(
                "https://vimeo.com/123456789",
                encoding="utf-8",
            )
            highlight_video.parent.mkdir()
            highlight_video.write_text("mp4", encoding="utf-8")

            with (
                mock.patch.object(generate_pages, "REPO_ROOT", root),
                mock.patch.object(generate_pages, "GENERATED_WEBSITE_DIR", root / "generated-website"),
                mock.patch.object(generate_pages, "vimeo_thumbnail_url", return_value=None),
                mock.patch.object(generate_pages, "ensure_highlight_tile_video_variants") as ensure_variants,
            ):
                work = generate_pages.load_work(source, write_assets=True)

        ensure_variants.assert_called_once_with(
            highlight_video,
            write_assets=True,
            check_generated_assets=False,
        )
        self.assertEqual(work.highlight_media[0].kind, "video")

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
                "{{THEME_INIT_JS_URL}}"
                "{{LANGUAGE_INIT_JS_URL}}"
                "{{LANGUAGE_TOGGLE_JS_URL}}"
                "{{THEME_TOGGLE_JS_URL}}"
                "{{LAZY_MEDIA_JS_URL}}"
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
        self.assertNotIn('works-index-page fade-up content-visibility-auto', rendered)
        self.assertIn('data-grid-mode="justify"', rendered)
        self.assertIn('data-justify-mobile-max-items="2"', rendered)
        self.assertNotIn("data-row-height", rendered)
        self.assertIn('href="films/sample-film/"', rendered)
        self.assertIn('href="commercials/sample-ad/"', rendered)
        self.assertIn("works-grid-title-chevron", rendered)
        self.assertIn("interactive-chevron--right", rendered)
        self.assertIn("css/site-header.css", rendered)
        self.assertIn("css/shared-effects.css", rendered)
        self.assertIn("js/preferences.js", rendered)
        self.assertIn("js/theme-init.js", rendered)
        self.assertIn("js/language-init.js", rendered)
        self.assertIn("js/language-toggle.js", rendered)
        self.assertIn("js/theme-toggle.js", rendered)
        self.assertIn("js/lazy-media.js", rendered)
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

    def test_prune_stale_generated_media_removes_orphaned_responsive_variants(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            editable_content = root / "editable-content"
            editable_work = editable_content / "work"
            generated_site = root / "generated-website"
            media_dir = generated_site / "media"

            highlight_dir = editable_work / "films" / "sample" / "highlight"
            highlight_dir.mkdir(parents=True)
            (highlight_dir / "1_still.webp").write_text("webp", encoding="utf-8")
            trailer_dir = editable_work / "films" / "sample" / "trailer"
            trailer_dir.mkdir(parents=True)
            (trailer_dir / "trailer_link.md").write_text(
                "https://vimeo.com/123", encoding="utf-8"
            )

            output_highlight = (
                media_dir / "editable-content" / "work" / "films" / "sample" / "highlight"
            )
            output_highlight.mkdir(parents=True)
            for width in generate_pages.RESPONSIVE_IMAGE_WIDTHS:
                (output_highlight / f"1_still-{width}.webp").write_text("", encoding="utf-8")
            for width in generate_pages.RESPONSIVE_IMAGE_WIDTHS:
                (output_highlight / f"2_deleted-{width}.webp").write_text("", encoding="utf-8")

            with (
                contextlib.redirect_stdout(io.StringIO()),
                mock.patch.object(generate_pages, "REPO_ROOT", root),
                mock.patch.object(generate_pages, "EDITABLE_CONTENT_DIR", editable_content),
                mock.patch.object(generate_pages, "EDITABLE_WORK_DIR", editable_work),
                mock.patch.object(generate_pages, "GENERATED_WEBSITE_DIR", generated_site),
            ):
                failures = generate_pages.prune_stale_generated_media(
                    editable_content_dir=editable_content,
                    editable_work_dir=editable_work,
                    repo_root=root,
                    generated_website_dir=generated_site,
                )

            remaining = sorted(p.name for p in output_highlight.iterdir() if p.is_file())

            self.assertEqual(failures, 0)
            self.assertEqual(
                remaining,
                sorted(f"1_still-{w}.webp" for w in generate_pages.RESPONSIVE_IMAGE_WIDTHS),
            )

    def test_prune_stale_generated_media_check_mode_reports_without_deleting(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            editable_content = root / "editable-content"
            editable_work = editable_content / "work"
            generated_site = root / "generated-website"
            media_dir = generated_site / "media"

            (editable_work / "films").mkdir(parents=True)

            stale_dir = media_dir / "editable-content" / "work" / "films" / "gone" / "highlight"
            stale_dir.mkdir(parents=True)
            stale_file = stale_dir / "1_old-480.webp"
            stale_file.write_text("", encoding="utf-8")

            stderr = io.StringIO()
            with (
                contextlib.redirect_stderr(stderr),
                mock.patch.object(generate_pages, "REPO_ROOT", root),
                mock.patch.object(generate_pages, "EDITABLE_CONTENT_DIR", editable_content),
                mock.patch.object(generate_pages, "EDITABLE_WORK_DIR", editable_work),
                mock.patch.object(generate_pages, "GENERATED_WEBSITE_DIR", generated_site),
            ):
                failures = generate_pages.prune_stale_generated_media(
                    check=True,
                    editable_content_dir=editable_content,
                    editable_work_dir=editable_work,
                    repo_root=root,
                    generated_website_dir=generated_site,
                )

            self.assertEqual(failures, 1)
            self.assertTrue(stale_file.exists())
            self.assertIn("stale", stderr.getvalue())

    def test_prune_stale_generated_media_removes_empty_directories(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            editable_content = root / "editable-content"
            editable_work = editable_content / "work"
            generated_site = root / "generated-website"
            media_dir = generated_site / "media"

            (editable_work / "films").mkdir(parents=True)

            stale_dir = media_dir / "editable-content" / "work" / "films" / "gone" / "highlight"
            stale_dir.mkdir(parents=True)
            (stale_dir / "1_old-480.webp").write_text("", encoding="utf-8")

            with (
                contextlib.redirect_stdout(io.StringIO()),
                mock.patch.object(generate_pages, "REPO_ROOT", root),
                mock.patch.object(generate_pages, "EDITABLE_CONTENT_DIR", editable_content),
                mock.patch.object(generate_pages, "EDITABLE_WORK_DIR", editable_work),
                mock.patch.object(generate_pages, "GENERATED_WEBSITE_DIR", generated_site),
            ):
                generate_pages.prune_stale_generated_media(
                    editable_content_dir=editable_content,
                    editable_work_dir=editable_work,
                    repo_root=root,
                    generated_website_dir=generated_site,
                )

            self.assertFalse(stale_dir.exists())
            self.assertFalse(stale_dir.parent.exists())

    def test_prune_stale_generated_media_keeps_video_preview_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            editable_content = root / "editable-content"
            editable_work = editable_content / "work"
            generated_site = root / "generated-website"

            preview_dir = editable_work / "commercials" / "sample" / "grid_preview"
            preview_dir.mkdir(parents=True)
            (preview_dir / "1_preview.mp4").write_text("mp4", encoding="utf-8")
            film_dir = editable_work / "commercials" / "sample" / "film"
            film_dir.mkdir(parents=True)
            (film_dir / "film_link.md").write_text(
                "https://vimeo.com/123", encoding="utf-8"
            )
            highlight_dir = editable_work / "commercials" / "sample" / "highlight"
            highlight_dir.mkdir(parents=True)
            (highlight_dir / "1_highlight.webp").write_text("webp", encoding="utf-8")

            with (
                mock.patch.object(generate_pages, "REPO_ROOT", root),
                mock.patch.object(generate_pages, "EDITABLE_CONTENT_DIR", editable_content),
                mock.patch.object(generate_pages, "EDITABLE_WORK_DIR", editable_work),
                mock.patch.object(generate_pages, "GENERATED_WEBSITE_DIR", generated_site),
            ):
                expected_video = generate_pages.optimized_grid_preview_video_path(
                    preview_dir / "1_preview.mp4"
                )
                expected_video.parent.mkdir(parents=True, exist_ok=True)
                expected_video.write_text("mp4", encoding="utf-8")

                stale_video = expected_video.parent / "old_preview-grid-preview-720p-v3.mp4"
                stale_video.write_text("mp4", encoding="utf-8")

                stdout = io.StringIO()
                with contextlib.redirect_stdout(stdout):
                    failures = generate_pages.prune_stale_generated_media(
                        editable_content_dir=editable_content,
                        editable_work_dir=editable_work,
                        repo_root=root,
                        generated_website_dir=generated_site,
                    )

            self.assertEqual(failures, 0)
            self.assertTrue(expected_video.exists())
            self.assertFalse(stale_video.exists())

    def test_prune_stale_generated_media_removes_deleted_highlight_video_variants(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            editable_content = root / "editable-content"
            editable_work = editable_content / "work"
            generated_site = root / "generated-website"
            media_dir = generated_site / "media"

            highlight_dir = editable_work / "commercials" / "sample" / "highlight"
            highlight_dir.mkdir(parents=True)
            highlight_video = highlight_dir / "1_clip.mp4"
            highlight_video.write_text("mp4", encoding="utf-8")
            film_dir = editable_work / "commercials" / "sample" / "film"
            film_dir.mkdir(parents=True)
            (film_dir / "film_link.md").write_text(
                "https://vimeo.com/123",
                encoding="utf-8",
            )

            with (
                mock.patch.object(generate_pages, "REPO_ROOT", root),
                mock.patch.object(generate_pages, "EDITABLE_CONTENT_DIR", editable_content),
                mock.patch.object(generate_pages, "EDITABLE_WORK_DIR", editable_work),
                mock.patch.object(generate_pages, "GENERATED_WEBSITE_DIR", generated_site),
            ):
                expected_variants = generate_pages.highlight_tile_video_variant_paths(highlight_video)
                for target in expected_variants:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text("mp4", encoding="utf-8")

                stale_dir = (
                    media_dir
                    / "editable-content"
                    / "work"
                    / "commercials"
                    / "sample"
                    / "highlight"
                )
                stale_480 = stale_dir / "2_deleted-tile-480p-v1.mp4"
                stale_720 = stale_dir / "2_deleted-tile-720p-v1.mp4"
                stale_480.write_text("mp4", encoding="utf-8")
                stale_720.write_text("mp4", encoding="utf-8")

                stdout = io.StringIO()
                with contextlib.redirect_stdout(stdout):
                    failures = generate_pages.prune_stale_generated_media(
                        editable_content_dir=editable_content,
                        editable_work_dir=editable_work,
                        repo_root=root,
                        generated_website_dir=generated_site,
                    )

            self.assertEqual(failures, 0)
            self.assertTrue(all(target.exists() for target in expected_variants))
            self.assertFalse(stale_480.exists())
            self.assertFalse(stale_720.exists())

    def test_prune_no_op_when_media_dir_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            generated_site = root / "generated-website"
            generated_site.mkdir()

            failures = generate_pages.prune_stale_generated_media(
                editable_content_dir=root / "editable-content",
                editable_work_dir=root / "editable-content" / "work",
                repo_root=root,
                generated_website_dir=generated_site,
            )

        self.assertEqual(failures, 0)

    def test_expected_generated_media_includes_about_image_variants(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            editable_content = root / "editable-content"
            about_dir = editable_content / "about"
            about_dir.mkdir(parents=True)
            (about_dir / "1_image.webp").write_text("webp", encoding="utf-8")
            (editable_content / "work" / "films").mkdir(parents=True)

            with (
                mock.patch.object(generate_pages, "REPO_ROOT", root),
                mock.patch.object(generate_pages, "GENERATED_WEBSITE_DIR", root / "generated-website"),
            ):
                expected = generate_pages.expected_generated_media(
                    editable_content_dir=editable_content,
                    editable_work_dir=editable_content / "work",
                    repo_root=root,
                    generated_website_dir=root / "generated-website",
                )

        self.assertEqual(len(expected), len(generate_pages.RESPONSIVE_IMAGE_WIDTHS))
        self.assertTrue(all("1_image-" in str(p) for p in expected))

    def test_expected_generated_media_includes_highlight_video_variants(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            editable_content = root / "editable-content"
            editable_work = editable_content / "work"
            generated_site = root / "generated-website"

            highlight_dir = editable_work / "films" / "sample" / "highlight"
            highlight_dir.mkdir(parents=True)
            highlight_video = highlight_dir / "1_clip.mp4"
            highlight_video.write_text("mp4", encoding="utf-8")
            trailer_dir = editable_work / "films" / "sample" / "trailer"
            trailer_dir.mkdir(parents=True)
            (trailer_dir / "trailer_link.md").write_text(
                "https://vimeo.com/123",
                encoding="utf-8",
            )

            with (
                mock.patch.object(generate_pages, "REPO_ROOT", root),
                mock.patch.object(generate_pages, "GENERATED_WEBSITE_DIR", generated_site),
            ):
                expected = generate_pages.expected_generated_media(
                    editable_content_dir=editable_content,
                    editable_work_dir=editable_work,
                    repo_root=root,
                    generated_website_dir=generated_site,
                )
                expected_variants = set(
                    generate_pages.highlight_tile_video_variant_paths(highlight_video)
                )
                unexpected_grid_preview = generate_pages.optimized_grid_preview_video_path(
                    highlight_video
                )

        self.assertTrue(expected_variants.issubset(expected))
        self.assertNotIn(unexpected_grid_preview, expected)


if __name__ == "__main__":
    unittest.main()
