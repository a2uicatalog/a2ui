#!/usr/bin/env python3
"""a2a_agent_sketch.py — a REAL agent (Gemini, via scripts/vertex_gemini.py)
decides what to draw, not a hardcoded coordinate list like
scripts/a2a_demo_sketch.py. One structured-output Gemini call plans a
stroke sequence for the given subject; each stroke is then sent as its
own real, separate A2A updateComponents call to a2a_counterpart, exactly
the same delivery mechanism a2a_demo_sketch.py already proved -- the
difference is entirely in WHERE the strokes come from.

Usage:
    uvicorn a2a_counterpart.main:app --port 8091 &   (with AGENT_BASE_URL set)
    MAISON_PROJECT=<your-gcp-project> python3 scripts/a2a_agent_sketch.py \\
        --subject "a rocket ship" --url http://localhost:8091
"""
import argparse
import asyncio
import json
import os
import sys
import time
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))

import httpx
from a2a.client import A2ACardResolver, ClientConfig, ClientFactory
from a2a.types import DataPart, Message, Part, Role

import vertex_gemini
from renderers.a2a_extension import A2A_EXTENSION_URI, wrap_messages_for_sdk
from renderers.a2ui_v1 import emit_surface
from renderers.a2ui_v1_updates import update_components

STROKE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "strokes": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "element": {"type": "STRING"},
                    "label": {"type": "STRING"},
                },
                "required": ["element"],
            },
        },
    },
    "required": ["strokes"],
}

SYSTEM_PROMPT = """You are a minimalist line-art SVG artist. Given a subject, \
produce a JSON object with a "strokes" array of 4 to 8 strokes that together \
form a simple, recognizable line drawing of the subject.

Canvas: SVG viewBox "0 0 400 200" (x: 0-400, y: 0-200, origin top-left). Keep \
all coordinates within roughly x: 20-380, y: 10-190, and keep the drawing \
centered and reasonably balanced in the frame.

Each stroke:
  - "element": exactly ONE raw SVG element, e.g. \
'<circle cx="200" cy="80" r="30" fill="#f4d35e"/>' or \
'<path d="M 20 60 L 80 60" stroke="#1f2937" stroke-width="3" fill="none"/>'. \
Allowed tags: circle, ellipse, rect, line, polyline, polygon, path, g (g may \
group several of the others). Allowed attributes: cx, cy, r, rx, ry, x, y, \
width, height, x1, y1, x2, y2, points, d, fill, stroke, stroke-width, \
opacity, fill-opacity, stroke-opacity, stroke-linecap, stroke-linejoin, \
transform. No other tags/attributes -- an element using anything else is \
rejected by the renderer and simply won't appear. NEVER use white, ivory, \
snow, or any near-white fill/stroke color (e.g. #fff, #f8f8f8, ghostwhite) \
on a part that needs to be visible -- the canvas background is white, so a \
white-on-white shape is invisible. If a real object is conventionally white \
or very pale, use its outline in a DARK or saturated color instead.
  - "label": a short phrase (3-6 words) describing what this element depicts, \
e.g. "the lighthouse tower".

Keep adjacent elements' edges touching or overlapping where they should \
visually connect (e.g. a mast's base should meet the hull it stands on, a \
sail's corner should meet the mast) -- do not leave small unintentional gaps \
between parts that belong together.

Order elements from broad/major shapes FIRST to fine details LAST, as if a \
human were sketching progressively -- the strokes will be revealed one at a \
time, in the order you return them, so the ordering matters for how the \
drawing appears to build up.

Output ONLY the JSON object, matching the given schema exactly."""


def _extract_strokes_response(resp: dict) -> list[dict]:
    """Shared by both the initial plan and the critique/revise pass --
    same real bugs fixed in both call sites, not just the first one found:
    (1) Gemini can split one JSON response across MULTIPLE text parts in
    the same candidate (found live) -- concatenate every part, not just
    parts[0]; (2) validate/clean each stroke defensively before it can
    reach a real A2A message. The real safety check (tag/attribute
    allowlist) lives in the renderer (renderers/web_article.py's
    _validate_sketchpad_element / atoms_charts.gs's
    _validateSketchpadElement) -- this only drops elements too malformed
    to be worth sending at all (empty, absurdly long, not a string)."""
    try:
        parts = resp["candidates"][0]["content"]["parts"]
    except (KeyError, IndexError):
        vertex_gemini.first_part(resp)  # raises the real, specific error
        raise
    text = "".join(p.get("text", "") for p in parts)
    if not text.strip():
        reason = resp["candidates"][0].get("finishReason", "unknown")
        raise RuntimeError(f"Gemini returned no text (finishReason: {reason})")
    data = json.loads(text)
    strokes = data.get("strokes") or []
    valid = []
    for s in strokes:
        element = s.get("element")
        if not isinstance(element, str) or not element.strip() or len(element) > 4096:
            print(f"[a2a_agent_sketch] skipping malformed stroke: {s!r}")
            continue
        valid.append({"element": element.strip(), "label": s.get("label") or ""})
    if not valid:
        raise RuntimeError("Gemini returned no usable strokes -- try a different subject/model")
    return valid


