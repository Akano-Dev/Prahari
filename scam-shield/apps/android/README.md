# ScamShield Android App (scaffold)

Kotlin app that detects calls, runs **consented** on-device speech-to-text, and
streams the transcript to the backend over a WebSocket for live scam analysis,
warning the user with a high-priority notification.

> ⚠️ **Not compiled in this environment.** This is reviewed, structured Kotlin —
> open it in Android Studio (Giraffe+), let Gradle sync, and run on a device/emulator.

## The platform reality (important)

Since Android 10, third-party apps **cannot record the remote party of a phone
call** — the call-audio source is reserved for the system dialer. So ScamShield
does the only lawful, technically-possible thing:

1. **Detect** the call — `CallDetectionService` (`CallScreeningService`) +
   `CallStateReceiver` (number, unknown-caller flag, duration).
2. **Ask for consent** and prompt the user to switch to **speaker**.
3. **Capture mic audio** (which, on speaker, includes the caller) and run on-device
   STT — `SpeechStreamer` (`SpeechRecognizer`).
4. **Stream + warn** — `AnalysisSocket` (OkHttp WebSocket → `/ws/calls/{id}`),
   `LiveAnalysisService` (foreground), `RiskNotifier` (heads-up alert).

We never claim to silently tap a call. Call-recording legality varies by region;
consent is explicit and the foreground notification is always visible.

## Source map (`app/src/main/java/com/scamshield/app/`)
| File | Role |
|---|---|
| `call/CallDetectionService.kt` | Screen incoming calls, capture caller id |
| `call/CallStateReceiver.kt` | Call lifecycle + shared `CallContext` |
| `call/LiveAnalysisService.kt` | Foreground: STT → WS → notification |
| `stt/SpeechStreamer.kt` | On-device speech-to-text stream |
| `net/AnalysisSocket.kt` | WebSocket transcript streaming |
| `net/ApiClient.kt` | REST: auth, create call, upload-scan |
| `notify/RiskNotifier.kt` | High-priority scam-risk notification |
| `ui/MainActivity.kt` | Sign-in, consent, paste-to-scan uploads |

## Also supported (uploads → `/analyze`)
SMS scanning, screenshot text, WhatsApp chat export, and voice-recording
transcripts all post to the same explainable analysis endpoint via `ApiClient`.

Set the backend in `app/build.gradle.kts` (`API_BASE` / `WS_BASE`). `10.0.2.2`
is the host machine from the Android emulator.
