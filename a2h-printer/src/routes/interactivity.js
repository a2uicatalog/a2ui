// POST /slack/interactivity — public, Slack-signed (verified by server.js's
// shared middleware before this handler runs), ≤3s ack deadline.
import { processInteractivity } from '../lib/slack-interactivity.js';

export async function handleInteractivity(c) {
  const rawBody = c.get('rawBody');
  // processInteractivity resolves fast for response_url-deferred actions
  // (fire-and-forget) and only actually awaits the network round-trip for
  // the modal-open path, where trigger_id validity forces it — see
  // lib/slack-interactivity.js for the split.
  await processInteractivity(rawBody);
  return c.text('', 200);
}
