import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  base: '/FFXIV_PatchScan/',
  server: {
    fs: {
      allow: ['.']
    }
  }
})