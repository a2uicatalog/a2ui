// a2ui-tool.ts — the ChannelTool + system prompt, extracted so BOTH the live
// channel (channel.ts) and any offline routing harness exercise the same
// artifacts. Testing a copy of the prompt would let the test and production
// drift, which is the whole failure class this split exists to prevent.

import { defineChannelTool } from "@copilotkit/channels";
import { z } from "zod";
import { a2uiAtomToCopilotKit, a2uiAtomToImage, TIER1_ATOM_TYPES, type A2uiAtom } from "./a2ui-bridge.ts";
import { fetchWeatherBlocks } from "../src/lib/weather.js";

/** Variant A — the prompt as live-tested on 2026-08-08 (baseline), extended
 * with fetch_weather once render_a2ui_atom-alone was found to have no live
 * data source (a real gap: asked "weather toulouse", the model correctly
 * declined rather than inventing numbers, since nothing supplied real data). */
export const A2UI_PROMPT_BASELINE = `You have a tool called render_a2ui_atom that displays a2uicatalog A2UI \
atoms natively in this chat (as a real Slack chart, field, button, etc). \
When you want to SHOW a2uicatalog content here, call render_a2ui_atom \
directly with the atom's type and props — do NOT call a2uicatalog's own \
render_surface/preview_url/make_surface_url MCP tools for display, they \
return a ui:// resource this chat cannot render. You may still use \
list_catalogs/get_catalog to discover what atom types and data shapes \
exist. render_a2ui_atom renders these atom types as real native Slack blocks: \
${[...TIER1_ATOM_TYPES].join(", ")}. Any OTHER real a2ui atom type is still \
worth calling render_a2ui_atom for — it falls back to rendering a real image, \
which may take a few seconds. If the tool reports it could not display \
something, say so honestly rather than claiming it rendered. For WEATHER \
requests specifically, call fetch_weather(city) instead — it fetches real, \
live data and displays it itself; render_a2ui_atom has no weather data of \
its own, so never guess or invent weather numbers.`;

/** Variant B — short and imperative. Tests the prompt-dilution hypothesis:
 * baseline inlines all 35 atom names, which may bury the actual instruction. */
export const A2UI_PROMPT_SHORT = `To show any a2uicatalog A2UI atom in this chat, call the \
render_a2ui_atom tool. Always call it — never describe an atom in text instead of rendering it, \
and never use render_surface/preview_url/make_surface_url (they return a ui:// resource this \
chat cannot display). Use list_catalogs/get_catalog only to look up atom types and prop shapes.`;

/** Variant C — baseline content, but leads with the imperative instead of
 * burying it after the capability list. Tests instruction ORDER separately
 * from instruction LENGTH. */
export const A2UI_PROMPT_IMPERATIVE_FIRST = `ALWAYS call the render_a2ui_atom tool to display \
a2uicatalog A2UI atoms in this chat. Never answer a "show me an atom" request with text alone. \
Never call render_surface/preview_url/make_surface_url for display — they return a ui:// resource \
this chat cannot render. You may call list_catalogs/get_catalog first to discover atom types and \
prop shapes. render_a2ui_atom renders these types as real native Slack blocks: \
${[...TIER1_ATOM_TYPES].join(", ")}. Any other real a2ui atom type still works — it falls back to \
a rendered image. If the tool reports failure, say so honestly rather than claiming it rendered.`;

/** The live prompt. Swap this constant to change what channel.ts uses. */
export const A2UI_PROMPT = A2UI_PROMPT_BASELINE;

/**
 * Shared Tier1->Tier2 post logic, extracted so render_a2ui_atom AND
 * fetch_weather (below — which already has real, ready-to-render atom data,
 * no need to route back through the model) post identically. Returns a
 * short human-readable status string, never throws.
 */
