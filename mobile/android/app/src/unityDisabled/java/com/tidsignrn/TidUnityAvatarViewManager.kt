package com.tidsignrn

import android.widget.FrameLayout
import com.facebook.react.uimanager.SimpleViewManager
import com.facebook.react.uimanager.ThemedReactContext

class TidUnityAvatarViewManager : SimpleViewManager<FrameLayout>() {
  override fun getName(): String = "TidUnityAvatarView"

  override fun createViewInstance(reactContext: ThemedReactContext): FrameLayout =
    FrameLayout(reactContext)
}
