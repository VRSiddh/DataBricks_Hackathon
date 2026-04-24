"use client";

import { useEffect } from "react";

export function ThemeInit() {
  useEffect(() => {
    const stored = localStorage.getItem("nyaya-theme");
    const prefersDark = window.matchMedia?.("(prefers-color-scheme: dark)")?.matches;
    const light = stored === "light" || (stored == null && !prefersDark);
    document.documentElement.classList.toggle("dark", !light);
    document.documentElement.classList.toggle("light", light);
  }, []);
  return null;
}

export function setTheme(dark: boolean) {
  document.documentElement.classList.toggle("dark", dark);
  document.documentElement.classList.toggle("light", !dark);
  localStorage.setItem("nyaya-theme", dark ? "dark" : "light");
}
