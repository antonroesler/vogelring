/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_CARTO_BASEMAP_KEY?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

declare const __APP_VERSION__: string
declare const __BACKEND_VERSION__: string
