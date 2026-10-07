#!/usr/bin/env python3
"""Builds README.md: the article analyser's architecture tour, with every code excerpt cut from the real source files
in this repo (so an excerpt cannot drift from the code). Excerpts are found by a start pattern plus a line count.

    python3 android/article-analyser/tools/build_readme.py
"""
import pathlib
import re

HERE = pathlib.Path(__file__).resolve().parent
APP = HERE.parent
ROOT = APP.parents[1]
KA = APP / "app/src/main/java/ai/a2uicatalog/analyser/"
AT = ROOT / "android/a2ui-atoms/src/main/java/ai/a2uicatalog/android/"
RA = APP / "server/read-article.js"


def cut(path, start, n):
    lines = pathlib.Path(path).read_text().split("\n")
    i = next(k for k, l in enumerate(lines) if re.search(start, l))
    return "\n".join(lines[i:i + n])


def rel(p):
    return str(pathlib.Path(p).resolve().relative_to(ROOT))


S = []


def add(id, title, path, lang, why, code):
    S.append(dict(id=id, title=title, path=rel(path), lang=lang, why=why, code=code.rstrip()))


add("share", "The share sheet is the front door", KA / "ShareActivity.kt", "kotlin",
    "Any shared link lands in the app, with a lens picker (explain, apply, challenge, situate) and an optional concern. "
    "The sheet only queues the work and closes, so it takes a second even with no signal. The manifest entry "
    "(`app/src/main/AndroidManifest.xml`) is what puts the app in the share sheet.",
    cut(KA / "ShareActivity.kt", r"val shared = intent", 9) + "\n        …\n\n" + cut(KA / "ShareActivity.kt", r"val r = Store.add", 2))
add("fetch", "The phone reads the page itself", KA / "Work.kt", "kotlin",
    "The article is fetched from the phone's own network, so pages the reader is signed into work. If the page is too thin "
    "to quote from, the phone sends only the URL and the server fetches it instead.",
    cut(KA / "Work.kt", r"^object Article", 13))
add("queue", "A queued job that survives the app closing", KA / "Work.kt", "kotlin",
    "WorkManager runs the read once there is a network and retries with backoff. One case is handled on purpose: if the "
    "phone times out, the server is still reading and will save the reading, so the worker marks it for the next sync "
    "instead of retrying and reading the article twice.",
    cut(KA / "Work.kt", r"^class ReadWorker", 12) + "\n        …\n" + cut(KA / "Work.kt", r"catch \(e: SocketTimeoutException\)", 5)
    + "\n        …\n\n" + cut(KA / "Work.kt", r"fun enqueue", 8))
add("mcp", "The phone is the MCP host", KA / "Mcp.kt", "kotlin",
    "This is the part Claude or Gemini Enterprise plays in an MCP App, moved onto the phone. There is no model on this "
    "side: a plain JSON-RPC `tools/call` with an OAuth bearer token. A tool refusal is a `ToolError`, which retrying "
    "will not fix. Sign-in is a public PKCE client in `Auth.kt`.",
    cut(KA / "Mcp.kt", r"suspend fun call\(ctx", 6) + "\n            …\n" + cut(KA / "Mcp.kt", r"if \(code == 401\)", 11)
    + "\n            …\n\n" + cut(KA / "Mcp.kt", r"suspend fun readArticle", 6))
add("tool", "read_article: a closed tool list and a daily cap", RA, "javascript",
    "The server runs the reading loop with Gemini. The model gets only the tools this call needs: with text from the "
    "phone it may only stamp a reading, so it cannot fetch anything else. A name outside the list gets \"unknown tool\". "
    "A per-reader daily cap sits on top of the account-wide budget, and the loop runs under `waitUntil` so a phone "
    "dropping signal still gets its reading on the next sync.",
    cut(RA, r"^export function toolsFor", 3) + "\n\n" + cut(RA, r"const allowed = new Set", 1) + "\n    …\n"
    + cut(RA, r"if \(!allowed\.has\(name\)\)", 3) + "\n    …\n\n" + cut(RA, r"^export async function takeQuota", 8)
    + "\n}\n\n" + cut(RA, r"const ctx = env\.__CTX__", 2))
add("prompt", "The prompt: the whole system instruction", RA, "javascript",
    "This is the entire system instruction the model receives. Everything the product promises about a reading is in it: "
    "the article text is data and not instructions, quotations must be verbatim, and the model may only quote the text it "
    "was given. The runbook's own contract (what a reading must contain) is returned by the first `emit_runbook_surface` "
    "call, so it reaches the model as a tool result and not as part of this prompt. That contract is public: "
    "[`runbooks/article_playbook.yaml`](../../runbooks/article_playbook.yaml).",
    cut(RA, r"^const SYSTEM_INSTRUCTION", 14) + "\n\n" + cut(RA, r"^export function buildInstruction", 10) + "\n  …")
