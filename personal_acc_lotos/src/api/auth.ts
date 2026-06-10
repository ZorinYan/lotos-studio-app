import { apiFetch } from './client'

export type AuthStatus = {
  authenticated: boolean
  phone: string | null
  phoneDisplay: string | null
  clientName: string | null
}

export type PublicConfig = {
  studioName: string
  bookingUrl: string
}

export type PhoneCheckResponse = {
  step: 'name'
  phone: string
  requiresSurname: boolean
}

export type VerifyResponse = {
  success: boolean
  phone: string
  phoneDisplay: string
}

export function fetchPublicConfig() {
  return apiFetch<PublicConfig>('/api/config/public')
}

export function fetchAuthStatus(vkUserId: number) {
  return apiFetch<AuthStatus>(`/api/auth/status?vk_user_id=${vkUserId}`)
}

export function submitPhone(vkUserId: number, phone: string) {
  return apiFetch<PhoneCheckResponse>('/api/auth/phone', {
    method: 'POST',
    body: JSON.stringify({ vk_user_id: vkUserId, phone }),
  })
}

export function verifyName(vkUserId: number, phone: string, name: string) {
  return apiFetch<VerifyResponse>('/api/auth/verify', {
    method: 'POST',
    body: JSON.stringify({ vk_user_id: vkUserId, phone, name }),
  })
}

export function logout(vkUserId: number) {
  return apiFetch<{ success: boolean }>('/api/auth/logout', {
    method: 'POST',
    body: JSON.stringify({ vk_user_id: vkUserId }),
  })
}
