package com.scamshield.app.net

import com.scamshield.app.BuildConfig
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject

/**
 * REST calls to the ScamShield backend: auth, call creation, and one-shot
 * analysis of uploaded content (SMS / screenshot OCR text / WhatsApp export /
 * voice transcript). All blocking; call from a background dispatcher.
 */
class ApiClient(var jwt: String? = null) {
    private val client = OkHttpClient()
    private val json = "application/json".toMediaType()

    private fun post(path: String, body: JSONObject, auth: Boolean = true): JSONObject {
        val builder = Request.Builder()
            .url("${BuildConfig.API_BASE}$path")
            .post(body.toString().toRequestBody(json))
        if (auth) jwt?.let { builder.header("Authorization", "Bearer $it") }
        client.newCall(builder.build()).execute().use { resp ->
            val text = resp.body?.string().orEmpty()
            return if (text.isBlank()) JSONObject() else JSONObject(text)
        }
    }

    fun login(email: String, password: String): String {
        runCatching { post("/auth/register",
            JSONObject().put("email", email).put("password", password), auth = false) }
        val r = post("/auth/login",
            JSONObject().put("email", email).put("password", password), auth = false)
        return r.getString("access_token").also { jwt = it }
    }

    fun createCall(callerNumber: String): String =
        post("/calls", JSONObject().put("caller_number", callerNumber)).getString("id")

    /** Analyse a block of text from SMS/screenshot/WhatsApp/voice. */
    fun analyzeBlock(text: String, source: String): JSONObject =
        post("/analyze", JSONObject().put("text", text).put("source", source))
}
