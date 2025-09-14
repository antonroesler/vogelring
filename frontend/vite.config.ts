import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'
import fs from 'fs'
import { execSync } from 'child_process'
import { extractChangelog, getLatestVersion } from './scripts/extract-changelog.js'

// Generate a version string and extract changelog data
const generateVersionInfo = () => {
  const now = new Date()
  const buildTime = now.toISOString()
  
  // Extract changelog data
  const changelog = extractChangelog()
  const backendVersion = getLatestVersion(changelog)
  
  let version = process.env.npm_package_version || backendVersion || '1.0.0'
  
  // Try to get git commit hash
  try {
    const gitHash = execSync('git rev-parse --short HEAD').toString().trim()
    version = `${version}-${gitHash}`
  } catch (e) {
    // No git or not a git repository, use timestamp instead
    const timestamp = Math.floor(now.getTime() / 1000)
    version = `${version}-local-${timestamp}`
  }
  
  // Write version info to public directory
  const versionInfo = {
    version,
    buildTime,
    backendVersion
  }
  
  // Ensure public directory exists
  if (!fs.existsSync('./public')) {
    fs.mkdirSync('./public', { recursive: true })
  }
  
  fs.writeFileSync('./public/version.json', JSON.stringify(versionInfo, null, 2))
  fs.writeFileSync('./public/changelog.json', JSON.stringify(changelog, null, 2))
  
  return {
    version,
    buildTime,
    backendVersion
  }
}

const versionInfo = generateVersionInfo()

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  build: {
    assetsInlineLimit: 0,
    rollupOptions: {
      output: {
        // Use content hash for all files to ensure cache busting
        entryFileNames: `assets/[name].[hash].js`,
        chunkFileNames: `assets/[name].[hash].js`,
        assetFileNames: `assets/[name].[hash].[ext]`
      }
    }
  },
  define: {
    __APP_VERSION__: JSON.stringify(versionInfo.version),
    __BACKEND_VERSION__: JSON.stringify(versionInfo.backendVersion),
    global: 'window'
  }
})
