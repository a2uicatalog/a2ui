package ai.a2uicatalog.android

import androidx.a2ui.compose.runtime.A2uiComponentProperties
import androidx.a2ui.compose.runtime.A2uiComponentScope
import androidx.a2ui.compose.runtime.A2uiComponentState
import androidx.a2ui.compose.runtime.A2uiProperty
import androidx.a2ui.compose.runtime.observeA2uiComponentState
import androidx.a2ui.compose.ui.A2uiComponent
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.IntrinsicSize
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.key
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.text.LinkAnnotation
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.TextLinkStyles
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextDecoration
import androidx.compose.ui.text.withLink
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

/*
 * concept_ladder and concept_rung drawn NATIVELY in Compose (2026-10-05): the reading a server-side agent stamps through
 * the article_playbook runbook renders with no WebView. Same design as the web renderer (atoms_concept.gs /
 * renderers/web_article.py): the a2uicatalog brand palette by default, the 14-token `palette` and the `fonts` roles
 * honoured, the rung rail, the verbatim-quote blocks. The ladder's `rungs` are component ids (A2UI v1.0 child refs),
 * resolved through the engine like Column's children; inline rung objects work too.
 *
 * Compose and a browser lay text out differently, so this matches the web design closely rather than pixel for pixel.
 * Fonts map to the platform families (sans, serif, monospace); IBM Plex is not bundled.
 */

private val LIGHT = mapOf(
    "paper" to 0xFFF6F9FD, "paper_raised" to 0xFFFFFFFF, "ink" to 0xFF141B24, "ink_soft" to 0xFF515963,
    "line" to 0xFFDDE3EC, "accent" to 0xFF6267E7, "accent_soft" to 0xFFE6E8FF, "blocked" to 0xFFC5221F,
    "blocked_soft" to 0xFFFCE8E6, "cleared" to 0xFF188038, "cleared_soft" to 0xFFE6F4EA,
    "mono_bg" to 0xFF1E2733, "mono_fg" to 0xFFEAEFF5, "mono_accent" to 0xFF8D98FF,
)
private val DARK = mapOf(
    "paper" to 0xFF1E2733, "paper_raised" to 0xFF2D3642, "ink" to 0xFFEAEFF5, "ink_soft" to 0xFF9CA5B1,
    "line" to 0xFF3A4554, "accent" to 0xFF8D98FF, "accent_soft" to 0xFF3A4160, "blocked" to 0xFFFF8A80,
    "blocked_soft" to 0xFF4A2A2A, "cleared" to 0xFF81C995, "cleared_soft" to 0xFF23382A,
    "mono_bg" to 0xFF141B24, "mono_fg" to 0xFFEAEFF5, "mono_accent" to 0xFF2AC4CE,
)
private val FONT_ROLES = mapOf("sans" to FontFamily.SansSerif, "serif" to FontFamily.Serif, "mono" to FontFamily.Monospace)

/** The ladder's resolved design tokens: colours by token name, and a family per type role. */
internal class ConceptTokens(val c: Map<String, Color>, val body: FontFamily, val heading: FontFamily, val label: FontFamily) {
    operator fun get(k: String): Color = c.getValue(k)
}

private fun hexColor(v: Any?): Color? {
    val s = (v as? String)?.trim() ?: return null
    if (!Regex("^#[0-9a-fA-F]{6}$").matches(s)) return null   // hex only: never a raw CSS value
    return Color(0xFF000000 or s.substring(1).toLong(16))
}

internal fun conceptTokens(theme: Any?, palette: Any?, fonts: Any?): ConceptTokens {
    val base = if (theme == "dark") DARK else LIGHT
    val ov = palette as? Map<*, *> ?: emptyMap<Any, Any>()
    val c = base.mapValues { (k, v) -> hexColor(ov[k]) ?: Color(v) }
    val f = fonts as? Map<*, *> ?: emptyMap<Any, Any>()
    fun role(k: String, d: String) = FONT_ROLES[f[k] as? String] ?: FONT_ROLES.getValue(d)
    return ConceptTokens(c, role("body", "sans"), role("heading", "sans"), role("label", "mono"))
}

private val DEFAULT_TOKENS = conceptTokens(null, null, null)

/** `code` spans in a field, as the web renderer's _journeyMdCode draws them. */
private fun md(text: String, t: ConceptTokens): AnnotatedString = buildAnnotatedString {
    val parts = text.split('`')
    parts.forEachIndexed { i, p ->
        if (i % 2 == 1 && i < parts.size - 1) {
            withStyle(SpanStyle(fontFamily = FontFamily.Monospace, fontSize = 0.88.em(), color = t["accent"], background = t["accent_soft"])) { append(p) }
        } else append(if (i % 2 == 1) "`$p" else p)
    }
}

