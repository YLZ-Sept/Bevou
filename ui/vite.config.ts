import {fileURLToPath, URL} from 'node:url'
import type {ProxyOptions} from 'vite'
import {defineConfig, loadEnv} from 'vite'
import vue from '@vitejs/plugin-vue'
import vueJsx from '@vitejs/plugin-vue-jsx'
import DefineOptions from 'unplugin-vue-define-options/vite'
import path from 'path'
import {createHtmlPlugin} from 'vite-plugin-html'
import fs from 'fs'
// import vueDevTools from 'vite-plugin-vue-devtools'
const envDir = './env'
// 自定义插件：重命名入口文件
const renameHtmlPlugin = (outDir: string, entry: string) => {
  return {
    name: 'rename-html',
    closeBundle: () => {
      const buildDir = path.resolve(__dirname, outDir)
      const oldFile = path.join(buildDir, entry)
      const newFile = path.join(buildDir, 'index.html')

      // 检查文件是否存在
      if (fs.existsSync(oldFile)) {
        // 删除已存在的 index.html
        if (fs.existsSync(newFile)) {
          fs.unlinkSync(newFile)
        }
        // 重命名文件
        fs.renameSync(oldFile, newFile)
      }
    },
  }
}
// 开发环境：把 /admin/*、/chat/* 这类无扩展名的页面请求回退到对应入口 html
// （生产由后端 page_not_found 兜底，Vite dev 本身只按文件路径提供服务）
const devHistoryFallback = (base: string, entry: string) => {
  const normalizedBase = base.endsWith('/') ? base : `${base}/`
  return {
    name: 'dev-history-fallback',
    configureServer(server: any) {
      server.middlewares.use((req: any, _res: any, next: any) => {
        if (req.method !== 'GET' || !(req.headers.accept || '').includes('text/html')) {
          return next()
        }
        const [pathname, query] = (req.url || '').split('?')
        const rest = pathname.slice(normalizedBase.length)
        if (pathname.startsWith(normalizedBase) && rest && !/\.[a-zA-Z0-9]+$/.test(rest)) {
          req.url = `/${entry}${query ? `?${query}` : ''}`
        }
        next()
      })
    },
  }
}

// https://vite.dev/config/
export default defineConfig((conf: any) => {
  const mode = conf.mode
  const ENV = loadEnv(mode, envDir)
  const proxyConf: Record<string, string | ProxyOptions> = {}
  proxyConf['/admin/api'] = {
    target: 'http://127.0.0.1:8080',
    changeOrigin: true,
  }
  proxyConf['/chat/api'] = {
    target: 'http://127.0.0.1:8080',
    changeOrigin: true,
  }
  proxyConf['/doc'] = {
    target: 'http://127.0.0.1:8080',
    changeOrigin: true,
    rewrite: (path: string) => path.replace(ENV.VITE_BASE_PATH, '/'),
  }
  proxyConf['/schema'] = {
    target: 'http://127.0.0.1:8080',
    changeOrigin: true,
    rewrite: (path: string) => path.replace(ENV.VITE_BASE_PATH, '/'),
  }
  proxyConf['/static'] = {
    target: 'http://127.0.0.1:8080',
    changeOrigin: true,
    rewrite: (path: string) => path.replace(ENV.VITE_BASE_PATH, '/'),
  }

  // 前端静态资源转发到本身
  proxyConf[`^${ENV.VITE_BASE_PATH}.+\/oss\/file\/.*$`] = {
    target: `http://127.0.0.1:8080`,
    changeOrigin: true,
  }
  // 前端静态资源转发到本身
  proxyConf[`^${ENV.VITE_BASE_PATH}oss\/file\/.*$`] = {
    target: `http://127.0.0.1:8080`,
    changeOrigin: true,
  }
  proxyConf[`^${ENV.VITE_BASE_PATH}oss\/get_url\/.*$`] = {
    target: `http://127.0.0.1:8080`,
    changeOrigin: true,
  }
  // 前端静态资源转发到本身
  proxyConf[ENV.VITE_BASE_PATH] = {
    target: `http://127.0.0.1:${ENV.VITE_APP_PORT}`,
    changeOrigin: true,
    rewrite: (path: string) => path.replace(ENV.VITE_BASE_PATH, '/'),
  }

  return {
    preflight: false,
    lintOnSave: false,
    base: './',
    envDir: envDir,
    // admin/chat 两个 dev server 共用 node_modules/.vite 会互相抢占依赖缓存（EPERM），按 mode 隔离
    cacheDir: `node_modules/.vite-${mode}`,
    plugins: [
      vue(),
      vueJsx(),
      DefineOptions(),
      createHtmlPlugin({template: ENV.VITE_ENTRY}),
      renameHtmlPlugin(`dist${ENV.VITE_BASE_PATH}`, ENV.VITE_ENTRY),
      devHistoryFallback(ENV.VITE_BASE_PATH, ENV.VITE_ENTRY),
    ],
    server: {
      cors: true,
      host: '0.0.0.0',
      port: Number(ENV.VITE_APP_PORT),
      strictPort: true,
      proxy: proxyConf,
    },
    build: {
      outDir: `dist${ENV.VITE_BASE_PATH}`,
      target: 'es2022',
      rollupOptions: {
        input: ENV.VITE_ENTRY,
      },
    },
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url)),
      },
    },
  }
})
