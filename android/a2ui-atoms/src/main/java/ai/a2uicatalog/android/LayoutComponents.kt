package ai.a2uicatalog.android

import android.content.Context
import android.content.Intent
import android.net.Uri
import androidx.a2ui.compose.runtime.A2uiComponentReference
import androidx.a2ui.compose.runtime.A2uiComponentScope
import androidx.a2ui.compose.ui.catalog.A2uiBasicCatalogV1
import androidx.a2ui.compose.ui.catalog.A2uiBasicCatalogV1.AccessibilityAttributes
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.clickable
import androidx.compose.foundation.gestures.awaitEachGesture
import androidx.compose.foundation.gestures.awaitFirstDown
import androidx.compose.foundation.gestures.waitForUpOrCancellation
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.material3.Card
import androidx.compose.material3.LocalContentColor
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.PrimaryTabRow
import androidx.compose.material3.Tab
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.drawscope.withTransform
import androidx.compose.ui.graphics.vector.PathParser
import androidx.compose.ui.input.pointer.PointerEventPass
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp
import androidx.compose.ui.window.Dialog
import org.json.JSONObject

/*
 * The rest of the Basic Catalog: Icon, Video, AudioPlayer, List, Tabs, Modal. With
 * BasicComponents.kt and InputComponents.kt, every one of the spec's 18 components draws
 * (tests/test_basic_catalog_coverage.py checks against the vendored spec catalog).
 */

/** The 59 built-in icon names -> SVG path data, from the shared atoms/basic-catalog-icons.json. */
private object IconPaths {
    @Volatile private var paths: Map<String, String>? = null
    var viewBox = floatArrayOf(0f, -960f, 960f, 960f)
        private set

    fun get(ctx: Context, name: String): String? {
        val p = paths ?: synchronized(this) {
            paths ?: JSONObject(ctx.assets.open("basic-icons.json").bufferedReader().readText()).let { doc ->
                viewBox = doc.getString("viewBox").trim().split(Regex("\\s+")).map { it.toFloat() }.toFloatArray()
                val icons = doc.getJSONObject("icons")
                icons.keys().asSequence().associateWith { icons.getJSONObject(it).getString("d") }
            }.also { paths = it }
        }
        return p[name]
    }
}

object DefaultIcon : A2uiBasicCatalogV1.Icon {
    @Composable
    override fun A2uiComponentScope.TypedContent(
        source: A2uiBasicCatalogV1.Icon.Source, accessibility: AccessibilityAttributes?, modifier: Modifier,
    ) {
        val ctx = LocalContext.current
        val (d, box, name) = when (source) {
            is A2uiBasicCatalogV1.Icon.BuiltIn -> Triple(IconPaths.get(ctx, source.value), IconPaths.viewBox, source.value)
            is A2uiBasicCatalogV1.Icon.SvgPath -> Triple(source.svgPath, floatArrayOf(0f, 0f, 24f, 24f), "icon")
            is A2uiBasicCatalogV1.Icon.Unrecognized -> Triple(null, IconPaths.viewBox, source.name)
            else -> Triple(null, IconPaths.viewBox, "icon")
        }
        val path = remember(d) { d?.let { runCatching { PathParser().parsePathString(it).toPath() }.getOrNull() } }
        val tint = LocalContentColor.current
        if (path == null) {
            Text("[$name]", style = MaterialTheme.typography.labelSmall, modifier = modifier)
            return
        }
        Canvas(modifier.size(24.dp).semantics { contentDescription = name }) {
            val s = size.minDimension / maxOf(box[2], box[3])
            withTransform({ scale(s, s, pivot = Offset.Zero); translate(-box[0], -box[1]) }) {
                drawPath(path, tint)
            }
        }
    }
}

/** Video and audio open in the device's own player: no media dependency in the library. */
@Composable
private fun MediaCard(url: String, glyph: String, caption: String, modifier: Modifier) {
    val ctx = LocalContext.current
    Card(modifier.fillMaxWidth().clickable {
        runCatching { ctx.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)) }
    }) {
        Row(Modifier.padding(16.dp), verticalAlignment = Alignment.CenterVertically) {
            Text(glyph, style = MaterialTheme.typography.headlineSmall)
            Column(Modifier.padding(start = 12.dp)) {
                Text(caption, style = MaterialTheme.typography.titleSmall)
                Text(Uri.parse(url).host ?: url, style = MaterialTheme.typography.bodySmall)
            }
        }
    }
}

