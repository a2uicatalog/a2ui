# a2h Printer has moved

This package used to live here as a subdirectory of `a2ui-catalogue`. It's now a
standalone repository:

**https://github.com/a2uicatalog/a2hprinter**

Full history (commits, README, ARCHITECTURE.md, self-hosted mode, and the CopilotKit
Channels bridge) was preserved in the move — nothing was lost, this directory is just a
pointer.

Rationale: a2h Printer is a self-hostable product for third parties (its own audience,
license, install flow, and CI), distinct from this repo's atom-vocabulary/catalog
product. Bundling it in the same repo mixed those concerns and buried it behind this
repo's own ops.py/staging machinery, which is irrelevant to someone trying to clone and
self-host a Slack/Teams/Chat bot.
