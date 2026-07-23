import path from 'node:path'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  preview: {
    // Railway's public domain isn't known until after the first deploy,
    // and Vite's preview server rejects unrecognized Host headers by
    // default (DNS-rebinding protection) -- this is a public demo app,
    // not internal tooling, so allowing any host here is fine.
    allowedHosts: true,
  },
})
