import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{js,ts,jsx,tsx}", "./components/**/*.{js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      fontFamily: {
        sans: ["var(--font-sans)"],
      },
      colors: {
        brand: {
          DEFAULT: "#0f766e",
          dim: "#134e4a",
        },
      },
      backgroundImage: {
        grid: "radial-gradient(circle at 1px 1px, rgba(15,23,42,0.12) 1px, transparent 0)",
      },
    },
  },
  plugins: [],
};

export default config;
