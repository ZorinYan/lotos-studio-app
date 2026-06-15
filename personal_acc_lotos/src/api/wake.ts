const API_BASE = import.meta.env.VITE_API_BASE ?? ''

/** Разбудить API на Render Free (лёгкий запрос без авторизации). */
export async function wakeApi(timeoutMs = 90_000): Promise<void> {
  if (API_BASE === '' && import.meta.env.PROD) {
    return
  }

  const controller = new AbortController()
  const timeoutId = window.setTimeout(() => controller.abort(), timeoutMs)

  try {
    await fetch(`${API_BASE}/health`, {
      method: 'GET',
      signal: controller.signal,
      cache: 'no-store',
    })
  } finally {
    window.clearTimeout(timeoutId)
  }
}