private fun Double.em() = androidx.compose.ui.unit.TextUnit(this.toFloat(), androidx.compose.ui.unit.TextUnitType.Em)

private fun str(m: Map<*, *>, k: String): String = (m[k] as? String)?.trim().orEmpty()

@Composable
private fun Label(text: String, color: Color, t: ConceptTokens, size: Int = 11, modifier: Modifier = Modifier) =
    Text(text.uppercase(), color = color, fontFamily = t.label, fontWeight = FontWeight.Bold, fontSize = size.sp,
        letterSpacing = 0.09.em(), modifier = modifier)

/** The attribution bar: what this is a reading OF, who read it, what steered it. */
@Composable
private fun SourceBar(ladder: Map<*, *>, t: ConceptTokens) {
    val src = ladder["source"] as? Map<*, *> ?: return
    val title = str(src, "title"); val url = str(src, "url")
    val analysed = (src["analysed_by"] ?: ladder["analysed_by"]) as? String
    val verified = (src["analysed_verified"] ?: ladder["analysed_verified"]) == true
    val meta = listOfNotNull(src["author"], src["publication"], src["published"],
        src["read_minutes"]?.let { "$it min read" }).joinToString(" · ")
    Row(Modifier.fillMaxWidth().padding(bottom = 20.dp).clip(RoundedCornerShape(8.dp))
        .background(t["paper_raised"]).border(1.dp, t["line"], RoundedCornerShape(8.dp)).height(IntrinsicSize.Min)) {
        Box(Modifier.width(3.dp).fillMaxHeight().background(t["accent"]))
        Column(Modifier.padding(horizontal = 14.dp, vertical = 11.dp), verticalArrangement = Arrangement.spacedBy(5.dp)) {
            Label(str(src, "label").ifBlank { "Analysis of" }, t["accent"], t, 10)
            if (title.isNotBlank()) Text(
                if (url.startsWith("https://") || url.startsWith("http://")) buildAnnotatedString {
                    withLink(LinkAnnotation.Url(url, TextLinkStyles(SpanStyle(color = t["ink"], textDecoration = TextDecoration.Underline)))) { append(title) }
                } else AnnotatedString(title),
                color = t["ink"], fontFamily = t.body, fontSize = 15.sp, lineHeight = 20.sp)
            Text(if (analysed != null) "Analysed by $analysed" + (if (verified) "" else " (self-reported)") else "Analysing model not recorded",
                color = t["ink_soft"], fontFamily = t.label, fontSize = 10.sp)
            if (meta.isNotBlank()) Text(meta, color = t["ink_soft"], fontFamily = t.label, fontSize = 11.sp)
            val steered = (src["steered_by"] as? List<*>)?.mapNotNull { it as? String } ?: listOfNotNull(src["steered_by"] as? String)
            if (steered.any { it.isNotBlank() }) {
                Box(Modifier.fillMaxWidth().padding(top = 4.dp).height(1.dp).background(t["line"]))
                Label("Reading steered by", t["ink_soft"], t, 10)
                steered.filter { it.isNotBlank() }.forEach {
                    Text(md(it, t), color = t["ink"], fontFamily = t.body, fontStyle = FontStyle.Italic, fontSize = 13.sp, lineHeight = 18.sp)
                }
            }
        }
    }
}

/** A dark mono block with the accent '>' — the verbatim quote (takeaway) or a code sample. */
@Composable
private fun MonoBlock(text: String, t: ConceptTokens, quote: Boolean) =
    Text(buildAnnotatedString {
        if (quote) withStyle(SpanStyle(color = t["mono_accent"], fontWeight = FontWeight.SemiBold)) { append("> ") }
        // A model sometimes writes the article's line breaks into a quote as the two characters \n; show them as breaks.
        append(text.replace("\\n", "\n"))
    }, color = t["mono_fg"], fontFamily = FontFamily.Monospace, fontSize = 13.sp, lineHeight = 20.sp,
        modifier = Modifier.fillMaxWidth().padding(bottom = 12.dp).clip(RoundedCornerShape(8.dp)).background(t["mono_bg"])
            .padding(horizontal = 14.dp, vertical = 12.dp))

