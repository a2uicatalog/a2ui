package ai.a2uicatalog.analyser

import android.content.Context
import android.util.Base64
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.io.IOException
import java.net.HttpURLConnection
import java.net.URL
import java.util.zip.GZIPInputStream

/**
 * The catalog's MCP server, called directly as an MCP client: JSON-RPC tools/call on the authenticated endpoint.
 * The phone is the host here, the part Claude or Gemini Enterprise plays in an MCP App, so there is no model in
 * the loop on this side: read_article runs Gemini server-side and keeps the reading in this reader's store.
 */
object Mcp {
    private const val ENDPOINT = "https://a2uicatalog.ai/mcp-auth"

    /** A tool-level refusal (bad input, daily cap, the model gave up): retrying the same call won't help. */
    class ToolError(message: String) : Exception(message)

    suspend fun call(ctx: Context, tool: String, args: JSONObject, readTimeoutMs: Int = 30_000): JSONObject =
        withContext(Dispatchers.IO) {
            val token = Auth.freshToken(ctx)
            val body = JSONObject().put("jsonrpc", "2.0").put("id", System.currentTimeMillis())
                .put("method", "tools/call").put("params", JSONObject().put("name", tool).put("arguments", args))
            val conn = (URL(ENDPOINT).openConnection() as HttpURLConnection).apply {
                requestMethod = "POST"
                doOutput = true
                connectTimeout = 15_000
                readTimeout = readTimeoutMs
                setRequestProperty("Content-Type", "application/json")
                setRequestProperty("Accept", "application/json")
                setRequestProperty("Authorization", "Bearer $token")
            }
            try {
                conn.outputStream.use { it.write(body.toString().toByteArray()) }
                val code = conn.responseCode
                if (code == 401) throw Auth.SignInRequired()
                val text = (if (code in 200..299) conn.inputStream else conn.errorStream)?.bufferedReader()?.readText().orEmpty()
                if (code !in 200..299) throw IOException("MCP server returned HTTP $code")
                val res = JSONObject(text)
                res.optJSONObject("error")?.let { throw ToolError(it.optString("message", "MCP error")) }
                val result = res.getJSONObject("result")
                if (result.optBoolean("isError")) {
                    val msg = result.optJSONArray("content")?.optJSONObject(0)?.optString("text").orEmpty()
                    throw ToolError(msg.ifBlank { "the tool refused" })
                }
                result.optJSONObject("structuredContent") ?: JSONObject()
            } finally {
                conn.disconnect()
            }
        }

    /** read_article: 20-60 s, so a long read timeout. Returns {payload, reading_id, analysed_by, retrieval, ...}. */
    suspend fun readArticle(ctx: Context, url: String, text: String?, title: String?, lens: String, concerns: String?): JSONObject =
        call(ctx, "read_article", JSONObject().put("url", url).put("lens", lens).apply {
            if (!text.isNullOrBlank()) put("text", text)
            if (!title.isNullOrBlank()) put("source_title", title)
            if (!concerns.isNullOrBlank()) put("concerns", concerns)
        }, readTimeoutMs = 120_000)

    suspend fun listReadings(ctx: Context, limit: Int = 100): JSONObject =
        call(ctx, "list_readings", JSONObject().put("runbook", "article_playbook").put("limit", limit))

    suspend fun deleteReadings(ctx: Context, ids: List<String>): JSONObject =
        call(ctx, "delete_reading", JSONObject().put("ids", org.json.JSONArray(ids)))

    /** A stored reading's payload_p: the same gzip + url-safe base64 as a ?p= link, decoded back to the A2UI JSON. */
    fun decodePayload(p: String): String {
        val bytes = Base64.decode(p, Base64.URL_SAFE or Base64.NO_PADDING or Base64.NO_WRAP)
        return GZIPInputStream(bytes.inputStream()).bufferedReader().readText()
    }
}
