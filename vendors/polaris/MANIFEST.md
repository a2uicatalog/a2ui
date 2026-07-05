# Vendor: Shopify Polaris

**Source:** https://github.com/Shopify/polaris (`polaris-react/src/components`)
**License:** MIT
**Atom count:** 3
**Attribution:** Atoms in this set adapt Polaris component prop schemas and visual patterns. Field names are mapped to A2UI snake_case conventions; rendering is recompiled into `web_article.py` — no React or Polaris runtime dependency.

## Why

The A2UI benchmark e-commerce scenario (product listing, order management, inventory) produced weak coverage. Existing atoms (`table`, `badge_group`, `metric_comparison_card`) are generic; Polaris offers commerce-specific vocabulary that maps precisely to the scenario's UI requirements.

## Component → atom mapping

| Polaris component | A2UI atom | Adaptation notes |
|---|---|---|
| `ResourceItem` + `Thumbnail` | `product_thumbnail` | Image, title, vendor, SKU, price, compare-at price, status badge, tags. Image is optional — placeholder shown if absent |
| `Card` + `Badge` (order context) | `order_status_card` | Order number, date, fulfilment status, customer, line items, total. Status colour-coded: fulfilled→green, unfulfilled→amber, partial→blue, cancelled→red |
| `DataTable` (inventory context) | `inventory_table` | SKU, product, available, committed, location columns. Available < threshold → amber row highlight |

## Surface notes

All three atoms render on `web`, `meet-stage`, `email`, and `pdf`. Google Chat degrades to plain text. The `image_url` field in `product_thumbnail` is optional and renders a placeholder box when absent — safe for all surfaces.

## Polaris design tokens used

Colours are hardcoded to Polaris equivalents rather than CSS variables to avoid a Polaris runtime dependency:
- `#202223` — text primary
- `#6d7175` — text subdued
- `#e1e3e5` — border default
- `#f1f2f3` — background surface
- Status badge backgrounds match Polaris Badge appearance variants
