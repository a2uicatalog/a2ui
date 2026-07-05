# Playbook: AI Workflow Explainer

Show the full prompt → schema → app journey.
Good for explaining how to use the renderer to a new user or in a demo.

```json
{
  "title": "From Prompt to App in 60 Seconds",
  "theme": "light",
  "blocks": [
    {
      "type": "heading",
      "level": 1,
      "text": "From prompt to app in 60 seconds"
    },
    {
      "type": "body",
      "text": "This is the entire workflow. Three steps. No code required."
    },
    {
      "type": "next_step_strip",
      "steps": [
        { "label": "1. Describe", "detail": "Tell Gemini what page you want" },
        { "label": "2. Generate", "detail": "Get a JSON schema back" },
        { "label": "3. Encode", "detail": "Base64 the schema into a URL" },
        { "label": "4. Share", "detail": "The URL is your app" }
      ],
      "accent": "#6366f1"
    },
    {
      "type": "prompt_to_schema",
      "prompt": "Create a product launch announcement page with a countdown to midnight tonight, three key stats (10K users, 99.9% uptime, $0 hosting), and a bold headline.",
      "schema": "{\"title\":\"Launch\",\"theme\":\"dark\",\"blocks\":[{\"type\":\"big_reveal\",\"equation\":\"10K users\",\"result\":\"Day one\"},{\"type\":\"counter_group\",\"counters\":[{\"label\":\"Users\",\"value\":10000},{\"label\":\"Uptime\",\"value\":\"99.9%\"},{\"label\":\"Hosting\",\"value\":\"$0\"}]},{\"type\":\"countdown_timer\",\"label\":\"Launches in\",\"target\":\"2026-06-18T00:00:00\"}]}",
      "accent": "#6366f1"
    },
    {
      "type": "copy_prompt",
      "label": "Gemini prompt — paste this to generate a schema",
      "text": "You are an A2UI schema generator. I will describe a page and you will return a JSON schema using the A2UI atom vocabulary. Respond with only valid JSON, no explanation.\n\nAtom types available: heading, body, big_reveal, counter_group, countdown_timer, glass_card, alert_banner, cta_button, accordion, quiz_set, word_cloud, live_vote, take_away_card, next_step_strip, copy_prompt, renderer_stats, surface_map, before_after_stack.\n\nEach block has a \"type\" field. Other fields depend on the atom.\n\nMy page: [describe your page here]"
    },
    {
      "type": "url_anatomy",
      "accent": "#6366f1"
    },
    {
      "type": "take_away_card",
      "headline": "Anyone can build a web app now.",
      "sub": "If you can describe it in a sentence, Gemini can schema it. If it has a schema, the renderer can run it.",
      "gradient": ["#6366f1", "#4f46e5"],
      "text_color": "#fff"
    }
  ]
}
```
