package com.tidsignrn

import com.facebook.react.bridge.Promise
import com.facebook.react.bridge.ReactApplicationContext
import com.facebook.react.bridge.ReactContextBaseJavaModule
import com.facebook.react.bridge.ReactMethod

class TidUnityAvatarModule(
  reactContext: ReactApplicationContext
) : ReactContextBaseJavaModule(reactContext) {
  override fun getName(): String = "TidUnityAvatar"

  @ReactMethod
  fun isAvailable(promise: Promise) {
    promise.resolve(false)
  }

  @ReactMethod
  fun open(promise: Promise) {
    promise.resolve(false)
  }

  @ReactMethod
  fun playGlosses(glossCsv: String, promise: Promise) {
    promise.resolve(false)
  }

  @ReactMethod
  fun playText(text: String, promise: Promise) {
    promise.resolve(false)
  }

  @ReactMethod
  fun stop(promise: Promise) {
    promise.resolve(false)
  }
}
