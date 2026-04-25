"use client";

import { useCallback, useRef, useState } from "react";

interface SpeechRec extends EventTarget {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  maxAlternatives: number;
  onresult: ((e: SpeechRecResultEvent) => void) | null;
  onerror: ((e: SpeechRecErrorEvent) => void) | null;
  onend: (() => void) | null;
  onstart: (() => void) | null;
  start: () => void;
  stop: () => void;
}

interface SpeechRecResultEvent {
  resultIndex: number;
  results: SpeechRecognitionResultList;
}

interface SpeechRecErrorEvent {
  error: string;
  message?: string;
}

type SpeechRecCtor = new () => SpeechRec;

function getSR(): SpeechRecCtor | undefined {
  if (typeof window === "undefined") return undefined;
  const w = window as unknown as { SpeechRecognition?: SpeechRecCtor; webkitSpeechRecognition?: SpeechRecCtor };
  return w.SpeechRecognition ?? w.webkitSpeechRecognition;
}

function humanizeSpeechError(code: string): string {
  switch (code) {
    case "not-allowed":
    case "service-not-allowed":
      return "Microphone blocked — allow mic for this site in the browser lock icon, then try again.";
    case "no-speech":
      return "No speech heard — speak closer to the mic or check input volume.";
    case "audio-capture":
      return "No microphone found — plug in a mic or enable the built-in mic.";
    case "network":
      return "Speech service network error — check connection (Chrome uses Google’s STT).";
    case "aborted":
      return "Speech capture aborted.";
    default:
      return `Speech recognition error: ${code}`;
  }
}

interface Props {
  /** BCP-47 language tag, e.g. "hi-IN", "en-IN" — controls recognition language */
  language: string;
  onTranscript: (text: string) => void;
  onSpeechError?: (message: string) => void;
  disabled?: boolean;
}

export default function VoiceInput({ language, onTranscript, onSpeechError, disabled }: Props) {
  const [listening, setListening] = useState(false);
  const recRef = useRef<SpeechRec | null>(null);
  const SR = getSR();

  const stopInternal = useCallback(() => {
    try {
      recRef.current?.stop();
    } catch {
      /* ignore */
    }
    recRef.current = null;
    setListening(false);
  }, []);

  const startListening = useCallback(async () => {
    const Ctor = getSR();
    if (!Ctor) {
      onSpeechError?.("Voice input needs Chrome or Edge over HTTPS (Web Speech API).");
      return;
    }
    if (typeof window !== "undefined" && !window.isSecureContext) {
      onSpeechError?.("Voice input requires HTTPS (secure context).");
      return;
    }
    try {
      await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch {
      onSpeechError?.("Microphone permission denied — allow access when the browser prompts.");
      return;
    }

    const rec = new Ctor();
    rec.lang = language;
    rec.continuous = true;
    rec.interimResults = true;
    rec.maxAlternatives = 1;

    const finals: string[] = [];
    rec.onresult = (e: SpeechRecResultEvent) => {
      for (let i = e.resultIndex; i < e.results.length; i++) {
        const r = e.results[i];
        if (r.isFinal) {
          finals.push(r[0].transcript);
        }
      }
    };
    rec.onerror = (ev: SpeechRecErrorEvent) => {
      const msg = humanizeSpeechError(ev.error || "unknown");
      onSpeechError?.(msg);
      stopInternal();
    };
    rec.onend = () => {
      const text = finals.join(" ").trim();
      if (text) onTranscript(text);
      recRef.current = null;
      setListening(false);
    };

    recRef.current = rec;
    try {
      rec.start();
      setListening(true);
    } catch (err) {
      onSpeechError?.(`Could not start speech recognition: ${String(err)}`);
      stopInternal();
    }
  }, [language, onSpeechError, onTranscript, stopInternal]);

  const toggle = useCallback(() => {
    if (listening) {
      try {
        recRef.current?.stop();
      } catch {
        /* ignore */
      }
      return;
    }
    void startListening();
  }, [listening, startListening]);

  const unsupported = !SR;

  return (
    <button
      type="button"
      onClick={() => {
        if (unsupported) {
          onSpeechError?.("Voice input needs Chrome or Edge over HTTPS (Web Speech API). Firefox/Safari are not supported.");
          return;
        }
        void toggle();
      }}
      disabled={disabled}
      aria-label={
        unsupported
          ? "Voice input not supported in this browser"
          : listening
            ? "Stop recording"
            : `Speak in ${language}`
      }
      title={
        unsupported
          ? "Use Chrome or Edge on HTTPS for multilingual voice (hi-IN, ta-IN, …)"
          : listening
            ? "Tap to stop and insert text"
            : `Speak in ${language} — works best in Chrome`
      }
      className={`h-11 w-11 shrink-0 rounded-2xl transition-all duration-200
        flex items-center justify-center
        ${
          listening
            ? "bg-red-500 text-white mic-recording border border-red-400"
            : unsupported
              ? "opacity-50 border border-dashed"
              : "btn-icon"
        }
        ${disabled ? "opacity-40 cursor-not-allowed" : ""}
      `}
    >
      {listening ? (
        <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 24 24">
          <rect x="6" y="6" width="12" height="12" rx="2" />
        </svg>
      ) : (
        <svg className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
          <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
          <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
          <line x1="12" y1="19" x2="12" y2="23" />
          <line x1="8" y1="23" x2="16" y2="23" />
        </svg>
      )}
    </button>
  );
}