async function postA2uiAtom(thread: { post: (el: unknown) => Promise<unknown> }, atom: A2uiAtom): Promise<string> {
  const { type: atomType, props = {} } = atom;
  const element = a2uiAtomToCopilotKit(atom);
  if (element) {
    try {
      await thread.post(element);
      return `Displayed the ${atomType} atom.`;
    } catch (e) {
      // Native post can throw at Slack-validation time (e.g. a chart whose
      // series/categories don't match Slack's contract) — NOT the same as
      // "no Tier-1 analogue" (a2uiAtomToCopilotKit returning null), so it
      // needs its own catch and falls back to Tier 2 rather than failing.
      console.error(`Tier 1 post failed for ${atomType}:`, e);
    }
  }
  try {
    const image = await a2uiAtomToImage(atom);
    await thread.post(image);
    return `Displayed the ${atomType} atom as an image.`;
  } catch (e) {
    console.error(`Tier 2 image render failed for ${atomType}:`, e);
    const msg = (e as Error).message;
    // Self-correcting error path. Live 2026-08-08: asked for a sparkline,
    // the model invented the atom type "spark_chart" (the real one is
    // "sparkline"), the renderer correctly rejected it, and the model then
    // told the user the atom "isn't supported" — a wrong and discouraging
    // answer to a request the catalogue can actually satisfy. The model has
    // list_catalogs/get_catalog available but does not reach for them when
    // it *believes* it already knows the name. So an unknown-type error
    // returns an explicit instruction rather than a dead end.
    if (/unknown atom type/i.test(msg)) {
      return (
        `"${atomType}" is not a real a2ui atom type — you guessed the name. ` +
        `Do NOT tell the user it is unsupported. Call get_catalog to look up the ` +
        `exact type (charts live in "a2ui-charts-v1"), then call render_a2ui_atom ` +
        `again with the correct name.`
      );
    }
    return `Could not display "${atomType}": ${msg}`;
  }
}

export const renderA2uiAtomTool = defineChannelTool({
  name: "render_a2ui_atom",
  description:
    "Render an a2uicatalog A2UI atom natively in this chat (as a real Slack " +
    "block — chart, field, button, text, image, or divider). Use this to " +
    "SHOW a2uicatalog content; a2uicatalog's own render/preview MCP tools " +
    "return a resource type this chat cannot display. For live weather, " +
    "use fetch_weather instead — this tool has no data source of its own, " +
    "it only renders props you already have.",
  parameters: z.object({
    atomType: z.string().describe("The a2ui atom type, e.g. chartjs_bar, stat_card, cta_button."),
    props: z
      .record(z.string(), z.unknown())
      .describe("The atom's props, matching a2uicatalog's schema for that atom type."),
  }),
  async handler({ atomType, props }, { thread }) {
    console.log(`render_a2ui_atom called: ${atomType}`, JSON.stringify(props));
    return postA2uiAtom(thread, { type: atomType, props });
  },
});

/**
 * fetch_weather — live weather data as ready-to-render a2uicatalog atoms.
 * render_a2ui_atom alone cannot do this: it only renders props the MODEL
 * already has, and the model has no live weather data source of its own —
 * asking it to invent temperature/forecast numbers would mean the "shown"
 * card is fabricated, not real. This wraps the SAME Open-Meteo call
 * self-hosted mode's `weather` command already uses
 * (../src/lib/weather.js's fetchWeatherBlocks — free, no API key, real geo +
 * forecast data), so both modes report identical live weather from one
 * source. Posts both resulting atoms (current conditions + 3-day outlook)
 * directly via the same Tier1/Tier2 dispatch render_a2ui_atom uses, rather
 * than making the model re-call render_a2ui_atom per atom with data it
 * would have to copy out of this tool's result — fewer round trips, and no
 * chance of the model transcribing a number wrong along the way.
 */
export const fetchWeatherTool = defineChannelTool({
  name: "fetch_weather",
  description:
    "Get LIVE current weather + 3-day outlook for a city and display it here as real " +
    "a2uicatalog weather cards. This is the ONLY source of real weather data available — " +
    "render_a2ui_atom cannot fetch weather itself, so never invent weather numbers to pass " +
    "to render_a2ui_atom; always call this tool instead when asked about weather.",
  parameters: z.object({
    city: z.string().describe("City name, e.g. \"Toulouse\" or \"New York\"."),
  }),
  async handler({ city }, { thread }) {
    console.log(`fetch_weather called: ${city}`);
    const weather = await fetchWeatherBlocks(city);
    if (weather.error) return `Could not get weather for "${city}": ${weather.error}`;
    // fetchWeatherBlocks (like every stored a2uicatalog reading block
    // elsewhere in this codebase — confirmed against
    // ../src/lib/render-to-teams.js:39's `props: b`) returns FLAT blocks:
    // {type, component, ...actualFields} with no nested `props` sub-object.
    // The whole block IS the props, redundant type/component keys and all —
    // wrapping it as {type, props: block} here, NOT passing it straight
    // through, is what render-to-teams.js's own convention requires.
    const results = await Promise.all(
      weather.blocks.map((block: Record<string, unknown>) => postA2uiAtom(thread, { type: block.type as string, props: block })),
    );
    return `Displayed live weather for ${weather.location}. ${results.join(" ")}`;
  },
});
