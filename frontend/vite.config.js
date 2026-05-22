import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

const apiUrl = process.env.VITE_API_URL || 'http://localhost:9000'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    vueDevTools(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
  server: {
    port: 5174,
    proxy: {
      '/api': {
        target: apiUrl,
        changeOrigin: true,
      },
      '/health': {
        target: apiUrl,
        changeOrigin: true,
      },
      '/docs': {
        target: apiUrl,
        changeOrigin: true,
      },
      '/ws': {
        target: apiUrl,
        changeOrigin: true,
        ws: true,
      },
      '/uiautodev': {
        target: 'https://uiauto2.devsleep.com',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/uiautodev/, ''),
        ws: true,
        secure: true,
      },
    },
  },
})
