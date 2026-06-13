import { useState } from 'react'
import {
  STUDIO_CONTACT_TOPICS,
  type StudioContactContext,
  type StudioContactTopic,
} from '../../content/studioGuide'
import { StudioContactSheet } from './StudioContactSheet'
import './StudioContactSection.css'

type StudioContactSectionProps = {
  vkGroupId?: number | null
  context: StudioContactContext
  onNotice?: (message: string) => void
}

export function StudioContactSection({
  vkGroupId,
  context,
  onNotice,
}: StudioContactSectionProps) {
  const [activeTopic, setActiveTopic] = useState<StudioContactTopic | null>(null)

  function handleTopicClick(topic: StudioContactTopic) {
    if (!vkGroupId) {
      onNotice?.('Напишите нам в сообщения сообщества VK — кнопка появится после настройки группы.')
      return
    }
    setActiveTopic(topic)
  }

  return (
    <>
      <section className="studio-contact" aria-label="Написать в студию">
        <h3 className="lotos-section-title">Написать в студию</h3>
        <p className="studio-contact__hint">
          Откроется готовый текст — скопируйте его и вставьте в чат сообщества VK.
        </p>
        <div className="studio-contact__grid">
          {STUDIO_CONTACT_TOPICS.map((topic) => (
            <button
              key={topic.id}
              type="button"
              className="studio-contact__btn lotos-btn lotos-btn--secondary"
              onClick={() => handleTopicClick(topic.id)}
            >
              {topic.label}
            </button>
          ))}
        </div>
      </section>

      {activeTopic && vkGroupId && (
        <StudioContactSheet
          topic={activeTopic}
          context={context}
          vkGroupId={vkGroupId}
          onClose={() => setActiveTopic(null)}
          onNotice={onNotice}
        />
      )}
    </>
  )
}
