/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./learnmusic/templates/**/*.html",
    "./notes/templates/**/*.html",
    "./learnmusic/static/js/**/*.js",
    "./notes/templates/js/**/*.js",
  ],
  theme: {
    extend: {
      colors: {
        // Add any custom colors here if needed
      },
    },
  },
  plugins: [require("daisyui")],
  daisyui: {
    themes: ["light", "dark"],
  },
}
