"use client";

import { useEffect } from "react";

export function ThemeInit() {
  useEffect(() => {
    // Fallback: if anti-FOUC script didn't run, set dark (default)
    const hasClass =
      document.documentElement.classList.contains("dark") ||
      document.documentElement.classList.contains("light");
    if (hasClass) return;
    const stored = localStorage.getItem("nyaya-theme");
    const dark = stored !== "light"; // default → dark
    document.documentElement.classList.add(dark ? "dark" : "light");
  }, []);
  return null;
}

export function setTheme(dark: boolean) {
  document.documentElement.classList.toggle("dark", dark);
  document.documentElement.classList.toggle("light", !dark);
  localStorage.setItem("nyaya-theme", dark ? "dark" : "light");
}
