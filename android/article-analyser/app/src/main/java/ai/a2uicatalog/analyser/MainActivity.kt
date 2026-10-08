package ai.a2uicatalog.analyser

import ai.a2uicatalog.android.RendererWebView
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.BackHandler
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawingPadding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.launch
import androidx.a2ui.model.processor.processInput

/**
 * The library: every shared link and its reading, kept on the phone. Opening a reading paints its stored A2UI
 * payload with the catalog's bundled renderer (the AAR's RendererWebView): the same payload the web Workspace and
 * Claude's MCP Apps view render, offline, with no screen of its own.
 */
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        Store.init(this)
        setContent { BrandTheme { Surface(Modifier.fillMaxSize(), color = Brand.bg) { App() } } }
    }
}

@Composable
private fun App() {
    val ctx = LocalContext.current
    val scope = rememberCoroutineScope()
    var signedIn by remember { mutableStateOf(Auth.isSignedIn(ctx)) }
    var open by remember { mutableStateOf<String?>(null) }
    var note by remember { mutableStateOf("") }
    val readings by Store.all.collectAsState()

    fun requeueWaiting() = Store.all.value.filter { it.status == Status.SIGN_IN || it.status == Status.QUEUED }
        .forEach { Store.update(it.id) { r -> r.copy(status = Status.QUEUED, error = "") }; ReadWorker.enqueue(ctx, it.id) }

    fun sync() = scope.launch {
        note = "Syncing…"
        note = try { Sync.run(ctx) } catch (e: Auth.SignInRequired) { signedIn = false; "Sign in to sync" } catch (e: Exception) { "Offline: showing what's on the phone" }
    }

    val signIn = rememberLauncherForActivityResult(ActivityResultContracts.StartActivityForResult()) { res ->
        scope.launch {
            note = try { Auth.complete(ctx, res.data); signedIn = true; requeueWaiting(); sync(); "Signed in" }
                   catch (e: Exception) { "Sign-in didn't finish: ${e.message}" }
        }
    }
    LaunchedEffect(signedIn) { if (signedIn) sync() }

    open?.let { id ->
        BackHandler { open = null }
        Reader(id) { open = null }
        return
    }

    Column(Modifier.fillMaxSize().safeDrawingPadding().padding(horizontal = 16.dp)) {
        Header(onSync = { sync() }, signedIn = signedIn)
        if (note.isNotBlank()) Text(note, color = Brand.mute, fontSize = 12.sp, modifier = Modifier.padding(bottom = 8.dp))
        if (!signedIn) SignInCard { signIn.launch(Auth.signInIntent(ctx)) }
        // A newly shared link lands at the top; LazyColumn otherwise keeps the old first item anchored and the
        // new one appears above the fold, out of sight.
        val listState = androidx.compose.foundation.lazy.rememberLazyListState()
        val newest = readings.firstOrNull()?.id
        LaunchedEffect(newest) { if (newest != null) listState.animateScrollToItem(0) }
        if (readings.isEmpty()) Empty() else LazyColumn(state = listState, verticalArrangement = Arrangement.spacedBy(10.dp)) {
            items(readings, key = { it.id }) { r ->
                ReadingRow(r, onOpen = { if (r.status == Status.READY) open = r.id },
                    onRetry = { Store.update(r.id) { it.copy(status = Status.QUEUED, error = "") }; ReadWorker.enqueue(ctx, r.id) },
                    onDelete = {
                        Store.remove(r.id)
                        if (r.remoteId.isNotEmpty()) scope.launch { runCatching { Mcp.deleteReadings(ctx, listOf(r.remoteId)) } }
                    })
            }
            item { Spacer(Modifier.height(24.dp)) }
        }
    }
}

@Composable
private fun Header(onSync: () -> Unit, signedIn: Boolean) {
    Row(Modifier.fillMaxWidth().padding(vertical = 14.dp), verticalAlignment = Alignment.CenterVertically) {
        Mark()
        Column(Modifier.padding(start = 12.dp).weight(1f)) {
            Text("A2UI Article Analyser", color = Brand.ink, fontSize = 21.sp, fontWeight = FontWeight.Black)
            Text("Share a link. Keep the reading.", color = Brand.mute, fontSize = 13.sp)
        }
        if (signedIn) TextButton(onSync) { Text("Sync", color = Brand.accent2, fontWeight = FontWeight.Bold) }
    }
}

/** The A2UI Catalog mark (res/drawable/ic_mark.xml, the motion_mark atom's geometry). */
@Composable
private fun Mark() = androidx.compose.foundation.Image(
    androidx.compose.ui.res.painterResource(R.drawable.ic_mark), contentDescription = "A2UI Catalog", Modifier.size(40.dp))

@Composable
private fun SignInCard(onSignIn: () -> Unit) = Column(
    Modifier.fillMaxWidth().padding(bottom = 14.dp).background(Brand.panel, RoundedCornerShape(16.dp)).padding(16.dp),
    verticalArrangement = Arrangement.spacedBy(10.dp)) {
    Text("Sign in with your A2UI account", color = Brand.ink, fontWeight = FontWeight.Bold, fontSize = 16.sp)
    Text("Readings are kept in your A2UI history, so they also open in Claude and on the web.",
        color = Brand.mute, fontSize = 13.sp)
    Button(onSignIn, colors = ButtonDefaults.buttonColors(containerColor = Brand.accent, contentColor = Brand.bg)) {
        Text("Sign in", fontWeight = FontWeight.Bold)
    }
}

