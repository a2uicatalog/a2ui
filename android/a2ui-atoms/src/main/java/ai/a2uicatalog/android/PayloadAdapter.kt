package ai.a2uicatalog.android

import org.json.JSONArray
import org.json.JSONObject

/**
 * Turns whatever the user loads into the message stream Google's alpha parser accepts.
 *
 * Three gaps between our emitter (renderers/a2ui_v1.py) and androidx.a2ui 1.0.0-alpha01:
 *  1. We stamp "v1.0"; the parser only accepts v0.9 / v0.9.1 and throws on anything else
 *     (its own source carries a TODO to move to v1.0).
 *  2. We put components inside createSurface; v0.9 expects them in a separate
 *     updateComponents message and silently skips unknown fields, so ours would vanish.
 *  3. The engine throws on any component type its catalog doesn't register, so any
 *     type we can't draw is rewritten to a visible placeholder instead of crashing.
 *
 * Also accepts our legacy {"title","theme","blocks":[...]} payload, flat blocks only.
 */
object PayloadAdapter {
    const val ENGINE_VERSION = "v0.9"
    const val UNKNOWN = "UnknownPlaceholder"

    class Result(
        val messages: List<String>,
        val report: List<String>,
        /** Our theme ("light" / "dark" / "terminal"), passed to the bridge's web renderer. */
        val theme: String,
        /** The original text, for whole-surface WebView mode. */
        val original: String,
    )

    fun adapt(input: String, known: Set<String>): Result {
        val report = mutableListOf<String>()
        var theme = "light"
        val trimmed = input.trim()
        val raw: List<JSONObject> = when {
            trimmed.startsWith("[") -> JSONArray(trimmed).let { a -> List(a.length()) { a.getJSONObject(it) } }
            else -> listOf(JSONObject(trimmed))
        }

        val out = mutableListOf<JSONObject>()
        val versions = sortedSetOf<String>()
        for (msg in raw) {
            when {
                msg.has("blocks") -> {
                    report += "Legacy {blocks} payload: wrapped flat blocks in a root Column"
                    theme = msg.optString("theme", theme)
                    out += legacyToMessages(msg)
                }
                msg.has("createSurface") && msg.getJSONObject("createSurface").has("components") -> {
                    val cs = msg.getJSONObject("createSurface")
                    cs.optJSONObject("metadata")?.optJSONObject("extensions")
                        ?.optJSONObject("a2uicatalog_surface")?.optString("theme")
                        ?.takeIf { it.isNotEmpty() }?.let { theme = it }
                    val comps = cs.getJSONArray("components")
                    msg.optString("version").takeIf { it.isNotEmpty() }?.let { versions += it }
                    report += "Split createSurface into createSurface + updateComponents " +
                        "(${comps.length()} components)"
                    out += JSONObject().put("createSurface", JSONObject()
                        .put("surfaceId", cs.getString("surfaceId"))
                        .put("catalogId", cs.getString("catalogId")))
                    out += JSONObject().put("updateComponents", JSONObject()
                        .put("surfaceId", cs.getString("surfaceId"))
                        .put("components", comps))
                }
                else -> out += msg
            }
        }

        val unknown = sortedSetOf<String>()
        for (msg in out) {
            msg.optString("version").takeIf { it.isNotEmpty() }?.let { versions += it }
            msg.put("version", ENGINE_VERSION)
            val comps = msg.optJSONObject("updateComponents")?.optJSONArray("components") ?: continue
            for (i in 0 until comps.length()) {
                val c = comps.getJSONObject(i)
                val type = c.optString("component")
                if (type !in known) {
                    unknown += type
                    val id = c.getString("id")
                    comps.put(i, JSONObject().put("id", id).put("component", UNKNOWN)
                        .put("originalType", type))
                }
            }
        }
        versions.filter { it != ENGINE_VERSION }.takeIf { it.isNotEmpty() }?.let {
            report += "Rewrote version ${it.joinToString()} -> $ENGINE_VERSION"
        }
        if (unknown.isNotEmpty()) report += "Not drawable, shown as placeholders: ${unknown.joinToString()}"
        return Result(out.map { it.toString() }, report, theme, input)
    }

    private fun legacyToMessages(p: JSONObject): List<JSONObject> {
        val sid = "legacy"
        val blocks = p.getJSONArray("blocks")
        val comps = JSONArray()
        val children = JSONArray()
        for (i in 0 until blocks.length()) {
            val b = blocks.getJSONObject(i)
            val c = JSONObject().put("id", "b$i").put("component", b.getString("type"))
            for (k in b.keys()) if (k != "type") c.put(k, b.get(k))
            comps.put(c)
            children.put("b$i")
        }
        comps.put(JSONObject().put("id", "root").put("component", "Column").put("children", children))
        return listOf(
            JSONObject().put("createSurface", JSONObject().put("surfaceId", sid).put("catalogId", CATALOG_ID)),
            JSONObject().put("updateComponents", JSONObject().put("surfaceId", sid).put("components", comps)),
        )
    }
}
