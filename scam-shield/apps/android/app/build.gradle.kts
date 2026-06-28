plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "com.scamshield.app"
    compileSdk = 34

    defaultConfig {
        applicationId = "com.scamshield.app"
        minSdk = 26
        targetSdk = 34
        versionCode = 1
        versionName = "0.1.0"
        // Point the app at your backend. Use ws:// for local, wss:// in production.
        buildConfigField("String", "API_BASE", "\"http://10.0.2.2:8000\"")
        buildConfigField("String", "WS_BASE", "\"ws://10.0.2.2:8000\"")
    }
    buildFeatures { buildConfig = true; compose = true }
    composeOptions { kotlinCompilerExtensionVersion = "1.5.14" }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions { jvmTarget = "17" }
}

dependencies {
    implementation("androidx.core:core-ktx:1.13.1")
    implementation("androidx.activity:activity-compose:1.9.0")
    implementation(platform("androidx.compose:compose-bom:2024.06.00"))
    implementation("androidx.compose.material3:material3")
    implementation("androidx.compose.ui:ui")
    implementation("com.squareup.okhttp3:okhttp:4.12.0")
}
