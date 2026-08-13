/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // AgroSmart brand palette
        agro: {
          green:      '#2d7a3a',
          'green-light': '#4caf50',
          'green-pale':  '#e8f5e9',
          earth:      '#795548',
          'earth-light': '#a1887f',
          sky:        '#0288d1',
          amber:      '#f59e0b',
          red:        '#ef4444',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
