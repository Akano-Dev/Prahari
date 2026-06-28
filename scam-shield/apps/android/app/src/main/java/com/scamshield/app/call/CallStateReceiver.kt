package com.scamshield.app.call

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.telephony.TelephonyManager

/**
 * Tracks call lifecycle (ringing → off-hook → idle) so the app knows a call is in
 * progress and can show the live duration + offer to start analysis. Also a simple
 * shared holder ([CallContext]) for the current call's metadata.
 */
object CallContext {
    @Volatile var number: String = "unknown"
    @Volatile var isUnknown: Boolean = true
    @Volatile var startedAtMs: Long = 0L
    fun update(number: String? = null, unknown: Boolean? = null) {
        number?.let { this.number = it }
        unknown?.let { this.isUnknown = it }
    }
    fun durationSeconds(): Long =
        if (startedAtMs == 0L) 0 else (System.currentTimeMillis() - startedAtMs) / 1000
}

class CallStateReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        when (intent.getStringExtra(TelephonyManager.EXTRA_STATE)) {
            TelephonyManager.EXTRA_STATE_RINGING ->
                intent.getStringExtra(TelephonyManager.EXTRA_INCOMING_NUMBER)
                    ?.let { CallContext.update(number = it) }
            TelephonyManager.EXTRA_STATE_OFFHOOK -> {
                CallContext.startedAtMs = System.currentTimeMillis()
                // The UI prompts the user; on consent it starts LiveAnalysisService.
            }
            TelephonyManager.EXTRA_STATE_IDLE -> {
                CallContext.startedAtMs = 0L
                context.stopService(Intent(context, LiveAnalysisService::class.java))
            }
        }
    }
}
