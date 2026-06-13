import type { StudioPlace } from '../types/studio'

export function buildStudioRouteUrl(place: StudioPlace | null | undefined): string | null {
  if (!place) return null
  if (place.mapUrl) return place.mapUrl
  if (place.latitude != null && place.longitude != null) {
    return `https://yandex.ru/maps/?rtext=~${place.latitude},${place.longitude}&rtt=auto`
  }
  if (place.address) {
    return `https://yandex.ru/maps/?text=${encodeURIComponent(place.address)}`
  }
  return null
}
