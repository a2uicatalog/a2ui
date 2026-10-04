import javax.inject.Inject
import org.gradle.process.ExecOperations

plugins {
    id("com.android.library")
    id("org.jetbrains.kotlin.plugin.compose")
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
    @get:OutputDirectory abstract val outputDir: DirectoryProperty
    @get:Inject abstract val exec: ExecOperations

    @TaskAction
    fun generate() {
        exec.exec { commandLine("python3", script.get(), outputDir.get().asFile.path) }
    }
}

val generateA2uiAssets = tasks.register<GenerateA2uiAssets>("generateA2uiAssets") {
    val repo = rootProject.layout.projectDirectory.dir("..")
    sources.from(
        repo.file("atoms/schema.yaml"),
        repo.file("atoms/atom-packs.yaml"),
        repo.file("public/surfaces/mcp-apps/renderer-bundle.html"),
        rootProject.layout.projectDirectory.file("tools/gen_android_assets.py"),
    )
    script.set(rootProject.layout.projectDirectory.file("tools/gen_android_assets.py").asFile.path)
}

androidComponents {
    onVariants { variant ->
        variant.sources.assets?.addGeneratedSourceDirectory(generateA2uiAssets, GenerateA2uiAssets::outputDir)
    }
}

dependencies {
    val a2ui = "1.0.0-alpha01"
    api("androidx.a2ui.compose:compose-ui:$a2ui")
    api("androidx.a2ui.compose:compose-runtime:$a2ui")
    api("androidx.a2ui:a2ui-engine:$a2ui")
    api("androidx.a2ui:a2ui-model:$a2ui")

    implementation("androidx.compose.foundation:foundation:1.13.0-alpha03")
    implementation("androidx.compose.material3:material3:1.5.0-alpha29")
}
