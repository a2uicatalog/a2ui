# Order Status Card

Shopify Polaris-style order summary card showing order number, date, fulfilment status badge, customer name, line item list, and total. Status is colour-coded — fulfilled (green), unfulfilled (amber), partial (blue), cancelled (red), refunded (grey). Adapted from Polaris Card + Badge patterns.

## Surfaces

web, google-meet-stage, email, pdf, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| order_number | string. Order identifier, e.g. "#1042". |
| date | string (optional). Order date displayed next to the order number. |
| status | string. One of fulfilled | unfulfilled | partial | cancelled | refunded. |
| customer | string (optional). Customer display name. |
| items | array (optional). List of {title, qty, price} line items. |
| total | string (optional). Formatted grand total, e.g. "$124.00". |

## Example payload

```json
{
  "type": "order_status_card",
  "order_number": "Order number",
  "status": "Active"
}
```

Live page: https://a2uicatalog.ai/atoms/order_status_card/
Full field contract: https://a2uicatalog.ai/spec.json
