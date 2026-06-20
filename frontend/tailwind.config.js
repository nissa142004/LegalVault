export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        vault: {
          950: "#080b10",
          900: "#0d1118",
          850: "#121824",
          800: "#182131",
          700: "#223047",
          accent: "#4fd1c5",
          gold: "#d8b55f",
        },
      },
      boxShadow: {
        glow: "0 0 40px rgba(79, 209, 197, 0.12)",
      },
    },
  },
  plugins: [],
};
