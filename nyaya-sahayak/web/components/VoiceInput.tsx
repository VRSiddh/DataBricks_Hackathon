"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { getApiBase } from "@/lib/apiBase";

interface Props {
  language: string;
  onTranscript: (text: string) => void;
  onError?: (msg: string) => void;
  disabled?: boolean;
}

export default function VoiceInput({ language, onTranscript, onError, disabled }: Props) {
  const [listening, setListening] = useState(false);
  const [supported, setSupported] = useState(false);
  const mediaRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const base = getApiBase();

  useEffect(() => {
    setSupported(!!(navigator.mediaDevices && window.MediaRecorder));
  }, []);

  const stop = useCallback(() => {
    if (mediaRef.current && mediaRef.current.state !== "inactive") {
      mediaRef.current.stop();
    }
    setListening(false);
  }, []);

  const start = useCallback(async () => {
    let stream: MediaStream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch {
      onError?.("Microphone permission denied — allow access in the browser address bar.");
      return;
    }

    // Pick a supported MIME type
    const mime = ["audio/webm;codecs=opus", "audio/webm", "audio/ogg", "audio/mp4", ""].find(
      (m) => !m || MediaRecorder.isTypeSupported(m),
    ) ?? "";

    const rec = new MediaRecorder(stream, mime ? { mimeType: mime } : undefined);
    chunksRef.current = [];

    rec.ondataavailable = (e) => {
      if (e.data.size > 0) chunksRef.current.push(e.data);
    };

    rec.onstop = async () => {
      stream.getTracks().forEach((t) => t.stop());
      const blob = new Blob(chunksRef.current, { type: rec.mimeType || "audio/webm" });
      if (blob.size < 100) return; // nothing recorded

      const ext = (rec.mimeType || "audio/webm").includes("ogg") ? "ogg" : "webm";
      const fd = new FormData();
      fd.append("audio", blob, `recording.${ext}`);
      fd.append("language_code", language);

      try {
        const r = await fetch(`${base}/api/stt`, { method: "POST", body: fd });
        const data = await r.json();
        if (!r.ok) {
          onError?.(data?.detail || `STT error ${r.status}`);
          return;
        }
        if (data.transcript) onTranscript(data.transcript);
      } catch (e) {
        onError?.(`STT request failed: ${e}`);
      }
    };

    rec.start(200);
    mediaRef.current = rec;
    setListening(true);
  }, [base, language, onError, onTranscript]);

  const toggle = useCallback(() => {
    if (listening) stop();
    else void start();
  }, [listening, start, stop]);

  if (!supported) return null;

  return (
    <button
      type="button"
      onClick={toggle}
      disabled={disabled}
      aria-label={listening ? "Stop recording" : `Speak in ${language}`}
      title={listening ? "Tap to stop and transcribe" : `Voice input (${language}) — powered by Sarvam AI`}
      className={[
        "h-11 w-11 shrink-0 rounded-2xl transition-all duration-200 flex items-center justify-center",
        listening ? "bg-red-500 text-white mic-recording border border-red-400" : "btn-icon",
        disabled ? "opacity-40 cursor-not-allowed" : "",
      ].join(" ")}
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
