package ai.a2uicatalog.android

import android.graphics.BitmapFactory
import androidx.a2ui.compose.runtime.A2uiComponentProperties
import androidx.a2ui.compose.runtime.A2uiComponentReference
import androidx.a2ui.compose.runtime.A2uiComponentScope
import androidx.a2ui.compose.runtime.A2uiComponentState
import androidx.a2ui.compose.runtime.A2uiProperty
import androidx.a2ui.compose.runtime.observeA2uiComponentState
import androidx.a2ui.compose.ui.A2uiComponent
import androidx.a2ui.compose.ui.catalog.A2uiBasicCatalogV1
import androidx.a2ui.compose.ui.catalog.A2uiBasicCatalogV1.AccessibilityAttributes
import androidx.a2ui.compose.ui.catalog.A2uiBasicCatalogV1.CheckRule
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.VerticalDivider
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.key
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.net.URL
import org.json.JSONObject

/*
 * androidx.a2ui's Basic Catalog V1 is definitions and parsing; Google draws it in Material 3
 * in a separate artifact, material3-a2ui, which the library uses by default
 * (A2uiAtomicCatalog.materialBasicComponents). These are the library's OWN implementations,
 * kept as defaultBasicComponents and used for Image/Video/AudioPlayer. These are the seven display
 * components the viewer draws (the five inputs are in InputComponents.kt); any other Basic Catalog type is replaced with a placeholder by
 * PayloadAdapter, because the engine throws on unregistered types.
 */

/** Draws a child component by id, the way Card/Button/Column reference their children. */
@Composable
fun A2uiComponentScope.Child(id: String, modifier: Modifier = Modifier) {
    when (val s = observeA2uiComponentState(id)) {
        is A2uiComponentState.Success -> A2uiComponent(s.component, modifier)
        is A2uiComponentState.Error -> ErrorBox("$id: ${s.exception.message}")
        A2uiComponentState.Loading -> Unit
    }
}

@Composable
fun A2uiComponentScope.Child(ref: A2uiComponentReference, modifier: Modifier = Modifier) {
    when (val s = observeA2uiComponentState(ref)) {
        is A2uiComponentState.Success -> A2uiComponent(s.component, modifier)
        is A2uiComponentState.Error -> ErrorBox("${ref.id}: ${s.exception.message}")
        A2uiComponentState.Loading -> Unit
    }
}

@Composable
fun ErrorBox(msg: String) {
    Text(msg, color = Color(0xFFB00020), style = MaterialTheme.typography.bodySmall,
        modifier = Modifier.fillMaxWidth().background(Color(0x14B00020)).padding(8.dp))
}

object DefaultText : A2uiBasicCatalogV1.Text {
    @Composable
    override fun A2uiComponentScope.TypedContent(
        text: String, variant: A2uiBasicCatalogV1.Text.Variant,
        accessibility: AccessibilityAttributes?, modifier: Modifier,
    ) {
        // Our converter maps heading/subheading to Text with a markdown prefix ("# ", "## ").
        // Honour it: strip the marker and, unless a variant was set explicitly, use its level.
        val md = Regex("^(#{1,5})\\s+(.*)$", RegexOption.DOT_MATCHES_ALL).find(text)
        val body = md?.groupValues?.get(2) ?: text
        val v = if (md != null && variant == A2uiBasicCatalogV1.Text.Variant.Body) {
            A2uiBasicCatalogV1.Text.Variant.fromValue("h" + md.groupValues[1].length)
        } else variant
        val t = MaterialTheme.typography
        val style = when (v) {
            A2uiBasicCatalogV1.Text.Variant.H1 -> t.headlineLarge
            A2uiBasicCatalogV1.Text.Variant.H2 -> t.headlineMedium
            A2uiBasicCatalogV1.Text.Variant.H3 -> t.headlineSmall
            A2uiBasicCatalogV1.Text.Variant.H4 -> t.titleLarge
            A2uiBasicCatalogV1.Text.Variant.H5 -> t.titleMedium
            A2uiBasicCatalogV1.Text.Variant.Caption -> t.labelMedium
            A2uiBasicCatalogV1.Text.Variant.Body -> t.bodyLarge
        }
        Text(body, style = style, modifier = modifier.padding(vertical = 2.dp))
    }
}

