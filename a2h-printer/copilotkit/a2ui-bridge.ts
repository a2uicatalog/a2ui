// a2ui-bridge.ts — Tier 1 of the CopilotKit <-> a2uicatalog bridge.
//
// Maps a2uicatalog A2UI atoms onto CopilotKit's Slack rendering, for the
// subset of atoms (a2ui-atoms-v1 + a2ui-charts-v1) that have a genuinely
// native analogue. Everything else (structurally complex atoms — hub, tabs,
// tree_view, diagrams — and specialized chart types beyond the three
// chartjs_* atoms) is Tier 2, the image-fallback path, a2uicatalog's actual
// differentiated value over what CopilotKit already does natively.
//
// TWICE CORRECTED 2026-08-08, worth recording so the mistake isn't repeated:
// (1) First pass treated the *portable* `<Chart>` (@copilotkit/channels-ui)
// as native, based on finding data-visualization.js's validator without
// checking whether anything calls it. Live Slack test: nothing rendered.
// (2) Checked the real IR->Block Kit dispatcher (dist/render/block-kit.js,
// a subdirectory the first grep pass missed) — its switch statement has no
// "chart" case at all, confirming the portable Chart primitive genuinely
// doesn't render. Concluded CopilotKit had no working chart support.
// WRONG — there's a THIRD API surface: `Slack.Block.DataVisualization`,
// Slack-specific native JSX from @copilotkit/channels-slack directly (NOT
// the portable channels-ui set), documented under "Native Slack JSX" in
// that package's own README and implementing Slack's real chart contract
// exactly. Charts aren't in the portable set by design — not every
// platform Channels targets has a native chart concept, so CopilotKit
// keeps it as a Slack-specific escape hatch rather than forcing a lossy
// abstraction. `<Table>`, unlike Chart, genuinely IS in both the portable
// primitive set AND the real dispatcher (confirmed in block-kit.js) — a
// real Slack native `table` block, `columns` + `Row`/`Cell` children.

import { Field, Fields, Button, Actions, Markdown, Image, Divider, Section, Table, Row, Cell } from "@copilotkit/channels-ui";
import { Slack } from "@copilotkit/channels-slack";
import { signRenderUrl } from "../src/lib/crypto-utils.js";

export interface A2uiAtom {
  type: string;
  props?: Record<string, unknown>;
}

/** Chart family — a2ui-charts-v1's three chartjs_* atoms -> Slack's real native chart. */
const CHART_TYPE_MAP: Record<string, "bar" | "line" | "pie"> = {
  chartjs_bar: "bar",
  chartjs_line: "line",
  chartjs_pie: "pie",
};

/** Normalizes a2ui's own `series`/`segments` convention AND Chart.js's
 * native `labels`/`datasets` shape (live-tested finding, 2026-08-08: an
 * agent asked to fill a `chartjs_bar` atom reasonably reached for Chart.js's
 * own config format — {labels, datasets:[{label, data}]} — not
 * a2uicatalog's `series` convention. Both are real inputs to expect. */
function normalizeSeries(props: Record<string, unknown>): { name: string; data: { label: string; value: number }[] }[] {
  const series = props.series as { name: string; data: { label: string; value: number }[] }[] | undefined;
  if (Array.isArray(series) && series.length > 0) return series;
  const labels = props.labels as string[] | undefined;
  const datasets = props.datasets as { label?: string; data: number[] }[] | undefined;
  if (Array.isArray(labels) && Array.isArray(datasets)) {
    return datasets.map((ds, i) => ({
      name: ds.label ?? `Series ${i + 1}`,
      data: labels.map((label, j) => ({ label, value: ds.data[j] })),
    }));
  }
  return [];
}

/** a2uicatalog chart props -> Slack.Block.DataVisualization's exact contract
 * (SlackDataVisualizationProps: pie -> {segments}, bar/line/area ->
 * {series, axis_config: {categories}} — categories is REQUIRED and must
 * match every series point's label exactly, per Slack's own validation). */
function chartElement(chartType: "bar" | "line" | "pie", props: Record<string, unknown>) {
  const title = String(props.title ?? "");
  if (chartType === "pie") {
    const segments = (props.segments ?? []) as { label: string; value: number }[];
    return Slack.Block.DataVisualization({ title, chart: { type: "pie", segments } });
  }
  const series = normalizeSeries(props);
  const categories = [...new Set(series.flatMap((s) => s.data.map((d) => d.label)))];
  return Slack.Block.DataVisualization({
    title,
    chart: { type: chartType, series, axis_config: { categories } },
  });
}

/** Table-shaped atoms -> CopilotKit's Table/Row/Cell (confirmed native, see header comment). */
const TABLE_ATOMS = new Set(["table", "data_table_sortable"]);

/** a2uicatalog's table-shaped props -> CopilotKit Table children. Tolerant of
 * a couple of plausible shapes (rows of objects keyed by column, or rows of
 * plain arrays) since the exact a2uicatalog `table` schema wasn't pulled
 * from the live catalog before writing this — verify against a real
 * response and tighten if it doesn't match. */
function tableElement(props: Record<string, unknown>) {
  const headers = (props.headers ?? props.columns) as (string | { header: string })[] | undefined;
  const columns = Array.isArray(headers)
    ? headers.map((h) => ({ header: typeof h === "string" ? h : h.header }))
    : undefined;
  const rows = (props.rows ?? []) as unknown[];
  const rowElements = rows.map((row) => {
    const cells = Array.isArray(row) ? row : Object.values(row as Record<string, unknown>);
    return Row({ children: cells.map((c) => Cell({ children: String(c) })) });
  });
  return Table({ columns, children: rowElements });
}

