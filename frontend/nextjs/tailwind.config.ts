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
      lg: '898px',
      // xl:"1024px"
    },
    container: {
      center: true,
    },
    extend: {
      animation: {
        'gradient-x': 'gradient-x 10s ease infinite',
        'shimmer': 'shimmer 2s linear infinite',
        'pulse-slow': 'pulse 8s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        'gradient-x': {
          '0%, 100%': { backgroundPosition: '0% 50%' },
          '50%': { backgroundPosition: '100% 50%' },
        },
        'shimmer': {
          '100%': { transform: 'translateX(100%)' },
        },
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'custom-gradient':
          'linear-gradient(150deg, #1B1B16 1.28%, #565646 90.75%)',
        'gradient-conic':
          'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
        'hero-gradient': 'linear-gradient(135deg, #9867F0, #ED4E50)',
        'teal-gradient': 'linear-gradient(135deg, #0d9488, #0891b2, #2563eb)',
      },
      boxShadow: {
        'glow': '0 0 40px rgba(152, 103, 240, 0.5)',
        'teal-glow': '0 0 40px rgba(13, 148, 136, 0.5)',
      },
      fontFamily: {
        display: ['var(--font-display)', 'Georgia', 'serif'],
        body: ['var(--font-body)', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        code: ['var(--font-code)', 'ui-monospace', 'SFMono-Regular', 'monospace'],
      },
      colors: {
        paper: { DEFAULT: '#EEE7D8', deep: '#E6DDCA', hi: '#F6F1E7' },
        ink: { DEFAULT: '#1A1612', 2: '#39332B', 3: '#5F574B' },
        rubric: '#B8381C',
        rule: { DEFAULT: 'rgba(29, 25, 21, 0.26)', soft: 'rgba(29, 25, 21, 0.14)' },
        'primary': {
          '50': '#f0fdfa',
          '100': '#ccfbf1',
          '200': '#99f6e4',
          '300': '#5eead4',
          '400': '#2dd4bf',
          '500': '#14b8a6',
          '600': '#0d9488',
          '700': '#0f766e',
          '800': '#115e59',
          '900': '#134e4a',
          '950': '#042f2e',
        },
      },
    },
  },
  plugins: [],
};
export default config;
