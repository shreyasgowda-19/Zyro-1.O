import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const apiProxy = {
  target: 'http://127.0.0.1:8000',
  changeOrigin: true,
  bypass: (req: any) => {
    // If the browser requests an HTML document (SPA page navigation or reload),
    // bypass the proxy and serve /index.html for React Router.
    if (req.headers.accept?.includes('text/html')) {
      return '/index.html';
    }
  },
};

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/auth': apiProxy,
      '/users': apiProxy,
      '/payments': apiProxy,
      '/transactions': apiProxy,
      '/risk': apiProxy,
      '/review': apiProxy,
      '/budgets': apiProxy,
      '/goals': apiProxy,
      '/alerts': apiProxy,
      '/guidance': apiProxy,
      '/accounting': apiProxy,
      '/demo': apiProxy,
      '/health': apiProxy,
      '/accounts': apiProxy,
      '/statements': apiProxy,
    }
  }
})
