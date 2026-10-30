package com.fabapps.livetvflutter

import android.app.PictureInPictureParams
import android.content.pm.PackageManager
import android.content.res.Configuration
import android.os.Build
import android.util.Rational
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

/** Adds picture-in-picture for the player (lib/player/pip.dart). */
class MainActivity : FlutterActivity() {
    private var pip: MethodChannel? = null
    private var autoEnter = false

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        pip = MethodChannel(flutterEngine.dartExecutor.binaryMessenger, "fab_live_tv/pip").apply {
            setMethodCallHandler { call, result ->
                when (call.method) {
                    "available" -> result.success(supported())
                    "enter" -> result.success(enter())
                    "autoEnter" -> {
                        autoEnter = call.arguments == true
                        if (supported()) setPictureInPictureParams(params())
                        result.success(null)
                    }
                    else -> result.notImplemented()
                }
            }
        }
    }

    private fun supported() =
        Build.VERSION.SDK_INT >= Build.VERSION_CODES.O && packageManager.hasSystemFeature(PackageManager.FEATURE_PICTURE_IN_PICTURE)

    private fun params(): PictureInPictureParams {
        val builder = PictureInPictureParams.Builder().setAspectRatio(Rational(16, 9))
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) builder.setAutoEnterEnabled(autoEnter).setSeamlessResizeEnabled(true)
        return builder.build()
    }

    private fun enter(): Boolean {
        if (!supported()) return false
        return runCatching { enterPictureInPictureMode(params()) }.getOrDefault(false)
    }

    // Android 12+ enters by itself (setAutoEnterEnabled); older versions need this.
    override fun onUserLeaveHint() {
        super.onUserLeaveHint()
        if (autoEnter && Build.VERSION.SDK_INT < Build.VERSION_CODES.S) enter()
    }

    override fun onPictureInPictureModeChanged(isInPictureInPictureMode: Boolean, newConfig: Configuration) {
        super.onPictureInPictureModeChanged(isInPictureInPictureMode, newConfig)
        pip?.invokeMethod("changed", isInPictureInPictureMode)
    }
}
