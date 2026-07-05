# Renderers — Surface-Specific Implementations

Each renderer takes a list of atom blocks (conforming to `../atoms/schema.yaml`) and returns output for a specific surface.

| File | Surface | Output |
|---|---|---|
| `web_article.py` | Web / blog | Clean HTML |
| `googlechat.py` | Google Chat | cardsV2 JSON (planned) |
| `meet_stage.py` | Google Meet gdm-html-panel | Self-contained HTML (planned) |