add("store", "An offline library that reconciles with the server", KA / "Work.kt", "kotlin",
    "Each reading is kept on the phone as a small file plus its payload. The server's store stays the source of truth: sync "
    "collects readings the phone timed out on, adds readings made in Claude or the web app, and drops local copies deleted "
    "elsewhere. Deletions only run when the list came back whole.",
    cut(KA / "Work.kt", r"^object Sync", 3) + "\n        …\n" + cut(KA / "Work.kt", r"if \(remote\.size < 100\)", 5)
    + "\n        …\n\n" + cut(KA / "Mcp.kt", r"fun decodePayload", 4))
add("web", "The concept ladder on the web: the reference renderer", ROOT / "renderers/web_article.py", "python",
    "The reading is a concept ladder: a hook, a mental model, then rungs that go one level deeper each. The web renderer is "
    "the reference implementation. Every colour is a palette token with a default, so a payload can restyle the whole ladder.",
    cut(ROOT / "renderers/web_article.py", r"^def _render_concept_rung", 14) + "\n        …")
add("native", "The same atom drawn natively in Compose", AT / "ConceptComponents.kt", "kotlin",
    "`concept_ladder` and `concept_rung` draw in Compose with no WebView, using the same 14 palette token names as the web "
    "version. The component declares no typed properties on purpose: the alpha renderer rejected the whole component when "
    "the ladder's object and list fields were declared as dynamic values, so every field is read from the raw payload instead.",
    cut(AT / "ConceptComponents.kt", r"^private val LIGHT", 6) + "\n    …\n\n" + cut(AT / "ConceptComponents.kt", r"^object NativeConceptLadder", 17) + "\n        …")
add("rungs", "Rungs are child references, resolved through the engine", AT / "ConceptComponents.kt", "kotlin",
    "In A2UI v1.0 a ladder's rungs are component ids, like a Column's children. The native ladder resolves each one through "
    "the renderer's state, and also accepts inline rung objects.",
    cut(AT / "ConceptComponents.kt", r"rungs\.forEachIndexed", 17) + "\n            }\n            …")
add("catalog", "Native atoms beside Google's Material 3 components", AT / "A2uiAtomicCatalog.kt", "kotlin",
    "The Basic Catalog (the root Column, text, buttons) draws with Google's own Material 3 implementation. Atoms ported to "
    "Compose draw natively; every other atom goes through one WebView bridge running the same web renderer. Native wins over "
    "the bridge by name, so porting an atom means adding it to the list.",
    cut(AT / "A2uiAtomicCatalog.kt", r"fun catalog\(context: Context, basicComponents: List<A2uiComponent>, nativeAtoms", 7)
    + "\n    }\n\n" + cut(AT / "A2uiAtomicCatalog.kt", r"fun materialBasicComponents", 5))
add("render", "Drawing a stored reading, with a fallback so it never goes blank", KA / "MainActivity.kt", "kotlin",
    "The stored payload (A2UI v1.0) is converted to the v0.9 the alpha engine accepts by `adapt()`, then goes through Google's `androidx.a2ui` engine with the catalog. If the engine cannot take a payload, "
    "the catalog's bundled web renderer paints it instead. The app's own colours come from one Material colour scheme, so "
    "Google's components pick them up without any change to the catalog.",
    cut(KA / "MainActivity.kt", r"private fun NativeReading", 12) + "\n    …\n\n" + cut(KA / "Brand.kt", r"^private val scheme", 8)
    + "\n    …\n)\n\n@Composable\n" + cut(KA / "Brand.kt", r"^fun BrandTheme", 1))

STEPS = [("On the phone", [("share", "Share sheet"), ("fetch", "Fetch the page"), ("queue", "Queue"), ("mcp", "MCP call")]),
         ("On the server", [("tool", "`read_article`"), ("prompt", "The prompt")]),
         ("Back on the phone", [("store", "Offline library"), ("web", "Concept ladder on the web"), ("native", "Native ladder"),
                                ("catalog", "Material 3 beside native atoms"), ("render", "Draw it, with a fallback")])]