object DefaultVideo : A2uiBasicCatalogV1.Video {
    @Composable
    override fun A2uiComponentScope.TypedContent(url: String, accessibility: AccessibilityAttributes?, modifier: Modifier) =
        MediaCard(url, "▶", "Play video", modifier)
}

object DefaultAudioPlayer : A2uiBasicCatalogV1.AudioPlayer {
    @Composable
    override fun A2uiComponentScope.TypedContent(
        url: String, description: String?, accessibility: AccessibilityAttributes?, modifier: Modifier,
    ) = MediaCard(url, "♫", description ?: "Play audio", modifier)
}

object DefaultList : A2uiBasicCatalogV1.List {
    @Composable
    override fun A2uiComponentScope.TypedContent(
        children: List<A2uiComponentReference>, direction: A2uiBasicCatalogV1.List.Direction,
        align: A2uiBasicCatalogV1.List.Align, accessibility: AccessibilityAttributes?, modifier: Modifier,
    ) {
        if (direction == A2uiBasicCatalogV1.List.Direction.Horizontal) {
            Row(modifier.fillMaxWidth().horizontalScroll(rememberScrollState()),
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                verticalAlignment = when (align) {
                    A2uiBasicCatalogV1.List.Align.Start -> Alignment.Top
                    A2uiBasicCatalogV1.List.Align.End -> Alignment.Bottom
                    else -> Alignment.CenterVertically
                }) { children.forEach { Child(it) } }
        } else {
            Column(modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(8.dp),
                horizontalAlignment = when (align) {
                    A2uiBasicCatalogV1.List.Align.Center -> Alignment.CenterHorizontally
                    A2uiBasicCatalogV1.List.Align.End -> Alignment.End
                    else -> Alignment.Start
                }) {
                children.forEach {
                    Child(it, if (align == A2uiBasicCatalogV1.List.Align.Stretch) Modifier.fillMaxWidth() else Modifier)
                }
            }
        }
    }
}

object DefaultTabs : A2uiBasicCatalogV1.Tabs {
    @Composable
    override fun A2uiComponentScope.TypedContent(
        tabs: List<A2uiBasicCatalogV1.Tabs.Tab>, accessibility: AccessibilityAttributes?, modifier: Modifier,
    ) {
        if (tabs.isEmpty()) return
        var sel by remember { mutableIntStateOf(0) }
        val i = sel.coerceIn(0, tabs.lastIndex)
        Column(modifier.fillMaxWidth()) {
            PrimaryTabRow(selectedTabIndex = i) {
                tabs.forEachIndexed { n, t -> Tab(selected = n == i, onClick = { sel = n }, text = { Text(t.title) }) }
            }
            Box(Modifier.padding(top = 12.dp)) { Child(tabs[i].childId) }
        }
    }
}

object DefaultModal : A2uiBasicCatalogV1.Modal {
    @Composable
    override fun A2uiComponentScope.TypedContent(
        triggerId: String, contentId: String, accessibility: AccessibilityAttributes?, modifier: Modifier,
    ) {
        var open by remember { mutableStateOf(false) }
        // Watch taps on the trigger without consuming them: a Button trigger still fires its own action.
        Box(modifier.pointerInput(Unit) {
            awaitEachGesture {
                awaitFirstDown(requireUnconsumed = false, pass = PointerEventPass.Initial)
                if (waitForUpOrCancellation(pass = PointerEventPass.Initial) != null) open = true
            }
        }) { Child(triggerId) }
        if (open) Dialog(onDismissRequest = { open = false }) {
            Card {
                Column(Modifier.padding(20.dp)) {
                    Child(contentId)
                    TextButton(onClick = { open = false }, modifier = Modifier.align(Alignment.End)) { Text("Close") }
                }
            }
        }
    }
}
