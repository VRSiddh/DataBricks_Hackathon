"use client";

import { useRef, useEffect } from "react";

interface AudioPlayerProps {
  audioBase64: string | null;
  autoPlay?: boolean;
}

export default function AudioPlayer({ audioBase64, autoPlay = false }: AudioPlayerProps) {
  const audioRef = useRef<HTMLAudioElement>(null);

  useEffect(() => {
    if (audioBase64 && autoPlay && audioRef.current) {
      audioRef.current.play().catch(() => {});
    }
  }, [audioBase64, autoPlay]);

  if (!audioBase64) return null;

  const audioSrc = audioBase64.startsWith("data:")
    ? audioBase64
    : `data:audio/wav;base64,${audioBase64}`;

  return (
    <div className="mt-2 flex items-center gap-2">
      <audio ref={audioRef} src={audioSrc} controls className="audio-player" />
      <span className="text-xs" style={{ color: "var(--fg2)" }}>
        🔊 Listen
      </span>
    </div>
  );
}
