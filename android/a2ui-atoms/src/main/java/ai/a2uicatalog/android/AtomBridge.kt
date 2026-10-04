package ai.a2uicatalog.android

import android.annotation.SuppressLint
import android.content.Context
import android.util.Log
import android.webkit.ConsoleMessage
import android.webkit.JavascriptInterface
import android.webkit.WebChromeClient
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
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import org.json.JSONArray
import org.json.JSONObject

/** Our catalogue id: what every surface our emitter produces declares. */
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
internal class AtomBridgeComponent(private val spec: AtomSpec) : A2uiComponent {
    override val name = spec.name
    override val description = "${spec.name} (${spec.pack}), drawn by the a2uicatalog web renderer"
    override val properties = spec.fields.map { A2uiProperty.any(it) }

    @Composable
    override fun A2uiComponentScope.Content(properties: A2uiComponentProperties, modifier: Modifier) {
        val block = JSONObject().put("type", spec.name)
        rawProps(properties)?.forEach { (k, v) ->
            if (k != "id" && k != "component") block.put(k, JSONObject.wrap(v))
        } ?: this@AtomBridgeComponent.properties.forEach { p ->
            // Fallback if the alpha's internals move: only the schema's declared fields.
            if (p in properties) block.put(p.key, JSONObject.wrap(properties[p]))
        }
        val payload = JSONObject().put("theme", LocalSurfaceTheme.current)
            .put("blocks", JSONArray().put(block))
        RendererWebView(payload.toString(), modifier)
    }

    /**
     * Every field the agent sent, not just the ones schema.yaml declares. The alpha keeps
     * them in an internal `raw` map; reading it by reflection keeps unknown-to-schema
     * fields from being silently dropped.
     */
    @Suppress("UNCHECKED_CAST")
    private fun rawProps(p: A2uiComponentProperties): Map<String, Any?>? = try {
        A2uiComponentProperties::class.java.getDeclaredField("raw")
            .apply { isAccessible = true }.get(p) as? Map<String, Any?>
    } catch (e: Exception) {
        null
    }
}

/**
 * A WebView holding our renderer bundle, painted with [payloadJson] (a legacy payload or
 * a v1.0 createSurface envelope; paint() accepts both). Sizes itself to its content.
 */
@SuppressLint("SetJavaScriptEnabled")
@Composable
fun RendererWebView(payloadJson: String, modifier: Modifier = Modifier, onError: (String) -> Unit = {}) {
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
                }, "AndroidHost")
                webViewClient = object : WebViewClient() {
                    override fun onPageFinished(view: WebView, url: String?) {
                        Log.i(TAG, "page loaded, painting")
                        (view.tag as? String)?.let { view.evaluateJavascript(paintScript(it), null) }
                    }
                }
                tag = payloadJson
                // Base URL = the live site, so relative fetches (e.g. brick part shapes) resolve.
                loadDataWithBaseURL("https://a2uicatalog.ai/", Atoms.rendererBundle(ctx),
                    "text/html", "utf-8", null)
            }
        },
        update = { wv ->
            if (painted != payloadJson) {
                painted = payloadJson
                wv.tag = payloadJson
                if (wv.progress == 100) wv.evaluateJavascript(paintScript(payloadJson), null)
            }
        },
    )
}

private fun paintScript(payload: String) = """
(function(){
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
