/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        apple: {
          gray:   "#F5F5F7",
          blue:   "#0071E3",
          dark:   "#1D1D1F",
          light:  "#86868B",
          border: "#D2D2D7",
        },
      },
      fontFamily: {
        sans: [
          "-apple-system", "BlinkMacSystemFont", "SF Pro Display",
          "SF Pro Text", "Helvetica Neue", "Arial", "sans-serif",
        ],
      },
    },
  },
  plugins: [],
};