private fun arrangementV(j: String) = when (j) {
    "center" -> Arrangement.Center
    "end" -> Arrangement.Bottom
    "spaceBetween" -> Arrangement.SpaceBetween
    "spaceAround" -> Arrangement.SpaceAround
    "spaceEvenly" -> Arrangement.SpaceEvenly
    else -> Arrangement.spacedBy(8.dp)
}

private fun arrangementH(j: String) = when (j) {
    "center" -> Arrangement.Center
    "end" -> Arrangement.End
    "spaceBetween" -> Arrangement.SpaceBetween
    "spaceAround" -> Arrangement.SpaceAround
    "spaceEvenly" -> Arrangement.SpaceEvenly
    else -> Arrangement.spacedBy(8.dp)
}

object DefaultColumn : A2uiBasicCatalogV1.Column {
    @Composable
    override fun A2uiComponentScope.TypedContent(
        children: List<A2uiComponentReference>, justify: A2uiBasicCatalogV1.Column.Justify,
        align: A2uiBasicCatalogV1.Column.Align, accessibility: AccessibilityAttributes?,
        modifier: Modifier,
    ) {
        val h = when (align) {
            A2uiBasicCatalogV1.Column.Align.Center -> Alignment.CenterHorizontally
            A2uiBasicCatalogV1.Column.Align.End -> Alignment.End
            else -> Alignment.Start
        }
        Column(modifier.fillMaxWidth(), verticalArrangement = arrangementV(justify.value),
            horizontalAlignment = h) {
            // Consecutive bridged atoms share ONE WebView (one renderer load instead of one
            // per atom), which matters on low-end phones; everything else draws as before.
            val states = children.map { observeA2uiComponentState(it) }
            val theme = LocalSurfaceTheme.current
            var i = 0
            while (i < children.size) {
                var j = i
                val run = mutableListOf<JSONObject>()
                while (j < children.size) {
                    val s = states[j]
                    val comp = (s as? A2uiComponentState.Success)?.component
                        ?.takeIf { it.type in BridgedTypes.names } ?: break
                    run += key(children[j].id) { resolvedBlock(comp.type, comp.properties) } ?: break
                    j++
                }
                if (run.size >= 2) {
                    val start = i
                    key(children[start].id) {
                        // If painting the run together ever throws, one bad atom would blank
                        // the whole run: fall back to one WebView per atom so only it suffers.
                        var groupFailed by remember(children[start].id, run.size) { mutableStateOf(false) }
                        if (groupFailed) {
                            Column { for (k in start until j) Child(children[k]) }
                        } else {
                            RendererWebView(bridgePayload(run, theme), onError = { groupFailed = true },
                                onAction = { dispatchAction(it) })
                        }
                    }
                    i = j
                } else {
                    key(children[i].id) { Child(children[i]) }
                    i++
                }
            }
        }
    }
}

object DefaultRow : A2uiBasicCatalogV1.Row {
    @Composable
    override fun A2uiComponentScope.TypedContent(
        children: List<A2uiComponentReference>, justify: A2uiBasicCatalogV1.Row.Justify,
        align: A2uiBasicCatalogV1.Row.Align, accessibility: AccessibilityAttributes?,
        modifier: Modifier,
    ) {
        val v = when (align) {
            A2uiBasicCatalogV1.Row.Align.Center -> Alignment.CenterVertically
            A2uiBasicCatalogV1.Row.Align.End -> Alignment.Bottom
            else -> Alignment.Top
        }
        Row(modifier.fillMaxWidth(), horizontalArrangement = arrangementH(justify.value),
            verticalAlignment = v) {
            children.forEach { Child(it) }
        }
    }
}

object DefaultCard : A2uiBasicCatalogV1.Card {
    @Composable
    override fun A2uiComponentScope.TypedContent(
        childId: String, accessibility: AccessibilityAttributes?, modifier: Modifier,
    ) {
        Card(modifier.fillMaxWidth()) { Box(Modifier.padding(16.dp)) { Child(childId) } }
    }
}

