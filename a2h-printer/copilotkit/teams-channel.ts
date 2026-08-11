// teams-channel.ts — THIRD-platform proof for the a2uicatalog escape hatch.
// Run with `npm run teams` (see package.json / README.md).
//
// Same deliberate shape as telegram-channel.ts: a separate Intelligence
// channel, importing a2ui-tool.ts / a2ui-bridge.ts UNCHANGED. If an atom
// renders here too, the escape hatch is platform-independent in practice
// across three genuinely different rendering models — Slack Block Kit,
// Telegram HTML+photo, and Teams Adaptive Cards.
//
// NO MICROSOFT CREDENTIALS needed for local dev, which is why this is worth
// doing before any Azure Bot registration: `teams({ port })` with no
// clientId runs anonymous, and Microsoft's own M365 Agents Playground
// (`npx @microsoft/m365agentsplayground`, http://localhost:56150) speaks to
// it on :3978 and renders REAL Adaptive Cards. That makes this a genuine
// test of Teams' card renderer, not a mock — while deferring the Azure Bot
// App ID/secret until there's a reason to talk to a real tenant.
//
// Credential posture, third variant in three platforms (worth recording —
// "CopilotKit holds your platform credentials" is a Slack-specific
// observation and does not generalise):
//   Slack    — credentials live server-side in CopilotKit's Intelligence
//   Telegram — bot token held LOCALLY by the adapter
//   Teams    — either (self-hosted adapter holds clientId/secret/tenantId,
//              OR Managed Channels holds them); anonymous for local dev
import { createChannel } from "@copilotkit/channels";
import { teams } from "@copilotkit/channels-teams";
import { BuiltInAgent, CopilotRuntime, CopilotKitIntelligence } from "@copilotkit/runtime/v2";
import { createCopilotNodeListener } from "@copilotkit/runtime/v2/node";
import { A2UI_PROMPT, renderA2uiAtomTool, fetchWeatherTool } from "./a2ui-tool.ts";

function required(name: string): string {
  const v = process.env[name];
  if (!v) throw new Error(`Missing required env var: ${name}`);
  return v;
}

const MODEL = process.env.A2UI_MODEL ?? "vertex:gemini-2.5-flash";
const TEAMS_PORT = Number(process.env.TEAMS_PORT ?? 3978);
const A2UICATALOG_MCP_URL = process.env.A2UICATALOG_MCP_URL ?? "https://a2uicatalog.ai/mcp";

function makeAgent(threadId: string) {
  const headers: Record<string, string> = {};
  if (process.env.A2UICATALOG_DEMO_BYPASS_KEY) {
    headers["x-demo-bypass"] = process.env.A2UICATALOG_DEMO_BYPASS_KEY;
  }
  const agent = new BuiltInAgent({
    model: MODEL,
    maxSteps: 10,
    prompt: A2UI_PROMPT,
    mcpServers: [{ type: "http", url: A2UICATALOG_MCP_URL, options: { requestInit: { headers } } }],
  });
  agent.threadId = threadId;
  return agent;
}

// Credentials are passed ONLY when present: `teams({ port })` alone is the
// documented anonymous local-dev mode, and sending empty-string clientId /
// clientSecret would be a different (broken) configuration rather than the
// same one, so the keys are omitted entirely instead of blanked.
const teamsOpts: Record<string, unknown> = { port: TEAMS_PORT };
if (process.env.TEAMS_APP_ID) teamsOpts.clientId = process.env.TEAMS_APP_ID;
if (process.env.TEAMS_APP_PASSWORD) teamsOpts.clientSecret = process.env.TEAMS_APP_PASSWORD;
if (process.env.TEAMS_TENANT_ID) teamsOpts.tenantId = process.env.TEAMS_TENANT_ID;

const channel = createChannel({
  name: process.env.TEAMS_CHANNEL_CODE ?? "a2h-printer-teams",
  identifyUser: "platform",
  adapters: [teams(teamsOpts as never)],
  agent: makeAgent,
});

channel.tool(renderA2uiAtomTool);
channel.tool(fetchWeatherTool);

channel.onMessage(async ({ thread, message }) => {
  await thread.runAgent({
    prompt: message.text,
    context: [{ description: "Originating platform", value: message.platform }],
  });
});

const runtime = new CopilotRuntime({
  intelligence: new CopilotKitIntelligence({ apiKey: required("INTELLIGENCE_API_KEY") }),
  channels: [channel],
});

const listener = createCopilotNodeListener({ runtime });
(async () => {
  await listener.channels.ready();
  const mode = teamsOpts.clientId ? "authenticated" : "anonymous (local dev)";
  console.log(`Teams channel live on :${TEAMS_PORT} — ${mode}`);
  console.log(`Point the playground at it:  npx @microsoft/m365agentsplayground`);
})();