def _plan_strokes(subject: str, model: str) -> list[dict]:
    resp = vertex_gemini.call(
        model,
        [{"role": "user", "parts": [{"text": f"Subject to draw: {subject}"}]}],
        system=SYSTEM_PROMPT,
        schema=STROKE_SCHEMA,
        temperature=0.6,
        # 2.5-series models spend real budget on extended-thinking tokens
        # BEFORE any output text (found live: a 2000-token budget was
        # entirely consumed by ~1900 thinking tokens, finishReason
        # MAX_TOKENS, near-zero actual JSON) -- generous headroom needed.
        max_output_tokens=8000,
        timeout=150,
    )
    return _extract_strokes_response(resp)


def render_strokes_to_png(strokes: list[dict], view_box: str = "0 0 400 200") -> bytes:
    """Reuses the REAL renderer (renderers/web_article.py's
    _render_agent_sketchpad -- the same one a2a_counterpart's own
    /render endpoint and the GAS renderer are proven to agree with,
    tests/test_agent_sketchpad.py) rather than reimplementing SVG
    generation here. cairosvg needs an explicit width/height on the root
    <svg> -- the real renderer's own output only carries viewBox + a
    percentage `style="width:100%"` (correct for an HTML page, meaningless
    to a standalone SVG rasterizer) -- found live building this, fixed by
    patching those two attributes onto the extracted root tag rather than
    changing the shared renderer's real HTML-embedding behavior."""
    import re as _re

    from renderers.web_article import _render_agent_sketchpad
    html = _render_agent_sketchpad({"strokes": strokes, "viewBox": view_box})
    m = _re.search(r"<svg[^>]*>.*?</svg>", html, _re.S)
    if not m:
        raise RuntimeError("renderer produced no <svg> -- cannot preview")
    svg = m.group(0)
    # Drop the incomplete draw-in animation (dasharray/dashoffset never
    # resolves in a static rasterizer -- the stroke would render invisible)
    # and stamp real pixel dimensions cairosvg needs.
    svg = _re.sub(r'\s*stroke-dasharray="1000"\s*stroke-dashoffset="1000"', "", svg)
    svg = _re.sub(r"^<svg\s+viewBox=\"([^\"]+)\"[^>]*>",
                  r'<svg viewBox="\1" width="400" height="200" '
                  r'xmlns="http://www.w3.org/2000/svg">', svg, count=1)

    import cairosvg
    return cairosvg.svg2png(bytestring=svg.encode(), output_width=800,
                            background_color="white")


def critique_and_revise(subject: str, strokes: list[dict], model: str) -> list[dict]:
    """The actual answer to "free prompt to drawing" needing to work for
    ANY subject, not just one hand-tuned example: a blind, one-shot
    coordinate plan has no way to know if it drew something recognizable
    (found live: an unprompted "sailboat" came out with a hull that reads
    as a hill, not a boat). Render what was planned via the SAME real
    renderer everything else uses, hand the actual PNG back to Gemini
    (multimodal input) alongside the original strokes, and ask it to
    revise its own coordinates having SEEN the result -- real visual
    self-correction, not a second blind guess."""
    import base64

    png_bytes = render_strokes_to_png(strokes)
    png_b64 = base64.b64encode(png_bytes).decode()

    critique_prompt = f"""Here is the line drawing your strokes produced for \
the subject "{subject}" (rendered at 800px wide from your own {len(strokes)} \
strokes, viewBox "0 0 400 200"). Look at the actual image. If it reads as a \
clear, recognizable "{subject}", you may return the same strokes unchanged. \
If any part is wrong, mis-proportioned, disconnected, or doesn't read as the \
intended subject (e.g. a shape that should curve down instead curves up, a \
part that looks like the wrong object), REVISE the coordinates to fix it. \
You may add, remove, or reorder strokes. Return your best, final version."""

    resp = vertex_gemini.call(
        model,
        [{"role": "user", "parts": [
            {"text": f"Original strokes (JSON): {json.dumps(strokes)}"},
            {"inlineData": {"mimeType": "image/png", "data": png_b64}},
            {"text": critique_prompt},
        ]}],
        system=SYSTEM_PROMPT,
        schema=STROKE_SCHEMA,
        temperature=0.4,
        max_output_tokens=8000,
        timeout=150,
    )
    return _extract_strokes_response(resp)


async def _send(client, context_id, message_id, messages):
    msg = Message(role=Role.user, message_id=message_id, context_id=context_id,
                  parts=[Part(root=DataPart(**wrap_messages_for_sdk(messages)))])
    async for _ in client.send_message(msg, extensions=[A2A_EXTENSION_URI]):
        pass


