# Playbook: Meeting Briefing / Pre-Read

A pre-meeting briefing page sent as a URL. Recipient opens the link on any device —
no attachment, no login, no formatting to worry about.

Swap the content fields for each meeting. Encode the schema, share the link.

```json
{
  "title": "Q3 Board Briefing — Pre-Read",
  "theme": "light",
  "blocks": [
    {
      "type": "heading",
      "level": 1,
      "text": "Q3 Board Briefing"
    },
    {
      "type": "body",
      "text": "Pre-read for the board session on **17 June 2026**. Please review before the meeting — we will not be presenting slides."
    },
    {
      "type": "alert_banner",
      "variant": "info",
      "text": "90 minute session · 3 agenda items · Decision required on Item 2"
    },
    {
      "type": "status_timeline",
      "title": "Agenda",
      "items": [
        { "label": "09:00", "text": "Q3 Performance Review — CFO", "status": "done" },
        { "label": "09:30", "text": "Strategic Investment Decision — CEO (decision required)", "status": "active" },
        { "label": "10:00", "text": "Risk & Compliance Update — CRO", "status": "pending" }
      ]
    },
    {
      "type": "accordion",
      "items": [
        {
          "title": "Item 1 — Q3 Performance",
          "content": "Revenue £4.2M (+18% YoY). Gross margin 68% (target 65%). CAC down 12% vs Q2. Three key wins: Acme Corp, Global Foods, Metro Health. Full P&L in the appendix."
        },
        {
          "title": "Item 2 — Investment Decision",
          "content": "Proposal to allocate £800K to the AI-native product track in Q4. Two options on the table: (A) build internally over 6 months, (B) acquire a seed-stage team now. Board vote required."
        },
        {
          "title": "Item 3 — Risk Update",
          "content": "Three open items: data residency compliance (EU AI Act), key-person dependency on engineering lead, and supply chain exposure in APAC. Full risk register attached."
        }
      ]
    },
    {
      "type": "glass_card",
      "title": "What we need from you",
      "body": "A decision on Item 2 by end of session. If you have questions before the meeting, reply to this briefing thread.",
      "accent": "#1d4ed8"
    },
    {
      "type": "countdown_timer",
      "label": "Meeting starts in",
      "target": "2026-06-17T09:00:00",
      "accent": "#1d4ed8"
    }
  ]
}
```
