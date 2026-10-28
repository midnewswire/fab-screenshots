# kotlinx.serialization
-keepattributes *Annotation*, InnerClasses
-dontnote kotlinx.serialization.AnnotationsKt
-keepclassmembers @kotlinx.serialization.Serializable class com.fabapps.webview.** {
    *** Companion;
    kotlinx.serialization.KSerializer serializer(...);
}
-keep,includedescriptorclasses class com.fabapps.webview.**$$serializer { *; }

# AppLovin
-keep class com.applovin.** { *; }
-dontwarn com.applovin.**

# Meta Audience Network, Unity Ads, Start.io
-keep class com.facebook.ads.** { *; }
-dontwarn com.facebook.ads.**
-keep class com.unity3d.** { *; }
-dontwarn com.unity3d.**
-keep class com.startapp.** { *; }
-dontwarn com.startapp.**
# JavaScript bridge used by pages loaded in the WebView
-keepclassmembers class com.fabapps.webview.web.JsBridge {
    @android.webkit.JavascriptInterface <methods>;
}

# License check (BouncyCastle lightweight API only; the JCA provider parts are unused)
-dontwarn org.bouncycastle.**
