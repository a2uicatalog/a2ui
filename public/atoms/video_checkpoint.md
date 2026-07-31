# Video Checkpoint

YouTube video with interactive quiz questions injected at specified timestamps. Video pauses at each checkpoint and the learner must answer before playback resumes. Correct/wrong feedback shown with explanation. Checkpoint state tracked per-session; completed checkpoints are skipped on replay.

## Surfaces

google-apps-script-web, web, google-meet-stage, mcp-apps

## Fields

| Field | Type |
|---|---|
| youtube_id | string (required). YouTube video ID. |
| title | string (optional). Section heading above the player. |
| checkpoints | array (required). Array of {at_seconds, question, options[], correct (0-based index), explanation} objects. |

## Example payload

```json
{
  "type": "video_checkpoint",
  "youtube_id": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "checkpoints": [
    {
      "time": "1:30",
      "question": "What is X?"
    },
    {
      "time": "3:00",
      "question": "How does Y work?"
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/video_checkpoint/
Full field contract: https://a2uicatalog.ai/spec.json
