const API_BASE = import.meta.env.VITE_API_BASE ?? ''

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

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
  })

  if (!response.ok) {
    throw await parseError(response)
  }

  return response.json() as Promise<T>
}
