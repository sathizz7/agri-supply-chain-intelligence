/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: { DEFAULT: '#1B7A3D', light: '#27AE60', dark: '#145c2e' },
        warning: '#F39C12',
        critical: '#E74C3C',
        caution: '#F1C40F',
        adequate: '#27AE60',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        label: ['Space Grotesk', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
