/** @type {import('tailwindcss').Config} */
// Paleta "Trust & Authority" (UI/UX Pro Max) adaptada a light-first para el
// asegurado: navy de confianza + verde positivo + slate neutro. Tokens semánticos
// para estados del reclamo.
module.exports = {
  content: ["./app/**/*.{js,jsx,ts,tsx}", "./components/**/*.{js,jsx,ts,tsx}"],
  presets: [require("nativewind/preset")],
  theme: {
    extend: {
      colors: {
        // Marca / superficies
        brand: {
          DEFAULT: "#0F172A", // navy 900 — headers, texto primario
          600: "#1E293B",
          500: "#334155",
        },
        accent: {
          DEFAULT: "#16A34A", // verde CTA (contraste AA sobre blanco)
          600: "#15803D",
          50: "#F0FDF4",
        },
        surface: "#FFFFFF",
        background: "#F8FAFC", // slate-50
        muted: {
          DEFAULT: "#64748B", // slate-500 texto secundario
          fg: "#94A3B8",
        },
        line: "#E2E8F0", // slate-200 bordes
        danger: {
          DEFAULT: "#DC2626",
          50: "#FEF2F2",
        },
        warning: {
          DEFAULT: "#D97706",
          50: "#FFFBEB",
        },
        info: {
          DEFAULT: "#2563EB",
          50: "#EFF6FF",
        },
      },
      fontFamily: {
        sans: ["IBMPlexSans_400Regular"],
        medium: ["IBMPlexSans_500Medium"],
        semibold: ["IBMPlexSans_600SemiBold"],
        bold: ["IBMPlexSans_700Bold"],
      },
      borderRadius: {
        xl: "16px",
        "2xl": "20px",
      },
    },
  },
  plugins: [],
};
