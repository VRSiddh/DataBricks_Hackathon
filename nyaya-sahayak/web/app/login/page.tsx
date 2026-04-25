"use client";

import { ThemeInit } from "@/components/ThemeInit";
import ThemeToggle from "@/components/ThemeToggle";
import { saveUser } from "@/lib/auth";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize: (cfg: object) => void;
          renderButton: (el: HTMLElement, cfg: object) => void;
          prompt: () => void;
        };
      };
    };
    handleGoogleCredential?: (res: { credential: string }) => void;
  }
}

function parseJwt(token: string) {
  try {
    return JSON.parse(atob(token.split(".")[1]));
  } catch {
    return null;
  }
}

export default function LoginPage() {
  const router = useRouter();

  useEffect(() => {
    window.handleGoogleCredential = (response) => {
      const payload = parseJwt(response.credential);
      if (!payload) return;
      saveUser({ name: payload.name, email: payload.email, picture: payload.picture });
      router.push("/onboarding/");
    };

    const id = setTimeout(() => {
      if (!window.google) return;
      window.google.accounts.id.initialize({
        client_id: process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || "YOUR_GOOGLE_CLIENT_ID",
        callback: "handleGoogleCredential",
      });
      const el = document.getElementById("google-btn");
      if (el) {
        window.google.accounts.id.renderButton(el, { theme: "outline", size: "large", width: 300 });
      }
    }, 300);
    return () => clearTimeout(id);
  }, [router]);

  return (
    <>
      <ThemeInit />
      <script src="https://accounts.google.com/gsi/client" async defer />
      <div
        className="flex min-h-dvh flex-col items-center justify-center px-4"
        style={{ background: "var(--bg)" }}
      >
        {/* Nav */}
        <div className="absolute right-5 top-5">
          <ThemeToggle />
        </div>

        {/* Card */}
        <div className="glass w-full max-w-sm px-8 py-10 text-center shadow-2xl">
          <div
            className="mx-auto mb-5 flex h-16 w-16 items-center justify-center rounded-2xl text-3xl text-white"
            style={{ background: "var(--user-grad)", boxShadow: "0 8px 32px var(--glow)" }}
          >
            ⚖
          </div>
          <h1 className="text-2xl font-black tracking-tight">Nyaya-Sahayak</h1>
          <p className="mt-2 text-sm" style={{ color: "var(--fg2)" }}>
            Sign in to get personalised legal guidance and government scheme recommendations.
          </p>

          <div className="mt-8 flex justify-center">
            <div id="google-btn" />
          </div>

          <p className="mt-6 text-xs" style={{ color: "var(--fg2)" }}>
            Your data stays in your browser. No server login required.
          </p>
        </div>

        <p className="mt-6 text-xs" style={{ color: "var(--fg2)" }}>
          Prototype — not legal advice
        </p>
      </div>
    </>
  );
}
