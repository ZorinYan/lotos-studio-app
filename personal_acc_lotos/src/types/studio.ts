export type VkWallPost = {
  id: number
  ownerId: number
  date: number
  text: string
  imageUrl: string | null
  postUrl: string
}

export type VkStory = {
  id: number
  ownerId: number
  previewUrl: string
  linkUrl: string
}

export type StudioPlace = {
  title: string | null
  address: string | null
  phone: string | null
  hours: string | null
  latitude: number | null
  longitude: number | null
  mapUrl: string | null
  groupUrl: string | null
  ownerId: number
}

export type StudioFeed = {
  posts: VkWallPost[]
  stories: VkStory[]
  storiesAvailable: boolean
  place: StudioPlace | null
}
