# Playbook: Pitch / Announcement Page

High-impact reveal page for a product launch, initiative announcement, or concept pitch.
Designed to be shared as a URL — no deck, no login, no install.

```json
{
  "title": "The Pitch",
  "theme": "dark",
  "blocks": [
    {
      "type": "cursor_glow",
      "color": "#6366f1",
      "size": 320,
      "opacity": 0.14
    },
    {
      "type": "mesh_gradient",
      "colors": ["#0f0c29", "#302b63", "#24243e"],
      "height": "100vh"
    },
    {
      "type": "marquee_strip",
      "items": ["Zero infrastructure", "Schema in the URL", "273 atoms", "Describe → Generate → Share", "No deploy", "No hosting"],
      "speed": 38,
      "background": "#6366f1",
      "color": "#fff"
    },
    {
      "type": "big_reveal",
      "equation": "Apps Script × A2UI",
      "result": "Pop-up Web App Renderer",
      "color": "#a5b4fc"
    },
    {
      "type": "glass_card",
      "title": "The idea",
      "body": "Describe a page to an AI. Get back a JSON schema. Paste it into a URL. Share the link. The link **is** the app — hosted by Google, always live, zero maintenance.",
      "accent": "#6366f1"
    },
    {
      "type": "counter_group",
      "counters": [
        { "label": "Atoms", "value": 273, "suffix": "" },
        { "label": "Deploys needed", "value": 0, "suffix": "" },
        { "label": "Lines of infra", "value": 0, "suffix": "" },
        { "label": "Surfaces", "value": 3, "suffix": "" }
      ],
      "accent": "#6366f1"
    },
    {
      "type": "split_reveal",
      "left": { "label": "Before", "text": "Hosting. Framework. Deploy pipeline. Database. Auth. Build step. CDN. DevOps." },
      "right": { "label": "After", "text": "Describe it. Get a URL. Done." },
      "accent": "#6366f1"
    },
    {
      "type": "text_reveal_mask",
      "text": "What if the URL was the app?",
      "size": "2.4rem",
      "color": "#a5b4fc"
    }
  ]
}
```
