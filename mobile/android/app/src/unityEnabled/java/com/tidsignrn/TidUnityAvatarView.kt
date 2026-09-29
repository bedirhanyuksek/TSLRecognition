package com.tidsignrn

import android.util.Log
import android.view.Gravity
import android.view.SurfaceView
import android.view.View
import android.view.ViewGroup
import android.widget.FrameLayout
import com.facebook.react.uimanager.ThemedReactContext

class TidUnityAvatarView(
  private val reactContext: ThemedReactContext
) : FrameLayout(reactContext) {
  init {
    Log.i("TidUnity", "TidUnityAvatarView init")
    setBackgroundColor(0x00000000)
  }

  override fun onAttachedToWindow() {
    super.onAttachedToWindow()
    Log.i("TidUnity", "TidUnityAvatarView attached")
    attachUnityView()
  }

  override fun onSizeChanged(w: Int, h: Int, oldw: Int, oldh: Int) {
    super.onSizeChanged(w, h, oldw, oldh)
    Log.i("TidUnity", "TidUnityAvatarView size $w x $h")
    attachUnityView()
  }

  private fun attachUnityView() {
    val activity = reactContext.currentActivity
    if (activity == null) {
      Log.w("TidUnity", "attachUnityView skipped: currentActivity is null")
      return
    }

    if (width <= 0 || height <= 0) {
      Log.w("TidUnity", "attachUnityView delayed: size is ${width}x${height}")
      return
    }

    Log.i("TidUnity", "attachUnityView starting")
    val view = TidUnityHost.ensure(activity)
    val parent = view.parent
    if (parent is FrameLayout && parent !== this) {
      Log.i("TidUnity", "Removing Unity view from old parent")
      parent.removeView(view)
    }

    if (view.parent == null) {
      addView(
        view,
        LayoutParams(LayoutParams.MATCH_PARENT, LayoutParams.MATCH_PARENT, Gravity.CENTER)
      )
      Log.i("TidUnity", "Unity view added")
    } else {
      Log.i("TidUnity", "Unity view already has this parent")
    }

    view.visibility = View.VISIBLE
    view.requestFocus()
    forceUnityLayout(view)
    configureUnitySurface(view)
    TidUnityHost.resumeAndFocus()
    postDelayed({
      Log.i("TidUnity", "post-layout Unity size ${view.width}x${view.height}")
      forceUnityLayout(view)
      configureUnitySurface(view)
      TidUnityHost.resumeAndFocus()
    }, 500)
    postDelayed({
      Log.i("TidUnity", "late Unity size ${view.width}x${view.height}")
      forceUnityLayout(view)
      TidUnityHost.resumeAndFocus()
    }, 1500)
  }

  private fun forceUnityLayout(view: View) {
    if (width <= 0 || height <= 0) {
      return
    }
    val widthSpec = MeasureSpec.makeMeasureSpec(width, MeasureSpec.EXACTLY)
    val heightSpec = MeasureSpec.makeMeasureSpec(height, MeasureSpec.EXACTLY)
    view.measure(widthSpec, heightSpec)
    view.layout(0, 0, width, height)
    view.requestLayout()
    Log.i("TidUnity", "forceUnityLayout parent=${width}x${height} child=${view.width}x${view.height}")
  }

  private fun configureUnitySurface(root: View) {
    Log.i("TidUnity", "Unity root hierarchy:\n${describeView(root)}")
    forEachView(root) { child ->
      if (child is SurfaceView) {
        Log.i("TidUnity", "Configuring Unity SurfaceView z-order: ${child.javaClass.name}")
        child.setZOrderMediaOverlay(true)
        child.setZOrderOnTop(true)
        child.visibility = View.VISIBLE
      }
    }
  }

  private fun forEachView(view: View, action: (View) -> Unit) {
    action(view)
    if (view is ViewGroup) {
      for (index in 0 until view.childCount) {
        forEachView(view.getChildAt(index), action)
      }
    }
  }

  private fun describeView(view: View, depth: Int = 0): String {
    val indent = "  ".repeat(depth)
    val builder = StringBuilder()
    builder.append(indent)
      .append(view.javaClass.name)
      .append(" ")
      .append(view.width)
      .append("x")
      .append(view.height)
      .append(" vis=")
      .append(view.visibility)
      .append('\n')
    if (view is ViewGroup) {
      for (index in 0 until view.childCount) {
        builder.append(describeView(view.getChildAt(index), depth + 1))
      }
    }
    return builder.toString()
  }
}
