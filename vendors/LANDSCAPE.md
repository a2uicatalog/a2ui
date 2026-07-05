# Competitive Landscape — A2UI Atom Catalogue

Vendor libraries analysed against the A2UI catalogue to identify gaps, source atoms, and prioritise adaptation work. Updated 2026-06-13.

---

## Tier 1 — Act now

| Library | Why | License | Angle for A2UI |
|---|---|---|---|
| **AI-native patterns** | A2UI's actual differentiator — nobody else does this | Original | `streaming_text`, `source_citation`, `llm_comparison_table`, `confidence_bar` are atoms only an AI catalogue would have |
| **Microsoft Fluent UI** | Teams Meeting App renders Fluent natively; atoms built for the meet-stage surface apply here | MIT | `persona_card`, `presence_badge`, `message_bar` are Teams-first patterns with no equivalents |

**Status:** AI-native atoms delivered (v211 → see schema). Fluent UI gap analysis pending.

---

## Tier 2 — High value, distinct vocabulary

| Library | Gap atoms | License | Notes | Status |
|---|---|---|---|---|
| **Shopify Polaris** | `product_thumbnail`, `order_status_card`, `inventory_table` | MIT | E-commerce scenario in the benchmark barely maps well; Polaris is fully MIT | ✅ Delivered v220 |
| **Atlassian Design System** | `jira_ticket`, `sprint_board`, `lozenge` | Apache-2.0 | Project management is a heavy Meet/Teams use case; sprint review runbook already exists but atoms were approximations | ✅ Delivered v220 |
| **IBM Carbon** | `data_grid`, `tree_view`, `heatmap_calendar` | Apache-2.0 | Enterprise data-heavy; `table` and `data_table_sortable` don't scale to Carbon's grid capabilities | ✅ Delivered v220 |

---

## Tier 3 — Monitor, not adapt

| Library | Reason | What to watch instead |
|---|---|---|
| **Tailwind UI** | Paid, not MIT — pattern inspiration only (same treatment as Vercel Geist) | DaisyUI (MIT) and HyperUI (MIT) are free Tailwind component libraries worth scanning |
| **React / Radix UI** | React is an implementation layer, irrelevant to A2UI. Radix UI (headless primitives that shadcn builds on) is the best semantic reference in the ecosystem — its prop schemas are exactly what A2UI schema design should reference when in doubt | When designing new field schemas, cross-check against Radix UI's prop definitions |
| **MagicUI / Aceternity** | Animation-heavy; most atoms would be `incompatible_on` all A2UI surfaces anyway | — |

---

## Benchmark coverage by scenario

| Scenario | Coverage before Tier 2 | Gap addressed |
|---|---|---|
| Contact form | ✅ via OpenUI atoms | — |
| Settings panel | ✅ via OpenUI atoms | — |
| E-commerce product page | ⚠️ partial | `product_thumbnail`, `order_status_card`, `inventory_table` |
| Sprint review | ⚠️ approximations | `jira_ticket`, `sprint_board`, `lozenge` |
| Enterprise dashboard | ⚠️ table too limited | `data_grid`, `tree_view`, `heatmap_calendar` |
| AI system demo | ✅ AI-native atoms | — |

---

## How to use this document

When a new library is proposed:
1. Check if it is MIT / Apache-2.0 / permissive. If not, cap at Tier 3.
2. Run it through the benchmark scenarios — does it surface genuine atom gaps, or just aliases?
3. Check against the existing schema for redundancy. Sub-components (RadioItem, SelectItem) are not gaps.
4. If ≥ 3 genuine gaps and permissive license → Tier 2. If AI-native value → Tier 1.