/** Text-family atoms with no styled analogue in CopilotKit's primitive set -> plain Markdown. */
const MARKDOWN_ATOMS = new Set([
  "body", "paragraph", "text_block", "quote", "blockquote", "code", "code_block",
  "inline_code", "callout", "alert_banner", "inline_alert", "text_callout",
  "bullet_list", "numbered_list", "steps", "markdown_block",
]);

const HEADING_ATOMS = new Set(["heading", "subheading", "page_header"]);
const BUTTON_ATOMS = new Set(["cta_button", "link_button", "back_button"]);
const DIVIDER_ATOMS = new Set(["divider", "section_break"]);
const IMAGE_ATOMS = new Set(["image", "image_with_caption"]);
/** label+value shaped atoms -> Field/Fields, the closest CopilotKit primitive. */
const FIELD_ATOMS = new Set(["key_value", "metric_row", "stat_card", "donut_stat"]);

function textOf(props: Record<string, unknown>): string {
  return String(props.text ?? props.body ?? props.content ?? props.value ?? "");
}

/**
 * Map one a2uicatalog atom to a CopilotKit channels-ui JSX element, or
 * `null` if it has no Tier-1 (native) analogue — caller should fall back to
 * Tier 2 (image render) for a `null` result.
 */
export function a2uiAtomToCopilotKit(atom: A2uiAtom) {
  const { type, props = {} } = atom;

  const chartType = CHART_TYPE_MAP[type];
  if (chartType) {
    return chartElement(chartType, props);
  }

  if (TABLE_ATOMS.has(type)) {
    return tableElement(props);
  }

  if (FIELD_ATOMS.has(type)) {
    const label = String(props.label ?? props.title ?? "");
    const value = String(props.value ?? "");
    return Field({ label, children: value });
  }

  if (BUTTON_ATOMS.has(type)) {
    return Actions({
      children: Button({
        children: String(props.label ?? props.text ?? "Open"),
        url: props.url as string | undefined,
      }),
    });
  }

  if (IMAGE_ATOMS.has(type)) {
    return Image({ url: String(props.url ?? props.src ?? ""), alt: props.alt as string | undefined });
  }

  if (DIVIDER_ATOMS.has(type)) {
    return Divider({});
  }

  if (HEADING_ATOMS.has(type)) {
    return Section({ children: Markdown({ children: `**${textOf(props)}**` }) });
  }

  if (MARKDOWN_ATOMS.has(type)) {
    return Markdown({ children: textOf(props) });
  }

  // No Tier-1 analogue (table, and everything structurally complex or
  // chart-specialized beyond the three chartjs_* types) — Tier 2's job.
  return null;
}

export const TIER1_ATOM_TYPES = new Set([
  ...Object.keys(CHART_TYPE_MAP),
  ...TABLE_ATOMS,
  ...FIELD_ATOMS,
  ...BUTTON_ATOMS,
  ...IMAGE_ATOMS,
  ...DIVIDER_ATOMS,
  ...HEADING_ATOMS,
  ...MARKDOWN_ATOMS,
]);

// ---------------------------------------------------------------------------
// Tier 2 — image fallback via a2ui-renderer-public's signed /render.png
// (a2ui-catalogue/cloud-run-renderer/server.py). For atoms with no Tier-1
// analogue: the ~400+ of 532 atoms with genuinely no CopilotKit primitive
// equivalent (sparkline, gauge_sla, sankey_flow, heatmap, table, and every
// structurally complex atom) — this IS a2uicatalog's actual differentiated
// value over what CopilotKit does natively on its own.
//
// Signing delegates to ../src/lib/crypto-utils.js's signRenderUrl — the ONE
// shared implementation this repo's self-hosted mode already uses for
// Slack/Chat, rather than a second local reimplementation (the original
// prototype had its own Node-native gzipSync/createHmac copy here, verified
// byte-compatible but independently maintained; now there is exactly one).
// theme:'light' is passed explicitly — CopilotKit-connected chat surfaces
// (Slack, Telegram, Teams) are overwhelmingly light-background, and without
// this every Tier-2 image rendered on the renderer's dark default regardless
// of host (observed directly on Teams; the exact fix already proven for this
// repo's own Teams self-host path — see ../src/lib/teams-blocks.js).
const RENDERER_URL = process.env.A2UI_RENDERER_URL ?? "https://a2ui-renderer-public-ggbfj7axza-uc.a.run.app";
const RENDER_SIGNING_KEY = process.env.RENDER_SIGNING_KEY;

/**
 * Tier 2 fallback: renders an a2uicatalog atom with no Tier-1 analogue to a
 * real image via a2ui-renderer-public, returns a CopilotKit <Image> element.
 */
export async function a2uiAtomToImage(atom: A2uiAtom) {
  if (!RENDER_SIGNING_KEY) {
    throw new Error("RENDER_SIGNING_KEY not set — Tier 2 image fallback unavailable");
  }
  const url = await signRenderUrl(atom.type, atom.props ?? {}, {
    signingKey: RENDER_SIGNING_KEY,
    baseUrl: RENDERER_URL,
    theme: "light",
  });
  return Image({ url, alt: atom.type });
}
