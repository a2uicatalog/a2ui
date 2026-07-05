---
category: learning_and_gamification
title: Learning & Gamification
atom_count: 13
platform_support:
  web: 13/13
  meet-stage: 0/13
  googlechat: 0/13
  google-apps-script-web: 13/13
  email: 0/13
  pdf: 0/13
maturity: stable
source: atoms/schema.yaml
---

# Learning & Gamification

> 13 atoms · `*` = degraded (limited support) · Bold surface = full support

| Atom type | Description | Surfaces | Key fields |
|-----------|-------------|----------|------------|
| `quiz_question` | MCQ or true/false question with CSS-only correct/wrong feedback | **Web/Blog** · **GAS Web App** | `question` — string. The question text.<br>`options` — list[string]. Answer options — 2 to 6 items.<br>`correct` — integer. Zero-based index of the correct option.<br>`explanation` — string (optional). Shown after any option is selected.<br>`style` — "default" | "dark" | "minimal"  (optional, default "default") |
| `fill_in_blank` | cloze-test sentence with inline inputs and correct/wrong highlight on submit | **Web/Blog** · **GAS Web App** | `template` — string. Sentence with {blank} placeholders marking each gap.<br>`answers` — list[string | list[string]]. Accepted answer(s) per blank in order. A list entry may itself be a list of acceptable alternatives.<br>`hint` — string (optional). Shown below the exercise as a nudge.<br>`case_sensitive` — boolean (optional, default false). |
| `match_exercise` | click-to-pair matching exercise with green lock and red mismatch flash | **Web/Blog** · **GAS Web App** | `pairs` — list[{term: string, definition: string}]. 3 to 8 pairs recommended.<br>`shuffle` — boolean (optional, default true). Randomise right-column order on render. |
| `hint_reveal` | show/hide hint disclosure using HTML details/summary — no JS | **Web/Blog** · **GAS Web App** | `hint` — string. The hint text revealed on expand.<br>`label` — string (optional). Button label. Default "Show hint".<br>`accent` — string (optional). Left-border and icon colour. Default "#6366f1". |
| `achievement_badge` | unlockable achievement badge with locked/unlocked state and optional date | **Web/Blog** · **GAS Web App** · **Email** · **PDF** | `title` — string. Achievement name.<br>`description` — string (optional). Short achievement description.<br>`icon` — string (optional). Emoji or single character used as the badge icon. Default "🏆".<br>`locked` — boolean (optional, default false). Shows greyscale padlock overlay when true.<br>`unlocked_at` — string (optional). ISO date string shown beneath the badge when unlocked.<br>`color` — string (optional). Badge accent colour. Default "#f59e0b".<br>`size` — "card" | "pill"  (optional, default "card") |
| `score_summary` | end-of-exercise score card with correct/total, percentage, grade, and CTA | **Web/Blog** · **GAS Web App** · **PDF** | `correct` — integer. Number of correct answers.<br>`total` — integer. Total number of questions.<br>`time_taken` — string (optional). Human-readable time string e.g. "2m 14s".<br>`pass_threshold` — integer (optional). Percentage (0–100) required to pass. Drives pass/fail label colour.<br>`retry_label` — string (optional). Label for the retry button. Omit to hide retry CTA.<br>`continue_label` — string (optional). Label for the continue button. Omit to hide continue CTA.<br>`continue_url` — url (optional). Destination for the continue button. |
| `xp_bar` | animated XP/points progress bar with level label and level-up flash | **Web/Blog** · **GAS Web App** | `level_label` — string. Current level name e.g. "Level 3 — Intermediate".<br>`xp_current` — integer. Current XP within the current level.<br>`xp_next` — integer. XP required to reach the next level.<br>`accent` — string (optional). Bar fill colour. Default "#6366f1".<br>`show_flash` — boolean (optional, default true). Trigger level-up flash when xp_current >= xp_next. |
| `lesson_nav` | prev/next lesson navigation with module context and optional completion checkbox | **Web/Blog** · **GAS Web App** | `module_label` — string (optional). Module or section name shown above the nav bar.<br>`current_title` — string. Title of the current lesson.<br>`prev_title` — string (optional). Title of the previous lesson. Omit to hide prev arrow.<br>`prev_url` — url (optional). Link for the previous lesson.<br>`next_title` — string (optional). Title of the next lesson. Omit to hide next arrow.<br>`next_url` — url (optional). Link for the next lesson.<br>`show_completion` — boolean (optional, default false). Show a "Mark as complete" checkbox persisted in localStorage. |
| `course_progress_card` | course-level progress card with per-module bars and aggregate completion ring | **Web/Blog** · **GAS Web App** · **PDF** | `course_title` — string. Course name shown at the top of the card.<br>`modules` — list[{title: string, lessons_total: integer, lessons_done: integer}].<br>`accent` — string (optional). Progress fill colour. Default "#6366f1". |
| `progress_checkpoint` | milestone progress indicator across multi-step tutorial | **Web/Blog** · **GAS Web App** | `current_step` — integer. The current active step index.<br>`total_steps` — integer. Total steps in the sequence. |
| `capability_checklist` | feature capability tick list per tier capability using checkmarks | **Web/Blog** · **GAS Web App** · **PDF** | `capability_names` — array<br>`items` — array |
| `shortcut_legend` | keyboard shortcut cheat-sheet grid with key combos and labels | **Web/Blog** · **GAS Web App** · **Email** · **PDF** | `title` — string (optional). Heading above the grid.<br>`items` — List of {keys, action} entries. keys is an array of key strings e.g. ["⌘", "K"]. action is the human-readable description. |
| `prompt_template` | LLM prompt with highlighted {variable} slots and copy button | **Web/Blog** · **GAS Web App** · **PDF** | `template` — string. The prompt text containing {slot} placeholders.<br>`accent` — string (optional, default<br>`copyable` — boolean (optional, default true). Show copy button.<br>`label` — string (optional). Small label shown above the template block. |
