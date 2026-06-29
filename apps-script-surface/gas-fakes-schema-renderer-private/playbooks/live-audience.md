# Playbook: Live Audience Session

Run this during a talk or workshop. Audience submits words to the live cloud,
votes on a question, and reacts in real time — all from one URL.

Replace `sheet_url` and `write_url` with your published Google Sheet CSV and
GAS write endpoint before encoding.

```json
{
  "title": "Live Audience Session",
  "theme": "dark",
  "blocks": [
    {
      "type": "heading",
      "level": 1,
      "text": "You're live"
    },
    {
      "type": "body",
      "text": "This page is connected to a Google Sheet. Everything you submit appears for everyone in real time."
    },
    {
      "type": "raise_hand",
      "label": "Raise your hand ✋",
      "sheet_url": "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/gviz/tq?tqx=out:csv",
      "write_url": "https://script.google.com/macros/s/YOUR_WRITE_ENDPOINT/exec",
      "accent": "#6366f1"
    },
    {
      "type": "live_vote",
      "question": "How would you describe your current workflow?",
      "options": ["Mostly manual", "Some automation", "Heavily automated", "AI-first"],
      "sheet_url": "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/gviz/tq?tqx=out:csv",
      "write_url": "https://script.google.com/macros/s/YOUR_WRITE_ENDPOINT/exec",
      "accent": "#6366f1",
      "poll_interval": 4000
    },
    {
      "type": "word_cloud",
      "title": "One word that describes your day",
      "sheet_url": "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/gviz/tq?tqx=out:csv&sheet=words",
      "write_url": "https://script.google.com/macros/s/YOUR_WRITE_ENDPOINT/exec",
      "accent": "#6366f1",
      "poll_interval": 3000
    },
    {
      "type": "reaction_shower",
      "reactions": ["🔥", "💡", "👏", "🤯", "🚀"],
      "sheet_url": "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/gviz/tq?tqx=out:csv&sheet=reactions",
      "write_url": "https://script.google.com/macros/s/YOUR_WRITE_ENDPOINT/exec",
      "accent": "#6366f1"
    }
  ]
}
```

## Sheet structure

Create one Google Sheet with tabs:
- `votes` — columns: `option`, `count`
- `words` — column: `word`
- `reactions` — column: `emoji`

Publish each tab as CSV (File → Share → Publish to web → CSV).
