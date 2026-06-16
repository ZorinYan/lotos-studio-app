import type { StudioFeed } from '../types/studio'
import { apiFetch, withRefresh } from './client'

const EMPTY_STUDIO_FEED: StudioFeed = {
  posts: [],
  stories: [],
  storiesAvailable: false,
  place: null,
}

export function fetchStudioFeed(refresh = false) {
  return apiFetch<StudioFeed>(withRefresh('/api/studio/feed', refresh))
}

export { EMPTY_STUDIO_FEED }
