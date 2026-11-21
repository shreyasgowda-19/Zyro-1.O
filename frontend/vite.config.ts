import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/auth': 'http://127.0.0.1:8000',
      '/users': 'http://127.0.0.1:8000',
      '/payments': 'http://127.0.0.1:8000',
      '/transactions': 'http://127.0.0.1:8000',
      '/risk': 'http://127.0.0.1:8000',
      '/review': 'http://127.0.0.1:8000',
      '/budgets': 'http://127.0.0.1:8000',
      '/goals': 'http://127.0.0.1:8000',
      '/alerts': 'http://127.0.0.1:8000',
      '/guidance': 'http://127.0.0.1:8000',
      '/accounting': 'http://127.0.0.1:8000',
      '/demo': 'http://127.0.0.1:8000',
      '/health': 'http://127.0.0.1:8000',
    }
  }
})
