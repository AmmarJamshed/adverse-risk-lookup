/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        navy: {
          950: "#071525",
          900: "#0c2340",
          800: "#143a5c",
          700: "#1c4d75",
          600: "#256090",
        },
        steel: {
          50: "#f4f6f9",
          100: "#e8edf3",
          200: "#d5dee8",
          300: "#b7c5d4",
          400: "#8aa0b5",
          500: "#5f7690",
          600: "#455a70",
          700: "#344556",
          800: "#243040",
          900: "#17212c",
        },
        brand: {
          DEFAULT: "#0a6e8a",
          mid: "#0d87a8",
          soft: "#e6f3f7",
        },
        hit: {
          critical: "#b42318",
          high: "#c2410c",
          medium: "#a16207",
          low: "#0f766e",
          clear: "#0a6e8a",
        },
      },
      fontFamily: {
        sans: ['"Source Sans 3"', "Segoe UI", "sans-serif"],
        display: ['"Source Sans 3"', "Segoe UI", "sans-serif"],
        mono: ['"IBM Plex Mono"', "ui-monospace", "monospace"],
      },
      boxShadow: {
        desk: "0 1px 2px rgba(12, 35, 64, 0.06)",
      },
      borderRadius: {
        panel: "4px",
      },
    },
  },
  plugins: [],
};
