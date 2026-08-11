// channel.ts — the live Slack channel entrypoint for CopilotKit mode. Run
// with `npm run slack` (see package.json / README.md).
import { createChannel } from "@copilotkit/channels";
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

/**
 * Retry a run that produced NOTHING — no text, no tool call.
 *
 * Measured, not guessed: Gemini returns a completely empty completion on a
 * real fraction of runs. The raw AG-UI event stream for one is exactly
 * `RUN_STARTED -> RUN_FINISHED` with no RUN_ERROR — so it is neither an
 * error the SDK retries nor a routing decision, and nothing downstream can
 * distinguish it from "the agent chose to say nothing." It surfaces to the
 * user as a message that gets no reply at all.
 *
 * Rate: ~12% unthrottled, rising to ~40% when the model provider's project
 * is under quota pressure. Retrying is cheap and fixes both regimes; kept
 * independent of model choice because an empty completion is a failure mode
 * worth defending against regardless of which model is configured.
 */
function withEmptyRunRetry(agent: BuiltInAgent, maxAttempts = 3): BuiltInAgent {
  const original = agent.runAgent.bind(agent);
  agent.runAgent = async (input?: unknown, subscriber?: unknown) => {
    let last: unknown;
    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
      let produced = false;
      // Pass the caller's subscriber through untouched, wrapping only the two
      // callbacks that signal "the model actually emitted something".
      const probing: Record<string, unknown> = { ...((subscriber as object) ?? {}) };
      for (const hook of ["onTextMessageContentEvent", "onToolCallStartEvent"]) {
        const orig = probing[hook] as ((p: unknown) => unknown) | undefined;
        probing[hook] = (p: unknown) => {
          produced = true;
          return orig?.(p);
        };
      }
      last = await original(input as never, probing as never);
      if (produced) return last as never;
      if (attempt < maxAttempts) {
        console.warn(`[empty-run] attempt ${attempt}/${maxAttempts} produced no output — retrying`);
        // Backoff, not an immediate retry: empty completions cluster under
        // provider quota pressure, so retrying instantly just hits the same
        // wall.
        await new Promise((r) => setTimeout(r, 3000 * attempt));
      } else {
        console.error(`[empty-run] all ${maxAttempts} attempts produced no output; giving up`);
      }
    }
    return last as never;
  };
  return agent;
}

function makeAgent(threadId: string) {
  const headers: Record<string, string> = {};
  // Optional — a2uicatalog.ai/mcp's own server-card.json declares
  // authentication:{type:"none"} (the public endpoint needs no credential at
  // all). This header only matters if you have your own a2uicatalog.ai
  // owner-bypass key for its demo rate limiter; a fresh deployer without one
  // just gets normal public rate limits, a reasonable default, not a broken
  // one. NEVER hardcode a real key here — see README.md.
  if (process.env.A2UICATALOG_DEMO_BYPASS_KEY) {
    headers["x-demo-bypass"] = process.env.A2UICATALOG_DEMO_BYPASS_KEY;
  }
  const agent = new BuiltInAgent({
    model: MODEL,
    maxSteps: 10,
    prompt: A2UI_PROMPT,
    mcpServers: [
      {
        type: "http",
        url: A2UICATALOG_MCP_URL,
        options: { requestInit: { headers } },
      },
    ],
  });
  agent.threadId = threadId;
  return withEmptyRunRetry(agent);
}

const channel = createChannel({
  name: required("CHANNEL_CODE"),
  identifyUser: "platform",
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
  intelligence: new CopilotKitIntelligence({
    apiKey: required("INTELLIGENCE_API_KEY"),
  }),
  channels: [channel],
});

const listener = createCopilotNodeListener({ runtime });
(async () => {
  await listener.channels.ready();
  console.log(`Channel "${required("CHANNEL_CODE")}" is live.`);
})();
