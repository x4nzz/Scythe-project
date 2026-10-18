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
      keyframes: {
        'blade-slash': {
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(100%)' }
        }
      },
      animation: {
        'blade-slash': 'blade-slash 0.6s ease-out'
      }
    },
  },
  plugins: [
    function({ addUtilities }) {
      addUtilities({
        '.bg-grid-pattern': {
          backgroundImage: "url('data:image/svg+xml;utf8,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%22100%22 height=%22100%22 viewBox=%220 0 100 100%22><path d=%22M0 0 L100 100 M100 0 L0 100%22 stroke=%22%231a1a1a%22 stroke-width=%220.5%22/%22></svg>')",
          backgroundSize: '20px 20px',
          backgroundRepeat: 'repeat'
        }
      })
    }
  ],
};