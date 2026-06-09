import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      injectRegister: 'auto',
      scope: '/',
      manifest: {
        name: 'Human-Behavior-Aware Baseball Optimizer',
        short_name: 'BaseballOpt',
        start_url: '/',
        theme_color: '#0E3386',
        icons: [
          {
            src: '/icon.png',
            sizes: '192x192',
            type: 'image/png'
          }
        ]
      },
      workbox: {
        maximumFileSizeToCacheInBytes: 3000000,
        globPatterns: ['**/*.{js,css,html,ico,png,svg}']
      }
    })
  ],
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8080',
        changeOrigin: true,
      }
    }
  },
  build: {
    outDir: '../static',
    emptyOutDir: true,
  }
})
