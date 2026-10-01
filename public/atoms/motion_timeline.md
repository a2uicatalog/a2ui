# Motion Timeline

A stage of child atoms choreographed on ONE clock, the way a product or launch video is: everything on screen is a pure function of time (seek(t)), so it plays, loops, scrubs, and can be frozen on any frame (open the page with #t=3.2). Children are any atoms, placed in percent of a fixed-size stage (so the composition is identical at every width) and addressed by id; tracks animate them by opacity, x/y, scale, rotate, 3D tilt, blur, wipe, and two custom properties the demo kit listens to (p = progress, step = which caption/nav item); a camera track pans, zooms and tilts the world while layer:"hud" children (captions) stay put. Each key is a DESTINATION: {t, x, ease} means arrive at x at time t using ease, like GSAP .to(); before a property's first key it holds that first value, so an element can be hidden until its first key. Ease is a token name from motion_tokens (expo-out, standard, quart-in-out, overshoot, hold...) or four cubic-bezier numbers; with bpm set, keys take beat instead of t so the piece sits on a grid. Style that reads as designed rather than generated: one orchestrated moment per scene, entrances 600 ms or less on expo-out, on-screen moves on standard, the camera on quart-in-out, a shared motion vector between scenes, restraint over noise (no particle bursts, neon glows or bouncy easing on UI). Honours prefers-reduced-motion (holds the poster frame; controls still work).

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| title | string (optional, max 80). Accessible name of the stage. Default "Motion sequence". |
| aspect | "16:9" | "4:3" | "1:1" | "9:16" (optional, default "16:9"). The stage is laid out at 1280x720, 1200x900, 1000x1000 or 720x1280 logical px and scaled to the container. |
| duration | number (optional). Seconds, clamped 2-120. Default 12. |
| bpm | integer (optional). 0-240. When set, keys may use `beat` (t = beat * 60 / bpm) instead of `t`. |
| ease | string | [x1,y1,x2,y2] (optional). Default ease for keys that do not name one. A token from motion_tokens (not "hold"). Default "standard". |
| loop | bool (optional). Default true. |
| autoplay | bool (optional). Plays when scrolled into view, pauses when it leaves. Default true. Off, or under prefers-reduced-motion, it shows the poster frame. |
| controls | bool (optional). Play/pause button, scrubber and clock. Default true. |
| poster | number (optional). Seconds; the frame shown when not autoplaying. Default 60% of duration. |
| theme | "dark" | "light"  (optional, default "dark"). Stage background and control colours. |
| accent | "#rrggbb" (optional). Glow and control accent. Default "#38bdf8". |
| background | "#rrggbb" (optional). Stage background override. |
| backdrop | "glow" | "grid" | "flat" (optional, default "glow") |
| blocks | array (max 24) of any atom blocks. Each may also carry id (^[a-z][a-z0-9_-]{0,31}$, makes it addressable by a track), place {x, y, w, h, z, origin} (x/y/w/h in percent of the stage; z 0-99; origin "c"|"tl"|"t"|"b"|"l"|"r" is the transform origin), and layer "world" (default, moves with the camera) or "hud" (stays on screen). |
| tracks | array (max 40) of {target: id, keys: [...]} (max 48 keys each). A key is {t | beat, ease?, x?, y?, opacity?, scale?, rotate?, rx?, ry?, blur?, clip?, p?, step?}. x,y are the element's top-left in percent of the stage (for an element nested in another, an offset from its natural place); opacity 0-1; scale 0-6; rotate, rx, ry in degrees (tilt -80..80); blur 0-40 px; clip 0-1 is a left-to-right wipe; p 0-1 drives a demo atom's progress (chart draw, bar growth, toggles, fills, click ripple, orb level) and recounts its numbers; step is a float that crossfades captions and selects the active nav item. ease on a key is the ease of the segment ARRIVING at that key: a token name, "hold" (jump at the key), or four numbers. |
| scenes | array (max 12) of {layer: id, t | beat, transition?}, optional. STITCHES scenes together: each layer (usually a motion_layer) is hidden until its start and hands over to the next scene instead of cutting. Within `overlap` seconds of the next scene's start the old one leaves while the new one arrives. transition is one of cut, dissolve, push, zoom-through, blur, rise, whip, wipe and applies to the scene it names (the hand-over INTO it); without one the timeline's `stitch` is used. Your own tracks on the same layer are applied after these and win, so a scene can still do its own entrance. |
| stitch | "cut" | "dissolve" | "push" | "zoom-through" | "blur" | "rise" | "whip" | "wipe" (optional, default "dissolve"). whip is a fast push with heavy motion blur; wipe reveals the new scene left to right over the old one. The hand-over used by scenes that do not name one. Pick one per film: a shared motion vector between scenes is what reads as designed. |
| overlap | number (optional). Seconds a hand-over takes, 0-3. Default 0.6. Ignored by cut. |
| camera | {keys: [{t | beat, ease?, x?, y?, zoom?, rx?, ry?, rz?}]} (max 48 keys), optional. x,y are the focus point in percent of the stage (default 50,50); zoom 0.25-6 (default 1); rx, ry, rz tilt in degrees. Moves only layer:"world" children. |

## Example payload

```json
{
  "type": "motion_timeline",
  "tracks": 1
}
```

Live page: https://a2uicatalog.ai/atoms/motion_timeline/
Full field contract: https://a2uicatalog.ai/spec.json