/** One rung's card: chip, title, body, code, takeaway. */
@Composable
internal fun RungCard(r: Map<*, *>, t: ConceptTokens) {
    val example = r["kind"] == "example"
    val badge = r["badge"]?.toString()?.takeIf { it.isNotBlank() && it != "null" }
    val label = str(r, "label").ifBlank { if (example) "WORKED EXAMPLE" else listOfNotNull("DEPTH", badge).joinToString(" ") }
    Column(Modifier.fillMaxWidth().padding(bottom = 20.dp)) {
        Label(label, if (example) t["mono_accent"] else t["accent"], t, 11,
            Modifier.padding(bottom = 8.dp).clip(RoundedCornerShape(4.dp))
                .background(if (example) t["mono_bg"] else t["accent_soft"]).padding(horizontal = 8.dp, vertical = 3.dp))
        str(r, "title").takeIf { it.isNotBlank() }?.let {
            Text(md(it, t), color = t["ink"], fontFamily = t.heading, fontWeight = FontWeight.Bold, fontSize = 17.sp,
                lineHeight = 22.sp, letterSpacing = (-0.01).em(), modifier = Modifier.padding(bottom = 7.dp))
        }
        str(r, "body").split("\n\n").map { it.trim() }.filter { it.isNotEmpty() }.forEach {
            Text(md(it, t), color = t["ink"], fontFamily = t.body, fontSize = 15.sp, lineHeight = 23.sp, modifier = Modifier.padding(bottom = 12.dp))
        }
        str(r, "code").takeIf { it.isNotBlank() }?.let { MonoBlock(it, t, quote = false) }
        str(r, "code_caption").takeIf { it.isNotBlank() }?.let {
            Text(md(it, t), color = t["ink_soft"], fontFamily = t.body, fontStyle = FontStyle.Italic, fontSize = 13.sp, modifier = Modifier.padding(bottom = 12.dp))
        }
        str(r, "takeaway").takeIf { it.isNotBlank() }?.let { MonoBlock(it, t, quote = true) }
    }
}

/** The rail beside each rung: its number in a circle, and the line down to the next one. */
@Composable
private fun RailRow(index: Int, last: Boolean, rung: Map<*, *>, t: ConceptTokens) {
    val example = rung["kind"] == "example"
    // A model sometimes puts a word in `badge`; the circle only has room for a number or a short mark.
    val badge = rung["badge"]?.toString()?.takeIf { it.isNotBlank() && it != "null" && it.length <= 3 } ?: "${index + 1}"
    Row(Modifier.fillMaxWidth().height(IntrinsicSize.Min)) {
        Column(Modifier.width(38.dp).fillMaxHeight(), horizontalAlignment = Alignment.CenterHorizontally) {
            Box(Modifier.size(34.dp).clip(CircleShape).background(if (example) t["mono_bg"] else t["accent_soft"]),
                contentAlignment = Alignment.Center) {
                Text(badge, color = if (example) t["mono_accent"] else t["accent"], fontFamily = t.label, fontWeight = FontWeight.SemiBold, fontSize = 13.sp)
            }
            if (!last) Box(Modifier.padding(vertical = 5.dp).width(1.5.dp).weight(1f).heightIn(min = 22.dp).background(t["line"]))
        }
        Spacer(Modifier.width(14.dp))
        Box(Modifier.weight(1f)) { RungCard(rung, t) }
    }
}


/**
 * Every field the agent sent, data bindings resolved (resolvedBlock, the bridge's own reader of the alpha's raw props).
 * Empty if the alpha's internals move; the ladder then draws an empty card rather than crashing.
 */
@Composable
private fun A2uiComponentScope.fields(props: A2uiComponentProperties): Map<String, Any?> =
    resolvedBlock("_", props)?.let { b -> b.keys().asSequence().filter { it != "type" }.associateWith { k -> unwrap(b.opt(k)) } }
        ?: emptyMap()

private fun unwrap(v: Any?): Any? = when (v) {
    is org.json.JSONObject -> v.keys().asSequence().associateWith { unwrap(v.opt(it)) }
    is org.json.JSONArray -> List(v.length()) { unwrap(v.opt(it)) }
    org.json.JSONObject.NULL -> null
    else -> v
}

object NativeConceptLadder : A2uiComponent {
    override val name = "concept_ladder"
    override val description = "Layered-depth reading (attribution, hero model, rung rail), drawn natively in Compose"
    // No typed properties, on purpose: androidx.a2ui 1.0.0-alpha01 rejected the whole component (Google's Column then
    // draws a red "Error" chip in its place) when the ladder's object and list fields (source, rungs, palette) were
    // declared as dynamic values. Every field is read from the raw payload instead (fields(), bindings resolved).
    override val properties = emptyList<A2uiProperty<*>>()

