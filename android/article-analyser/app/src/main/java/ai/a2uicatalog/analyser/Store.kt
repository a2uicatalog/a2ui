package ai.a2uicatalog.analyser

import android.content.Context
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import org.json.JSONObject
import java.io.File
import java.util.UUID

enum class Status { QUEUED, READING, READY, FAILED, SIGN_IN, CHECKING }

/** One shared link and, once read, its reading. The payload (the A2UI surface JSON) is kept in its own file. */
data class Reading(
    val id: String,
    val url: String,
    val title: String,
    val lens: String = "explain",
    val concerns: String = "",
    val status: Status = Status.QUEUED,
    val error: String = "",
    val remoteId: String = "",
    val analysedBy: String = "",
    val retrieval: String = "",
    val createdAt: Long = System.currentTimeMillis(),
) {
    val host: String get() = runCatching { java.net.URI(url).host.removePrefix("www.") }.getOrDefault(url)

    fun toJson(): JSONObject = JSONObject().put("id", id).put("url", url).put("title", title).put("lens", lens)
        .put("concerns", concerns).put("status", status.name).put("error", error).put("remoteId", remoteId)
        .put("analysedBy", analysedBy).put("retrieval", retrieval).put("createdAt", createdAt)

    companion object {
        fun fromJson(j: JSONObject) = Reading(
            id = j.getString("id"), url = j.getString("url"), title = j.optString("title"),
            lens = j.optString("lens", "").takeUnless { j.isNull("lens") || it == "null" }.orEmpty(), concerns = j.optString("concerns"),
            status = runCatching { Status.valueOf(j.optString("status")) }.getOrDefault(Status.QUEUED),
            error = j.optString("error"), remoteId = j.optString("remoteId"), analysedBy = j.optString("analysedBy"),
            retrieval = j.optString("retrieval"), createdAt = j.optLong("createdAt", System.currentTimeMillis()),
        )
    }
}

/**
 * The offline library: one JSON file per reading plus its payload, in app-private storage. Small enough that a
 * file per row is simpler than Room (and needs no annotation processor on this toolchain); the server's store
 * stays the source of truth and [Sync] reconciles against it.
 */
object Store {
    private val _all = MutableStateFlow<List<Reading>>(emptyList())
    val all: StateFlow<List<Reading>> = _all
    private lateinit var dir: File

    @Synchronized fun init(ctx: Context) {
        if (::dir.isInitialized) return
        dir = File(ctx.filesDir, "readings").apply { mkdirs() }
        reload()
    }

    @Synchronized private fun reload() {
        _all.value = dir.listFiles { f -> f.name.endsWith(".row.json") }.orEmpty()
            .mapNotNull { runCatching { Reading.fromJson(JSONObject(it.readText())) }.getOrNull() }
            .sortedByDescending { it.createdAt }
    }

    fun get(id: String) = _all.value.firstOrNull { it.id == id }

    fun add(url: String, title: String, lens: String, concerns: String): Reading =
        Reading(UUID.randomUUID().toString(), url, title.ifBlank { url }, lens, concerns).also { put(it) }

    @Synchronized fun put(r: Reading) {
        File(dir, "${r.id}.row.json").writeText(r.toJson().toString())
        reload()
    }

    fun update(id: String, f: (Reading) -> Reading) { get(id)?.let { put(f(it)) } }

    fun payload(id: String): String? = File(dir, "$id.payload.json").takeIf { it.exists() }?.readText()

    fun savePayload(id: String, json: String) = File(dir, "$id.payload.json").writeText(json)

    @Synchronized fun remove(id: String) {
        File(dir, "$id.row.json").delete(); File(dir, "$id.payload.json").delete()
        reload()
    }
}
