# Portfolio reference

Extracted from `rae hu 2026.pdf` (64 pages, 79 MB, 1920×1080 landscape) on 2026-05-12. The PDF lives at `~/Desktop/rae/rae hu 2026.pdf` and is **not** committed (large binary, design source only). This file is the Claude-facing reference when the owner makes design requests — it's the canonical record of the portfolio's design vocabulary, voice, and project catalog. Update it whenever the portfolio PDF is revised.

When the owner says "use the portfolio" or "match the PDF," consult this file first. If a project the owner mentions isn't here, ask them whether the PDF was updated.

## Quick index

- [Visual identity](#visual-identity) — palette, type, red-dot motif, cover illustration, page rhythm
- [Voice and copy](#voice-and-copy) — canonical bio, the quote, director's-note voice patterns
- [Contact channels](#contact-channels) — including the email mismatch with the site
- [Selected works — the Films tier](#selected-works--the-films-tier) — *Strange Fruit*, *We Don't Dance For Nothing*
- [Commercial work — catalog](#commercial-work--catalog) — featured projects, in PDF order
- [Lighter-treatment works](#other-works-no-featured-detail-page) — only appear as thumbnails
- [PDF sequencing](#front-of-book-structure-the-order-projects-appear-in-the-pdf) — informs site IA
- [Discrepancies to flag](#discrepancies-to-flag) — site vs. PDF differences

---

## Visual identity

### Palette

Hex values are **my approximations from the rendered PDF**, not sampled from a brand spec. The amber matches the site's `--amber: #c8943a` very closely. If precise values matter for new assets, ask the owner for source colors.

- **Amber** `#c8943a` — cover background; the dominant brand color
- **Black** `#0a0a0a` — every interior page; the dominant editorial color
- **Cream / off-white** `#f4f1ec` — body text on dark; brands-grid background
- **Red dot** `#c0392b` — recording-light motif (used as a label bullet)
- **Brown line work** `#6b3a00` — the cover illustration is rendered in this single weight against the amber
- **Yellow accent** — used very sparingly: contact page has a yellow-dot variant beside "RAE HU", and the bottom "FILM / COMMERCIAL" markers on the final page

These five are the entire palette. The current site uses the same five. **Don't introduce additional colors without explicit owner approval.**

### Typography

Font identification is inferential — I'm matching what I see in the PDF against the site's CSS. The PDF was likely set in InDesign with these same families:

- **Serif** — EB Garamond (regular + italic). Used for headlines, project titles, body, director's notes. Headline scale is always **lowercase** ("about", "all works", "rae hu", "thank you").
- **Sans** — Syne. Used for small labels, page numbers, section tags, project metadata strips (e.g., "SHORT FILM · 2022 · FESTIVAL SELECTIONS"). Wide letter-spacing, uppercase.
- **Numerals** — sans, in the same uppercase-feel tracking ("PAGE 12").

The site already imports these via Google Fonts. Don't add a third typeface without checking.

### The red dot motif

A small red dot recurs as a recording-indicator metaphor on **every section header**. It sits inline before a sans-uppercase label. The vocabulary of those labels is film-set call-sheet language:

| Label | Where it appears |
|---|---|
| `RUNDOWN` | Table of contents page |
| `CAMERA, ROLLING!` | About section |
| `AND...ACTION!` | Films/Commercial divider page |
| `DIRECTOR'S NOTE` | Over project notes |
| `SYNOPSIS` | Over feature-film note (e.g., *We Don't Dance For Nothing*) |
| `AND... CUT!` | Closing thank-you page |
| `CONTACT` | (Implied on closing page) |

**Preserve this vocabulary when adding new sections.** Don't substitute generic labels ("ABOUT", "PROJECTS") without checking.

### Cover illustration

A loose **single-weight brown line drawing** of a figure / mythical creature: visible eyes (two small dark spots), elf-like pointed ear, flowing hair, hands. It renders against the amber background. Intentionally naive — outsider-art / folk-art rendering, not polished commercial illustration. Probably hand-drawn original artwork.

The site's current hero SVG is a hand-coded approximation of this illustration. **It's not great** — when the owner is ready, ask her for the actual source asset (SVG / PDF export from the original file). The placeholder SVG has hardcoded brown strokes that only work on amber backgrounds.

### Page rhythm

Every project in the PDF follows the same three-beat structure:

1. **Cover page** — full-bleed cinematic still, project title in white serif overlay (upper-left), Chinese subtitle / talent name in smaller sans below the title. Bottom-left has a sans-uppercase metadata strip (`FORMAT · YEAR · DESCRIPTOR`). Bottom-right has the page number.
2. **Director's note / synopsis page** — pure black background, bold serif headline (the takeaway sentence in larger weight), 1–3 lighter-weight paragraphs below, optional accompanying still or illustration on the right. Red dot + sans label (`DIRECTOR'S NOTE` or `SYNOPSIS`) at bottom-left.
3. **Still grids** — pure black background, 3-column grids of cinematic stills, usually 6 or 9 per page (2×3 or 3×3).

The site's Works section should honor this rhythm: an opening hero card, room for a director's note when one exists, then a stills grid.

---

## Voice and copy

### Bio (canonical, from page 3)

> Rae Hu 樂瑞 is a director and filmmaker based in Shanghai, working with creative partners across China, the US, Europe, and Latin America.
>
> She has spent the past decade making commercial work for global brands — Google, Samsung, Gucci, Miu Miu, Adidas, Bose and others — while developing an independent voice in parallel.
>
> Her short film *Strange Fruit* — set in 1990s Wenzhou, about a six-year-old girl who lies to her parents for the first time — has screened internationally and won multiple awards. Her debut feature, currently in development, follows a grown woman learning to be honest again — set in Mexico City.
>
> She works in English, conversational Spanish, Mandarin, and Cantonese.

This is also the current site copy (matches exactly). Treat this as the authoritative source — if the owner wants a revision, change it here and on the site in the same edit.

### The quote (page 5, FILMS/COMMERCIAL divider page)

> "nobody knows why and how creativity works.
> just living in discoveries."

Lowercase throughout, no capitalisation. Line break before "just". Don't auto-capitalise; the styling is intentional.

### Director's-note voice

Across the ~10 director's notes in the PDF, a consistent voice emerges. If asked to write copy in Rae's voice, mirror it:

- **Open with a setup sentence**, often a constraint or paradox.
  - "Three problems, one film." (Under Armour)
  - "Set in 1990s Wenzhou, China." (Strange Fruit)
  - "The brief was about outdoor culture in China. But the real question underneath it was about love..." (小红书)
  - "Had a lot of 'fun' shooting in a (fake) motel room..." (Gucci)
  - "This was made when AI video generation was still barely functional. Slow, unpredictable, often stupid." (Champion)
- **Reveal process and craft thinking, not glamour.** Specifics like prop differentiation across eras, CG rain/snow built on real anchors, magic-hour scheduling for opposite-season shoots, "I made a rule for myself early on: every memory sequence, fixed camera only."
- **Close on a wry beat.**
  - "We were just trying not to break the lights."
  - "Nobody asked us to do that. We just did it."
  - "The strangeness held."
- **Em-dashes**, not commas, for emphatic asides. Conversational, observational. Not corporate.

---

## Contact channels

- **Email — on the site**: `hello@raehufilm.com`
- **Email — in the PDF (page 63)**: a personal `@gmail.com` address — **redacted here** to keep it out of the search index, since this file is web-accessible at `raehu.com/docs/portfolio-reference.md`. Look at page 63 of the PDF when you need the exact value.
- **Instagram**: `@raehufilm` (https://instagram.com/raehufilm)
- **Vimeo**: display name "Rae Hu" — URL is https://vimeo.com/raehu
- **Based in**: Shanghai (PDF). Site says "Shanghai · Mexico City" because the debut feature is set in Mexico City.

The email mismatch is worth flagging when the owner edits anything contact-related — confirm which email she wants public.

---

## Selected works — the "Films" tier

The PDF treats two pieces as Films (not Commercial). These should headline the site's Works section.

### 1. Strange Fruit · 奇怪的果

| | |
|---|---|
| Year | 2022 |
| Format | Short Film |
| Festival status | Festival Selections (multiple awards per bio) |
| Role | Writer / Director |
| Setting | 1990s Wenzhou, China |

**Logline**: A six-year-old girl learns to lie for the first time in her life.

**Director's note** (page 7):
> Absent parents. A girl finding edges she wasn't supposed to see. It started as something about loss of innocence, but really it's about the silence before you understand what you lost.

**Visual palette**: muted greys and browns; industrial smokestacks against grey sky; red knit clothing on the child as a color pop; period costume (1990s tracksuits, red cable-knit sweaters, lace collars); cinematic 2.39:1 framing.

**Key images** (from pages 8–9): father smoking on bridge with child behind him + smokestacks; family washing scene in basin with red thermos; close-up of child with sad expression in red collar; girl reaching into wooden basin; girl looking at framed photo.

**Companion artwork**: there's a stylized illustrated poster (page 7, right side) — green/teal background, two girls back-to-back (one in red, one in orange), electric pylons, sun motif, label reads "THE STRANGE FRUIT / DIRECTED BY RAE HU". Treat as an existing brand asset; ask for the source file before recreating it.

### 2. We Don't Dance For Nothing

| | |
|---|---|
| Year | 2023 |
| Format | Feature Film |
| Festival status | Festival Selections |
| Role | **Producer** (the PDF lists "Produced by Rae" — she did not direct) |
| Setting | Hong Kong, shot on Super-16 amidst the Hong Kong Protests |

**Logline**: Trapped by her servitude in Hong Kong, a Filipina domestic worker plans to dance her way towards independence, romantic love, and true motherhood.

**Synopsis** (page 11, verbatim):
> La Jetée meets La La Land — this unique photo-montage celebrates a forgotten community of millions of women, dancing simply to feel they exist. Captured on Super-16 amidst the Hong Kong Protests, it dares to paint these heroes beyond their job descriptions, as people full of talent, joy, and grace. It is the first film of its kind.

**Visual palette**: warm sunset golds, cool urban teals, neon greens, Super-16 grain; high-energy candid composition.

**Key images** (pages 12–13): two women intimate close-up at beach sunset; group of women laughing on city street; subway / bus introspective portraits; dancing in motion blur; club kiss; underwater play.

> **Site note**: the live site currently has a card titled "Rooftop" that uses the "La Jetée meets La La Land" line — that copy is borrowed from this film's synopsis. "Rooftop" may have been a placeholder or working title. Check with the owner before keeping it as a separate work.

---

## Commercial work — catalog

Listed in **PDF order** (the curatorial order — most-prominent first). For each: format · year · talent (if any) · client. Visual note for design recall, plus a director's-note hook where the PDF includes one.

### 小红书 — Outdoor Activities In Chinese Style · 中式户外

- 2024 · Brand Film · Narrative · ft. 张震岳 (A-Yue / Chang Chen-yueh)
- Multi-generational family across decades — picnic and outdoor scenes in Chinese gardens and mountainsides; spans early '90s to present day
- **Director's note hook**: "The brief was about outdoor culture in China. But the real question underneath was about love — how Chinese people express it without ever quite saying it."
- **Craft detail worth remembering**: red plastic bags as the connective motif across every era; the prop team graded the material from translucent (1990s) to sturdy (present day). "Chinese love is a bit like those bags. Lightweight. Unpretentious."
- **Visual palette**: lush forest greens, pink picnic blankets, the recurring red bag

### Gucci Dreamscraper · 下一站

- 2024 · Brand Film · Suspenseful Thriller · ft. 肖战 (Xiao Zhan)
- Lynchian / Wong Kar-wai noir: a maroon-suited man in a fake motel, dark hotel corridors, vintage 8mm camera, swirling lights, "poor man's process" shaking-car scene
- **Director's note hook**: "Had a lot of 'fun' shooting in a (fake) motel room, let alone swirling the lights (without taking our crew member's head off hehe)... We were just trying not to break the lights."
- **Visual palette**: warm tobacco interior (red/orange tungsten) ↔ cool teal-green corridors, deep blacks. Two-temperature split

### Champion CNY · 小龍人

- 2024 · Product Film · Quirky Turfing · AIGC
- Year-of-the-Dragon CNY film. Entirely tufted/yarn world — Ames-room sets, tufted props, livestream aesthetic, AI-generated city backgrounds
- **Director's note hook**: "This was made when AI video generation was still barely functional. Slow, unpredictable, often stupid... I found something in that friction I couldn't name... The strangeness held."
- **Visual palette**: high chroma — kelly green, hot pink, mustard yellow, crimson red. Textile texture everywhere

### Under Armour · 陪你过寒冬

- 2023 · Product Film · Off-Season Shoot
- Athletes in winter conditions, restrained / static camera; CG rain and snow built on real anchors (car windows, bathroom mirrors). Shot in Chongqing in August
- **Director's note hook**: "Three problems, one film." Hot August shoot for a winter piece; down jacket as hero needed to feel like action despite being a warmth product; rain/snow done in CG built on real anchors. "Authenticity in post starts in pre-production."
- **Visual palette**: cold blue-greys, slate, low-saturation winter

### Bose

- 2024 · Product Film · 15s
- Tagline: "Style for your room. / Tune your space." (yellow type on warm interior)
- **Visual palette**: warm dusk interiors, ochres, rust, soft light. Lookbook/lifestyle feel

### Spotify

- 2021 · Brand Film · 15s
- Tagline beat: "New Genres."
- NYC street energy — Chinatown, Lower East Side, graffiti alleys, subway entrances. Diverse cast (Asian skater, woman in leather, Black woman with headwrap, blonde woman dancing)
- **Visual palette**: neon-on-rain, urban evening, full chroma

### Miumiu · ft. 邱天 / 刘柏辛

- 2022 · Fashion Film · Female Friendship
- Two young women, ornate domestic interior with green velvet curtains, dotted dresses, candle-lit; mirrored / paired compositions; soft pictorialist focus
- **Visual palette**: forest greens, candlelight golds, ivory whites. Lush, slow, intimate

### Fendi CNY

- 2023 · Fashion Film · CNY
- Chinese New Year, Year of the Rabbit. Red lanterns, paper-cuts, blue-and-white porcelain, fisheye lens, white rabbit cameo
- **Visual palette**: deep saturated reds, jade greens, lacquer black. Distortion as aesthetic choice

### Popsockets · 一扭一换 快樂架到

- 2023 · Brand Film · Studio Shoot
- Pastel studio set, bubblegum-pink and powder-blue, top-down "tennis court" stage, bubblegum motif
- **Visual palette**: pastel pink, sky blue, lemon — playful, high-key, candy

### Crocs · ft. 白鹿 (Bai Lu)

- 2025 · Product Film · CG
- CG-heavy dreamscape: lavender Ames-room, clouds, miniature Crocs-themed city, "GAME START" type
- **Visual palette**: pastel lavender, pink, sky blue, mint. Dollhouse / soft-toy world

### Tiktok · ft. 陈奕迅 (Eason Chan)

- 2023 · Brand Film · Concert
- Primary-color studio set, cassette-tape motif, Eason Chan in striped shirt against red curtain / yellow / blue wall blocks
- **Visual palette**: pure red, pure yellow, royal blue, white. Constructivist / Bauhaus

### Mentholatum (曼秀雷敦) · ft. 张艺兴 (Lay Zhang)

- 2025 · Product Film · CG
- Asian-fusion CG world: cherry-blossom branches, paper screens, silver-coat performer, blue water orb, spiral white set
- **Visual palette**: dusty rose, silver-grey, pale teal. Premium beauty-ad polish

### Vans · 下一格 更出格 · ft. JahJahWay

- 2024 · Brand Film · Non-Fiction Fiction · Surfing
- Documentary-feel surfing piece. Hainan / Bali. Sub-aquatic shots, sun flares, hand-held, life-on-the-beach
- **Visual palette**: warm sun, salt-bleached blues, sand. Lo-fi photo-real

### Yili (伊利) · 让"她"的称呼成为称赞 · ft. 刘晓庆

- 2025 · Brand Film · Narrate · Women's Day
- Multi-generational women — driver, factory worker, mother, daughter, weightlifter. Naturalistic doc style
- **Visual palette**: natural light, warm interiors, blue-grey daylight

### YILI · 把小观念养养大 · ft. 王刚

- 2025 · Product Film · Coming of Age
- A young woman's life chapters — early childhood with grandfather, birthday parties through ages, family hospital scene, pet illness
- **Visual palette**: rose tones, warm domestic, medical-blue contrast in clinic

### Tiktok · 晚八乐小区

- 2024 · Commercial · CNY
- Apartment-block CNY ensemble. Older neighbors, kids eating, fireworks over building marked 晚八乐小区. Lots of group laughter
- **Cast**: 孟鹤堂、周九良 / 齐思钧 (per "all works" caption)
- **Visual palette**: warm bulb light, deep wood interiors, fireworks oranges

### Wild Aid · 因为我们，东北虎回来了 · ft. 吴京 (Wu Jing)

- 2022 · Brand Film · Wild Ranger
- Northeast tigers conservation. Snowy forest, fire-lit night, ranger character, slow snowfall
- **Visual palette**: cold blues, firelight oranges. High-contrast snow-noir

### Lego

- 2024 · Brand Film · Christmas
- Vertical 9:16 frames with LEGO red corner logos; shiba inu in lego bow-tie, lego lobster on Christmas dinner, kid with helmet, lego skateboard. Holiday warmth
- **Visual palette**: Christmas reds, golden bokeh, warm domestic, blue-green

### YILI · 不够五个人 · ft. 五条人

- 2025 · Product Film · Band
- The band 五条人 plays in pool halls, mountain settings, surreal "less than five people" sketch. Retro Hong Kong gangster aesthetic
- **Visual palette**: tobacco gold, dim bar greens, oranges and rusts

### YILI · 不够五个人 (call-to-action version)

- 2022 · Product Film
- Same campaign theme, more on-pack call-to-action ("码上邀好友 天天赢免单 FREE!"), goofy ensemble in train, white-horse mascot
- **Visual palette**: brighter, with graphic-overlay treatment

### AXA · ft. Sammi Cheng (郑秀文)

- 2022 · Brand Film · Female Friendship
- HK celebrity-friendship piece — ring reveal, modern apartments, soft window light
- **Visual palette**: champagne neutrals, AXA-red graphic accent

### Google x Yeswelder

- 2022 · Brand Film · Non-Fiction Fiction
- Real welder portraiture — workshop interiors, motorcycle shop, helmet riding shots, blue protective gear, smoky craft
- **Visual palette**: deep blue protective wear, warehouse greys, industrial sparks

### Anta · 这条路我探过

- 2024 · Product Film · Outdoor
- Urban-to-trail explorers; hand-held wandering, daffodil close-up, upside-down portrait, rooftop tree-climbing
- **Visual palette**: green leaves, washed earth, summer sky

### Under Armour · 冬练要趁热

- 2023 · Product Film · Outdoor Training
- Strength training in snow — tire flips, parachute drag-runs, frost on hand. Combination of indoor gym and outdoor winter
- **Visual palette**: cold blues, gym warm tungsten, ice-frost transparency

### Adidas Neo

- 2022 · Brand Film · CNY
- Old-Shanghai apartment courtyards, multi-generational family ensemble, '90s street fashion mash-up. Yellow "neo" graphic-dot brand mark
- **Visual palette**: vintage cream walls, sun-warm courtyard greens, '90s costume pop

### Google x Furrytail

- 2021 · Brand Film · Pets
- Cat / dog product-design vignettes — orange cat, fluffy white cat on bench, yoga downward-dog with cat, water-tower silhouette
- **Visual palette**: warm afternoon light, neutral homes, pet warmth

### Coach Joy of Unboxing

- 2023 · Fashion Film · 11.11 (Singles' Day shopping)
- Girls running with Coach shopping bags in park; couch acrobatics; sunset by lake; sprocket-hole film-frame overlay treatment
- **Visual palette**: golden hour, blush, denim. Super-8 grain

### Fila "Why so serious" · 玩真的！ · ft. 王猛 / Milo

- 2024 · Brand Film · Father and Son · Tennis
- Tennis dad-son dynamic with comic / wry undertone; lightning over stadium, bald father comic-grimace, kid playing
- **Visual palette**: stormy blue, court teal, late-evening drama

### HK Series · ft. handsome factory / young master brewery / 粤东磁厂

- 2022 · Brand Film · F&B / Barbershop / Skate / Porcelain
- A series of HK-based brand portraits: skater in tunnel, barbershop chairs, brewery interior, porcelain artisan
- **Visual palette**: HK-fluorescent on cool surfaces, neon reds against gritty industrial

---

## Other works (no featured detail page)

These appear **only in the "all works" thumbnail grids** on pages 57–62 — they're part of the broader portfolio backbone but don't get full-page treatment. If the owner asks to "add the L'Oréal piece" or similar, look here first:

- **L'Oréal × 肖战** — men's grooming with Xiao Zhan, glass elevator + city skyline. (The current site card calls this "L'Oréal Men's × Xiao Zhan — Four 15-second films: elevator, cycling, helicopter, airport.")
- **抖音 × 谢霆锋** (Douyin × Nicholas Tse) — bedroom phone-call portrait
- **兰蔻 × 张凌赫 / 赵昭仪** (Lancôme) — forest portrait, white tank top
- **Kipling × 范玮琪** (Christine Fan) — couple in retail / store interior
- **君乐宝** (JunLeBao) — young boy unboxing toy in domestic setting
- **Apple** — Shot on iPhone 13 Pro, tunnel light streaks (B&W)
- **HKSE** (Hong Kong Stock Exchange) — outdoor cityscape, green sign signal
- **SOACAI** — corporate / office portrait
- **Pepper Lab** — street portrait in red hoodie
- **Coach** (separate from *Coach Joy of Unboxing*) — couch / acrobatic moment shown in thumbnail
- **McDonald's 《我就喜欢薯条》** — Wang Leehom × Wang Sulong music video. **Not in the PDF I read** but referenced on the live site under "W+K Shanghai · 2025". Confirm with the owner before listing as canonical.

---

## Brands / Clients (the white panel, page 4)

The PDF panel displays real logos in their original colors. Order, left-to-right, top-to-bottom (5–6 per row):

Samsung · L'Oréal · Lancôme · Hennessy · PopSockets · WildAid · Vans · Fila · Anta · Crocs · Bose · On · Adidas · Fendi · Miu Miu · Gucci · 小红书 · Champion · Yili · Under Armour · TikTok · Spotify · Lego · 京东 · Uniqlo · AXA · 淘宝 · Google

The current site uses **text labels** instead of logos (a deliberate art-direction choice — text reads cleaner on dark and avoids licensing/quality issues with rasterized logos). 30 entries originally; duplicates removed in commit `d82c040` — now 30 unique. If the owner wants to switch to real logos, this is the canonical brand list and order.

---

## Front-of-book structure (the order projects appear in the PDF)

The PDF orders projects with a clear hierarchy. The site's information architecture should respect this same hierarchy unless the owner explicitly wants to reshuffle:

1. **Cover** (amber + line illustration)
2. **Rundown** (TOC: about / selected works / all works / contact)
3. **About** (bio with red-lit BTS portrait)
4. **Brands / Clients** (white panel — real logos)
5. **The quote** / FILMS-COMMERCIAL divider
6. **Films** — Strange Fruit (cover + note + 2 grids) → We Don't Dance For Nothing (cover + synopsis + 2 grids)
7. **Commercial** — featured works first, each with cover + (optional note) + 1–2 grids
8. **All works** — thumbnail-grid index covering everything, including pieces too small for full treatment (~6 pages)
9. **Thank you / Contact** (BTS image + name + email + Instagram + Vimeo)

The site doesn't yet have an "all works" thumbnail-grid section — only the featured pieces in the Films/Commercial tabs. Worth raising with the owner whether the broader backbone (L'Oréal, McDonald's, etc.) should get thumbnail tiles too.

---

## Discrepancies to flag

These are places where the site and PDF disagree. Resolve with the owner before "fixing" either:

1. **Email**: site uses `hello@raehufilm.com`. The PDF lists a different personal `@gmail.com` address — possibly her private account. The `hello@` alias is the public-facing one; confirm with the owner before changing the contact section.
2. **Based in**: site says "Shanghai · Mexico City", PDF says only Shanghai (debut feature is set in Mexico City).
3. **"Rooftop"** on the current site: copy is borrowed from *We Don't Dance For Nothing*'s synopsis. Unclear if "Rooftop" is meant to be a separate work or a placeholder for a future short.
4. **McDonald's** is on the live site but not in the PDF — confirm with the owner whether it's a forthcoming project or one she chose to omit from the portfolio.
5. **Brands grid**: previously had Fendi and Lancôme duplicated on the site; removed in commit `d82c040`. PDF has 28 unique brands; the site has 30 (PDF + McDonald's + Wieden+Kennedy as separate entry). Keep aligned.
