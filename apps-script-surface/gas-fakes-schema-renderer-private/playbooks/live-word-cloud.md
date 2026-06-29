# Playbook: Live Audience Word Cloud

Real-time word cloud backed by a Google Sheet. Participants type a word — it appears
on screen within 5 seconds. Perfect for icebreakers, retrospectives, or live Q&A.

## Setup

1. Create a Google Sheet with headers `word,count` in row 1
2. **File → Share → Publish to web → Sheet1 → CSV → Publish**
3. Copy the published CSV URL into `sheet_url` below
4. (Optional) For write-back from the input field, deploy a separate GAS `doGet`
   endpoint that appends `?word=foo` to the Sheet, and set that URL as `write_url`

## Schema

```json
{
  "title": "What word comes to mind?",
  "theme": "dark",
  "blocks": [
    {
      "type": "cursor_glow",
      "color": "#6366f1",
      "opacity": 0.12
    },
    {
      "type": "heading",
      "level": 1,
      "text": "What word comes to mind?"
    },
    {
      "type": "body",
      "text": "Type a word below — it joins the cloud in real time."
    },
    {
      "type": "word_cloud",
      "sheet_url": "PASTE_YOUR_PUBLISHED_CSV_URL_HERE",
      "write_url": "",
      "poll": 5,
      "placeholder": "Type a word and press Enter…",
      "accent": "#6366f1",
      "palette": ["#6366f1", "#8b5cf6", "#ec4899", "#f59e0b", "#10b981", "#3b82f6", "#ef4444", "#14b8a6"]
    }
  ]
}
```

## Static version (no Sheet required)

```json
{
  "title": "Session Themes",
  "blocks": [
    {
      "type": "word_cloud",
      "words": [
        { "text": "innovation", "weight": 9 },
        { "text": "scale", "weight": 7 },
        { "text": "simplicity", "weight": 8 },
        { "text": "velocity", "weight": 6 },
        { "text": "trust", "weight": 5 },
        { "text": "automation", "weight": 7 },
        { "text": "impact", "weight": 6 },
        { "text": "clarity", "weight": 4 },
        { "text": "resilience", "weight": 5 },
        { "text": "collaboration", "weight": 8 }
      ],
      "accent": "#6366f1",
      "placeholder": "Add your word…"
    }
  ]
}
```
