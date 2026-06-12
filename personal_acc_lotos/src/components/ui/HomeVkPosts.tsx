import { useCallback, useRef, useState } from 'react'
import type { VkWallPost } from '../../types/studio'
import { openVkWallPost } from '../../vkBridge'
import './HomeVkPosts.css'

type HomeVkPostsProps = {
  posts: VkWallPost[]
}

function formatPostDate(timestamp: number): string {
  if (!timestamp) return ''
  return new Intl.DateTimeFormat('ru-RU', {
    day: 'numeric',
    month: 'short',
  }).format(new Date(timestamp * 1000))
}

export function HomeVkPosts({ posts }: HomeVkPostsProps) {
  const trackRef = useRef<HTMLDivElement>(null)
  const [activeIndex, setActiveIndex] = useState(0)

  const updateActiveIndex = useCallback(() => {
    const track = trackRef.current
    if (!track || posts.length === 0) return

    const card = track.querySelector<HTMLElement>('.home-vk-posts__card')
    if (!card) return

    const gap = 12
    const cardWidth = card.offsetWidth + gap
    const index = Math.round(track.scrollLeft / cardWidth)
    setActiveIndex(Math.max(0, Math.min(index, posts.length - 1)))
  }, [posts.length])

  const scrollToIndex = (index: number) => {
    const track = trackRef.current
    if (!track) return

    const card = track.querySelector<HTMLElement>('.home-vk-posts__card')
    if (!card) return

    const gap = 12
    track.scrollTo({
      left: index * (card.offsetWidth + gap),
      behavior: 'smooth',
    })
    setActiveIndex(index)
  }

  if (posts.length === 0) {
    return null
  }

  return (
    <section className="home-vk-posts" aria-label="Новости студии">
      <h3 className="lotos-section-title home-vk-posts__title">Новости студии</h3>
      <div
        ref={trackRef}
        className="home-vk-posts__track"
        onScroll={updateActiveIndex}
      >
        {posts.map((post) => (
          <button
            key={post.id}
            type="button"
            className="home-vk-posts__card lotos-card"
            onClick={() => void openVkWallPost(post.ownerId, post.id)}
          >
            {post.imageUrl && (
              <img src={post.imageUrl} alt="" className="home-vk-posts__image" loading="lazy" />
            )}
            <div className="home-vk-posts__body">
              {post.text && <p className="home-vk-posts__text">{post.text}</p>}
              <span className="home-vk-posts__meta">
                {formatPostDate(post.date)}
                <span aria-hidden="true"> · </span>
                Читать в VK
              </span>
            </div>
          </button>
        ))}
      </div>
      {posts.length > 1 && (
        <div className="home-vk-posts__dots" role="tablist" aria-label="Слайды новостей">
          {posts.map((post, index) => (
            <button
              key={post.id}
              type="button"
              role="tab"
              className={`home-vk-posts__dot${index === activeIndex ? ' home-vk-posts__dot--active' : ''}`}
              aria-label={`Новость ${index + 1}`}
              aria-selected={index === activeIndex}
              onClick={() => scrollToIndex(index)}
            />
          ))}
        </div>
      )}
    </section>
  )
}
