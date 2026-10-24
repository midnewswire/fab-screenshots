# kotlinx.serialization
-keepattributes *Annotation*, InnerClasses
-dontnote kotlinx.serialization.AnnotationsKt
-keepclassmembers @kotlinx.serialization.Serializable class com.fabapps.recipes.** {
    *** Companion;
    kotlinx.serialization.KSerializer serializer(...);
}
-keep,includedescriptorclasses class com.fabapps.recipes.**$$serializer { *; }

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