out = ["# Article analyser (Android)", "",
       "**Share a link, get a reading that works offline.** The app takes an article from the Android share sheet, a "
       "server-side model reads it into a *concept ladder*, and the phone draws that ladder natively and keeps it for offline "
       "use. The phone plays the part Claude or Gemini Enterprise plays in an MCP App.", "",
       "![Sharing an article from the browser to the article analyser on a Pixel 7 Pro: the share sheet asks for a lens "
       "(Explain, Apply, Challenge or Situate) and an optional note, then Read it](docs/share-sheet.jpg)", "",
       "![The article analyser's architecture: share sheet, fetch and queue, read_article, Gemini, store, offline library, "
       "native reader](docs/architecture.png)", "",
       "[`docs/architecture-film.html`](docs/architecture-film.html) is the same diagram as a 24-second animation, drawn with the "
       "catalog's own `motion_arch` atom. Download it and open it in a browser.", "",
       "The reading travels as an A2UI payload (gzip then base64url, the same form as a `?p=` link), so the phone, Claude and "
       "the web player all open the same document. Readings are stamped A2UI v1.0, but Google's `androidx.a2ui` alpha only accepts v0.9 "
       "and v0.9.1, so the app converts each reading with `A2uiAtomicCatalog.adapt()` before drawing it.", "", "## The path", ""]
n = 0
for lane, items in STEPS:
    out.append(f"**{lane}**")
    out.append("")
    for sid, label in items:
        n += 1
        out.append(f"{n}. [{label}](#{sid})")
    out.append("")
out += ["## The code, in pipeline order", "",
        "Excerpts are cut from the real files and trimmed for reading, with `…` marking cuts.", ""]
for s in S:
    out += [f'<a id="{s["id"]}"></a>', f'### {s["title"]}', "", s["why"], "", f'`{s["path"]}`', "",
            f'```{s["lang"]}', s["code"], "```", ""]
out += ["## What is in this folder", "",
        "| Path | What it is |", "|---|---|",
        "| `app/` | The Android app (Kotlin, Jetpack Compose, WorkManager, AppAuth) |",
        "| `server/read-article.js` | The server side: the `read_article` tool and its prompt. A reference copy. It imports the "
        "reader's durable store and is handed `emit_runbook_surface` and `save_reading` by the Worker that hosts it, so it does "
        "not run on its own |",
        "| `docs/` | The architecture diagram and the animated film |",
        "| `tools/` | The scripts that regenerate the film and this README |", "",
        "## Configure and build", "",
        "The app talks to an MCP server you run, so the server details are build properties with placeholder defaults. Put your "
        "own in `~/.gradle/gradle.properties` (or pass `-P`), not in the repo:", "",
        "```properties",
        "analyser.mcpUrl=https://your-server.example/mcp",
        "analyser.authUrl=https://your-server.example/oauth/authorize",
        "analyser.tokenUrl=https://your-server.example/oauth/token",
        "analyser.clientId=your-client-id",
        "analyser.redirectScheme=com.example.analyser   # the custom scheme your OAuth client registered",
        "```", "",
        "The app builds against the atoms library one directory up (`android/a2ui-atoms`) as a Gradle composite build, so it "
        "always uses that source.", "",
        "```bash", "cd android/article-analyser", "./gradlew :app:assembleDebug", "```", "",
        "## What your server needs to provide", "",
        "`server/read-article.js` shows the interesting half. To point the app at your own server, it needs:", "",
        "- **Sign-in:** OAuth authorization code with PKCE (S256) for a public client with no secret, redirecting to "
        "`<scheme>:/oauth2redirect`. Access tokens are refreshed with a refresh token.",
        "- **An MCP endpoint** (JSON-RPC over HTTP, `tools/call`, bearer token) with three tools:",
        "  - `read_article` takes `{url, text?, source_title?, lens?, concerns?}` and returns "
        "`structuredContent` of `{payload, reading_id, analysed_by, retrieval}`, where `payload` is an A2UI surface containing a "
        "`concept_ladder`. It can take 20 to 60 seconds.",
        "  - `list_readings` takes `{runbook, limit}` and returns `{readings: [{id, source_url, title, lens, payload_p, "
        "stamped_at}]}`, where `payload_p` is the payload as gzip then base64url.",
        "  - `delete_reading` takes `{ids}`.",
        "- **A durable store per signed-in reader,** so a reading made in one place shows up in the others.", "",
        "## Regenerate", "",
        "```bash", "python3 android/article-analyser/tools/build_film.py", "python3 android/article-analyser/tools/build_readme.py", "```", ""]
(APP / "README.md").write_text("\n".join(out))
print("wrote", rel(APP / "README.md"), len("\n".join(out)), "chars")
