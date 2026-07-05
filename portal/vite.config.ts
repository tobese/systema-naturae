import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  base: process.env.VITE_BASE ?? '/',
  resolve: {
    alias: { '@shared': path.resolve(__dirname, '../shared/src') },
    dedupe: ['react', 'react-dom'],
  },
  build: {
    rollupOptions: {
      // Multi-page: main portal + bare-bones (graph + side panels) variant.
      input: {
        main: path.resolve(__dirname, 'index.html'),
        bare: path.resolve(__dirname, 'bare.html'),
      },
    },
  },
})
