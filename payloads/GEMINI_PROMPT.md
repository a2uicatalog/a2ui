# A2UI Gemini Prompts

---

## Prompt A — Hub (navigable slide deck)

Paste into Gemini. Replace the last line with your topic. Returns JSON — paste directly into the renderer.

```
You are generating a JSON payload for A2UI — a Google Apps Script renderer that turns structured JSON into a rich, navigable slide deck.

Return ONLY valid JSON. No markdown fences, no explanation, no comments.

## Top-level structure

{
  "title": "string",
  "theme": "dark" | "light",
  "blocks": [{ "type": "hub", "subjects": [ ...Subject ] }]
}

## Subject

{ "id": "snake_case", "label": "emoji + label", "color": "#hex", "slides": [ ...Slide ] }

## Slide

{ "id": "snake_case", "label": "short label", "blocks": [ ...Block ] }

## Atom vocabulary (use 3–5 blocks per slide)

gradient_hero   — badge, title, subtitle, accent, accent2, align("center")
dark_hero       — heading, subtext, badge, align("center")
metric_row      — metrics: [{label, value, sub, trend("up"|"down"|"flat")}]
key_takeaways   — points: [string] — supports **bold**
two_tone_card   — title, subtitle, accent, points: [string]
step_progress   — current(int), steps: [{label}], accent
risk_flag       — risks: [{level("high"|"medium"|"low"), title, detail}]
action_items    — items: [{owner(initials), text}]
highlight_box   — accent, title, body
icon_list       — items: [{icon(emoji), text}]

### News & headline atoms (use when topic = news briefing, digest, top stories)

breaking_banner — label("BREAKING"|"EXCLUSIVE"|"UPDATE"), title, summary?, source?, time?, accent
headline_list   — title?, accent, items: [{rank?, title, source?, time?, tag?, url?}]
news_digest     — title?, accent, items: [{title, body?, tag?, source?}] — grid of compact story cards

## Rules

- Exactly one hub block at top level
- 3–5 subjects per hub
- 1–2 slides per subject
- First block of each subject's first slide must be gradient_hero or dark_hero
- Use metric_row when showing numbers
- End overview slides with key_takeaways
- Pick one primary accent colour and use it consistently (default: #6366f1 indigo)

## Task

Generate a hub for: [YOUR TOPIC HERE]
```

---

## Prompt B — Animated Pitch (flat, full-screen presentation)

Use this for landing pages, pitches, or "wow" demos. No hub navigation — just a flowing animated page.

```
You are generating a JSON payload for A2UI — a Google Apps Script renderer that displays animated, full-screen content as a flowing page.

Return ONLY valid JSON. No markdown fences, no explanation, no comments.

## Top-level structure

{
  "title": "string",
  "theme": "dark",
  "blocks": [ ...Block ]
}

## Animation atom vocabulary

shimmer_text    — text, size("1rem"–"5rem"), from(hex), via(hex), to(hex), align("center"|"left")
marquee         — items: [{text?, icon?(emoji), image_url?(url), label?}], speed(10–40), direction("left"|"right"), gap(px int), color_icons(bool), pause_on_hover(bool)
animated_border — content(markdown string), from(hex), to(hex), via(hex), speed("3"–"8")
wave_divider    — color(hex), height(20–60), opacity("0.1"–"0.4"), flip(bool)
reveal          — animation("fade"|"slide"|"stagger"), stagger_delay(ms int), blocks: [ ...Block ]
columns         — cols(2|3), items: [{ blocks: [ ...Block ] }]
confetti_burst  — trigger("load"|"click"), count(30–120), duration(ms int)

## Standard atoms (can be used inside reveal/columns)

metric_row      — metrics: [{label, value, sub?, trend?}]
key_takeaways   — points: [string]
highlight_box   — accent, title, body
icon_list       — items: [{icon(emoji), text}]
headline_list   — title?, accent, items: [{rank?, title, source?, time?, tag?}]
breaking_banner — label?, title, summary?, source?, time?, accent
news_digest     — title?, accent, items: [{title, body?, tag?, source?}]

## Composition rules

- Open with shimmer_text for the headline (size 3rem–5rem, center aligned)
- Follow with a shimmer_text tagline (size 1.2rem–1.6rem, muted grey colours)
- Use a marquee of icons or feature tags after the headline section
- Separate major sections with wave_divider (alternate flip: true/false)
- Wrap groups of cards in reveal with animation "stagger" for entrance effects
- Use columns (cols: 3) inside reveal for side-by-side card sets
- Use animated_border for feature cards — each with a distinct gradient
- Use metric_row inside a reveal stagger to punch key numbers
- End with a second reverse-direction marquee (direction: "right") for a feature strip
- Close with confetti_burst trigger "load" for celebratory openers
- Dark theme only; use indigo (#6366f1), emerald (#10b981), violet (#8b5cf6), amber (#f59e0b) as accent colours
- Keep total block count under 15 for performance

## Task

Generate an animated pitch page for: [YOUR TOPIC HERE]
```
