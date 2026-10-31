package com.fabapps.tubeflutter

import android.content.pm.PackageManager
import android.os.Build
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel
import java.security.MessageDigest

/**
 * Tells the app the SHA-1 of the certificate it was signed with (lib/data/youtube_api.dart sends it to YouTube), so
 * the API key can be restricted to this Android app in Google Cloud.
 */
class MainActivity : FlutterActivity() {
    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, "fab_tube/app").setMethodCallHandler { call, result ->
            when (call.method) {
                "signature" -> result.success(signingSha1())
                else -> result.notImplemented()
            }
        }
    }

    @Suppress("DEPRECATION")
    private fun signingSha1(): String = runCatching {
        val signatures = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
            packageManager.getPackageInfo(packageName, PackageManager.GET_SIGNING_CERTIFICATES).signingInfo?.apkContentsSigners
        } else {
            packageManager.getPackageInfo(packageName, PackageManager.GET_SIGNATURES).signatures
        }
        val cert = signatures?.firstOrNull()?.toByteArray() ?: return@runCatching ""
        MessageDigest.getInstance("SHA-1").digest(cert).joinToString("") { "%02X".format(it) }
    }.getOrDefault("")
}
