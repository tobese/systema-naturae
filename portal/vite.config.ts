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
      // Multi-page: main portal + per-kingdom entry points.
      input: {
        main: path.resolve(__dirname, 'index.html'),
        bare: path.resolve(__dirname, 'bare.html'),
        'bare-plantae': path.resolve(__dirname, 'bare-plantae.html'),
        'bare-fungi': path.resolve(__dirname, 'bare-fungi.html'),
        'bare-chromista': path.resolve(__dirname, 'bare-chromista.html'),
        'bare-protozoa': path.resolve(__dirname, 'bare-protozoa.html'),
        'bare-archaea': path.resolve(__dirname, 'bare-archaea.html'),
        animalia: path.resolve(__dirname, 'animalia.html'),
        plantae: path.resolve(__dirname, 'plantae.html'),
        fungi: path.resolve(__dirname, 'fungi.html'),
        chromista: path.resolve(__dirname, 'chromista.html'),
        protozoa: path.resolve(__dirname, 'protozoa.html'),
        archaea: path.resolve(__dirname, 'archaea.html'),
      },
    },
  },
})