object DefaultButton : A2uiBasicCatalogV1.Button {
    @Composable
    override fun A2uiComponentScope.TypedContent(
        childId: String, variant: A2uiBasicCatalogV1.Button.Variant, action: Map<String, Any?>,
        accessibility: AccessibilityAttributes?, checks: List<CheckRule>, modifier: Modifier,
    ) {
        val onClick = { dispatchAction(action) }
        when (variant) {
            A2uiBasicCatalogV1.Button.Variant.Primary -> Button(onClick, modifier) { Child(childId) }
            A2uiBasicCatalogV1.Button.Variant.Borderless -> TextButton(onClick, modifier) { Child(childId) }
            A2uiBasicCatalogV1.Button.Variant.Secondary -> OutlinedButton(onClick, modifier) { Child(childId) }
        }
    }
}

object DefaultDivider : A2uiBasicCatalogV1.Divider {
    @Composable
    override fun A2uiComponentScope.TypedContent(
        axis: A2uiBasicCatalogV1.Divider.Axis, accessibility: AccessibilityAttributes?,
        modifier: Modifier,
    ) {
        if (axis == A2uiBasicCatalogV1.Divider.Axis.Vertical) VerticalDivider(modifier)
        else HorizontalDivider(modifier.padding(vertical = 8.dp))
    }
}

object DefaultImage : A2uiBasicCatalogV1.Image {
    @Composable
    override fun A2uiComponentScope.TypedContent(
        url: String, description: String?, fit: A2uiBasicCatalogV1.Image.Fit,
        variant: A2uiBasicCatalogV1.Image.Variant, accessibility: AccessibilityAttributes?,
        modifier: Modifier,
    ) {
        var bmp by remember(url) { mutableStateOf<ImageBitmap?>(null) }
        var err by remember(url) { mutableStateOf<String?>(null) }
        LaunchedEffect(url) {
            try {
                bmp = withContext(Dispatchers.IO) {
                    URL(url).openStream().use { BitmapFactory.decodeStream(it) }?.asImageBitmap()
                }
                if (bmp == null) err = "could not decode $url"
            } catch (e: Exception) {
                err = "${e.javaClass.simpleName}: $url"
            }
        }
        val scale = when (fit) {
            A2uiBasicCatalogV1.Image.Fit.Cover -> ContentScale.Crop
            A2uiBasicCatalogV1.Image.Fit.Contain, A2uiBasicCatalogV1.Image.Fit.ScaleDown -> ContentScale.Fit
            A2uiBasicCatalogV1.Image.Fit.None -> ContentScale.None
            A2uiBasicCatalogV1.Image.Fit.Fill -> ContentScale.FillBounds
        }
        bmp?.let { Image(it, description, modifier.fillMaxWidth().heightIn(max = 240.dp), contentScale = scale) }
        err?.let { ErrorBox("Image: $it") }
    }
}

/** Stand-in for any type the viewer can't draw; PayloadAdapter rewrites those to this. */
object UnknownPlaceholder : androidx.a2ui.compose.ui.A2uiComponent {
    private val OriginalType = A2uiProperty.string("originalType")
    override val name = PayloadAdapter.UNKNOWN
    override val description = "Placeholder for a component type this viewer cannot draw."
    override val properties = listOf(OriginalType)

    @Composable
    override fun A2uiComponentScope.Content(properties: A2uiComponentProperties, modifier: Modifier) {
        Text("Not drawable on Android yet: ${properties[OriginalType]}",
            style = MaterialTheme.typography.bodySmall,
            modifier = modifier.fillMaxWidth()
                .border(1.dp, Color(0xFFB00020), RoundedCornerShape(6.dp)).padding(10.dp))
    }
}

val defaultBasicComponents: List<androidx.a2ui.compose.ui.A2uiComponent> =
    listOf(DefaultText, DefaultColumn, DefaultRow, DefaultCard, DefaultButton, DefaultDivider, DefaultImage,
        DefaultTextField, DefaultCheckBox, DefaultChoicePicker, DefaultSlider, DefaultDateTimeInput,
        DefaultIcon, DefaultVideo, DefaultAudioPlayer, DefaultList, DefaultTabs, DefaultModal, UnknownPlaceholder)
