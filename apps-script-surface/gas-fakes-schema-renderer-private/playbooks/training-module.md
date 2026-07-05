# Playbook: Training Module with Quiz

A single-module training page with content, a knowledge check, and a pass/fail branch.
Set `on_pass.url` and `on_fail.url` to encoded schema URLs to chain modules together.

```json
{
  "title": "Module 1 — Cloud Fundamentals",
  "theme": "light",
  "blocks": [
    {
      "type": "heading",
      "level": 1,
      "text": "Cloud Fundamentals"
    },
    {
      "type": "body",
      "text": "This module covers the core concepts behind cloud computing — the building blocks every practitioner needs before diving into specific platforms."
    },
    {
      "type": "xp_bar",
      "level_label": "Module 1 of 4",
      "xp_current": 1,
      "xp_next": 4
    },
    {
      "type": "tabbed_section",
      "tabs": [
        {
          "label": "What is Cloud?",
          "content": "Cloud computing delivers compute, storage, and networking as on-demand services over the internet. You pay for what you use, scale instantly, and never manage physical hardware."
        },
        {
          "label": "Service Models",
          "content": "**IaaS** — raw infrastructure (VMs, storage). **PaaS** — managed runtime (App Engine, Cloud Run). **SaaS** — finished software (Gmail, Salesforce). Each layer abstracts more complexity."
        },
        {
          "label": "Key Benefits",
          "content": "Elasticity: scale up or down in seconds. Global reach: deploy in any region. Pay-as-you-go: no upfront capex. Managed services: no patching, no racking."
        }
      ]
    },
    {
      "type": "alert_banner",
      "variant": "info",
      "text": "Complete the quiz below with 70% or more to unlock Module 2."
    },
    {
      "type": "quiz_set",
      "title": "Knowledge Check — Cloud Fundamentals",
      "pass_score": 70,
      "accent": "#6366f1",
      "questions": [
        {
          "question": "Which service model gives you the most control over the underlying infrastructure?",
          "options": ["SaaS", "PaaS", "IaaS", "FaaS"],
          "correct": 2,
          "explanation": "IaaS gives you raw VMs and storage — you manage the OS, runtime, and application. More control, more responsibility."
        },
        {
          "question": "What does 'elasticity' mean in the context of cloud?",
          "options": [
            "The ability to recover from failures automatically",
            "The ability to scale resources up or down based on demand",
            "The ability to run workloads across multiple clouds",
            "The ability to encrypt data at rest"
          ],
          "correct": 1,
          "explanation": "Elasticity is the defining cloud characteristic — resources expand under load and contract when idle, matching capacity to demand in real time."
        },
        {
          "question": "Cloud Run is an example of which service model?",
          "options": ["IaaS", "SaaS", "PaaS", "On-premises"],
          "correct": 2,
          "explanation": "Cloud Run is a managed container runtime — you bring the container, Google manages the infrastructure. That's PaaS."
        }
      ],
      "on_pass": {
        "title": "Module 1 complete!",
        "badge": "Cloud Fundamentals",
        "icon": "☁️",
        "message": "Strong foundation. Head to Module 2 to explore compute options."
      },
      "on_fail": {
        "title": "Almost there",
        "message": "Review the tabs above and try again — 70% to unlock the next module."
      }
    }
  ]
}
```
