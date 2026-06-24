import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          50: "#f8fafc",
          100: "#eef3f8",
          200: "#dbe7f0",
          300: "#b7c5d4",
          400: "#8a99aa",
          500: "#64748b",
          600: "#475569",
          700: "#334155",
          800: "#1f2937",
          900: "#0b1220",
          DEFAULT: "#172033",
        },
        muted: "#64748b",
        panel: "#ffffffb8",
        line: "#dbe7f0",
        accent: "#3730a3",
        marble: "#F2F8FC",
      },
    },
  },
  plugins: [],
};

export default config;
