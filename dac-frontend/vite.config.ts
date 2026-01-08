import { defineConfig, loadEnv } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'

const env = loadEnv("all", false);
const apiHost = env.VITE_API_HOST || 'localhost';
const apiPort = env.VITE_API_PORT || '8000';
const apiTarget = `http://${apiHost}:${apiPort}`;


// https://vite.dev/config/
export default defineConfig({
  plugins: [svelte()],
  server: {
    proxy: {
      "/api": {
        target: apiTarget,
        changeOrigin: true,
      },
      '/app': {
        target: apiTarget,
        changeOrigin: true,
        ws: true,
      },
      '/mpl': {
        target: apiTarget,
        changeOrigin: true,
        ws: true,
        rewrite: (path) => path.replace(/^\/mpl/, ''),
      },

    }
  }
})
