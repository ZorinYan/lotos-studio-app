import { Icon24StoryOutline } from '@vkontakte/icons'
import type { VkStory } from '../../types/studio'
import { openVkUrl } from '../../vkBridge'
import './HomeVkStories.css'

type HomeVkStoriesProps = {
  stories: VkStory[]
  storiesAvailable: boolean
  groupUrl: string | null
}

export function HomeVkStories({ stories, storiesAvailable, groupUrl }: HomeVkStoriesProps) {
  if (stories.length > 0) {
    return (
      <section className="home-vk-stories" aria-label="Истории студии">
        <div className="home-vk-stories__head">
          <h3 className="lotos-section-title">Истории</h3>
        </div>
        <div className="home-vk-stories__row">
          {stories.map((story) => (
            <button
              key={story.id}
              type="button"
              className="home-vk-stories__item"
              onClick={() => void openVkUrl(story.linkUrl)}
            >
              <span className="home-vk-stories__ring">
                <img src={story.previewUrl} alt="" className="home-vk-stories__preview" />
              </span>
              <span className="home-vk-stories__label">Студия</span>
            </button>
          ))}
        </div>
      </section>
    )
  }

  if (!storiesAvailable || !groupUrl) {
    return null
  }

  return (
    <section className="home-vk-stories" aria-label="Истории студии">
      <button
        type="button"
        className="home-vk-stories__fallback lotos-card"
        onClick={() => void openVkUrl(groupUrl)}
      >
        <Icon24StoryOutline className="home-vk-stories__fallback-icon" />
        <span>
          <strong>Смотреть истории студии</strong>
          <small>Откроется сообщество VK</small>
        </span>
      </button>
    </section>
  )
}
