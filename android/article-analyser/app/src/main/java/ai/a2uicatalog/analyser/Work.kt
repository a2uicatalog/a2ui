package ai.a2uicatalog.analyser

import android.content.Context
import android.util.Log
import androidx.work.BackoffPolicy
import androidx.work.Constraints
import androidx.work.CoroutineWorker
import androidx.work.ExistingWorkPolicy
import androidx.work.NetworkType
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.WorkManager
import androidx.work.WorkerParameters
import androidx.work.workDataOf
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.jsoup.Jsoup
import org.json.JSONObject
import java.net.SocketTimeoutException
import java.util.concurrent.TimeUnit

private const val TAG = "A2uiAnalyser"

/** The phone reads the page itself, on its own network. It is a plain request with no browser cookies, so articles
 *  behind a login or paywall are not readable this way; a page too thin to quote falls back to the server's fetch. */
object Article {
    suspend fun text(url: String): Pair<String, String>? = withContext(Dispatchers.IO) {
        runCatching {
            val doc = Jsoup.connect(url).userAgent("Mozilla/5.0 (Android) A2UIAnalyser/0.1").timeout(15_000)
                .followRedirects(true).get()
            doc.select("script,style,nav,header,footer,aside,form,noscript").remove()
            val root = doc.selectFirst("article") ?: doc.selectFirst("main") ?: doc.body()
            val text = root.select("h1,h2,h3,p,li,blockquote").joinToString("\n\n") { it.text() }.trim()
            if (text.length < 400) null else doc.title() to text   // too thin to quote from: let the server fetch
        }.onFailure { Log.w(TAG, "fetch failed for $url", it) }.getOrNull()
    }
}

/** One shared link, read once there is a network. Queued by the share sheet; survives the app being closed. */
class ReadWorker(ctx: Context, params: WorkerParameters) : CoroutineWorker(ctx, params) {
    override suspend fun doWork(): Result {
        Store.init(applicationContext)
        val id = inputData.getString("id") ?: return Result.failure()
        val r = Store.get(id) ?: return Result.failure()
        Store.update(id) { it.copy(status = Status.READING, error = "") }
        return try {
            val page = Article.text(r.url)
            val title = r.title.takeIf { it != r.url } ?: page?.first.orEmpty()
            val out = Mcp.readArticle(applicationContext, r.url, page?.second, title, r.lens, r.concerns)
            val payload = out.optJSONObject("payload") ?: throw Mcp.ToolError("no reading came back")
            Store.savePayload(id, payload.toString())
            Store.update(id) {
                it.copy(status = Status.READY, title = readingTitle(payload) ?: title.ifBlank { it.title },
                    remoteId = out.optString("reading_id"), analysedBy = out.optString("analysed_by"),
                    retrieval = out.optString("retrieval"))
            }
            Result.success()
        } catch (e: Auth.SignInRequired) {
            Store.update(id) { it.copy(status = Status.SIGN_IN, error = "Sign in to read this") }
            Result.failure()
        } catch (e: Mcp.ToolError) {
            Store.update(id) { it.copy(status = Status.FAILED, error = e.message ?: "could not read it") }
            Result.failure()
        } catch (e: SocketTimeoutException) {
            // The server keeps reading after we drop (read_article runs under waitUntil and saves the reading),
            // so a retry would read it twice. Mark it and let the next sync collect it.
            Store.update(id) { it.copy(status = Status.CHECKING, error = "") }
            Result.success()
        } catch (e: Exception) {
            Log.w(TAG, "read failed, will retry", e)
            Store.update(id) { it.copy(status = Status.QUEUED, error = e.message ?: "") }
            Result.retry()
        }
    }

    companion object {
        fun enqueue(ctx: Context, id: String) {
            val req = OneTimeWorkRequestBuilder<ReadWorker>()
                .setInputData(workDataOf("id" to id))
                .setConstraints(Constraints.Builder().setRequiredNetworkType(NetworkType.CONNECTED).build())
                .setBackoffCriteria(BackoffPolicy.EXPONENTIAL, 30, TimeUnit.SECONDS)
                .build()
            WorkManager.getInstance(ctx).enqueueUniqueWork("read-$id", ExistingWorkPolicy.KEEP, req)
        }
    }
}

/** org.json's optString turns a JSON null into the text "null"; the store's rows have real nulls. */
internal fun JSONObject.str(k: String): String = if (isNull(k)) "" else optString(k)

internal fun readingTitle(payload: JSONObject): String? =
    payload.optJSONObject("createSurface")?.optJSONObject("surfaceProperties")?.optString("title")?.takeIf { it.isNotBlank() }

/**
 * Two-way reconcile with the reader's store (list_readings returns each row's payload_p, so this is one call):
 * collect readings the phone timed out on, add readings made elsewhere (Claude, the PWA), and drop local copies of
 * readings deleted elsewhere. Deletions only run when the list came back whole (under the 100-row page).
 */
object Sync {
    suspend fun run(ctx: Context): String {
        Store.init(ctx)
        val res = Mcp.listReadings(ctx)
        val rows = res.optJSONArray("readings") ?: return "nothing to sync"
        val remote = (0 until rows.length()).map { rows.getJSONObject(it) }
        var added = 0; var collected = 0; var removed = 0
        val local = Store.all.value
        for (row in remote) {
            val rid = row.str("id")
            val p = row.str("payload_p").takeIf { it.isNotBlank() } ?: continue
            val src = row.str("source_url")
            val match = local.firstOrNull { it.remoteId == rid }
                ?: local.firstOrNull { it.remoteId.isEmpty() && it.status == Status.CHECKING && it.url == src }
            if (match != null && match.status == Status.READY) continue
            val payload = runCatching { Mcp.decodePayload(p) }.getOrNull() ?: continue
            val r = match ?: Reading(java.util.UUID.randomUUID().toString(), src.ifBlank { row.str("url") },
                row.str("source_title").ifBlank { row.str("title") }, row.str("lens"),
                createdAt = row.optLong("stamped_at", System.currentTimeMillis()))
            Store.savePayload(r.id, payload)
            Store.put(r.copy(status = Status.READY, remoteId = rid, error = "",
                title = row.str("title").ifBlank { r.title }))
            if (match == null) added++ else collected++
        }
        if (remote.size < 100) {
            val ids = remote.map { it.str("id") }.toSet()
            Store.all.value.filter { it.status == Status.READY && it.remoteId.isNotEmpty() && it.remoteId !in ids }
                .forEach { Store.remove(it.id); removed++ }
        }
        return listOf("$added new", "$collected collected", "$removed removed").joinToString(" · ")
    }
}
