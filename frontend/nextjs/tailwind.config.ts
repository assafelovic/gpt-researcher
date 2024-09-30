import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    screens: {
      sm: '640px',
      md: '768px',
      lg: '1024px',
      xl: '1280px',
      '2xl': '1536px',
    },
    container: {
      center: true,
      padding: '2rem',
    },
    extend: {
      colors: {
        primary: {
          DEFAULT: '#0071e3',
          dark: '#0051a2',
        },
        secondary: {
          DEFAULT: '#6e6e73',
          dark: '#1d1d1f',
        },
        background: {
          light: '#f5f7fa',
          dark: '#1c1c1e',
        },
        surface: {
          light: '#ffffff',
          dark: '#2c2c2e',
        },
      },
      fontFamily: {
        sans: [
          '-apple-system',
          'BlinkMacSystemFont',
          'Segoe UI',
          'Roboto',
          'Helvetica',
          'Arial',
          'sans-serif',
        ],
        mono: [
          'SF Mono',
          'Menlo',
          'Monaco',
          'Courier New',
          'monospace',
        ],
      },
      boxShadow: {
        'apple-card': '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
        'apple-button': '0 2px 4px 0 rgba(0,0,0,0.1)',
      },
      borderRadius: {
        'apple': '0.75rem',
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'custom-gradient': 'linear-gradient(150deg, #1B1B16 1.28%, #565646 90.75%)',
        'gradient-conic': 'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
      },
    },
  },
  plugins: [],
};

export default config;
