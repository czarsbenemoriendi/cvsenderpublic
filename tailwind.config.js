/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./frontend/static/index.html"],
  plugins: [require("daisyui")],
  daisyui: {
    themes: ["dark"],
  },
};
