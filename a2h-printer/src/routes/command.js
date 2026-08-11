// POST /slack/command — public, Slack-signed (verified by adapters/slack.js's
// shared middleware before this handler runs). Unlike the source repo's
// slack-link.js, this command has no `link`/`unlink` subcommands — v1 has
// no separate reader identity to link to (plan decision #1); Slack's own
// team_id:user_id IS the identity, so storage keys directly on that.
//
// Envelope parsing + Slack-specific reply shaping only — the actual
// help|whoami|list|show|weather business logic lives once, in
// lib/command-handler.js, shared with routes/teams.js.
import { getStore, slackOwnerKey } from '../storage/index.js';
import { renderReadingToSlack, postBlocksToSlack } from '../lib/render-to-slack.js';
import { fetchWeatherBlocks } from '../lib/weather.js';
import { runCommand } from '../lib/command-handler.js';

export async function handleCommand(c) {
  const rawBody = c.get('rawBody');
  const params = new URLSearchParams(rawBody);
  const text = (params.get('text') || '').trim();
  const teamId = params.get('team_id');
  const userId = params.get('user_id');
  const channelId = params.get('channel_id');

  const ephemeral = (msg) => c.json({ response_type: 'ephemeral', text: msg });

  if (!teamId || !userId) {
    return ephemeral('Could not identify your Slack account — try again.');
  }

  // Slack's reply channel is the ephemeral HTTP response itself — buffer
  // the last reply() call and return it once runCommand resolves. Slack
  // sends AT MOST one ephemeral reply per command, unlike Teams' separate
  // POST-per-reply model, so "last call wins" is the correct collapse here.
  let replyPayload = null;
  const reply = (msg) => { replyPayload = ephemeral(msg); };

  await runCommand({
    text,
    ownerKey: slackOwnerKey(teamId, userId),
    getStore,
    reply,
    helpText: () => 'Usage: `/a2ui list` to see your saved readings, `/a2ui show <id>` to post one here, ' +
                     '`/a2ui weather <city>` for a live forecast card.',
    unknownText: () => 'Unknown command. Usage: `/a2ui list`, `/a2ui show <id>`, `/a2ui weather <city>`.',
    // Debug affordance — team_id/user_id aren't secrets, but there's no other
    // easy way to read them off without digging through Slack's UI, and
    // they're exactly what's needed to target a save via /mcp at this same
    // owner_key for testing.
    whoamiText: () => `team_id: \`${teamId}\`\nuser_id: \`${userId}\`\nchannel_id: \`${channelId}\``,
    listLineFor: (r) => `• \`${r.id}\` — ${r.title || '(untitled)'}`,
    renderReading: async (store, { id }) => {
      const result = await renderReadingToSlack(store, { id, channel: channelId });
      reply(result.ok
        ? `Posted "${result.title || result.reading_id}" to this channel.`
        : `Could not post: ${result.reason}`);
    },
    weatherUsageText: () => 'Usage: `/a2ui weather <city>`',
    fetchWeather: fetchWeatherBlocks,
    // Slack confirms explicitly on success (its ephemeral reply is a
    // separate channel from the post) — unlike Teams, which stays silent
    // and lets the card post itself be the confirmation.
    postWeather: async (store, weather) => {
      const result = await postBlocksToSlack(weather.blocks, { channel: channelId, title: `Weather — ${weather.location}` });
      reply(result.ok
        ? `Posted the ${weather.location} forecast to this channel.`
        : `Could not post: ${result.reason}`);
    },
  });

  return replyPayload || ephemeral('');
}
