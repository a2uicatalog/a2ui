# Firestore Read

Data connector: reads a single Firestore document (noun: document at project/collection/doc_id) on server-side render (verb: read) and publishes the deserialized result to window.A2UI_DATA[name]. Visual atoms subscribe via window.A2UI_CALLBACKS[name] — the named connector wires data to presentation without direct coupling. GAS surface fetches via Firestore REST API using ScriptApp.getOAuthToken(); requires the datastore OAuth scope in appsscript.json. Optional client-side refresh calls google.script.run.fetchFirestoreDoc() so the page stays live without a reload. Data shape is surface-agnostic — any visual atom can bind to the named feed.

## Surfaces

google-apps-script-web

## Fields

| Field | Type |
|---|---|
| name | string. Connector name — visual atoms subscribe via window.A2UI_CALLBACKS[name] (required). |
| project | string. GCP project ID that owns the Firestore database (required). |
| collection | string. Firestore collection name (required). |
| doc_id | string. Document ID within the collection (required). |
| refresh | integer (optional). Client-side refresh interval seconds. 0 = initial load only. Default 0. |

## Example payload

```json
{
  "type": "firestore_read",
  "name": "Firestore Read",
  "project": "my-project-id",
  "collection": "users",
  "doc_id": "Doc id"
}
```

Live page: https://a2uicatalog.ai/atoms/firestore_read/
Full field contract: https://a2uicatalog.ai/spec.json
