package com.scamshield.app.call

import android.telecom.Call
import android.telecom.CallScreeningService
import android.util.Log

/**
 * Screens incoming calls. We do NOT block calls; we use screening purely to learn
 * about the call early (number, whether it is an unknown caller) and to offer the
 * user the option to start consented, speaker-mode live analysis.
 *
 * Platform reality: a CallScreeningService cannot access call audio. Audio capture
 * happens only after the user consents and switches to speaker (see
 * [LiveAnalysisService] + [SpeechStreamer]).
 */
class CallDetectionService : CallScreeningService() {
    override fun onScreenCall(callDetails: Call.Details) {
        val handle = callDetails.handle?.schemeSpecificPart ?: "unknown"
        val isUnknown = callDetails.callerNumberVerificationStatus !=
            Call.Details.CALLER_NUMBER_VERIFICATION_STATUS_PASSED
        Log.i(TAG, "Incoming call from $handle (unknown=$isUnknown)")

        // Allow the call through unchanged; the UI/notification offers analysis.
        respondToCall(callDetails, CallResponse.Builder().build())
        CallContext.update(number = handle, unknown = isUnknown)
    }

    companion object { private const val TAG = "ScamShieldScreen" }
}
