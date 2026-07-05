# Vendor Sources — A2UI Catalogue

All atoms in the catalogue trace back to one of these sources. The `source` field in `atoms/schema.yaml` is the atom-level back-pointer; each vendor directory contains a `MANIFEST.md` with the forward mapping (vendor component → A2UI atom) and adaptation notes.

## Vendors

| Vendor | Atoms | License | Directory |
|---|---:|---|---|
| [a2ui](https://github.com/curtiskrygier/a2ui) | 137 | MIT | *(original — no vendor dir)* |
| [UIverse.io community](https://uiverse.io) | 31 | MIT | [uiverse/](uiverse/MANIFEST.md) |
| [OpenUI / Thesys](https://github.com/thesysdev/openui) | 15 | MIT | [openui/](openui/MANIFEST.md) |
| [Flowbite](https://flowbite.com) | 16 | MIT | [flowbite/](flowbite/MANIFEST.md) |
| [shadcn/ui](https://ui.shadcn.com) | 12 | MIT | [shadcn/](shadcn/MANIFEST.md) |
| [Shopify Polaris](https://github.com/Shopify/polaris) | 3 | MIT | [polaris/](polaris/MANIFEST.md) |
| [Atlassian Design System](https://atlassian.design) | 3 | Apache-2.0 | [atlassian/](atlassian/MANIFEST.md) |
| [IBM Carbon Design System](https://github.com/carbon-design-system/carbon) | 3 | Apache-2.0 | [carbon/](carbon/MANIFEST.md) |
| [ExtendLabs UI](https://github.com/extendlabs/ui) | 0 atoms · 12 stage components | MIT | [extendlabs-ui/](extendlabs-ui/MANIFEST.md) |
| [Vercel Geist](https://vercel.com/geist/introduction) | 0 | internal | [vercel/](vercel/MANIFEST.md) *(inspiration reference — atoms are a2ui originals)* |
| [Aceternity UI](https://ui.aceternity.com) | 0 | MIT | [aceternity/](aceternity/MANIFEST.md) *(inspiration reference — atoms are a2ui originals)* |
| **Total** | **236** | | |

## Design principle

No raw vendor source files are stored here. The MANIFEST records the translation: which vendor component became which A2UI atom, what fields were renamed or collapsed, and why. The `atoms/schema.yaml` entry for each atom holds the authoritative field definition and surface compatibility; the vendor MANIFEST holds the provenance and the reasoning behind the adaptation.

This keeps the vendor relationship **traceable** (you can find the original component and its props) without making the catalogue depend on or replicate the vendor's implementation.

## Adding a new vendor

1. Create `vendors/<vendor-name>/MANIFEST.md` following the pattern in any existing MANIFEST.
2. Add `source: {name, url, license}` to each new atom in `atoms/schema.yaml`.
3. Implement the renderer in `renderers/web_article.py` and register in `_RENDERERS`.
4. Add surface compatibility entries (`works_on`, `degraded_on`, `incompatible_on`).
5. Add renderer tests in `tests/test_renderer.py`.
6. Regenerate the README compat table: `python tests/generate_compat_table.py`.
7. Update this index with the new vendor row and atom count.
