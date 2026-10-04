package ai.a2uicatalog.android

import android.annotation.SuppressLint
import android.content.ActivityNotFoundException
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.util.Log
import android.webkit.ConsoleMessage
import android.webkit.JavascriptInterface
import android.webkit.WebChromeClient
import android.webkit.WebResourceRequest
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.a2ui.compose.runtime.A2uiComponentProperties
import androidx.a2ui.compose.runtime.A2uiComponentScope
import androidx.a2ui.compose.runtime.A2uiProperty
import androidx.a2ui.compose.ui.A2uiCatalog
import androidx.a2ui.compose.ui.A2uiComponent
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.runtime.Composable
import androidx.compose.runtime.compositionLocalOf
import androidx.compose.runtime.key
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import org.json.JSONArray
import org.json.JSONObject

/** Our catalog id: what every surface our emitter produces declares. */
private const val TAG = "A2uiBridge"

const val CATALOG_ID = "https://a2uicatalog.ai/catalogue/a2ui-atoms-v1.json"

/** Google's Basic Catalog id in androidx.a2ui 1.0.0-alpha01 (v0.9). */
const val BASIC_CATALOG_V09 = "https://a2ui.org/specification/v0_9/catalogs/basic/catalog.json"

internal class AtomSpec(val name: String, val pack: String, val fields: List<String>)

internal object Atoms {
    @Volatile private var cached: List<AtomSpec>? = null
    @Volatile private var bundle: String? = null

    fun specs(ctx: Context): List<AtomSpec> = cached ?: run {
        val a = JSONArray(ctx.assets.open("atoms.json").bufferedReader().readText())
        List(a.length()) { i ->
            val o = a.getJSONObject(i)
            val f = o.getJSONArray("fields")
            AtomSpec(o.getString("name"), o.getString("pack"), List(f.length()) { f.getString(it) })
        }.also { cached = it }
    }

    fun rendererBundle(ctx: Context): String = bundle
        ?: ctx.assets.open("renderer-bundle.html").bufferedReader().readText().also { bundle = it }

}

/** The surface theme from our payload metadata, read by every bridged atom. */
val LocalSurfaceTheme = compositionLocalOf { "light" }

/**
 * Registered once per atom name, all sharing this one class. Rebuilds the atom as a
 * legacy block ({"type": name, ...fields}) and hands it to our web renderer.
 */
/** Type names drawn by the bridge, filled by [A2uiAtomicCatalog.catalog]; Columns group them. */
internal object BridgedTypes {
    @Volatile var names: Set<String> = emptySet()
}

/**
 * Every field the agent sent, not just the ones schema.yaml declares. The alpha keeps
 * them in an internal `raw` map; reading it by reflection keeps unknown-to-schema fields
 * from being silently dropped. Null if the alpha's internals move.
 */
@Suppress("UNCHECKED_CAST")
internal fun rawProps(p: A2uiComponentProperties): Map<String, Any?>? = try {
    A2uiComponentProperties::class.java.getDeclaredField("raw")
        .apply { isAccessible = true }.get(p) as? Map<String, Any?>
} catch (e: Exception) {
    null
}

/** A value the A2UI data model must resolve: a path binding or a function call. */
private fun isBinding(v: Any?): Boolean = v is Map<*, *> && ("path" in v || "call" in v)

/**
 * One atom as a renderer block with its data bindings resolved. The web renderer knows
 * nothing of the surface's data model, so a field like `value: {path: "/sales"}` is
 * resolved here through bind(), which also recomposes (and repaints) when the agent
 * updates that path. Literal fields pass through unchanged. Null if raw props are
 * unreadable, so callers can fall back.
 */
@Composable
internal fun A2uiComponentScope.resolvedBlock(type: String, props: A2uiComponentProperties): JSONObject? {
    val raw = rawProps(props) ?: return null
    val block = JSONObject().put("type", type)
    raw.forEach { (k, v) ->
        if (k == "id" || k == "component") return@forEach
        val value = if (isBinding(v)) key(k) { props.bind(remember(k) { A2uiProperty.dynamicValue(k) }) } else v
        block.put(k, JSONObject.wrap(value))
    }
    return block
}

