package com.scamshield.app.notify

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.content.Context
import androidx.core.app.NotificationCompat

/**
 * Posts a high-priority, heads-up notification when the live risk crosses a
 * danger threshold during a call — the user's primary in-call warning.
 */
class RiskNotifier(private val context: Context) {
    init {
        val mgr = context.getSystemService(NotificationManager::class.java)
        mgr.createNotificationChannel(
            NotificationChannel(CHANNEL, "Scam alerts", NotificationManager.IMPORTANCE_HIGH)
                .apply { description = "Warns you when a call looks like a scam." })
    }

    fun showRisk(score: Int, scamType: String?, recommendation: String) {
        val title = when {
            score >= 75 -> "⚠ Almost certainly a scam ($score/100)"
            score >= 50 -> "⚠ Likely scam ($score/100)"
            else -> "Possible scam ($score/100)"
        }
        val text = buildString {
            scamType?.let { append("Type: $it. ") }
            append(recommendation)
        }
        val notif: Notification = NotificationCompat.Builder(context, CHANNEL)
            .setSmallIcon(android.R.drawable.ic_dialog_alert)
            .setContentTitle(title)
            .setContentText(text)
            .setStyle(NotificationCompat.BigTextStyle().bigText(text))
            .setPriority(NotificationCompat.PRIORITY_MAX)
            .setCategory(NotificationCompat.CATEGORY_CALL)
            .setOngoing(score >= 75)
            .build()
        context.getSystemService(NotificationManager::class.java).notify(NOTIF_ID, notif)
    }

    companion object {
        private const val CHANNEL = "scam_alerts"
        private const val NOTIF_ID = 4711
    }
}
