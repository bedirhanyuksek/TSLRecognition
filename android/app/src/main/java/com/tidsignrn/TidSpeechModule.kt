package com.tidsignrn

import android.speech.tts.TextToSpeech
import com.facebook.react.bridge.Promise
import com.facebook.react.bridge.ReactApplicationContext
import com.facebook.react.bridge.ReactContextBaseJavaModule
import com.facebook.react.bridge.ReactMethod
import java.util.Locale

class TidSpeechModule(private val reactContext: ReactApplicationContext) :
  ReactContextBaseJavaModule(reactContext), TextToSpeech.OnInitListener {

  private var tts: TextToSpeech? = null
  private var ready = false

  init {
    tts = TextToSpeech(reactContext, this)
  }

  override fun getName(): String = "TidSpeech"

  override fun onInit(status: Int) {
    if (status == TextToSpeech.SUCCESS) {
      val result = tts?.setLanguage(Locale("tr", "TR"))
      ready = result != TextToSpeech.LANG_MISSING_DATA &&
        result != TextToSpeech.LANG_NOT_SUPPORTED
      tts?.setSpeechRate(0.92f)
      tts?.setPitch(1.0f)
    }
  }

  @ReactMethod
  fun speak(text: String, promise: Promise) {
    val cleanText = text.trim()

    if (cleanText.isEmpty()) {
      promise.reject("empty_text", "Okunacak metin bos.")
      return
    }

    if (!ready) {
      promise.reject("tts_not_ready", "TextToSpeech hazir degil veya tr-TR desteklenmiyor.")
      return
    }

    tts?.speak(cleanText, TextToSpeech.QUEUE_FLUSH, null, "tid-speech")
    promise.resolve(true)
  }

  @ReactMethod
  fun stop() {
    tts?.stop()
  }

  override fun invalidate() {
    tts?.stop()
    tts?.shutdown()
    tts = null
    super.invalidate()
  }
}
