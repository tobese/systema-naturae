import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  base: process.env.VITE_BASE ?? '/',
  resolve: {
    alias: { '@shared': path.resolve(__dirname, '../../../shared/src') },
    dedupe: ['react', 'react-dom'],
  },
})
