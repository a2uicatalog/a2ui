# Vendor: Flowbite

**Source:** https://flowbite.com / https://github.com/themesberg/flowbite  
**License:** MIT  
**Atom count:** 16  
**Attribution:** Atoms in this set are adapted from content and documentation component patterns in the Flowbite component library (Tailwind CSS). Adaptations map Flowbite's Tailwind-class-driven props to A2UI's surface-agnostic field schema; rendering is recompiled into `web_article.py` without Tailwind or Alpine.js dependencies.

## Why

Flowbite's component library includes several documentation-specific and content-metadata patterns that have no equivalent in the general-purpose UI libraries (shadcn, UIverse). These atoms — reading time, author bio, keyboard shortcuts, release notes, learning objectives — are first-class citizens in technical blog content and appear repeatedly in the A2UI article format.

## Component → atom mapping

| Flowbite component | A2UI atom | Adaptation notes |
|---|---|---|
| Badge (variant: info) | `version_badge` | Narrowed to software version display; semver string + optional package name |
| Badge (variant: warning/yellow) | `experimental_banner` | Repurposed for feature-flag / unstable-API callout |
| Badge (complexity indicator) | `difficulty_badge` | Beginner / Intermediate / Advanced label |
| Timeline (reading progress) | `time_estimate` | Single read-time value; badge display |
| Alert (info, with list body) | `key_takeaways` | items array; rendered as highlighted bullet list |
| Checklist (education variant) | `learning_objectives` | items array with completion states |
| Checklist (system requirements) | `prerequisite_checklist` | items array; optional met/unmet state |
| Kbd component | `keyboard_shortcut` | keys array (e.g. `["Ctrl", "K"]`); rendered as `<kbd>` elements |
| Timeline (changelog variant) | `release_notes` | version + date + categories (added/changed/fixed/removed) |
| List group (links/downloads) | `resources_list` | items with label + url + optional filetype hint |
| Checklist (interactive / task) | `checklist_interactive` | name + items; checkbox state captured |
| CTA section (email variant) | `newsletter_cta` | headline + description + button label; no backend wiring |
| Card (author/bio variant) | `author_bio_card` | name + role + avatar + bio + social links |
| Blockquote (tweetable) | `share_quote` | text + attribution; styled for social sharing |
| CTA section (social follow) | `follow_cta` | platform + handle + headline + description |
| HTTP endpoint block | `http_request_block` | method + url + headers + body + example response |

## Surface notes

All Flowbite-derived atoms are static content patterns with no required JavaScript. They work on `web` and `meet-stage`. `http_request_block` and `keyboard_shortcut` are also compatible with `googlechat` (degraded styling). `newsletter_cta` renders but submit is non-functional on all surfaces except `web` with a backend integration.
