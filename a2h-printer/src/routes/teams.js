// POST /api/messages — the single Bot Framework endpoint Teams (and every
// other Bot Framework channel) delivers Activities to. Structurally
// different from the Slack routes: one endpoint for everything (commands,
// card clicks, membership events), routed by activity.type/activity.text,
// rather than Slack's separate /slack/command and /slack/interactivity.
//
// SCOPE (v1): 'message' activities only — list/show/help, parity with
// /slack/command. Adaptive Card Action.Submit ('invoke' activities) is NOT
// wired yet (Slack's decision-tree click-through equivalent) — deliberate
// scope cut, not an oversight, same incremental order Slack was built in
// (basic list/show landed before interactivity did).
//
// Envelope parsing + Teams-specific reply shaping only — the actual
// help|whoami|list|show|weather business logic lives once, in
// lib/command-handler.js, shared with routes/command.js.
import { verifyBotFrameworkAuth } from '../lib/teams-security.js';
import { getConnectorToken } from '../lib/teams-auth.js';
import { getStore, teamsOwnerKey } from '../storage/index.js';
import { renderReadingToTeams, postBlocksToTeams } from '../lib/render-to-teams.js';
import { fetchWeatherBlocks } from '../lib/weather.js';
import { runCommand } from '../lib/command-handler.js';
import { config } from '../config.js';

// Teams wraps its own @mention markup into activity.text as literal
// <at>Bot Name</at> tags (see activity.entities for the structured form) —
// strip it before parsing a command, same reasoning as Slack's slash-command
// text never containing the app name.
function stripMentions(text) {
  return (text || '').replace(/<at>.*?<\/at>/gi, '').trim();
}

async function replyText(serviceUrl, conversationId, activityId, text) {
  const token = await getConnectorToken();
  const url = `${serviceUrl.replace(/\/+$/, '')}/v3/conversations/${encodeURIComponent(conversationId)}/activities/${encodeURIComponent(activityId)}`;
  await fetch(url, {
    method: 'POST',
    headers: { 'content-type': 'application/json', authorization: `Bearer ${token}` },
    body: JSON.stringify({ type: 'message', text }),
  });
}

export async function handleTeamsMessage(c) {
  if (!config.teamsAppId || !config.teamsAppPassword) {
    return c.json({ error: 'Teams surface not configured (TEAMS_APP_ID/TEAMS_APP_PASSWORD unset)' }, 501);
  }

  try {
    await verifyBotFrameworkAuth(c.req.header('authorization'), config.teamsAppId);
  } catch (e) {
    return c.text('unauthorized', 401);
  }

  let activity = {};
  try { activity = await c.req.json(); } catch (e) { /* empty */ }

  // Ack everything that isn't a plain message immediately — membership
  // events, typing indicators, etc. all POST here too, and Bot Framework
  // expects a fast 200 regardless of whether we do anything with them.
  if (activity.type !== 'message') return c.text('', 200);

  const serviceUrl = activity.serviceUrl;
  const conversationId = activity.conversation && activity.conversation.id;
  const tenantId = activity.conversation && activity.conversation.tenantId;
  // aadObjectId is the stable AAD identity Teams attaches; .from.id is a
  // channel-specific id always present but not guaranteed stable across
  // conversation types — prefer aadObjectId, matching why Slack keys on
  // user_id (a real Slack ID) and never on the display-only user_name.
  const userId = (activity.from && (activity.from.aadObjectId || activity.from.id)) || null;

  if (!serviceUrl || !conversationId || !tenantId || !userId) {
    return c.text('', 200); // nothing safe to reply to — ack and drop
  }

  const text = stripMentions(activity.text);
  const reply = (msg) => replyText(serviceUrl, conversationId, activity.id, msg);

  await runCommand({
    text,
    ownerKey: teamsOwnerKey(tenantId, userId),
    getStore,
    reply,
    helpText: () => 'Usage: "list" to see your saved readings, "show <id>" to post one here, "weather <city>" for a live forecast card.',
    unknownText: () => 'Unknown command. Usage: "list", "show <id>", "weather <city>".',
    // Debug affordance, matching /a2ui whoami on the Slack side — tenantId
    // and the AAD object id aren't secrets, but there's no easy way to read
    // them off otherwise, and they're exactly what /mcp needs to target a
    // save against this same identity for testing.
    whoamiText: () => `tenant_id: ${tenantId}\nuser_id: ${userId}`,
    listLineFor: (r) => `- ${r.id} — ${r.title || '(untitled)'}`,
    renderReading: async (store, { id }) => {
      const result = await renderReadingToTeams(store, { id, serviceUrl, conversationId });
      // On success, renderReadingToTeams already posted the card as a new
      // activity — no separate confirmation reply needed, matching how the
      // card post itself IS the visible response (nothing ephemeral in
      // Teams the way Slack's ephemeral replies work). Only failure gets a
      // reply.
      if (!result.ok) await reply(`Could not post: ${result.reason}`);
    },
    weatherUsageText: () => 'Usage: "weather <city>"',
    fetchWeather: fetchWeatherBlocks,
    postWeather: async (store, weather) => {
      const result = await postBlocksToTeams(weather.blocks, { serviceUrl, conversationId });
      if (!result.ok) await reply(`Could not post: ${result.reason}`);
    },
  });

  return c.text('', 200);
}
