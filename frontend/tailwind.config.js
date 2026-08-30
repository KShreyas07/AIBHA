/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        // Warm cream surfaces
        cream: {
          50: "#FEFDFB",
          100: "#FAF6EC",
          200: "#F3EBD8",
          300: "#E8DCBE",
        },
        // Warm near-black ink for text
        ink: {
          900: "#211C15",
          700: "#453D31",
          500: "#726755",
          400: "#948A78",
          300: "#B8AF9E",
          200: "#DED5C2",
          100: "#EEE7D7",
        },
        // Terracotta accent — echoes the warm-orange tones in the reference
        brand: {
          50: "#FDF1EA",
          100: "#FADFCC",
          400: "#E1723A",
          500: "#C85A28",
          600: "#B14A1E",
          700: "#8F3A17",
        },
      },
      fontFamily: {
        display: ["'Fraunces'", "serif"],
        sans: ["'Inter'", "system-ui", "sans-serif"],
      },
      borderRadius: {
        "4xl": "2rem",
      },
    },
  },
  plugins: [],
};
