// whatsapp-channel.ts — fourth-platform port for the a2uicatalog escape
// hatch. Run with `npm run whatsapp` (see package.json / README.md).
//
// UNLIKE Slack/Telegram/Teams, this one is NOT yet live-proven — per the
// original evaluation, WhatsApp's dispatcher (channels-whatsapp/dist/render/
// message.js, `image.link`) was only confirmed by reading CopilotKit's own
// compiled source, never actually run. Same bridge code imported unchanged
// (a2ui-tool.ts / a2ui-bridge.ts), so the render logic itself is exactly as
// proven as the other three — what's untested is this ADAPTER specifically.
//
// STRUCTURALLY DIFFERENT from Telegram: WhatsApp has no long-polling mode.
// The Meta Cloud API delivers messages via an inbound WEBHOOK, so this
// process must be reachable at a public URL (locally: a tunnel like
// `ngrok http 3000`; in production: deploy it, same as Teams' authenticated
// mode). See README.md's WhatsApp section for the full Meta Business setup
// this needs BEFORE it can receive anything — a real WhatsApp Business
// number + Meta Developer app, not just an API key.
import { createChannel } from "@copilotkit/channels";
import { whatsapp, defaultWhatsAppContext } from "@copilotkit/channels-whatsapp";
import { BuiltInAgent, CopilotRuntime, CopilotKitIntelligence } from "@copilotkit/runtime/v2";
import { createCopilotNodeListener } from "@copilotkit/runtime/v2/node";
import { A2UI_PROMPT, renderA2uiAtomTool, fetchWeatherTool } from "./a2ui-tool.ts";

function required(name: string): string {
  const v = process.env[name];
  if (!v) throw new Error(`Missing required env var: ${name}`);
  return v;
}

const MODEL = process.env.A2UI_MODEL ?? "vertex:gemini-2.5-flash";
const WHATSAPP_PORT = Number(process.env.WHATSAPP_PORT ?? 3000);
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
  name: process.env.WHATSAPP_CHANNEL_CODE ?? "a2h-printer-whatsapp",
  identifyUser: "platform",
  adapters: [
    whatsapp({
      accessToken: required("WHATSAPP_ACCESS_TOKEN"),
      phoneNumberId: required("WHATSAPP_PHONE_NUMBER_ID"),
      appSecret: required("WHATSAPP_APP_SECRET"),
      verifyToken: required("WHATSAPP_VERIFY_TOKEN"),
      port: WHATSAPP_PORT,
    }),
  ],
  agent: makeAgent,
  context: [...defaultWhatsAppContext],
});

channel.tool(renderA2uiAtomTool);
channel.tool(fetchWeatherTool);

// Every inbound WhatsApp message is for the bot — there is no @-mention
// concept like Slack/Teams, matching @copilotkit/channels-whatsapp's own
// documented pattern (no message.text needed as a prompt override; the
// thread's own accumulated context already has it).
channel.onMessage(async ({ thread }) => {
  await thread.runAgent();
});

const runtime = new CopilotRuntime({
  intelligence: new CopilotKitIntelligence({ apiKey: required("INTELLIGENCE_API_KEY") }),
  channels: [channel],
});

const listener = createCopilotNodeListener({ runtime });
(async () => {
  await listener.channels.ready();
  console.log(`WhatsApp channel live — webhook on :${WHATSAPP_PORT}. Must be publicly reachable (see README.md).`);
})();
