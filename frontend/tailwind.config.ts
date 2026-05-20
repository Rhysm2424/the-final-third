import type { Config } from 'tailwindcss';

const config: Config = {
  darkMode: 'class',
  content: ['./app/**/*.{ts,tsx}', './components/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        // Chelsea-themed palette — deep blue, cream, sparing yellow/red signals
        cream: {
          DEFAULT: '#F5EFE0',
          50: '#FBF8F0',
          100: '#F5EFE0',
          200: '#EBE3CC',
          300: '#DDD0AC',
        },
        navy: {
          DEFAULT: '#034694',
          50: '#E8EEF7',
          100: '#C7D5EB',
          200: '#8FAAD7',
          300: '#5780C2',
          400: '#2C5FAB',
          500: '#034694',
          600: '#03397A',
          700: '#022C60',
          800: '#021F44',
          900: '#011429',
        },
        signal: {
          gold: '#F4C430',     // model pick / highlight
          red: '#C0392B',      // loss / negative signal
          green: '#2D6A4F',    // win / positive signal
        },
        ink: {
          DEFAULT: '#0F1A2E',
          mid: '#3C4860',
          soft: '#8A8580',
        },
        paper: {
          DEFAULT: '#FFFFFF',
          subtle: '#FAF7EE',
        },
        line: {
          DEFAULT: '#E6E0D3',
          strong: '#C9BFAA',
        },
      },
      fontFamily: {
        serif: ['Fraunces', 'Georgia', 'serif'],
        sans: ['"Inter Tight"', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      animation: {
        'fade-in': 'fadeIn 0.6s ease-out forwards',
        'slide-up': 'slideUp 0.7s cubic-bezier(0.22, 1, 0.36, 1) forwards',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(12px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [require('tailwindcss-animate')],
};

export default config;
