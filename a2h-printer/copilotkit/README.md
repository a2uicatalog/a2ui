# a2uicatalog a2h Printer — CopilotKit Channels mode

Hosted, LLM-agent-driven delivery of a2uicatalog content into Slack, Telegram, and Teams via
[CopilotKit](https://copilotkit.ai)'s Channels SDK — natural-language tool-calling instead of
fixed commands. This is the "shiny" companion to `../src/`'s self-hosted mode, not a
replacement for it.

**Read this before installing: this mode is NOT sovereign.** It runs through CopilotKit's own
hosted "Intelligence" backend (`CopilotRuntime` + `CopilotKitIntelligence`) — your Slack
workspace's credentials and message content transit CopilotKit's infrastructure, not just your
own. If that's a blocker for you, use `../src/` (self-hosted mode) instead; that's exactly why it
exists. Use this mode when you want the broadest reach and the most natural-language-driven demo
with the least setup, and are fine with CopilotKit's hosted trust model.

## What this actually proves — read the fine print

Not every platform below has been verified to the same degree. Be precise about this when
describing what works:

| Platform | Verified how |
|---|---|
| Slack | **Live** — real messages, real renders, cross-checked against the renderer's own logs |
| Telegram | **Live**, repeatedly — same bridge code, unchanged, imported not reimplemented. Also proved `fetch_weather` (live Open-Meteo data + Tier-2 image render) end-to-end here. |
| Teams | **Render-confirmed** via a non-LLM fixture harness, not the full live agent loop |
| WhatsApp | **Not yet live-tested** — `whatsapp-channel.ts` exists and imports the same unchanged bridge code, but the adapter itself has only been confirmed by reading CopilotKit's own compiled dispatcher, never run. Needs real Meta Business setup — see below. |
| Discord | **Static only** — confirmed by reading CopilotKit's own compiled dispatcher, never run, no channel file built |

The differentiator over CopilotKit's own ~35 native primitives: this bridge's Tier 2 image
fallback (`a2ui-bridge.ts`'s `a2uiAtomToImage`) reaches all 532 a2uicatalog atoms, not just the
ones CopilotKit has a native JSX element for.

**One known, unresolved upstream bug**: CopilotKit's own managed delivery layer has been observed
to silently drop a completed, correctly-rendered message mid-flight
(`ChannelDeliveryStoppedError`). This is a CopilotKit-side issue, not something this bridge can
fix — if a render appears to vanish with no error in this bridge's own logs, check for that error
in CopilotKit's dashboard/logs before assuming the bridge is broken.

## Install — for a human OR an AI coding agent following this file

**Fastest path: `./setup.sh`** — runs every scriptable step for you (npm installs, `.env`
scaffolding, the one static config value CopilotKit's own CLI doesn't provision), invokes each
interactive CLI step in turn and waits for you, and prompts you directly for the two values only
you can supply (`INTELLIGENCE_API_KEY`, `CHANNEL_CODE`) instead of sending you back to this file
to find where they go. Safe to re-run — never overwrites an existing `.env`, only fills in what's
missing.

The manual walkthrough below is the same steps, spelled out — useful if you'd rather do each one
yourself, or if you're an AI coding agent that should understand what `setup.sh` is actually
doing rather than just running it blind. Each step is marked **[scriptable]** (run it directly,
no human needed) or **[human]** (requires an interactive browser login or TUI prompt — an agent
following this file manually should stop and ask the operator to complete these, not attempt to
automate them).

1. **[human]** Install the CopilotKit CLI and log in:
   ```sh
   npm install -g copilotkit
   npx copilotkit login
   ```
   Opens a browser for OAuth. No way to script this — it's an interactive account login.

2. **[human]** Select or create a CopilotKit project:
   ```sh
   npx copilotkit project select
   ```
   Interactive TUI. Note the `INTELLIGENCE_API_KEY` it gives you.

3. **[human]** Set `INTELLIGENCE_GATEWAY_WS_URL` by hand. `project select` does **not**
   auto-provision this — a real, currently-tracked CopilotKit CLI gap (their issue OSS-714), not
   something you missed a step for. The correct value is always:
   ```
   INTELLIGENCE_GATEWAY_WS_URL=wss://realtime.intelligence.copilotkit.ai
   ```

4. **[human]** Create the Slack app, from CopilotKit's own CLI-generated manifest (do NOT create
   it from scratch on api.slack.com — that path is known to produce a silent Event-Subscriptions
   Request-URL gap and a scope-mismatch loop):
   ```sh
   npx copilotkit channels add --adapter slack
   ```
   Interactive — prompts for a channel name (this becomes `CHANNEL_CODE`) and walks you through
   installing the generated app manifest to your workspace.

5. **[scriptable]**
   ```sh
   cp .env.example .env
   ```
   Then fill in the values from steps 1-4, plus your model provider credentials (this bridge was
   live-tested against Vertex AI / `gemini-2.5-flash` — `GOOGLE_VERTEX_PROJECT`/
   `GOOGLE_VERTEX_LOCATION`, using `gcloud auth application-default login` — **[human]**, a
   one-time interactive step, not a scriptable API key). See `.env.example`'s own comments for
   every variable.

6. **[scriptable]**
   ```sh
   npm install
   ```

7. **[scriptable]**
   ```sh
   npm run slack
   ```
   Should print `Channel "<your CHANNEL_CODE>" is live.` Message the bot in Slack and ask for an
   atom — try `show me a bar chart` or `render a globe_3d atom` (the latter has no Tier-1
   analogue, so it exercises the Tier 2 image fallback specifically).

### Telegram (optional, cheapest second platform to prove)

**[human]**: get a bot token from [@BotFather](https://t.me/BotFather) on Telegram — no webhook
or public URL needed, this adapter long-polls. Set `TELEGRAM_BOT_TOKEN` in `.env`, then
**[scriptable]** `npm run telegram`.

### Teams (optional)

**[scriptable]**, no Microsoft credentials required for local dev: `npm run teams`, then in a
second terminal run Microsoft's own local test harness:
```sh
npx @microsoft/m365agentsplayground
```
Open the playground (prints its own local URL) and point it at `localhost:3978` — renders real
Adaptive Cards without any Azure Bot registration. Only set `TEAMS_APP_ID`/`TEAMS_APP_PASSWORD`/
`TEAMS_TENANT_ID` (all **[human]**, from a real Azure Bot resource) once you need a real tenant.

## Architecture

See `../ARCHITECTURE.md`'s "one repo, two entrypoints, one shared core" section for why this
lives as a sibling to `../src/` rather than folded into its platform-adapter registry, and how
`a2ui-bridge.ts`'s Tier 2 fallback shares its signing implementation
(`../src/lib/crypto-utils.js`'s `signRenderUrl`) with the self-hosted mode — same
`RENDER_SIGNING_KEY`, same public renderer, zero duplicated signing logic.

## Files

- `channel.ts` / `telegram-channel.ts` / `teams-channel.ts` — one entrypoint per platform, each
  importing the SAME `a2ui-tool.ts`/`a2ui-bridge.ts` unchanged (the point being that the bridge
  code itself is platform-independent, not reimplemented per platform)
- `a2ui-bridge.ts` — Tier 1 (native CopilotKit primitive mapping) + Tier 2 (signed-image
  fallback, delegating to the shared printer core)
- `a2ui-tool.ts` — the single `render_a2ui_atom` `ChannelTool` + system prompt, shared by every
  channel entrypoint so a prompt change can't silently drift between platforms

---

## ⚠️ WhatsApp — experimental, unverified, you would be the first live test

Slack, Telegram, and Teams above are all confirmed working, to the degrees shown in this
README's own proof table. WhatsApp is genuinely different, which is why it's set apart down
here rather than presented as a fourth peer alongside them.

**Read this before spending 15+ minutes on Meta's setup flow below.** This adapter has never
actually been run against a real message. `whatsapp-channel.ts` exists, imports the same
unchanged, already-proven bridge code (`a2ui-bridge.ts`/`a2ui-tool.ts`), and its own header
comment says so directly: *"this is the first live attempt at this specific adapter."*
Everything about it is real and complete except proof. If you set this up and hit a problem,
the most likely explanation is this specific adapter, not the shared rendering logic underneath
it — that part already has Slack- and Telegram-grade evidence behind it.

Unlike Telegram, there is no "just get a token" path — WhatsApp needs a real Meta Business
integration, and it receives messages via an inbound **webhook**, not long-polling, so this
process must be reachable at a public URL the whole time it runs.

Per Meta's own "WhatsApp Cloud API Get Started" guide:

1. **[human]** [Meta App Dashboard](https://developers.facebook.com/apps) → Create App → the
   **"Connect with customers through WhatsApp"** use case → pick/create a Business Portfolio.
   Lands you on **Customize use case → Connect on WhatsApp → Quickstart**.
2. **[human]** **API Setup** page → connect (or create) a WhatsApp Business Account → select/add
   a phone number. Note the **Phone Number ID** shown there.
3. **[human]** Get a PERMANENT token, not the quickstart's 24h temporary one: Meta's
   [Business Settings](https://business.facebook.com/latest/settings) → **System users** →
   Add+ → create a system user → **Assign Assets**: your app (toggle *Manage app* under Full
   control) and your WhatsApp account (toggle *Manage WhatsApp Business accounts* under Full
   control) → **Generate token**, granting `business_management`, `whatsapp_business_messaging`,
   `whatsapp_business_management`. This is your `WHATSAPP_ACCESS_TOKEN`.
4. **[human]** **App Settings → Basic** → note the **App Secret** (`WHATSAPP_APP_SECRET`).
5. **[human]** Pick any string yourself as `WHATSAPP_VERIFY_TOKEN` — a shared secret YOU invent,
   not one Meta gives you; you'll enter this exact value into Meta's webhook config in step 7.
6. **[scriptable]** Fill in `.env`'s WhatsApp section, then start the channel and expose it:
   ```sh
   npm run whatsapp
   # in a second terminal:
   ngrok http 3000   # or any other tunnel — note the https:// URL it prints
   ```
7. **[human]** WhatsApp → **Configuration** page (not the quickstart's own separate sample-echo-
   bot webhook flow — that's for learning the payload shape only, not needed here since
   `@copilotkit/channels-whatsapp` already IS the real webhook receiver): set the Callback URL to
   your tunnel URL, Verify Token to step 5's value, Verify and Save, then subscribe to the
   `messages` webhook field.
8. Message your WhatsApp Business number and confirm in this process's logs. **This is the first
   live attempt at this specific adapter** — if something breaks that isn't in the Slack/
   Telegram/Teams paths above, it's plausibly this adapter, not the shared bridge code
   (`a2ui-bridge.ts`/`a2ui-tool.ts` are unchanged from the platforms already proven live).

## License

MIT — see `LICENSE`.
