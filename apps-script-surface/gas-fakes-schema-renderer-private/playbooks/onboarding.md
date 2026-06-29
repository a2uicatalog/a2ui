# Playbook: User / Employee Onboarding

A self-paced onboarding page delivered as a URL. Works for product onboarding,
new employee day-one guides, or client kickoff pages.

```json
{
  "title": "Welcome to the team",
  "theme": "light",
  "blocks": [
    {
      "type": "heading",
      "level": 1,
      "text": "Welcome aboard 👋"
    },
    {
      "type": "body",
      "text": "Everything you need for day one is on this page. Work through it at your own pace — each section unlocks as you scroll."
    },
    {
      "type": "xp_bar",
      "level_label": "Onboarding Progress",
      "xp_current": 0,
      "xp_next": 5
    },
    {
      "type": "step_reveal_sequence",
      "steps": [
        {
          "title": "Set up your tools",
          "content": "Install Slack, set up your Google Workspace account, and join the #general and #engineering channels. Your IT ticket is in your inbox."
        },
        {
          "title": "Read the handbook",
          "content": "The company handbook covers how we work, our values, and what good looks like. It's a 20-minute read — do it today."
        },
        {
          "title": "Meet your team",
          "content": "Your manager has scheduled 1:1s with your five closest collaborators this week. Check your calendar — they're already booked."
        },
        {
          "title": "Your first task",
          "content": "Pick one small thing you can ship or improve in your first two weeks. Tell your manager what it is by end of week one."
        },
        {
          "title": "30-day check-in",
          "content": "At day 30 you'll have a structured check-in with your manager and People team. No surprises — the questions are in the handbook."
        }
      ],
      "accent": "#10b981"
    },
    {
      "type": "accordion",
      "items": [
        {
          "title": "Who to go to for what",
          "content": "IT issues → #it-help. HR questions → people@company.com. Expenses → finance@company.com. Technical questions → #engineering. Anything else → your manager."
        },
        {
          "title": "How we communicate",
          "content": "Async first. Slack for quick questions, email for anything that needs a paper trail, Notion for permanent documentation. Meetings are a last resort, not a default."
        },
        {
          "title": "What success looks like at 90 days",
          "content": "You've shipped something. You know who everyone is. You've identified one thing we should be doing differently and told someone about it."
        }
      ]
    },
    {
      "type": "achievement_badge",
      "title": "Day One Complete",
      "icon": "🚀",
      "color": "#10b981",
      "description": "You made it through day one. The hard part is over."
    },
    {
      "type": "cta_button",
      "label": "Open the team handbook →",
      "url": "https://notion.so"
    }
  ]
}
```
