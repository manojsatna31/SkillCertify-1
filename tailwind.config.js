/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',
    './static/js/**/*.js'
  ],
  theme: {
    extend: {
      colors: {
        primary: 'rgb(var(--color-primary))',
        secondary: 'rgb(var(--color-secondary))',
        success: 'rgb(var(--color-success))',
        danger: 'rgb(var(--color-danger))',
        dark: {
          800: 'rgb(var(--color-dark-800))',
          900: 'rgb(var(--color-dark-900))'
        }
      }
    },
  },
  plugins: [],
}
