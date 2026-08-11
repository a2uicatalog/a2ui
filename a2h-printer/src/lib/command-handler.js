// src/lib/command-handler.js — platform-agnostic implementation of
// help|whoami|list|show|weather, extracted from what were previously two
// independently-duplicated copies in routes/command.js (Slack) and
// routes/teams.js (Teams). See
// /home/curtis/.claude/plans/zany-petting-cray.md for why this extraction
// happened now.
//
// NOT everything about "list/show/weather" turned out to be identical
// across platforms once diffed side by side — three real divergences,
// preserved here rather than flattened away:
//   1. help/unknown-command TEXT differs (Slack: backtick-wrapped
//      `/a2ui <cmd>` slash-command syntax; Teams: plain quoted "<cmd>", no
//      slash concept) — caller-supplied via helpText()/unknownText().
//   2. `list`'s per-item bullet FORMAT differs (Slack: "• `id` — title";
//      Teams: "- id — title") — caller-supplied via listLineFor(reading).
//   3. `show`/`weather` SUCCESS behavior differs, not just wording: Slack
//      sends an explicit ephemeral confirmation in addition to the channel
//      post (its reply channel is separate from the post); Teams stays
//      silent on success because the card post itself IS the visible
//      confirmation, and only replies on failure. This is real platform
//      behavior, not formatting, so renderReading/postWeather are NOT
//      passed a target to post-then-confirm — they're handed the reply()
//      closure and decide for themselves whether/what to send, per
//      platform. runCommand does not add anything after they resolve.
// Everything else below (subcommand parsing, the "Nothing saved yet."/
// "Storage is unavailable" messages, weather's error-branch wording) was
// verified byte-identical between the two prior copies and is centralized
// here for real, not just superficially.
export async function runCommand({
  text,
  ownerKey,
  getStore,
  reply,           // (msg: string) => void|Promise<void> — may be called more than once, or not at all
  helpText,        // () => string
  unknownText,     // () => string
  whoamiText,      // () => string
  listLineFor,     // (reading) => string
  renderReading,   // (store, {id}) => Promise<any> — owns its own reply()s
  weatherUsageText,// () => string
  fetchWeather,    // (city) => Promise<{error?, blocks?, location?}>
  postWeather,     // (store, {blocks, location}) => Promise<any> — owns its own reply()s
}) {
  const [subRaw, ...rest] = (text || '').split(/\s+/).filter(Boolean);
  const sub = (subRaw || '').toLowerCase();

  if (!sub || sub === 'help') return reply(helpText());
  if (sub === 'whoami') return reply(whoamiText());

  let store;
  try {
    store = getStore(ownerKey);
  } catch (e) {
    // Fail closed (plan decision #3) — a storage misconfiguration is an
    // error state, never silently "you have nothing saved."
    return reply('Storage is unavailable right now — try again shortly.');
  }

  if (sub === 'list') {
    const { readings } = await store.list(null, 10);
    if (!readings.length) return reply('Nothing saved yet.');
    const lines = readings.map(listLineFor);
    return reply(`Your last ${readings.length} saved reading(s):\n${lines.join('\n')}`);
  }

  if (sub === 'show') {
    return renderReading(store, { id: rest[0] });
  }

  if (sub === 'weather') {
    const city = rest.join(' ').trim();
    if (!city) return reply(weatherUsageText());
    const weather = await fetchWeather(city);
    if (weather.error) return reply(`Could not get weather: ${weather.error}`);
    return postWeather(store, weather);
  }

  return reply(unknownText());
}