/** One atom as a legacy renderer block: {"type": name, ...fields}. */
internal fun atomBlock(type: String, raw: Map<String, Any?>): JSONObject {
    val block = JSONObject().put("type", type)
    raw.forEach { (k, v) -> if (k != "id" && k != "component") block.put(k, JSONObject.wrap(v)) }
    return block
}

/** A payload painting [blocks] in one renderer WebView. */
internal fun bridgePayload(blocks: List<JSONObject>, theme: String): String =
    JSONObject().put("theme", theme).put("blocks", JSONArray(blocks)).toString()

/**
 * Registered once per atom name, all sharing this one class. Draws a single atom; a
 * Column draws runs of consecutive bridged atoms together instead (see DefaultColumn).
 */
internal class AtomBridgeComponent(private val spec: AtomSpec) : A2uiComponent {
    override val name = spec.name
    override val description = "${spec.name} (${spec.pack}), drawn by the a2uicatalog web renderer"
    // Dynamic, so a field may be a data binding ({path} or {call}) and not only a literal.
    override val properties = spec.fields.map { A2uiProperty.dynamicValue(it) }

    @Composable
    override fun A2uiComponentScope.Content(properties: A2uiComponentProperties, modifier: Modifier) {
        val block = resolvedBlock(spec.name, properties)
            ?: JSONObject().put("type", spec.name).also { b ->
                // Fallback if the alpha's internals move: only the schema's declared fields.
                this@AtomBridgeComponent.properties.forEach { p ->
                    if (p in properties) key(p.key) { b.put(p.key, JSONObject.wrap(properties.bind(p))) }
                }
            }
        RendererWebView(bridgePayload(listOf(block), LocalSurfaceTheme.current), modifier,
            onAction = { dispatchAction(it) })
    }
}

/**
 * A WebView holding our renderer bundle, painted with [payloadJson] (a legacy payload or
 * a v1.0 createSurface envelope; paint() accepts both). Sizes itself to its content.
 *
 * [onAction] receives each agent action an atom raises (a wired tool call or a message for
 * the conversation) as an A2UI action map, `{event: {name, context}}`, the same shape a
 * native Button passes to dispatchAction. Links open in the browser, never in the frame.
 */
