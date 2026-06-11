import { resolve } from 'node:path'
import type { Plugin } from 'vite'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

/** В продакшене Vite оставляет только main.js — подключаем vkInit раньше React. */
function vkInitFirst(): Plugin {
  return {
    name: 'vk-init-first',
    transformIndexHtml: {
      order: 'post',
      handler(html, ctx) {
        if (!ctx.bundle) return html
        const chunk = Object.values(ctx.bundle).find(
          (item) => item.type === 'chunk' && item.name === 'vkInit',
        )
        if (!chunk || chunk.type !== 'chunk') return html
        const tag = `<script type="module" crossorigin src="/${chunk.fileName}"></script>`
        return html.replace(
          /(<script type="module" crossorigin src="\/assets\/index-[^"]+\.js"><\/script>)/,
          `${tag}\n    $1`,
        )
      },
    },
  }
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), vkInitFirst()],
  build: {
    rollupOptions: {
      input: {
        vkInit: resolve(__dirname, 'src/vk-init.ts'),
        index: resolve(__dirname, 'index.html'),
      },
    },
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8080',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://127.0.0.1:8080',
        changeOrigin: true,
      },
    },
  },
})
