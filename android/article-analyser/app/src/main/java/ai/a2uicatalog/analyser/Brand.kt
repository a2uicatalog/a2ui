package ai.a2uicatalog.analyser

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

/** The a2uicatalog brand (motion-demos/landing THEMES.dark): the same ink, accents and panels as the site and films. */
object Brand {
    val bg = Color(0xFF1E2733)
    val panel = Color(0xFF2D3642)
    val panelHi = Color(0xFF3A4554)
    val ink = Color(0xFFEAEFF5)
    val mute = Color(0xFF9CA5B1)
    val accent = Color(0xFF8D98FF)   // periwinkle
    val accent2 = Color(0xFF2AC4CE)  // teal
    val warn = Color(0xFFF0B45A)
    val bad = Color(0xFFFF8A80)
    val good = Color(0xFF81C995)
}

private val scheme = darkColorScheme(
    primary = Brand.accent, onPrimary = Color(0xFF141B24),
    secondary = Brand.accent2, onSecondary = Color(0xFF0B2A2D),
    background = Brand.bg, onBackground = Brand.ink,
    surface = Brand.bg, onSurface = Brand.ink,
    surfaceVariant = Brand.panel, onSurfaceVariant = Brand.mute,
    surfaceContainer = Brand.panel, surfaceContainerHigh = Brand.panelHi,
    outline = Color(0xFF4A5566), error = Brand.bad,
)

@Composable
fun BrandTheme(content: @Composable () -> Unit) = MaterialTheme(colorScheme = scheme, content = content)