@SuppressLint("SetJavaScriptEnabled")
@Composable
fun RendererWebView(
    payloadJson: String,
    modifier: Modifier = Modifier,
    onError: (String) -> Unit = {},
    onAction: (Map<String, Any?>) -> Unit = {},
) {
    val currentOnAction by rememberUpdatedState(onAction)
    // Start tall, then shrink to the reported height. Films autoplay from an IntersectionObserver
    // that fires once on first paint; at 48dp only ~1px of the stage showed, the 25% threshold was
    // missed and the observer never fired again when the WebView grew (seen on a Pixel 7 Pro).
    var heightDp by remember { mutableIntStateOf(400) }
    var painted by remember { mutableStateOf<String?>(null) }
    AndroidView(
        modifier = modifier.fillMaxWidth().height(heightDp.dp),
        factory = { ctx ->
            WebView(ctx).apply {
                settings.javaScriptEnabled = true
                settings.domStorageEnabled = true
                settings.mediaPlaybackRequiresUserGesture = false
                webChromeClient = object : WebChromeClient() {
                    override fun onConsoleMessage(m: ConsoleMessage): Boolean {
                        Log.i(TAG, "console ${m.messageLevel()}: ${m.message()} @${m.lineNumber()}")
                        return true
                    }
                }
                addJavascriptInterface(object {
                    @JavascriptInterface fun onHeight(h: Int) {
                        Log.i(TAG, "height $h")
                        post { if (h > 0) heightDp = h }
                    }
                    @JavascriptInterface fun onError(msg: String) {
                        Log.w(TAG, "paint error: $msg")
                        post { onError(msg) }
                    }
                    @JavascriptInterface fun onAction(json: String) {
                        Log.i(TAG, "action $json")
                        val action = try { actionMap(JSONObject(json)) } catch (e: Exception) {
                            Log.w(TAG, "bad action from renderer: $json", e); return
                        }
                        post { currentOnAction(action) }
                    }
                }, "AndroidHost")
                webViewClient = object : WebViewClient() {
                    // A tapped link would otherwise load the whole site inside this atom's frame.
                    override fun shouldOverrideUrlLoading(view: WebView, request: WebResourceRequest): Boolean {
                        if (!request.isForMainFrame) return false
                        val uri = request.url
                        if (uri.scheme !in setOf("http", "https", "mailto", "tel")) return true
                        try {
                            view.context.startActivity(Intent(Intent.ACTION_VIEW, uri).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
                        } catch (e: ActivityNotFoundException) {
                            Log.w(TAG, "no app to open $uri")
                        }
                        return true
                    }
                    override fun onPageFinished(view: WebView, url: String?) {
                        // Paint once per real load. Android's WebView also calls this for
                        // in-page navigations (hash changes, history.pushState); re-painting
                        // then let an atom that updates its hash re-trigger itself forever
                        // (seen on a Pixel 7 Pro: 150 repaints in 20 s, desktop Chrome: none).
                        val state = view.tag as? BridgeState ?: return
                        if (state.loaded) return
                        state.loaded = true
                        Log.i(TAG, "page loaded, painting")
                        view.evaluateJavascript(paintScript(state.payload), null)
                    }
                }
                tag = BridgeState(payloadJson)
                // Base URL = the live site, so relative fetches (e.g. brick part shapes) resolve.
                loadDataWithBaseURL("https://a2uicatalog.ai/", Atoms.rendererBundle(ctx),
                    "text/html", "utf-8", null)
            }
        },
        update = { wv ->
            if (painted != payloadJson) {
                painted = payloadJson
                val state = wv.tag as? BridgeState
                state?.payload = payloadJson
                if (state?.loaded == true) wv.evaluateJavascript(paintScript(payloadJson), null)
            }
        },
    )
}

/** What a bridge WebView should show, and whether its page has finished its one real load. */
private class BridgeState(var payload: String, var loaded: Boolean = false)

/**
 * Turns the renderer's {name, context} into an A2UI action, {event: {name, context}}, with
 * the context as plain Kotlin maps and lists so dispatchAction can serialise it.
 */
internal fun actionMap(o: JSONObject): Map<String, Any?> {
    val name = o.optString("name").ifEmpty { "action" }
    val context = o.optJSONObject("context")?.let { jsonToKotlin(it) } ?: emptyMap<String, Any?>()
    return mapOf("event" to mapOf("name" to name, "context" to context))
}

private fun jsonToKotlin(v: Any?): Any? = when (v) {
    is JSONObject -> v.keys().asSequence().associateWith { jsonToKotlin(v.opt(it)) }
    is JSONArray -> (0 until v.length()).map { jsonToKotlin(v.opt(it)) }
    JSONObject.NULL -> null
    else -> v
}

// The renderer's own host bridge posts JSON-RPC to window.parent, which in a WebView is the
// page itself, so nothing would answer and a wired button would hang until it timed out.
// This one hands each action to the app (dispatchAction -> the agent) and reports it sent.
private const val ACTION_SHIM = """
window._A2UI_HOST_BRIDGE = {
  callTool: function (name, args) {
    AndroidHost.onAction(JSON.stringify({ name: String(name), context: args || {} }));
    return Promise.resolve({ structuredContent: { ok: true, sent_to_agent: true, tool: String(name) } });
  },
  sendMessage: function (text, role) {
    AndroidHost.onAction(JSON.stringify({ name: 'host:message', context: { text: String(text || ''), role: role || 'user' } }));
    return Promise.resolve({});
  }
};
"""

private fun paintScript(payload: String) = """
(function(){
  $ACTION_SHIM
  try { window._A2UI_PAINT($payload); }
  catch (e) { AndroidHost.onError(String(e && e.stack || e)); }
  // Measure the painted content, not the document: documentElement.scrollHeight is never
  // smaller than the viewport, so it can only grow and would feed back on itself.
  function rep(){
    var r = document.getElementById('a2ui-root') || document.body;
    AndroidHost.onHeight(Math.ceil(r.getBoundingClientRect().bottom + window.scrollY + 8));
  }
  rep(); setTimeout(rep, 300); setTimeout(rep, 1500);
  if (window.ResizeObserver) new ResizeObserver(rep).observe(document.documentElement);
})();
""".trimIndent()
