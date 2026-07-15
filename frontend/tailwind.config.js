/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        ink: {
          950: "#06101c",
          900: "#0b1f33",
          800: "#122b45",
          700: "#1a3a5c",
          600: "#24507a",
        },
        signal: {
          DEFAULT: "#1f9d8a",
          soft: "#2bbfA8",
          warn: "#c9852c",
          danger: "#c44b4b",
          info: "#3a7ca5",
        },
        paper: {
          DEFAULT: "#f3f6f9",
          card: "#ffffff",
          muted: "#dbe4ee",
        },
      },
      fontFamily: {
        display: ['"Source Serif 4"', "Georgia", "serif"],
        sans: ['"IBM Plex Sans"', "Segoe UI", "sans-serif"],
        mono: ['"IBM Plex Mono"', "ui-monospace", "monospace"],
      },
      boxShadow: {
        panel: "0 1px 0 rgba(15,39,68,0.06), 0 12px 32px rgba(6,16,28,0.08)",
      },
      backgroundImage: {
        mesh: "radial-gradient(ellipse at 20% 0%, rgba(31,157,138,0.18), transparent 50%), radial-gradient(ellipse at 90% 10%, rgba(58,124,165,0.16), transparent 45%), linear-gradient(180deg, #0b1f33 0%, #122b45 40%, #0b1f33 100%)",
        "mesh-light": "radial-gradient(ellipse at 10% 0%, rgba(31,157,138,0.08), transparent 40%), linear-gradient(180deg, #eef3f8 0%, #f3f6f9 100%)",
      },
    },
  },
  plugins: [],
};
