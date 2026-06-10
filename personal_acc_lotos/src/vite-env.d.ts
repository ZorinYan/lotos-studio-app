/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE: string
  readonly VITE_SKIP_VK_BRIDGE: string
  readonly VITE_DEV_VK_USER_ID: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
