/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ['class'],
  content: [
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        black: '#000000',
        'dark-1': '#0a0a0a',
        'dark-2': '#111111',
        'dark-3': '#1a1a1a',
        white: '#ffffff',
        silver: '#c0c0c0',
        'dark-silver': '#a0a0a0',
      },
    },
  },
  plugins: [],
};