    @Composable
    override fun A2uiComponentScope.Content(properties: A2uiComponentProperties, modifier: Modifier) {
        val b = fields(properties)
        val t = conceptTokens(b["theme"], b["palette"], b["fonts"])
        val rungs = (b["rungs"] as? List<*>).orEmpty()
        Column(modifier.fillMaxWidth().clip(RoundedCornerShape(14.dp)).background(t["paper"])
            .border(1.dp, t["line"], RoundedCornerShape(14.dp)).padding(horizontal = 18.dp, vertical = 22.dp)) {
            SourceBar(b, t)
            str(b, "eyebrow").takeIf { it.isNotBlank() }?.let {
                Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.padding(bottom = 12.dp)) {
                    Box(Modifier.width(18.dp).height(1.5.dp).background(t["accent"])); Spacer(Modifier.width(8.dp))
                    Label(it, t["ink_soft"], t, 11)
                }
            }
            str(b, "title").takeIf { it.isNotBlank() }?.let {
                Text(it, color = t["ink"], fontFamily = t.heading, fontWeight = FontWeight.ExtraBold, fontSize = 25.sp,
                    lineHeight = 29.sp, letterSpacing = (-0.02).em(), modifier = Modifier.padding(bottom = 10.dp))
            }
            str(b, "dek").takeIf { it.isNotBlank() }?.let {
                Text(it, color = t["ink_soft"], fontFamily = t.body, fontStyle = FontStyle.Italic, fontSize = 16.sp, lineHeight = 22.sp,
                    modifier = Modifier.padding(bottom = 18.dp))
            }
            str(b, "hook").takeIf { it.isNotBlank() }?.let {
                Row(Modifier.padding(bottom = 20.dp).height(IntrinsicSize.Min)) {
                    Box(Modifier.width(3.dp).fillMaxHeight().background(t["accent"])); Spacer(Modifier.width(14.dp))
                    Text(md(it, t), color = t["ink"], fontFamily = t.body, fontSize = 17.sp, lineHeight = 25.sp)
                }
            }
            str(b, "model").takeIf { it.isNotBlank() }?.let { model ->
                Column(Modifier.fillMaxWidth().padding(bottom = 24.dp).clip(RoundedCornerShape(12.dp)).background(t["paper_raised"])
                    .border(1.dp, t["line"], RoundedCornerShape(12.dp)).padding(16.dp)) {
                    Label("The model", t["accent"], t, 11, Modifier.padding(bottom = 7.dp))
                    Text(md(model, t), color = t["ink"], fontFamily = t.body, fontStyle = FontStyle.Italic, fontSize = 17.sp, lineHeight = 24.sp)
                    str(b, "model_note").takeIf { it.isNotBlank() }?.let {
                        Text(md(it, t), color = t["ink_soft"], fontFamily = t.body, fontSize = 14.sp, lineHeight = 20.sp, modifier = Modifier.padding(top = 9.dp))
                    }
                }
            }
            rungs.forEachIndexed { i, ref ->
                val last = i == rungs.lastIndex
                when (ref) {
                    is String -> key(ref) {
                        // A v1.0 child ref: resolve it through the engine, the way Column draws its children.
                        when (val s = observeA2uiComponentState(ref)) {
                            is A2uiComponentState.Success -> {
                                val rf = rawProps(s.component.properties) ?: emptyMap()
                                RailRow(i, last, rf, t)
                            }
                            is A2uiComponentState.Error -> ErrorBox("$ref: ${s.exception.message}")
                            A2uiComponentState.Loading -> Unit
                        }
                    }
                    is Map<*, *> -> key(i) { RailRow(i, last, ref, t) }
                    else -> Unit
                }
            }
            str(b, "closing_note").takeIf { it.isNotBlank() }?.let {
                Text(md(it, t), color = t["ink_soft"], fontFamily = t.body, fontStyle = FontStyle.Italic, fontSize = 15.sp, lineHeight = 22.sp,
                    modifier = Modifier.padding(top = 8.dp))
            }
        }
    }
}

/** A rung drawn on its own (outside a ladder): the card with the default tokens. Inside a ladder the ladder draws it. */
object NativeConceptRung : A2uiComponent {
    override val name = "concept_rung"
    override val description = "One rung of a concept_ladder, drawn natively in Compose"
    override val properties = emptyList<A2uiProperty<*>>()   // read from the raw payload, as the ladder does

    @Composable
    override fun A2uiComponentScope.Content(properties: A2uiComponentProperties, modifier: Modifier) {
        Box(modifier.fillMaxWidth()) { RungCard(fields(properties), DEFAULT_TOKENS) }
    }
}

/**
 * theme_toggle on Android: the app's own theme applies (system dark mode, the host's MaterialTheme), so the web atom's
 * in-page toggle draws nothing here rather than a WebView holding one button.
 */
object NativeThemeToggle : A2uiComponent {
    override val name = "theme_toggle"
    override val description = "Theme toggle; on Android the host app's theme applies, so it draws nothing"
    override val properties = listOf("dark_bg", "initial", "label_dark", "label_light", "persist_action", "persist_to", "position")
        .map { A2uiProperty.dynamicValue(it) }

    @Composable
    override fun A2uiComponentScope.Content(properties: A2uiComponentProperties, modifier: Modifier) = Unit
}

/** Atoms this library draws natively; registered ahead of the WebView bridge. */
val nativeAtomComponents: List<A2uiComponent> = listOf(NativeConceptLadder, NativeConceptRung, NativeThemeToggle)
