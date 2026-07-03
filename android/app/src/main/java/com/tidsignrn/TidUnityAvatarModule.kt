package com.tidsignrn

import android.os.Handler
import android.os.Looper
import com.facebook.react.bridge.Promise
import com.facebook.react.bridge.ReactApplicationContext
import com.facebook.react.bridge.ReactContextBaseJavaModule
import com.facebook.react.bridge.ReactMethod

class TidUnityAvatarModule(
  private val reactContext: ReactApplicationContext
) : ReactContextBaseJavaModule(reactContext) {
  override fun getName(): String = "TidUnityAvatar"

  @ReactMethod
  fun isAvailable(promise: Promise) {
    promise.resolve(TidUnityHost.isAvailable())
  }

  @ReactMethod
  fun open(promise: Promise) {
    promise.resolve(TidUnityHost.isReady())
  }

  @ReactMethod
  fun playGlosses(glossCsv: String, promise: Promise) {
    Handler(Looper.getMainLooper()).post {
      promise.resolve(TidUnityHost.playGlossCsv(glossCsv))
    }
  }

  @ReactMethod
  fun playText(text: String, promise: Promise) {
    Handler(Looper.getMainLooper()).post {
      promise.resolve(TidUnityHost.playText(text))
    }
  }

  @ReactMethod
  fun stop(promise: Promise) {
    Handler(Looper.getMainLooper()).post {
      promise.resolve(TidUnityHost.stop())
    }
  }
}
