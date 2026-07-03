package com.tidsignrn

import com.facebook.react.uimanager.SimpleViewManager
import com.facebook.react.uimanager.ThemedReactContext

class TidUnityAvatarViewManager : SimpleViewManager<TidUnityAvatarView>() {
  override fun getName(): String = "TidUnityAvatarView"

  override fun createViewInstance(reactContext: ThemedReactContext): TidUnityAvatarView =
    TidUnityAvatarView(reactContext)
}
