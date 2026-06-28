package com.scamshield.app.stt

import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer

/**
 * Wraps Android on-device [SpeechRecognizer] to emit a stream of recognized
 * phrases. It captures the device microphone — which, in speaker mode and with
 * the user's consent, includes the caller's audio. It cannot tap the protected
 * call stream directly (Android platform limitation).
 *
 * Each finalized phrase is delivered to [onPhrase] for streaming to the backend.
 * A production build would prefer a Whisper-based recognizer for Hindi/Hinglish
 * robustness; the interface here stays the same.
 */
class SpeechStreamer(
    private val context: Context,
    private val onPhrase: (String) -> Unit,
) {
    private var recognizer: SpeechRecognizer? = null

    fun start(language: String = "en-IN") {
        recognizer = SpeechRecognizer.createSpeechRecognizer(context).apply {
            setRecognitionListener(listener)
            startListening(buildIntent(language))
        }
    }

    private fun buildIntent(language: String) =
        Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
            putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL,
                RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
            putExtra(RecognizerIntent.EXTRA_LANGUAGE, language)
            putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, true)
        }

    private val listener = object : RecognitionListener {
        override fun onResults(results: Bundle) {
            results.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                ?.firstOrNull()?.let { if (it.isNotBlank()) onPhrase(it) }
            // Re-arm for continuous capture across the call.
            recognizer?.startListening(buildIntent("en-IN"))
        }
        override fun onPartialResults(partialResults: Bundle) {}
        override fun onError(error: Int) { recognizer?.startListening(buildIntent("en-IN")) }
        override fun onReadyForSpeech(params: Bundle?) {}
        override fun onBeginningOfSpeech() {}
        override fun onRmsChanged(rmsdB: Float) {}
        override fun onBufferReceived(buffer: ByteArray?) {}
        override fun onEndOfSpeech() {}
        override fun onEvent(eventType: Int, params: Bundle?) {}
    }

    fun stop() {
        recognizer?.destroy()
        recognizer = null
    }
}
