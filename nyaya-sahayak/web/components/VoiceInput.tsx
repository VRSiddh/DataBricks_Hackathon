"use client";

import { useCallback, useRef, useState } from "react";
import { getApiBase } from "@/lib/apiBase";

/* ── Types ─────────────────────────────────────────────────────── */

interface Props {
  /** BCP-47 language tag, e.g. "hi-IN", "en-IN" */
  language: string;
  onTranscript: (text: string) => void;
  disabled?: boolean;
}

/* ── Component ──────────────────────────────────────────────────── */

export default function VoiceInput({ language, onTranscript, disabled }: Props) {
  const base = getApiBase();
  const [listening, setListening] = useState(false);
  const [processing, setProcessing] = useState(false);
  const mediaRecRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const toggle = useCallback(async () => {
    // Stop recording
    if (listening && mediaRecRef.current) {
      mediaRecRef.current.stop();
      setListening(false);
      return;
    }

    // Start recording
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

      // Prefer WebM (Chrome/Firefox), fall back to whatever is available
      const mimeType = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
        ? "audio/webm;codecs=opus"
        : MediaRecorder.isTypeSupported("audio/webm")
        ? "audio/webm"
        : MediaRecorder.isTypeSupported("audio/mp4")
        ? "audio/mp4"
        : "";

      const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : {});
      chunksRef.current = [];

      recorder.ondataavailable = (e: BlobEvent) => {
        if (e.data.size > 0) {
          chunksRef.current.push(e.data);
        }
      };

      recorder.onstop = async () => {
        // Stop all tracks
        stream.getTracks().forEach((t) => t.stop());

        const audioBlob = new Blob(chunksRef.current, {
          type: mimeType || "audio/webm",
        });

        if (audioBlob.size < 100) {
          return; // too short, ignore
        }

        setProcessing(true);

        try {
          // Send to Sarvam STT backend
          const formData = new FormData();
          formData.append("file", audioBlob, "recording.webm");
          formData.append("language", language);

          const resp = await fetch(`${base}/api/stt`, {
            method: "POST",
            body: formData,
          });

          if (resp.ok) {
            const data = await resp.json();
            if (data.transcript && data.transcript.trim()) {
              onTranscript(data.transcript.trim());
            } else if (data.fallback === "browser") {
              // Backend says use browser fallback
              fallbackBrowserSTT(audioBlob);
            }
          } else {
            // If backend STT fails, try browser Web Speech API as fallback
            console.warn("Sarvam STT failed, trying browser fallback");
            fallbackBrowserSTT(audioBlob);
          }
        } catch (err) {
          console.error("STT request failed:", err);
          fallbackBrowserSTT(audioBlob);
        } finally {
          setProcessing(false);
        }
      };

      recorder.onerror = () => {
        stream.getTracks().forEach((t) => t.stop());
        setListening(false);
      };

      mediaRecRef.current = recorder;
      recorder.start(250); // collect chunks every 250ms
      setListening(true);
    } catch (err) {
      console.error("Microphone access denied:", err);
      // Fall back to browser Web Speech API
      startBrowserSpeechRecognition();
    }
  }, [language, listening, onTranscript, base]);

  /* ── Browser Web Speech API fallback ─────────────────────────── */

  const startBrowserSpeechRecognition = useCallback(() => {
    const w = window as unknown as {
      SpeechRecognition?: new () => SpeechRecognitionInstance;
      webkitSpeechRecognition?: new () => SpeechRecognitionInstance;
    };
    const Ctor = w.SpeechRecognition ?? w.webkitSpeechRecognition;
    if (!Ctor) return;

    const rec = new Ctor();
    rec.lang = language;
    rec.continuous = false;
    rec.interimResults = false;

    rec.onresult = (e: SpeechRecognitionEvent) => {
      const transcript = e.results[e.resultIndex][0].transcript;
      onTranscript(transcript.trim());
    };
    rec.onerror = () => setListening(false);
    rec.onend = () => setListening(false);

    rec.start();
    setListening(true);
  }, [language, onTranscript]);

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const fallbackBrowserSTT = useCallback(
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    (_blob: Blob) => {
      // For pre-recorded audio we can't use Web Speech API (it needs live mic)
      // Just show a gentle error
      console.warn("Browser fallback: Web Speech API needs live mic access");
    },
    [],
  );

  /* ── Check for any audio input support ─────────────────────── */
  const hasMediaDevices =
    typeof navigator !== "undefined" &&
    navigator.mediaDevices &&
    typeof navigator.mediaDevices.getUserMedia === "function";

  const hasBrowserSTT =
    typeof window !== "undefined" &&
    !!(
      (window as unknown as Record<string, unknown>).SpeechRecognition ??
      (window as unknown as Record<string, unknown>).webkitSpeechRecognition
    );

  // Hide button if neither MediaRecorder nor browser STT is available
  if (!hasMediaDevices && !hasBrowserSTT) return null;

  const isActive = listening || processing;

  return (
    <button
      type="button"
      onClick={() => void toggle()}
      disabled={disabled || processing}
      aria-label={
        processing
          ? "Processing speech..."
          : listening
          ? "Stop voice input"
          : `Speak in ${language}`
      }
      title={
        processing
          ? "Transcribing..."
          : listening
          ? "Tap to stop recording"
          : "Tap to speak"
      }
      className={`h-11 w-11 shrink-0 rounded-2xl transition-all duration-200
        flex items-center justify-center
        ${
          listening
            ? "bg-red-500 text-white mic-recording border border-red-400"
            : processing
            ? "bg-amber-500 text-white animate-pulse border border-amber-400"
            : "btn-icon"
        }
        ${disabled ? "opacity-40 cursor-not-allowed" : ""}
      `}
    >
      {processing ? (
        /* Processing spinner */
        <svg
          className="h-4 w-4 animate-spin"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
          />
        </svg>
      ) : listening ? (
        /* Stop square */
        <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 24 24">
          <rect x="6" y="6" width="12" height="12" rx="2" />
        </svg>
      ) : (
        /* Microphone */
        <svg
          className="h-4 w-4"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          viewBox="0 0 24 24"
        >
          <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
          <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
          <line x1="12" y1="19" x2="12" y2="23" />
          <line x1="8" y1="23" x2="16" y2="23" />
        </svg>
      )}
    </button>
  );
}

/* ── Type declarations for Browser Speech API ──────────────────── */
interface SpeechRecognitionEvent {
  results: SpeechRecognitionResultList;
  resultIndex: number;
}

interface SpeechRecognitionResultList {
  [index: number]: SpeechRecognitionResult;
  length: number;
}

interface SpeechRecognitionResult {
  [index: number]: SpeechRecognitionAlternative;
  length: number;
  isFinal: boolean;
}

interface SpeechRecognitionAlternative {
  transcript: string;
  confidence: number;
}

interface SpeechRecognitionInstance {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  onresult: (e: SpeechRecognitionEvent) => void;
  onerror: () => void;
  onend: () => void;
  start: () => void;
  stop: () => void;
}
