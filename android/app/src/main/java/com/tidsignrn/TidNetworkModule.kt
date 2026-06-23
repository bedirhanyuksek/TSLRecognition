package com.tidsignrn

import android.content.Context
import android.net.ConnectivityManager
import android.net.NetworkCapabilities
import android.net.wifi.WifiManager
import com.facebook.react.bridge.Promise
import com.facebook.react.bridge.ReactApplicationContext
import com.facebook.react.bridge.ReactContextBaseJavaModule
import com.facebook.react.bridge.ReactMethod
import java.net.Inet4Address
import java.net.NetworkInterface

class TidNetworkModule(
  private val reactContext: ReactApplicationContext
) : ReactContextBaseJavaModule(reactContext) {
  override fun getName(): String = "TidNetwork"

  @ReactMethod
  fun getWifiIpAddress(promise: Promise) {
    try {
      val connectivityManager =
        reactContext.getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
      val activeNetwork = connectivityManager.activeNetwork
      val capabilities = connectivityManager.getNetworkCapabilities(activeNetwork)
      val isWifi = capabilities?.hasTransport(NetworkCapabilities.TRANSPORT_WIFI) == true
      if (!isWifi) {
        promise.resolve(null)
        return
      }

      val wifiIp = getWifiManagerIpAddress()
      if (wifiIp != null) {
        promise.resolve(wifiIp)
        return
      }

      promise.resolve(getNetworkInterfaceIpAddress())
    } catch (error: Exception) {
      promise.reject("TID_NETWORK_IP_ERROR", error.message, error)
    }
  }

  private fun getWifiManagerIpAddress(): String? {
    val wifiManager =
      reactContext.applicationContext.getSystemService(Context.WIFI_SERVICE) as WifiManager
    val ipAddress = wifiManager.connectionInfo.ipAddress
    if (ipAddress == 0) {
      return null
    }
    return listOf(
      ipAddress and 0xff,
      ipAddress shr 8 and 0xff,
      ipAddress shr 16 and 0xff,
      ipAddress shr 24 and 0xff
    ).joinToString(".")
  }

  private fun getNetworkInterfaceIpAddress(): String? {
    val interfaces = NetworkInterface.getNetworkInterfaces()
    for (networkInterface in interfaces) {
      if (!networkInterface.isUp || networkInterface.isLoopback) {
        continue
      }
      val addresses = networkInterface.inetAddresses
      for (address in addresses) {
        if (address is Inet4Address && !address.isLoopbackAddress) {
          return address.hostAddress
        }
      }
    }
    return null
  }
}
