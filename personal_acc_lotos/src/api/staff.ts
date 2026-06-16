import { apiFetch, AUTH_TIMEOUT_MS } from './client'

export type StaffHomeSection = {
  id: string
  title: string
  description: string
  status: 'coming_soon' | 'active'
}

export type StaffHomeData = {
  staffName: string
  staffId: number
  specialization: string | null
  positionTitle: string | null
  phoneDisplay: string | null
  sections: StaffHomeSection[]
}

export type StaffSessionPayload = {
  phone: string
  phoneDisplay: string
  staffName: string
  staffId: number
  specialization?: string | null
  positionTitle?: string | null
}

export type StaffAuthResponse = StaffSessionPayload & {
  success: boolean
  authenticated?: boolean
  role: 'staff'
}

export function verifyStaffPassword(vkUserId: number, phone: string, password: string) {
  return apiFetch<StaffAuthResponse>('/api/staff/auth/password/verify', {
    method: 'POST',
    timeoutMs: AUTH_TIMEOUT_MS,
    body: JSON.stringify({ vk_user_id: vkUserId, phone, password }),
  })
}

export function setStaffPassword(
  vkUserId: number,
  phone: string,
  password: string,
  passwordConfirm: string,
) {
  return apiFetch<StaffAuthResponse>('/api/staff/auth/password/set', {
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

export function fetchStaffHome(vkUserId: number) {
  return apiFetch<StaffHomeData>(`/api/staff/home?vk_user_id=${vkUserId}`)
}

export type StaffSettings = {
  staffName: string | null
  phoneDisplay: string | null
  colorScheme: 'light' | 'dark'
}

export function fetchStaffSettings(vkUserId: number) {
  return apiFetch<StaffSettings>(`/api/staff/settings?vk_user_id=${vkUserId}`).then((raw) => ({
    staffName: raw.staffName ?? null,
    phoneDisplay: raw.phoneDisplay ?? null,
    colorScheme: raw.colorScheme === 'dark' ? 'dark' : 'light',
  }))
}

export function updateStaffSettings(
  vkUserId: number,
  patch: { colorScheme?: 'light' | 'dark' },
) {
  return apiFetch<StaffSettings>('/api/staff/settings', {
    method: 'PUT',
    body: JSON.stringify({
      vk_user_id: vkUserId,
      color_scheme: patch.colorScheme,
    }),
  }).then((raw) => ({
    staffName: raw.staffName ?? null,
    phoneDisplay: raw.phoneDisplay ?? null,
    colorScheme: raw.colorScheme === 'dark' ? 'dark' : 'light',
  }))
}

export type StaffActivityClient = {
  clientId: number
  fullName: string
  phoneDisplay: string | null
  visitsToTrainer: number
}

export type StaffActivityClientsResponse = {
  clients: StaffActivityClient[]
}

export function fetchStaffActivityClients(
  vkUserId: number,
  activityId: number,
  activityDate: string,
) {
  return apiFetch<StaffActivityClientsResponse>('/api/staff/activity/clients', {
    method: 'POST',
    body: JSON.stringify({
      vk_user_id: vkUserId,
      activity_id: activityId,
      activity_date: activityDate,
    }),
  })
}
