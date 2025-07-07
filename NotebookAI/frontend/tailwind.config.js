/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      // Apple-inspired design system
      colors: {
        // Apple's refined color palette
        apple: {
          gray: {
            50: '#fafaf9',
            100: '#f5f5f4',
            200: '#e7e5e4',
            300: '#d6d3d1',
            400: '#a8a29e',
            500: '#78716c',
            600: '#57534e',
            700: '#44403c',
            800: '#292524',
            900: '#1c1917',
          },
          blue: {
            50: '#eff6ff',
            100: '#dbeafe',
            200: '#bfdbfe',
            300: '#93c5fd',
            400: '#60a5fa',
            500: '#3b82f6',
            600: '#2563eb',
            700: '#1d4ed8',
            800: '#1e40af',
            900: '#1e3a8a',
          }
        },
        // System colors
        system: {
          background: '#ffffff',
          backgroundSecondary: '#f5f5f7',
          backgroundTertiary: '#ffffff',
          label: '#000000',
          labelSecondary: '#3c3c43',
          labelTertiary: '#3c3c4399',
          separator: '#3c3c431f',
          fill: '#78788033',
        },
        // Glassmorphism
        glass: {
          white: 'rgba(255, 255, 255, 0.8)',
          gray: 'rgba(255, 255, 255, 0.1)',
          dark: 'rgba(0, 0, 0, 0.1)',
        }
      },
      // Apple's typography scale
      fontFamily: {
        'apple': ['-apple-system', 'BlinkMacSystemFont', 'SF Pro Display', 'Segoe UI', 'Roboto', 'Helvetica Neue', 'Arial', 'sans-serif'],
        'apple-mono': ['SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', 'monospace'],
        'display': ['SF Pro Display', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
        'text': ['SF Pro Text', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
      },
      fontSize: {
        // Apple's text sizes
        'title1': ['28px', { lineHeight: '34px', fontWeight: '400' }],
        'title2': ['22px', { lineHeight: '28px', fontWeight: '400' }],
        'title3': ['20px', { lineHeight: '24px', fontWeight: '400' }],
        'headline': ['17px', { lineHeight: '22px', fontWeight: '600' }],
        'body': ['17px', { lineHeight: '22px', fontWeight: '400' }],
        'callout': ['16px', { lineHeight: '21px', fontWeight: '400' }],
        'subhead': ['15px', { lineHeight: '20px', fontWeight: '400' }],
        'footnote': ['13px', { lineHeight: '18px', fontWeight: '400' }],
        'caption1': ['12px', { lineHeight: '16px', fontWeight: '400' }],
        'caption2': ['11px', { lineHeight: '13px', fontWeight: '400' }],
      },
      // Apple's spacing system
      spacing: {
        '4.5': '1.125rem',
        '5.5': '1.375rem',
        '6.5': '1.625rem',
        '7.5': '1.875rem',
        '8.5': '2.125rem',
        '9.5': '2.375rem',
        '13': '3.25rem',
        '15': '3.75rem',
        '17': '4.25rem',
        '18': '4.5rem',
        '19': '4.75rem',
        '21': '5.25rem',
        '22': '5.5rem',
        '25': '6.25rem',
        '26': '6.5rem',
        '28': '7rem',
        '30': '7.5rem',
      },
      // Apple's border radius system
      borderRadius: {
        'apple': '10px',
        'apple-sm': '6px',
        'apple-lg': '14px',
        'apple-xl': '20px',
        'apple-2xl': '28px',
        'apple-3xl': '40px',
      },
      // Apple's shadows
      boxShadow: {
        'apple-sm': '0 1px 3px rgba(0, 0, 0, 0.1)',
        'apple': '0 4px 16px rgba(0, 0, 0, 0.1)',
        'apple-lg': '0 8px 32px rgba(0, 0, 0, 0.15)',
        'apple-xl': '0 16px 64px rgba(0, 0, 0, 0.2)',
        'glass': '0 8px 32px rgba(31, 38, 135, 0.37)',
        'inner-glass': 'inset 0 1px 0 rgba(255, 255, 255, 0.1)',
      },
      // Apple's animations
      animation: {
        'fade-in': 'fadeIn 0.5s ease-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'slide-down': 'slideDown 0.3s ease-out',
        'bounce-gentle': 'bounceGentle 2s infinite',
        'pulse-gentle': 'pulseGentle 2s infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        slideDown: {
          '0%': { transform: 'translateY(-10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        bounceGentle: {
          '0%, 100%': { transform: 'translateY(-5%)' },
          '50%': { transform: 'translateY(0)' },
        },
        pulseGentle: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.8' },
        },
      },
      // Glassmorphism utilities
      backdropBlur: {
        'apple': '20px',
        'apple-sm': '10px',
        'apple-lg': '40px',
      },
      // Grid system for panels
      gridTemplateColumns: {
        'apple-3-panel': '300px 1fr 350px',
        'apple-mobile': '1fr',
      },
      // Apple's breakpoints
      screens: {
        'xs': '475px',
        'apple-sm': '390px',  // iPhone size
        'apple-md': '768px',  // iPad portrait
        'apple-lg': '1024px', // iPad landscape
        'apple-xl': '1440px', // MacBook
        'apple-2xl': '1728px', // Studio Display
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
    // Custom Apple-style utilities
    function({ addUtilities }) {
      const appleUtilities = {
        '.glass': {
          background: 'rgba(255, 255, 255, 0.8)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(255, 255, 255, 0.2)',
          boxShadow: '0 8px 32px rgba(31, 38, 135, 0.37)',
        },
        '.glass-dark': {
          background: 'rgba(0, 0, 0, 0.3)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3)',
        },
        '.apple-button': {
          borderRadius: '10px',
          padding: '12px 24px',
          fontWeight: '600',
          fontSize: '17px',
          lineHeight: '22px',
          transition: 'all 0.2s ease',
          cursor: 'pointer',
        },
        '.apple-button-primary': {
          background: '#007AFF',
          color: 'white',
          border: 'none',
          '&:hover': {
            background: '#0056CC',
            transform: 'translateY(-1px)',
          },
          '&:active': {
            transform: 'translateY(0)',
          },
        },
        '.apple-input': {
          borderRadius: '10px',
          padding: '12px 16px',
          fontSize: '17px',
          lineHeight: '22px',
          border: '1px solid rgba(60, 60, 67, 0.29)',
          backgroundColor: 'rgba(255, 255, 255, 0.8)',
          backdropFilter: 'blur(20px)',
          transition: 'all 0.2s ease',
          '&:focus': {
            outline: 'none',
            borderColor: '#007AFF',
            boxShadow: '0 0 0 3px rgba(0, 122, 255, 0.1)',
          },
        },
        '.apple-card': {
          background: 'rgba(255, 255, 255, 0.8)',
          backdropFilter: 'blur(20px)',
          borderRadius: '14px',
          border: '1px solid rgba(255, 255, 255, 0.2)',
          boxShadow: '0 4px 16px rgba(0, 0, 0, 0.1)',
        },
        '.text-balance': {
          textWrap: 'balance',
        },
      }
      addUtilities(appleUtilities)
    }
  ],
}