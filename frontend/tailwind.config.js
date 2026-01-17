/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Amazon Color Palette
        amazon: {
          dark: '#131921',       // Navbar background
          light: '#232F3E',      // Secondary dark
          orange: '#FF9900',     // Primary accent
          gold: '#FEBD69',       // Secondary accent (search button)
          bg: '#E3E6E6',         // Page background (updated Amazon gray)
          card: '#FFFFFF',       // Card background
          text: '#0F1111',       // Primary text
          link: '#007185',       // Link color
          green: '#067D62',      // Price/deals green
          red: '#CC0C39',        // Sale/discount red
          star: '#FFA41C',       // Star rating color
          border: '#DDD',        // Border color
        }
      },
      fontFamily: {
        amazon: ['Amazon Ember', 'Arial', 'sans-serif'],
      },
      boxShadow: {
        'amazon': '0 2px 5px 0 rgba(0,0,0,0.1)',
        'amazon-hover': '0 4px 10px 0 rgba(0,0,0,0.15)',
      }
    },
  },
  plugins: [],
}
