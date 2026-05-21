import type { Config } from 'tailwindcss';

const config: Config = {
  darkMode: 'class',
  content: ['./app/**/*.{ts,tsx}', './components/**/*.{ts,tsx}', './lib/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: {
          DEFAULT: '#0b0d12',
          subtle: '#11141b',
          card: '#151924',
        },
        border: {
          DEFAULT: 'rgba(255,255,255,0.08)',
          strong: 'rgba(255,255,255,0.14)',
        },
        accent: {
          DEFAULT: '#7c5cff',
          glow: '#a78bfa',
        },
        success: '#34d399',
        warning: '#fbbf24',
        danger: '#fb7185',
        info: '#22d3ee',
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        card: '0 1px 0 rgba(255,255,255,0.04) inset, 0 10px 30px -10px rgba(0,0,0,0.6)',
        glow: '0 0 40px -10px rgba(124,92,255,0.55)',
      },
      backgroundImage: {
        'grid-fade':
          'radial-gradient(circle at 50% 0%, rgba(124,92,255,0.15), transparent 60%)',
      },
      keyframes: {
        'fade-up': {
          '0%': { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
      animation: {
        'fade-up': 'fade-up 0.4s ease-out both',
      },
    },
  },
  plugins: [],
};

export default config;
