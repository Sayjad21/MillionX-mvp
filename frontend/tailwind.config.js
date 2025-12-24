/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        // Cyber-Deshi Color Palette
        "cyber-night": "#020617", // slate-950 - Deep Night Background
        "neon-green": "#39FF14", // Primary Action Color
        "rickshaw-orange": "#FF5F1F", // Alert/Urgency Color
        "jamdani-teal": "#008080", // Accent/Border Color
        "cyber-purple": "#9333EA", // Secondary Accent
        "glass-bg": "rgba(15, 23, 42, 0.6)", // Glass Background
      },
      backgroundImage: {
        "cyber-gradient": "linear-gradient(135deg, #020617 0%, #1e1b4b 100%)",
        "neon-glow": "linear-gradient(90deg, #39FF14 0%, #008080 100%)",
      },
      boxShadow: {
        neon: "0 0 10px rgba(57, 255, 20, 0.5), 0 0 20px rgba(57, 255, 20, 0.3)",
        "neon-strong":
          "0 0 20px rgba(57, 255, 20, 0.8), 0 0 40px rgba(57, 255, 20, 0.5)",
        "orange-glow":
          "0 0 10px rgba(255, 95, 31, 0.5), 0 0 20px rgba(255, 95, 31, 0.3)",
        glass: "0 8px 32px 0 rgba(31, 38, 135, 0.37)",
      },
      animation: {
        "pulse-neon": "pulse-neon 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "slide-up": "slide-up 0.3s ease-out",
        "radar-sweep": "radar-sweep 2s linear infinite",
      },
      keyframes: {
        "pulse-neon": {
          "0%, 100%": {
            opacity: "1",
            boxShadow:
              "0 0 10px rgba(57, 255, 20, 0.5), 0 0 20px rgba(57, 255, 20, 0.3)",
          },
          "50%": {
            opacity: ".8",
            boxShadow:
              "0 0 20px rgba(57, 255, 20, 0.8), 0 0 40px rgba(57, 255, 20, 0.5)",
          },
        },
        "slide-up": {
          "0%": { transform: "translateY(20px)", opacity: "0" },
          "100%": { transform: "translateY(0)", opacity: "1" },
        },
        "radar-sweep": {
          "0%": { transform: "rotate(0deg)" },
          "100%": { transform: "rotate(360deg)" },
        },
      },
    },
  },
  plugins: [],
};