async def run(url: str, subject: str, model: str, critique_model: str, wait_for_open,
              pace_seconds: float, refine_passes: int) -> str:
    print(f"[a2a_agent_sketch] asking {model} to plan a drawing of: {subject!r}")
    strokes_plan = _plan_strokes(subject, model)
    print(f"[a2a_agent_sketch] got {len(strokes_plan)} strokes")

    for i in range(refine_passes):
        print(f"[a2a_agent_sketch] critique pass {i + 1}/{refine_passes}: "
              f"rendering + showing {critique_model} its own drawing...")
        strokes_plan = critique_and_revise(subject, strokes_plan, critique_model)
        print(f"[a2a_agent_sketch] revised to {len(strokes_plan)} strokes")

    context_id = f"agent-sketch-{uuid.uuid4().hex[:8]}"
    surface_id = "agent-sketch-surface"

    demo_url = f"{url}/demo/{context_id}/{surface_id}"
    render_url = f"{url}/render/{context_id}/{surface_id}"
    print()
    print("LIVE demo (open this first, then come back here):")
    print(f"  {demo_url}")
    print()
    wait_for_open()

    async with httpx.AsyncClient(base_url=url, timeout=30) as hc:
        card = await A2ACardResolver(hc, url).get_agent_card()
        client = ClientFactory(ClientConfig(httpx_client=hc, streaming=False)).create(
            card, extensions=[A2A_EXTENSION_URI])

        create_msg = emit_surface({
            "title": f"Agent Sketchpad — {subject} (drawn by {model})",
            "blocks": [
                {"type": "body", "text": f"The agent is drawing: {subject}",
                 "id": "status_line"},
                {"type": "agent_sketchpad", "id": "sketch",
                 "viewBox": "0 0 400 200", "strokes": []},
            ],
        }, surface_id=surface_id)
        await _send(client, context_id, "agent-sketch-orch", [create_msg])

        strokes = []
        for i, stroke in enumerate(strokes_plan):
            strokes.append(stroke)
            upd = update_components(surface_id, [
                {"id": "sketch", "component": "agent_sketchpad",
                 "viewBox": "0 0 400 200", "strokes": list(strokes)}])
            await _send(client, context_id, f"agent-sketch-stroke-{i}", [upd])
            print(f"[a2a_agent_sketch] drew stroke {i + 1}/{len(strokes_plan)}")
            time.sleep(pace_seconds)

    return render_url


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--subject", required=True, help='What to draw, e.g. "a rocket ship"')
    ap.add_argument("--url", default="http://localhost:8091",
                    help="Base URL of a running a2a_counterpart service")
    ap.add_argument("--model", default="gemini-3.7-flash",
                    help="Needs Vertex AI Express Mode -- export "
                         "MAISON_GEMINI_API_KEY (Secret Manager: "
                         "maison-gintel, project static-hangout-500821-d3) "
                         "before running. gemini-2.5-flash/-pro work under "
                         "plain IAM (MAISON_PROJECT) instead if you don't "
                         "have that key.")
    ap.add_argument("--critique-model", default="gemini-3.7-flash",
                    help="Model for the visual self-critique pass "
                         "(--refine-passes). Found live, 2026-08-24, real "
                         "side-by-side on the same flawed drawing: "
                         "gemini-2.5-flash gave a weak, barely-changed "
                         "revision; gemini-2.5-pro gave a real improvement; "
                         "gemini-3.7-flash (Express Mode) gave the best "
                         "result of the three -- now the default.")
    ap.add_argument("--no-wait", action="store_true")
    ap.add_argument("--pace-seconds", type=float, default=1.5)
    ap.add_argument("--refine-passes", type=int, default=0,
                    help="How many times Gemini sees its own rendered "
                         "drawing and revises it before anything is sent "
                         "over A2A (real visual self-correction via "
                         "cairosvg + multimodal input, not a second blind "
                         "guess). Default 0 (Curtis's own call, "
                         "2026-08-24): doubles real latency for a marginal "
                         "gain now that SYSTEM_PROMPT already forbids the "
                         "worst failure mode (invisible strokes), and it's "
                         "a real extra failure point -- hit a genuine 429 "
                         "rate-limit live. Still available if you want it.")
    args = ap.parse_args()

    def wait_for_open():
        if args.no_wait:
            return
        input("Press Enter once the LIVE demo page above is open in a browser... ")

    render_url = asyncio.run(run(args.url.rstrip("/"), args.subject, args.model,
                                 args.critique_model, wait_for_open, args.pace_seconds,
                                 args.refine_passes))
    print()
    print("Static snapshot (reload to see the finished picture):")
    print(f"  {render_url}")


if __name__ == "__main__":
    main()
