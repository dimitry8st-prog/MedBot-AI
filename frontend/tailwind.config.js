/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0F1C1A",
        mist: "#E7F0EC",
        foam: "#F4FAF7",
        sea: "#1F6F63",
        seaDeep: "#134E48",
        sand: "#C9B8A0",
        alert: "#8B3A2F",
      },
      fontFamily: {
        display: ['"Fraunces"', "Georgia", "serif"],
        sans: ['"Manrope"', "system-ui", "sans-serif"],
      },
      boxShadow: {
        soft: "0 24px 60px rgba(15, 28, 26, 0.18)",
      },
    },
  },
  plugins: [],
};
