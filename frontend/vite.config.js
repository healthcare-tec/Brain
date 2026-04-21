import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // Use 127.0.0.1 instead of 0.0.0.0 to avoid the proot-distro / Termux
    // kernel restriction that causes: uv_interface_addresses Unknown system error 13
    host: '127.0.0.1',
    port: 8080,
    strictPort: true,
    // Explicit HMR config avoids network interface discovery (proot-distro fix)
    hmr: {
      host: '127.0.0.1',
      port: 8080,
    },
    proxy: {
      '/api': {
        // Local backend — no Docker, no service name
        target: 'http://127.0.0.1:8085',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://127.0.0.1:8085',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
  },
})
