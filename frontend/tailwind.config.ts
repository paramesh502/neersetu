import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Water blues
        water: {
          50:  "#eff8ff",
          100: "#dbeffe",
          200: "#bfe3fd",
          300: "#93d2fb",
          400: "#60b8f7",
          500: "#3b9af0",
          600: "#2579e5",
          700: "#1e63d2",
          800: "#1f50aa",
          900: "#1e4686",
          950: "#162b52",
        },
        // Farm greens
        farm: {
          50:  "#f0fdf5",
          100: "#dcfce8",
          200: "#bbf7d2",
          300: "#86efad",
          400: "#4ade80",
          500: "#22c55e",
          600: "#16a34a",
          700: "#15803d",
          800: "#166534",
          900: "#14532d",
          950: "#052e16",
        },
        // Soil / earthy amber
        soil: {
          50:  "#fffbeb",
          100: "#fef3c7",
          200: "#fde68a",
          300: "#fcd34d",
          400: "#fbbf24",
          500: "#f59e0b",
          600: "#d97706",
          700: "#b45309",
          800: "#92400e",
          900: "#78350f",
        },
      },
      backgroundImage: {
        "canal-gradient": "linear-gradient(135deg, #1e4686 0%, #2579e5 50%, #60b8f7 100%)",
        "farm-gradient": "linear-gradient(135deg, #052e16 0%, #16a34a 50%, #86efad 100%)",
      },
      animation: {
        "flow": "flow 3s ease-in-out infinite",
        "pulse-slow": "pulse 3s ease-in-out infinite",
        "slide-in": "slideIn 0.3s ease-out",
        "fade-in": "fadeIn 0.4s ease-out",
      },
      keyframes: {
        flow: {
          "0%, 100%": { transform: "translateX(-100%)", opacity: "0" },
          "50%": { transform: "translateX(0)", opacity: "1" },
          "100%": { transform: "translateX(100%)", opacity: "0" },
        },
        slideIn: {
          "0%": { transform: "translateY(-10px)", opacity: "0" },
          "100%": { transform: "translateY(0)", opacity: "1" },
        },
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
      },
    },
  },
  plugins: [],
};
export default config;
