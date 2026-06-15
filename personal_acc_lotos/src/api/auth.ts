import { apiFetch, AUTH_TIMEOUT_MS } from './client'

export type AuthStatus = {
  authenticated: boolean
  phone: string | null
  phoneDisplay: string | null
  clientName: string | null
}

export type PublicConfig = {
  studioName: string
  bookingUrl: string
  studioPhone?: string
  vkGroupId?: number
}

export type AuthStep = 'name' | 'password'

export type PhoneCheckResponse = {
  step: AuthStep
  phone: string
  requiresSurname: boolean
}

export type VerifyResponse = {
  success: boolean
  authenticated?: boolean
  phone: string
  phoneDisplay: string
  clientName?: string | null
  needsPassword: boolean
}

export type AuthSessionPayload = {
  phone: string
  phoneDisplay: string
  clientName?: string | null
}

export type UserPrefs = {
  colorScheme: 'light' | 'dark'
  welcomeBannerSeen: boolean
}

export type BootResponse = {
  config: PublicConfig
  auth: AuthStatus
  prefs?: UserPrefs
}

const DEFAULT_PREFS: UserPrefs = {
  colorScheme: 'light',
  welcomeBannerSeen: false,
}

function normalizePrefs(prefs?: Partial<UserPrefs> | null): UserPrefs {
  return {
    colorScheme: prefs?.colorScheme === 'dark' ? 'dark' : 'light',
    welcomeBannerSeen: Boolean(prefs?.welcomeBannerSeen),
  }
}

function normalizeBoot(raw: BootResponse): BootResponse & { prefs: UserPrefs } {
  return {
    ...raw,
    prefs: normalizePrefs(raw.prefs),
  }
}

const bootInflight = new Map<number, Promise<BootResponse & { prefs: UserPrefs }>>()

export function clearBootCache(vkUserId?: number) {
  if (vkUserId != null) {
    bootInflight.delete(vkUserId)
  } else {
    bootInflight.clear()
  }
}

export function fetchPublicConfig() {
  return apiFetch<PublicConfig>('/api/config/public')
}

export function fetchBoot(vkUserId: number) {
  const inflight = bootInflight.get(vkUserId)
  if (inflight) {
    return inflight
  }

  const request = apiFetch<BootResponse>(`/api/boot?vk_user_id=${vkUserId}`)
    .then(normalizeBoot)
    .finally(() => {
    bootInflight.delete(vkUserId)
  })
  bootInflight.set(vkUserId, request)
  return request
}

export function fetchAuthStatus(vkUserId: number) {
  return apiFetch<AuthStatus>(`/api/auth/status?vk_user_id=${vkUserId}`)
}

export function submitPhone(vkUserId: number, phone: string) {
  return apiFetch<PhoneCheckResponse>('/api/auth/phone', {
    method: 'POST',
    timeoutMs: AUTH_TIMEOUT_MS,
    body: JSON.stringify({
      vk_user_id: vkUserId,
      phone,
    }),
  })
}

export function verifyName(vkUserId: number, phone: string, name: string) {
  return apiFetch<VerifyResponse>('/api/auth/verify', {
    method: 'POST',
    timeoutMs: AUTH_TIMEOUT_MS,
    body: JSON.stringify({ vk_user_id: vkUserId, phone, name }),
  })
}

export function verifyPassword(vkUserId: number, phone: string, password: string) {
  return apiFetch<VerifyResponse>('/api/auth/password/verify', {
    method: 'POST',
    timeoutMs: AUTH_TIMEOUT_MS,
    body: JSON.stringify({ vk_user_id: vkUserId, phone, password }),
  })
}

export function setPassword(
  vkUserId: number,
  phone: string,
  password: string,
  passwordConfirm: string,
) {
  return apiFetch<VerifyResponse>('/api/auth/password/set', {
    method: 'POST',
    timeoutMs: AUTH_TIMEOUT_MS,
    body: JSON.stringify({
      vk_user_id: vkUserId,
      phone,
      password,
      password_confirm: passwordConfirm,
    }),
  })
}

export function logout(vkUserId: number) {
  return apiFetch<{ success: boolean }>('/api/auth/logout', {
    method: 'POST',
    body: JSON.stringify({ vk_user_id: vkUserId }),
  })
}
