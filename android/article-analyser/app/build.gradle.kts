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
        // AppAuth's redirect receiver: matches the a2ui-android client's registered redirect_uri
        // (mcp-worker/src/oauth.js HARDCODED_CLIENTS), ai.a2uicatalog.android:/oauth2redirect.
        manifestPlaceholders["appAuthRedirectScheme"] = "ai.a2uicatalog.android"
    }
    buildFeatures { compose = true }
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
