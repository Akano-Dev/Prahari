package com.scamshield.app.net

import com.scamshield.app.BuildConfig
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.WebSocket
import okhttp3.WebSocketListener
import org.json.JSONObject

/**
 * Streams transcript chunks to the backend over a WebSocket and surfaces the live
 * risk assessment back to the caller. One socket per active call.
 *
 *   AnalysisSocket(token, callId) { assessment -> ... }.also { it.connect() }
 *   socket.sendTranscript("you are under digital arrest")
 */
class AnalysisSocket(
    private val jwt: String,
    private val callId: String,
    private val onAssessment: (JSONObject) -> Unit,
) {
    private val client = OkHttpClient()
    private var ws: WebSocket? = null

    fun connect() {
        val url = "${BuildConfig.WS_BASE}/ws/calls/$callId?token=$jwt"
        val request = Request.Builder().url(url).build()
        ws = client.newWebSocket(request, object : WebSocketListener() {
            override fun onMessage(webSocket: WebSocket, text: String) {
                runCatching { onAssessment(JSONObject(text)) }
            }
        })
    }

    fun sendTranscript(text: String) {
        ws?.send(JSONObject().put("text", text).toString())
    }

    fun close() {
        ws?.close(1000, "call ended")
        ws = null
    }
}
