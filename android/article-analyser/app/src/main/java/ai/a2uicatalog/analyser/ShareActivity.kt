package ai.a2uicatalog.analyser

import android.content.Intent
import android.os.Bundle
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.FilterChip
import androidx.compose.material3.FilterChipDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

val LENSES = listOf("explain" to "Explain", "apply" to "Apply", "challenge" to "Challenge", "situate" to "Situate")

/**
 * The share target. It catches the link, asks for a lens, queues the read and gets out of the way: the reading
 * happens in [ReadWorker] whenever there is signal, so this sheet closes in a second even underground.
 */
class ShareActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        Store.init(this)
        val shared = intent?.takeIf { it.action == Intent.ACTION_SEND }
        val text = shared?.getStringExtra(Intent.EXTRA_TEXT).orEmpty()
        val url = Regex("""https?://\S+""").find(text)?.value?.trimEnd('.', ',', ')', '"', '\'')
        if (url == null) {
            Toast.makeText(this, "No link in what was shared", Toast.LENGTH_SHORT).show(); finish(); return
        }
        val subject = shared?.getStringExtra(Intent.EXTRA_SUBJECT).orEmpty()
            .ifBlank { text.replace(url, "").trim().lines().firstOrNull().orEmpty() }
        setContent { BrandTheme { Sheet(url, subject) } }
    }

    @androidx.compose.runtime.Composable
    private fun Sheet(url: String, subject: String) {
        var lens by remember { mutableStateOf("explain") }
        var concerns by remember { mutableStateOf("") }
        val signedIn = remember { Auth.isSignedIn(this) }
        Box(Modifier.fillMaxSize().clickable(remember { MutableInteractionSource() }, null) { finish() },
            contentAlignment = Alignment.BottomCenter) {
            Column(Modifier.fillMaxWidth()
                .clickable(remember { MutableInteractionSource() }, null) {}
                .background(Brand.bg, RoundedCornerShape(topStart = 24.dp, topEnd = 24.dp))
                .navigationBarsPadding().imePadding().padding(20.dp),
                verticalArrangement = Arrangement.spacedBy(14.dp)) {
                Text("A2UI ARTICLE ANALYSER", color = Brand.accent2, fontSize = 12.sp, fontWeight = FontWeight.Bold, letterSpacing = 2.sp)
                Text(subject.ifBlank { "Read this article" }, color = Brand.ink, fontSize = 20.sp,
                    fontWeight = FontWeight.Black, maxLines = 2, overflow = TextOverflow.Ellipsis)
                Text(url, color = Brand.mute, fontSize = 13.sp, maxLines = 1, overflow = TextOverflow.Ellipsis)
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    LENSES.forEach { (k, label) ->
                        FilterChip(lens == k, { lens = k }, { Text(label) },
                            colors = FilterChipDefaults.filterChipColors(selectedContainerColor = Brand.accent,
                                selectedLabelColor = Brand.bg, labelColor = Brand.ink, containerColor = Brand.panel))
                    }
                }
                OutlinedTextField(concerns, { concerns = it }, Modifier.fillMaxWidth(),
                    placeholder = { Text("Anything to look for or push back on? (optional)", color = Brand.mute) },
                    singleLine = false, maxLines = 3)
                if (!signedIn) Text("You're not signed in yet. It will wait in the app until you are.",
                    color = Brand.warn, fontSize = 13.sp)
                Button({
                    val r = Store.add(url, subject, lens, concerns.trim())
                    ReadWorker.enqueue(this@ShareActivity, r.id)
                    Toast.makeText(this@ShareActivity, "Queued: it reads when there's signal", Toast.LENGTH_SHORT).show()
                    finish()
                }, Modifier.fillMaxWidth(), colors = ButtonDefaults.buttonColors(containerColor = Brand.accent, contentColor = Brand.bg)) {
                    Text("Read it", fontWeight = FontWeight.Bold, fontSize = 16.sp)
                }
            }
        }
    }
}