@Composable
private fun Empty() = Column(Modifier.fillMaxWidth().padding(top = 48.dp), horizontalAlignment = Alignment.CenterHorizontally,
    verticalArrangement = Arrangement.spacedBy(8.dp)) {
    Text("Nothing kept yet", color = Brand.ink, fontWeight = FontWeight.Bold, fontSize = 18.sp)
    Text("Share an article from Chrome or any app to\n“A2UI Article Analyser”. It reads when there's signal.",
        color = Brand.mute, fontSize = 14.sp, lineHeight = 20.sp)
}

@Composable
private fun ReadingRow(r: Reading, onOpen: () -> Unit, onRetry: () -> Unit, onDelete: () -> Unit) {
    val (label, tint) = when (r.status) {
        Status.READY -> "Ready" to Brand.good
        Status.QUEUED -> "Waiting for signal" to Brand.warn
        Status.READING -> "Reading…" to Brand.accent2
        Status.CHECKING -> "Collecting at next sync" to Brand.accent2
        Status.SIGN_IN -> "Sign in to read" to Brand.warn
        Status.FAILED -> "Couldn't read it" to Brand.bad
    }
    Column(Modifier.fillMaxWidth().background(Brand.panel, RoundedCornerShape(16.dp)).clickable(onClick = onOpen).padding(14.dp),
        verticalArrangement = Arrangement.spacedBy(6.dp)) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Box(Modifier.size(8.dp).background(tint, CircleShape))
            Text("  $label" + if (r.lens.isNotBlank()) " · ${r.lens}" else "", color = tint, fontSize = 12.sp, fontWeight = FontWeight.Bold)
            Spacer(Modifier.weight(1f))
            Text(r.host, color = Brand.mute, fontSize = 12.sp)
        }
        Text(r.title, color = Brand.ink, fontSize = 16.sp, fontWeight = FontWeight.Bold, maxLines = 2, overflow = TextOverflow.Ellipsis)
        if (r.error.isNotBlank() && r.status != Status.READY) Text(r.error, color = Brand.mute, fontSize = 12.sp, maxLines = 3)
        if (r.status == Status.FAILED || r.status == Status.SIGN_IN) Row {
            TextButton(onRetry) { Text("Retry", color = Brand.accent) }
            TextButton(onDelete) { Text("Delete", color = Brand.mute) }
        }
    }
}

@Composable
private fun Reader(id: String, onBack: () -> Unit) {
    val r = Store.get(id)
    val payload = remember(id) { Store.payload(id) }
    Column(Modifier.fillMaxSize().safeDrawingPadding()) {
        Row(Modifier.fillMaxWidth().padding(8.dp), verticalAlignment = Alignment.CenterVertically) {
            TextButton(onBack) { Text("‹ Library", color = Brand.accent, fontWeight = FontWeight.Bold) }
            Spacer(Modifier.weight(1f))
            if (r != null && r.analysedBy.isNotBlank()) Text(
                "read by ${r.analysedBy}" + if (r.retrieval == "app_fetched") " · from this phone's copy" else "",
                color = Brand.mute, fontSize = 11.sp, modifier = Modifier.padding(end = 12.dp))
        }
        if (payload == null) Text("This reading isn't on the phone yet.", color = Brand.mute, modifier = Modifier.padding(16.dp))
        else Box(Modifier.fillMaxSize().verticalScroll(remember(id) { androidx.compose.foundation.ScrollState(0) })
            .background(Color(0xFFF6F9FD)).padding(10.dp)) {
            NativeReading(id, payload)
        }
    }
}

/**
 * The reading drawn NATIVELY: the stored A2UI payload goes through Google's androidx.a2ui engine with the catalog
 * (concept_ladder/concept_rung are Compose components in the library, the root Column is Google's Material 3 one). If
 * the engine can't take a payload, the catalog's bundled web renderer paints it instead, so a reading never goes blank.
 */
@Composable
private fun NativeReading(id: String, payload: String) {
    val ctx = LocalContext.current
    val catalog = remember { ai.a2uicatalog.android.A2uiAtomicCatalog.catalog(ctx) }
    val adapted = remember(id) { runCatching { ai.a2uicatalog.android.A2uiAtomicCatalog.adapt(payload, catalog) }.getOrNull() }
    var failed by remember(id) { mutableStateOf(adapted == null) }
    if (failed || adapted == null) { RendererWebView(payload); return }
    val processor = remember(id) { androidx.a2ui.compose.ui.A2uiMessageProcessor(listOf(catalog)) }
    LaunchedEffect(id) {
        launch { processor.collectMessages() }
        val parser = androidx.a2ui.compose.runtime.A2uiMessageParser()
        runCatching { adapted.messages.forEach { processor.processInput(parser, it) } }
            .onFailure { android.util.Log.w("A2uiReader", "processInput failed", it); failed = true }
    }
    val surfaces by processor.activeSurfaces.collectAsState()
    androidx.compose.runtime.CompositionLocalProvider(ai.a2uicatalog.android.LocalSurfaceTheme provides adapted.theme) {
        surfaces.forEach { surface ->
            when (val st = androidx.a2ui.compose.runtime.observeA2uiComponentState(surface)) {
                is androidx.a2ui.compose.runtime.A2uiComponentState.Success -> androidx.a2ui.compose.ui.A2uiComponent(st.component)
                is androidx.a2ui.compose.runtime.A2uiComponentState.Error -> { LaunchedEffect(Unit) {
                    android.util.Log.w("A2uiReader", "surface error", st.exception); failed = true } }
                androidx.a2ui.compose.runtime.A2uiComponentState.Loading -> Unit
            }
        }
    }
}
