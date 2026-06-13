import { vkLaunchHeaders } from '../vkLaunch'
import { isSessionExpiredError, notifySessionExpired } from './session'

const API_BASE = import.meta.env.VITE_API_BASE ?? ''
const API_TIMEOUT_MS = 25_000

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

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  ensureApiBase()

  const controller = new AbortController()
  const timeoutId = window.setTimeout(() => controller.abort(), API_TIMEOUT_MS)

  let response: Response
  try {
    response = await fetch(`${API_BASE}${path}`, {
      ...init,
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
        ...vkLaunchHeaders(),
        ...(init?.headers ?? {}),
      },
    })
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new ApiError(
        'timeout',
        'API не отвечает. Если сервер на Render Free — подождите до минуты и попробуйте снова.',
      )
    }
    throw new ApiError(
      'network',
      'Не удалось связаться с API. Проверьте VITE_API_BASE и что сервер на Render запущен.',
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
