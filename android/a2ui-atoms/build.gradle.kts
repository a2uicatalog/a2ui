import javax.inject.Inject
import org.gradle.process.ExecOperations

plugins {
    id("com.android.library")
    id("org.jetbrains.kotlin.plugin.compose")
    id("com.vanniktech.maven.publish")
}

group = "ai.a2uicatalog"
version = "0.1.0"

android {
    namespace = "ai.a2uicatalog.android"
    compileSdk { version = release(37) { minorApiLevel = 1 } }

    defaultConfig {
        minSdk = 26
    }
    buildFeatures { compose = true }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}

/**
 * atoms.json + renderer-bundle.html, generated from THIS checkout's schema and web bundle
 * at build time and never copied into git, so the AAR cannot drift from the catalogue.
 */
abstract class GenerateA2uiAssets : DefaultTask() {
    @get:InputFiles abstract val sources: ConfigurableFileCollection
    @get:Input abstract val script: Property<String>
    @get:Input abstract val stableOnly: Property<Boolean>
    @get:OutputDirectory abstract val outputDir: DirectoryProperty
    @get:Inject abstract val exec: ExecOperations

    @TaskAction
    fun generate() {
        val args = mutableListOf("python3", script.get(), outputDir.get().asFile.path)
        if (stableOnly.get()) args += "--stable-only"
        exec.exec { commandLine(args) }
    }
}

fun GenerateA2uiAssets.configureSources(stable: Boolean) {
    val repo = rootProject.layout.projectDirectory.dir("..")
    stableOnly.set(stable)
    sources.from(
        repo.file("atoms/schema.yaml"),
        repo.file("atoms/atom-packs.yaml"),
        repo.file("public/surfaces/mcp-apps/renderer-bundle.html"),
        rootProject.layout.projectDirectory.file("tools/gen_android_assets.py"),
    )
    script.set(rootProject.layout.projectDirectory.file("tools/gen_android_assets.py").asFile.path)
}

// Debug builds (the viewer, local testing) register every atom; release builds, the ones that
// get published, register stable atoms only. Preview atoms are repo-only by policy.
val generateA2uiAssets = tasks.register<GenerateA2uiAssets>("generateA2uiAssets") { configureSources(false) }
val generateA2uiAssetsStable = tasks.register<GenerateA2uiAssets>("generateA2uiAssetsStable") { configureSources(true) }

androidComponents {
    onVariants { variant ->
        val task = if (variant.buildType == "release") generateA2uiAssetsStable else generateA2uiAssets
        variant.sources.assets?.addGeneratedSourceDirectory(task, GenerateA2uiAssets::outputDir)
    }
}

dependencies {
    val a2ui = "1.0.0-alpha01"
    api("androidx.a2ui.compose:compose-ui:$a2ui")
    api("androidx.a2ui.compose:compose-runtime:$a2ui")
    api("androidx.a2ui:a2ui-engine:$a2ui")
    api("androidx.a2ui:a2ui-model:$a2ui")

    implementation("androidx.compose.foundation:foundation:1.13.0-alpha03")
    // material3 pinned to the version material3-a2ui requires ([1.5.0-alpha28], AndroidX group alignment)
    implementation("androidx.compose.material3:material3:1.5.0-alpha28")
    // Google's own Material 3 Basic Catalog for androidx.a2ui: the library's default basic components
    api("androidx.compose.material3:material3-a2ui:$a2ui")
}

// Maven Central (namespace ai.a2uicatalog, verified by a DNS TXT record on a2uicatalog.ai).
// Credentials and the signing key come from Gradle properties, never from this file:
// mavenCentralUsername / mavenCentralPassword (a Sonatype user token) and
// signingInMemoryKey / signingInMemoryKeyPassword, passed as ORG_GRADLE_PROJECT_* env vars by
// `ops.py run android-publish`. Publishing is per-release opt-in; a version can never be replaced.
mavenPublishing {
    publishToMavenCentral()
    signAllPublications()
    coordinates("ai.a2uicatalog", "atomic-catalog", version.toString())
    pom {
        name.set("A2UI Atomic Catalog for Android")
        description.set(
            "The stable a2uicatalog atoms registered with Google's androidx.a2ui Jetpack Compose renderer: " +
                "Basic Catalog components drawn in Compose, the rest through the catalog's web renderer. " +
                "Built against androidx.a2ui 1.0.0-alpha01, whose API may still change."
        )
        inceptionYear.set("2026")
        url.set("https://a2uicatalog.ai/surfaces/android/")
        licenses {
            license {
                name.set("MIT License")
                url.set("https://opensource.org/licenses/MIT")
                distribution.set("repo")
            }
        }
        developers {
            developer {
                id.set("a2uicatalog")
                name.set("Curtis Krygier")
                url.set("https://a2uicatalog.ai/")
            }
        }
        scm {
            url.set("https://github.com/a2uicatalog/a2ui")
            connection.set("scm:git:https://github.com/a2uicatalog/a2ui.git")
            developerConnection.set("scm:git:ssh://git@github.com/a2uicatalog/a2ui.git")
        }
    }
}
