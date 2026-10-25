/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        legal: {
          950: '#070C18',
          900: '#0D1527',
          850: '#111D36',
          800: '#172545',
          700: '#223663',
          600: '#324F8F',
          500: '#456DBF',
        },
        gold: {
          400: '#E6C665',
          500: '#D4AF37',
          600: '#B89726',
        },
        status: {
          verified: '#10B981',
          unsupported: '#EF4444',
          contradicted: '#F59E0B',
          review: '#8B5CF6',
        }
      },
      fontFamily: {
        serif: ['Merriweather', 'Georgia', 'serif'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      }
    },
  },
  plugins: [],
}
