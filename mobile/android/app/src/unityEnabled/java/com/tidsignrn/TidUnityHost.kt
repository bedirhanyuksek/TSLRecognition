package com.tidsignrn

import android.app.Activity
import android.util.Log
import android.view.View
import com.unity3d.player.IUnityPlayerLifecycleEvents
import com.unity3d.player.UnityPlayer
import com.unity3d.player.UnityPlayerForActivityOrService

object TidUnityHost : IUnityPlayerLifecycleEvents {
  private var unityPlayer: UnityPlayerForActivityOrService? = null
  private var unityView: View? = null

  fun isAvailable(): Boolean = try {
    Class.forName("com.unity3d.player.UnityPlayerForActivityOrService")
    true
  } catch (_: ClassNotFoundException) {
    false
  }

  fun isReady(): Boolean = unityPlayer != null && unityView != null

  fun ensure(activity: Activity): View {
    val existingView = unityView
    if (existingView != null) {
      Log.i("TidUnity", "Reusing Unity player view")
      UnityPlayer.currentActivity = activity
      unityPlayer?.onResume()
      unityPlayer?.windowFocusChanged(true)
      return existingView
    }

    Log.i("TidUnity", "Creating UnityPlayerForActivityOrService")
    loadUnityNativeLibraries()
    UnityPlayer.currentActivity = activity
    val player = UnityPlayerForActivityOrService(activity, this)
    unityPlayer = player
    unityView = player.view
    player.view.requestFocus()
    player.onStart()
    player.onResume()
    player.windowFocusChanged(true)
    Log.i("TidUnity", "Unity player created; view=${player.view.javaClass.name}")
    return player.view
  }

  fun resumeAndFocus() {
    unityPlayer?.onResume()
    unityPlayer?.windowFocusChanged(true)
    unityView?.requestFocus()
  }

  fun playGlossCsv(glossCsv: String): Boolean {
    Log.i("TidUnity", "playGlossCsv ready=${isReady()} payload=$glossCsv")
    if (!isReady()) {
      return false
    }

    UnityPlayer.UnitySendMessage("UnityAppBridge", "PlayGlossCsv", glossCsv)
    return true
  }

  fun playText(text: String): Boolean {
    Log.i("TidUnity", "playText ready=${isReady()} payload=$text")
    if (!isReady()) {
      return false
    }

    UnityPlayer.UnitySendMessage("UnityAppBridge", "PlayText", text)
    return true
  }

  fun stop(): Boolean {
    Log.i("TidUnity", "stop ready=${isReady()}")
    if (!isReady()) {
      return false
    }

    UnityPlayer.UnitySendMessage("UnityAppBridge", "Stop", "")
    return true
  }

  override fun onUnityPlayerUnloaded() {
    Log.i("TidUnity", "onUnityPlayerUnloaded")
    unityPlayer = null
    unityView = null
  }

  override fun onUnityPlayerQuitted() {
    Log.i("TidUnity", "onUnityPlayerQuitted")
    unityPlayer = null
    unityView = null
  }

  private fun loadUnityNativeLibraries() {
    listOf("game", "main", "unity").forEach { library ->
      try {
        System.loadLibrary(library)
        Log.i("TidUnity", "Loaded library $library")
      } catch (error: UnsatisfiedLinkError) {
        Log.w("TidUnity", "Library $library not loaded: ${error.message}")
      }
    }
  }
}
