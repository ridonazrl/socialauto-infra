/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['Fira Code', 'Courier New', 'monospace'],
      },
      colors: {
        slate: {
          850: '#151d2e',
          900: '#0f172a',
          950: '#080d1a',
        },
        terminal: {
          bg: '#0c1017',
          header: '#161b22',
          border: '#30363d',
          green: '#2ea043',
          red: '#f85149',
          yellow: '#d29922',
          cyan: '#58a6ff',
        }
      }
    },
  },
  plugins: [],
}
