"use client";

import { useCallback, useRef, useState } from "react";

interface SpeechRec {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  onresult: (e: SpeechRecEvent) => void;
  onerror: () => void;
  onend: () => void;
  start: () => void;
  stop: () => void;
}

interface SpeechRecEvent {
  results: { [k: number]: { [k: number]: { transcript: string } } };
  resultIndex: number;
}

type SpeechRecCtor = new () => SpeechRec;

function getSR(): SpeechRecCtor | undefined {
  if (typeof window === "undefined") return undefined;
  const w = window as unknown as { SpeechRecognition?: SpeechRecCtor; webkitSpeechRecognition?: SpeechRecCtor };
  return w.SpeechRecognition ?? w.webkitSpeechRecognition;
}

interface Props {
  /** BCP-47 language tag, e.g. "hi-IN", "en-IN" */
  language: string;
  onTranscript: (text: string) => void;
  disabled?: boolean;
}

export default function VoiceInput({ language, onTranscript, disabled }: Props) {
  const [listening, setListening] = useState(false);
  const recRef = useRef<SpeechRec | null>(null);
  const SR = getSR();

  const toggle = useCallback(() => {
    if (listening) {
      recRef.current?.stop();
      setListening(false);
      return;
    }
    const Ctor = getSR();
    if (!Ctor) return;

    const rec = new Ctor();
    rec.lang = language;
    rec.continuous = false;
    rec.interimResults = false;

    rec.onresult = (e: SpeechRecEvent) => {
      const transcript: string = e.results[e.resultIndex][0].transcript;
      onTranscript(transcript.trim());
    };
    rec.onerror = () => setListening(false);
    rec.onend = () => setListening(false);

    recRef.current = rec;
    rec.start();
    setListening(true);
  }, [language, listening, onTranscript]);

  if (!SR) return null;

  return (
    <button
      type="button"
      onClick={toggle}
      disabled={disabled}
      aria-label={listening ? "Stop voice input" : `Speak in ${language}`}
      title={listening ? "Tap to stop recording" : "Tap to speak"}
      className={`h-11 w-11 shrink-0 rounded-2xl transition-all duration-200
        flex items-center justify-center
        ${
          listening
            ? "bg-red-500 text-white mic-recording border border-red-400"
            : "btn-icon"
        }
        ${disabled ? "opacity-40 cursor-not-allowed" : ""}
      `}
    >
      {listening ? (
        /* Stop square */
        <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 24 24">
          <rect x="6" y="6" width="12" height="12" rx="2" />
        </svg>
      ) : (
        /* Microphone */
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
