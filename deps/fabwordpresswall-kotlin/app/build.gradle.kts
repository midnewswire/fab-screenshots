import java.util.Properties

plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
    alias(libs.plugins.kotlin.compose)
    alias(libs.plugins.kotlin.serialization)
    alias(libs.plugins.ksp)
    alias(libs.plugins.google.services)
    alias(libs.plugins.firebase.crashlytics)
}

/**
 * Your app's identity lives in app.properties at the project root (package name, name, version, ad SDK ids,
 * optional remote config link). Repositories, ads, theme and links are in app/src/main/assets/config.json.
 */
val appProps = Properties().apply {
    val f = rootProject.file("app.properties")
    check(f.isFile) { "app.properties is missing in the project root" }
    f.inputStream().use(::load)
}

fun prop(key: String, default: String? = null): String =
    appProps.getProperty(key)?.trim()?.takeIf { it.isNotEmpty() } ?: default ?: error("app.properties is missing '$key'")

android {
    namespace = "com.fabapps.wordpresswall"
    compileSdk = 36

    defaultConfig {
        applicationId = prop("applicationId")
        minSdk = 26
        targetSdk = 36
        versionCode = prop("versionCode", "1").toInt()
        versionName = prop("versionName", "1.0.0")
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
        resValue("string", "app_name", prop("appName"))
        buildConfigField("String", "REMOTE_CONFIG_URL", "\"${prop("remoteConfigUrl", "")}\"")
        // Ad SDK app ids must be in the manifest at build time; ad unit ids are in config.json.
        manifestPlaceholders["admobAppId"] = prop("admobAppId", "ca-app-pub-3940256099942544~3347511713")
        manifestPlaceholders["applovinSdkKey"] = prop("applovinSdkKey", "")
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

ksp {
    arg("room.schemaLocation", "$projectDir/schemas")
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
    implementation(libs.androidx.lifecycle.process)
    implementation(libs.androidx.navigation.compose)

    implementation(platform(libs.compose.bom))
    implementation(libs.compose.ui)
    implementation(libs.compose.ui.tooling.preview)
    implementation(libs.compose.material3)
    implementation(libs.compose.material.icons)
    debugImplementation(libs.compose.ui.tooling)

    implementation(libs.room.runtime)
    implementation(libs.room.ktx)
    ksp(libs.room.compiler)
    implementation(libs.work.runtime)
    implementation(libs.paging.runtime)
    implementation(libs.paging.compose)
    implementation(libs.datastore.preferences)
    implementation(libs.glance.appwidget)
    implementation(libs.glance.material3)
    implementation(libs.media3.exoplayer)
    implementation(libs.media3.ui)
    implementation(libs.biometric)
    implementation(libs.palette)

    implementation(platform(libs.firebase.bom))
    implementation(libs.firebase.analytics)
    implementation(libs.firebase.messaging)
    implementation(libs.firebase.crashlytics)

    implementation(libs.play.ads)
    implementation(libs.ump)
    implementation(libs.applovin)
    implementation(libs.meta.audience)
    implementation(libs.unity.ads)
    implementation(libs.startapp)
    implementation(libs.play.review)
    implementation(libs.play.app.update)

    implementation(libs.okhttp)
    implementation(libs.okhttp.logging)
    implementation(libs.kotlinx.serialization.json)
    // Verifies the Ed25519 signature of license.lic (Android has Ed25519 built in only from API 33).
    implementation(libs.bouncycastle)
    implementation(libs.coroutines.play)
    implementation(libs.coil.compose)
    implementation(libs.coil.network)
    implementation(libs.coil.gif)

    testImplementation(libs.junit)
}
