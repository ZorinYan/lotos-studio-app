import { vkLaunchHeaders } from '../vkLaunch'
import { isSessionExpiredError, notifySessionExpired } from './session'

const API_BASE = import.meta.env.VITE_API_BASE ?? ''
export type ApiFetchOptions = RequestInit & {
  timeoutMs?: number
}

const API_TIMEOUT_MS = 45_000
export const AUTH_TIMEOUT_MS = 90_000

export type ApiErrorBody = {
  code?: string
  message?: string
}

export class ApiError extends Error {
  code: string

  constructor(code: string, message: string) {
    super(message)
    this.code = code
  }
}

async function parseError(response: Response): Promise<ApiError> {
  try {
    const payload = await response.json()
    const detail = payload.detail
    if (typeof detail === 'object' && detail !== null) {
      return new ApiError(
        String(detail.code ?? 'unknown'),
        String(detail.message ?? 'Неизвестная ошибка'),
      )
    }
    if (typeof detail === 'string') {
      return new ApiError('unknown', detail)
    }
  } catch {
    // ignore json parse errors
  }
  return new ApiError('unknown', `Ошибка сервера (${response.status})`)
}

function ensureApiBase(): void {
  if (API_BASE || !import.meta.env.PROD) {
    return
  }
  throw new ApiError(
    'api_not_configured',
    'Не настроен VITE_API_BASE на Vercel. Укажите URL API с Render.',
  )
}

export function withRefresh(path: string, refresh = false): string {
  if (!refresh) return path
  return path.includes('?') ? `${path}&refresh=1` : `${path}?refresh=1`
}

export async function apiFetch<T>(path: string, init?: ApiFetchOptions): Promise<T> {
  ensureApiBase()

  const timeoutMs = init?.timeoutMs ?? API_TIMEOUT_MS
  const { timeoutMs: _omitTimeout, ...fetchInit } = init ?? {}
  void _omitTimeout

  const controller = new AbortController()
  const timeoutId = window.setTimeout(() => controller.abort(), timeoutMs)

  let response: Response
  try {
    response = await fetch(`${API_BASE}${path}`, {
      ...fetchInit,
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
        ...vkLaunchHeaders(),
        ...(fetchInit.headers ?? {}),
      },
    })
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new ApiError(
        'timeout',
        'Сервер долго не отвечает. Подождите немного и попробуйте снова.',
      )
    }
    throw new ApiError(
      'network',
      API_BASE.includes('onrender.com')
        ? 'Не удалось связаться с API на Render. Без VPN домен onrender.com часто недоступен из РФ. Локально: npm run dev:api и пустой VITE_API_BASE.'
        : 'Не удалось связаться с API. Локально запустите npm run dev:api в отдельном терминале.',
    )
  } finally {
    window.clearTimeout(timeoutId)
  }

  if (!response.ok) {
    const error = await parseError(response)
    if (response.status === 401 || isSessionExpiredError(error)) {
      notifySessionExpired(error.message, path)
    }
    throw error
  }

  const contentType = response.headers.get('content-type') ?? ''
  if (!contentType.includes('application/json')) {
    throw new ApiError(
      'invalid_response',
      'API вернул некорректный ответ. Проверьте VITE_API_BASE на Vercel.',
    )
  }

  return response.json() as Promise<T>
}
