import java.util.Properties

plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
    alias(libs.plugins.kotlin.compose)
    alias(libs.plugins.kotlin.serialization)
    alias(libs.plugins.google.services)
}

/** Build-time settings (package name, app name, version, API address, ad SDK app ids). Runtime settings come from the admin panel. */
val appProps = Properties().apply { rootProject.file("app.properties").inputStream().use(::load) }
/** FabAds (github.com/midnewswire/fabads-kotlin). Ship only the networks you use: see the README, "Ad networks". */
val fabAdsVersion = "98b01dab24"
val adNetworks: List<String> = appProps.getProperty("adNetworks", "admob").split(",")
    .map { it.trim().lowercase() }.filter { it.isNotEmpty() }
    .map { if (it == "admanager") "admob" else it }.distinct()
fun prop(key: String, default: String? = null): String =
    appProps.getProperty(key)?.takeIf { it.isNotBlank() } ?: default ?: error("app.properties is missing '$key'")

android {
    namespace = "com.fabapps.video"
    compileSdk = 36

    defaultConfig {
        applicationId = prop("applicationId")
        minSdk = 24
        targetSdk = 36
        versionCode = prop("versionCode", "1").toInt()
        versionName = prop("versionName", "1.0.0")
        resValue("string", "app_name", prop("appName"))
        buildConfigField("String", "API_BASE_URL", "\"${prop("apiBaseUrl").trimEnd('/')}/\"")
        manifestPlaceholders["admobAppId"] = prop("admobAppId", "ca-app-pub-3940256099942544~3347511713")
        manifestPlaceholders["applovinSdkKey"] = appProps.getProperty("applovinSdkKey", "")
    }

    signingConfigs {
        create("release") {
            val ks = rootProject.file("keystore.properties")
            if (ks.isFile) {
                val p = Properties().apply { ks.inputStream().use(::load) }
                storeFile = rootProject.file(p.getProperty("storeFile"))
                storePassword = p.getProperty("storePassword")
                keyAlias = p.getProperty("keyAlias")
                keyPassword = p.getProperty("keyPassword")
            }
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
            if (rootProject.file("keystore.properties").isFile) signingConfig = signingConfigs.getByName("release")
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    buildFeatures {
        compose = true
        buildConfig = true
    }
}

kotlin {
    compilerOptions { jvmTarget.set(org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17) }
}

googleServices {
    missingGoogleServicesStrategy = com.google.gms.googleservices.GoogleServicesPlugin.MissingGoogleServicesStrategy.WARN
}

dependencies {
    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.core.splashscreen)
    implementation(libs.androidx.activity.compose)
    implementation(libs.androidx.lifecycle.runtime.compose)
    implementation(libs.androidx.lifecycle.viewmodel.compose)
    implementation(libs.androidx.navigation.compose)

    implementation(platform(libs.compose.bom))
    implementation(libs.compose.ui)
    implementation(libs.compose.ui.tooling.preview)
    implementation(libs.compose.material3)
    implementation(libs.compose.material.icons)
    debugImplementation(libs.compose.ui.tooling)

    implementation(libs.datastore.preferences)

    implementation(platform(libs.firebase.bom))
    implementation(libs.firebase.analytics)
    implementation(libs.firebase.messaging)

    // Ad networks: one FabAds module per network listed in adNetworks (app.properties).
    adNetworks.forEach { implementation("com.github.midnewswire.fabads-kotlin:$it:$fabAdsVersion") }
    implementation(libs.play.review)

    implementation(libs.okhttp)
    implementation(libs.kotlinx.serialization.json)
    implementation(libs.coroutines.play)
    implementation(libs.coil.compose)
    implementation(libs.coil.network)
    // Verifies the Ed25519 signature of license.lic (Android has Ed25519 built in only from API 33).
    implementation(libs.bouncycastle)
    implementation(libs.media3.exoplayer)
    implementation(libs.media3.hls)
    implementation(libs.media3.dash)
    implementation(libs.media3.ui)
    implementation(libs.media3.session)

    testImplementation(libs.junit)
}
