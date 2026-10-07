plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.plugin.compose")
}

android {
    namespace = "ai.a2uicatalog.analyser"
    compileSdk { version = release(37) { minorApiLevel = 1 } }

    defaultConfig {
        applicationId = "ai.a2uicatalog.analyser"
        minSdk = 26
        targetSdk = 37
        versionCode = 1
        versionName = "0.1"
        // Your server's details. The defaults are placeholders: set the real values in ~/.gradle/gradle.properties or
        // with -P flags, never in this file (see "Configure" in the README).
        fun prop(name: String, default: String) = (project.findProperty(name) as String?) ?: default
        buildConfigField("String", "MCP_URL", "\"${prop("analyser.mcpUrl", "https://your-server.example/mcp")}\"")
        buildConfigField("String", "AUTH_URL", "\"${prop("analyser.authUrl", "https://your-server.example/oauth/authorize")}\"")
        buildConfigField("String", "TOKEN_URL", "\"${prop("analyser.tokenUrl", "https://your-server.example/oauth/token")}\"")
        buildConfigField("String", "CLIENT_ID", "\"${prop("analyser.clientId", "your-client-id")}\"")
        // AppAuth's redirect receiver: the custom scheme your OAuth client registered as its redirect_uri
        // (<scheme>:/oauth2redirect).
        val redirectScheme = prop("analyser.redirectScheme", "com.example.analyser")
        buildConfigField("String", "REDIRECT_SCHEME", "\"$redirectScheme\"")
        manifestPlaceholders["appAuthRedirectScheme"] = redirectScheme
    }
    buildFeatures { compose = true; buildConfig = true }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}

dependencies {
    implementation("ai.a2uicatalog:atomic-catalog:0.1.0")   // the reading view: RendererWebView, offline bundle

    implementation("androidx.activity:activity-compose:1.13.0")
    implementation("androidx.compose.foundation:foundation:1.13.0-alpha03")
    // aligned with material3-a2ui (pins [1.5.0-alpha28]); a newer material3 alpha breaks its Slider at runtime
    implementation("androidx.compose.material3:material3:1.5.0-alpha28")
    implementation("androidx.work:work-runtime-ktx:2.10.5")
    implementation("net.openid:appauth:0.11.1")
    implementation("org.jsoup:jsoup:1.21.2")
}
