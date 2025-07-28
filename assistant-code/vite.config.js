import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { viteStaticCopy } from 'vite-plugin-static-copy'

export default defineConfig({
  plugins: [
    react(),
    viteStaticCopy({
      targets: [
        // Add this NEW target ABOVE the others:
        { 
          src: 'node_modules/idb/build/index.js', 
          dest: 'Database',
          rename: 'idb.js'
        },
        { 
          src: 'src/extension/manifest.json', 
          dest: '.' 
        },
        { 
          src: 'src/extension/background.js', 
          dest: '.',
          transform: (content) => content.toString().replace(
            /from\s+['"](\.\.\/Database\/db\.js)['"]/g, 
            'from "./Database/db.js"'
          )
        },
        { 
          src: 'src/Database/db.js', 
          dest: 'Database' 
        },
        { 
          src: 'src/extension/contentScript.js', 
          dest: '.' 
        }
      ]
    })
  ],
  build: {
    rollupOptions: {
      output: {
        format: 'esm',
        entryFileNames: '[name].js',
        chunkFileNames: '[name].js',
        assetFileNames: '[name].[ext]'
      }
    }
  }
})