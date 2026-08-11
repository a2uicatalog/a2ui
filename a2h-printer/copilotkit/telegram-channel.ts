// telegram-channel.ts — second-platform proof for the a2uicatalog escape
// hatch. Run with `npm run telegram` (see package.json / README.md).
//
// WHY THIS EXISTS: the Tier 2 image fallback was originally live-proven on
// Slack only. Reading every CopilotKit platform adapter's dispatcher shows
// all five CopilotKit platforms render the PORTABLE `image` primitive and
// all five take a URL, never raw bytes — exactly what the shared printer
// (../src/lib/crypto-utils.js's signRenderUrl) produces. Telegram is the
// cheapest of the remaining four to prove live (long-polling by default, so
// no public URL / webhook / app-manifest setup at all), which turns
// "verified by reading their code" into "verified by running it."
//
// Deliberately a SEPARATE channel from channel.ts rather than a second
// adapter on the same one: a distinct Intelligence Channel name keeps this
// from disturbing a live Slack bot on the same CopilotKit project, and the
// whole point is that the SAME bridge code serves a different platform
// unchanged (a2ui-tool.ts / a2ui-bridge.ts are imported, not reimplemented).
//
// NOTE the trust-boundary difference from Slack, worth recording: Telegram's
// adapter holds its OWN bot token locally (`telegram({token})`), whereas the
// Slack channel's credentials live server-side in CopilotKit's Intelligence
// backend. Same SDK, materially different credential posture per platform.
import { createChannel } from "@copilotkit/channels";
import { telegram, defaultTelegramTools, defaultTelegramContext } from "@copilotkit/channels-telegram";
import { BuiltInAgent, CopilotRuntime, CopilotKitIntelligence } from "@copilotkit/runtime/v2";
import { createCopilotNodeListener } from "@copilotkit/runtime/v2/node";
import { A2UI_PROMPT, renderA2uiAtomTool, fetchWeatherTool } from "./a2ui-tool.ts";

function required(name: string): string {
  const v = process.env[name];
  if (!v) throw new Error(`Missing required env var: ${name}`);
  return v;
}

const MODEL = process.env.A2UI_MODEL ?? "vertex:gemini-2.5-flash";
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

const channel = createChannel({
  name: process.env.TELEGRAM_CHANNEL_CODE ?? "a2h-printer-telegram",
  identifyUser: "platform",
  adapters: [telegram({ token: required("TELEGRAM_BOT_TOKEN") })],
  agent: makeAgent,
  context: [...defaultTelegramContext],
  tools: [...defaultTelegramTools],
});

// Same ChannelTool as the Slack bridge — imported, not reimplemented. If this
// renders on Telegram, the escape hatch is platform-independent in practice
// and not just in the adapters' source.
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
  console.log(`Telegram channel "${channel.name ?? "a2h-printer-telegram"}" is live (long-polling).`);
})();
