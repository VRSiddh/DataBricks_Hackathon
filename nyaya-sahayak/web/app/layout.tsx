import type { Metadata } from "next";
import { Plus_Jakarta_Sans } from "next/font/google";
import "./globals.css";
import { ThemeInit } from "@/components/ThemeInit";

const jakarta = Plus_Jakarta_Sans({ subsets: ["latin", "latin-ext"], variable: "--font-sans" });

export const metadata: Metadata = {
  title: "Nyaya-Sahayak",
  description: "BNS-aware legal guidance for Indian law — Databricks RAG + Sarvam",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${jakarta.variable} min-h-dvh font-sans antialiased`}>
        <ThemeInit />
        {children}
      </body>
    </html>
  );
}
