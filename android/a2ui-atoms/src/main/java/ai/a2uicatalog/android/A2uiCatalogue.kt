package ai.a2uicatalog.android

import android.content.Context
import androidx.a2ui.compose.ui.A2uiCatalog
import androidx.a2ui.compose.ui.A2uiComponent

/**
 * The a2uicatalog atom catalogue for Google's androidx.a2ui Compose renderer.
 *
 * ```
 * val catalog = A2uiCatalogue.catalog(context)
 * val processor = A2uiMessageProcessor(listOf(catalog))
 * ```
 *
 * Every atom in the catalogue's schema is registered (androidx.a2ui throws on an
 * unregistered type, so nothing may be missing). Each draws through one WebView bridge
 * running the catalogue's own web renderer, bundled in this library from the same
 * commit. Basic Catalog components draw natively in Compose: ours by default, or pass
 * your own. Agents that read the renderer's capabilities send this catalogue only to
 * apps that registered it; apps without it get Basic Catalog surfaces.
 */
object A2uiCatalogue {
    /** The catalogue id surfaces declare and the renderer advertises. */
    const val ID: String = CATALOG_ID

    /**
     * The catalogue: [basicComponents] (Basic Catalog V1, drawn in Compose) plus every
     * atom on the bridge, plus a placeholder for types [adapt] could not map.
     */
    fun catalog(context: Context, basicComponents: List<A2uiComponent> = defaultBasicComponents): A2uiCatalog {
        val basic = basicComponents.filter { it.name != PayloadAdapter.UNKNOWN }
        val taken = basic.map { it.name }.toSet()
        val bridged = Atoms.specs(context).filter { it.name !in taken }.map { AtomBridgeComponent(it) }
        return A2uiCatalog(catalogId = CATALOG_ID, components = basic + UnknownPlaceholder + bridged)
    }

    /** Number of atoms bundled from the catalogue schema. */
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
