package com.scamshield.app.call

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Intent
import android.os.IBinder
import androidx.core.app.NotificationCompat
import com.scamshield.app.net.AnalysisSocket
import com.scamshield.app.notify.RiskNotifier
import com.scamshield.app.stt.SpeechStreamer

/**
 * Foreground service that ties the pieces together for an active, consented call:
 * mic STT → WebSocket → live risk → notification. Started only after the user
 * consents to analysis (and is told to switch to speaker). Stopped when the call
 * ends ([CallStateReceiver]).
 *
 * Expects a JWT and a backend callId via the start Intent extras.
 */
class LiveAnalysisService : Service() {
    private var socket: AnalysisSocket? = null
    private var stt: SpeechStreamer? = null
    private lateinit var notifier: RiskNotifier

    override fun onCreate() {
        super.onCreate()
        notifier = RiskNotifier(this)
        startForeground(FG_ID, buildForegroundNotification())
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        val jwt = intent?.getStringExtra(EXTRA_JWT) ?: return START_NOT_STICKY
        val callId = intent.getStringExtra(EXTRA_CALL_ID) ?: return START_NOT_STICKY

        socket = AnalysisSocket(jwt, callId) { assessment ->
            val score = assessment.optInt("risk_score")
            if (score >= 50) {
                val scamType = assessment.optJSONObject("top_scam_type")?.optString("label")
                notifier.showRisk(score, scamType, assessment.optString("recommendation"))
            }
        }.also { it.connect() }

        stt = SpeechStreamer(this) { phrase -> socket?.sendTranscript(phrase) }
            .also { it.start(language = "en-IN") }
        return START_STICKY
    }

    override fun onDestroy() {
        stt?.stop(); socket?.close()
        super.onDestroy()
    }

    override fun onBind(intent: Intent?): IBinder? = null

    private fun buildForegroundNotification(): Notification {
        val mgr = getSystemService(NotificationManager::class.java)
        mgr.createNotificationChannel(
            NotificationChannel(FG_CHANNEL, "Live call analysis",
                NotificationManager.IMPORTANCE_LOW))
        return NotificationCompat.Builder(this, FG_CHANNEL)
            .setSmallIcon(android.R.drawable.ic_menu_call)
            .setContentTitle("ScamShield is protecting this call")
            .setContentText("Analyzing speaker audio with your consent.")
            .setOngoing(true)
            .build()
    }

    companion object {
        const val EXTRA_JWT = "jwt"
        const val EXTRA_CALL_ID = "callId"
        private const val FG_CHANNEL = "live_analysis"
        private const val FG_ID = 4710
    }
}
