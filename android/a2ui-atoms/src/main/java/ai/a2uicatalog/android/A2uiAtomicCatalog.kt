package ai.a2uicatalog.android

import android.content.Context
import androidx.a2ui.compose.ui.A2uiCatalog
import androidx.a2ui.compose.ui.A2uiComponent
import androidx.compose.material3.a2ui.catalog.MaterialA2uiBasicCatalogV1Defaults

/**
 * The a2uicatalog atom catalog for Google's androidx.a2ui Compose renderer.
 *
 * ```
 * val catalog = A2uiAtomicCatalog.catalog(context)
 * val processor = A2uiMessageProcessor(listOf(catalog))
 * ```
 *
 * Every atom in the catalog's schema is registered (androidx.a2ui throws on an
 * unregistered type, so nothing may be missing). Each draws through one WebView bridge
 * running the catalog's own web renderer, bundled in this library from the same
 * commit. Basic Catalog components draw natively in Compose with Google's own
 * Material 3 implementation (androidx.compose.material3:material3-a2ui) by default;
 * pass [defaultBasicComponents] for ours, or your own for your design system. Agents that read the renderer's capabilities send this catalog only to
 * apps that registered it; apps without it get Basic Catalog surfaces.
 */
object A2uiAtomicCatalog {
    /** The catalog id surfaces declare and the renderer advertises. */
    const val ID: String = CATALOG_ID

    /**
     * The catalog: [basicComponents] (Basic Catalog V1, drawn in Compose) plus every
     * atom on the bridge, plus a placeholder for types [adapt] could not map.
     */
    fun catalog(context: Context, basicComponents: List<A2uiComponent> = materialBasicComponents()): A2uiCatalog {
        val basic = basicComponents.filter { it.name != PayloadAdapter.UNKNOWN }
        val taken = basic.map { it.name }.toSet()
        val bridged = Atoms.specs(context).filter { it.name !in taken }.map { AtomBridgeComponent(it) }
        BridgedTypes.names = BridgedTypes.names + bridged.map { it.name }
        return A2uiCatalog(catalogId = CATALOG_ID, components = basic + UnknownPlaceholder + bridged)
    }

    /**
     * The default Basic Catalog: Google's own Material 3 components (material3-a2ui, published
     * alongside androidx.a2ui on 2026-09-23) for the 15 that need nothing from the host, plus
     * this library's Image, Video and AudioPlayer, because Google's three take a host-supplied
     * media renderer. [defaultBasicComponents] (all 18 of ours) stays available.
     */
    fun materialBasicComponents(): List<A2uiComponent> = with(MaterialA2uiBasicCatalogV1Defaults) {
        listOf(text, icon, row, column, list, card, tabs, modal, divider, button,
            textField, checkBox, choicePicker, slider, dateTimeInput,
            DefaultImage, DefaultVideo, DefaultAudioPlayer)
    }

    /** Number of atoms bundled from the catalog schema. */
    fun atomCount(context: Context): Int = Atoms.specs(context).size

    /**
     * Safety net for payloads not emitted for this renderer: rewrites v1.0 to the v0.9 the
     * alpha parses, moves components out of createSurface into updateComponents, and turns
     * any type [catalog] does not register into a visible placeholder instead of a crash.
     * Feed each of [PayloadAdapter.Result.messages] to the processor.
     */
    fun adapt(input: String, catalog: A2uiCatalog): PayloadAdapter.Result =
        PayloadAdapter.adapt(input, catalog.components.map { it.name }.toSet())
}
