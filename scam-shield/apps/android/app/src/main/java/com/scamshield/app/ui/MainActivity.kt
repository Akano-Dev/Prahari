package com.scamshield.app.ui

import android.Manifest
import android.content.Intent
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.scamshield.app.call.CallContext
import com.scamshield.app.call.LiveAnalysisService
import com.scamshield.app.net.ApiClient
import kotlin.concurrent.thread

/**
 * Minimal control surface:
 *  1. Request the call/mic/notification permissions.
 *  2. Sign in to the backend.
 *  3. On an active call, START consented, speaker-mode live analysis.
 *  4. Paste content (SMS / WhatsApp / screenshot text) for one-shot analysis.
 *
 * The heavy lifting is in the call/stt/net packages; this Activity just wires
 * user consent to [LiveAnalysisService].
 */
class MainActivity : ComponentActivity() {
    private val api = ApiClient()

    private val permissions = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()) { /* handle denials in UI */ }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        permissions.launch(arrayOf(
            Manifest.permission.READ_PHONE_STATE,
            Manifest.permission.RECORD_AUDIO,
            Manifest.permission.READ_CONTACTS,
            Manifest.permission.POST_NOTIFICATIONS,
        ))
        setContent { MaterialTheme { Screen() } }
    }

    @Composable
    private fun Screen() {
        var email by remember { mutableStateOf("agent@scamshield.test") }
        var password by remember { mutableStateOf("supersecret1") }
        var status by remember { mutableStateOf("Not signed in") }
        var pasted by remember { mutableStateOf("") }
        var result by remember { mutableStateOf("") }

        Column(Modifier.fillMaxSize().padding(20.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Text("🛡 ScamShield", style = MaterialTheme.typography.headlineSmall)
            Text(status, style = MaterialTheme.typography.bodySmall)

            OutlinedTextField(email, { email = it }, label = { Text("Email") }, modifier = Modifier.fillMaxWidth())
            OutlinedTextField(password, { password = it }, label = { Text("Password") }, modifier = Modifier.fillMaxWidth())
            Button(onClick = {
                thread { runCatching { api.login(email, password) }
                    .onSuccess { status = "Signed in" }.onFailure { status = "Login failed: ${it.message}" } }
            }, modifier = Modifier.fillMaxWidth()) { Text("Sign in") }

            Divider()
            Text("Active call: ${CallContext.number} (${if (CallContext.isUnknown) "unknown" else "known"})")
            Button(onClick = { startProtectedAnalysis { status = it } }, modifier = Modifier.fillMaxWidth()) {
                Text("Start protected analysis (consent · use speaker)")
            }

            Divider()
            Text("Scan a message (SMS / WhatsApp / screenshot text)")
            OutlinedTextField(pasted, { pasted = it }, modifier = Modifier.fillMaxWidth().height(120.dp))
            Button(onClick = {
                thread { runCatching { api.analyzeBlock(pasted, "sms") }
                    .onSuccess { result = "Risk ${it.optInt("risk_score")}/100 — ${it.optString("recommendation")}" }
                    .onFailure { result = "Error: ${it.message}" } }
            }, modifier = Modifier.fillMaxWidth()) { Text("Scan") }
            if (result.isNotBlank()) Text(result)
        }
    }

    /** Create a backend call and start the foreground analysis service. */
    private fun startProtectedAnalysis(onStatus: (String) -> Unit) {
        val jwt = api.jwt ?: return onStatus("Sign in first")
        thread {
            runCatching { api.createCall(CallContext.number) }.onSuccess { callId ->
                startForegroundService(Intent(this, LiveAnalysisService::class.java).apply {
                    putExtra(LiveAnalysisService.EXTRA_JWT, jwt)
                    putExtra(LiveAnalysisService.EXTRA_CALL_ID, callId)
                })
                onStatus("Protecting call $callId")
            }.onFailure { onStatus("Could not start: ${it.message}") }
        }
    }
}
