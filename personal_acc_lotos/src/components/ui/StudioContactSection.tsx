import { useState } from 'react'
import {
  buildStudioContactMessage,
  STUDIO_CONTACT_TOPICS,
  type StudioContactContext,
  type StudioContactTopic,
} from '../../content/studioGuide'
import { openStudioContactChat } from '../../vkBridge'
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
  const [loadingTopic, setLoadingTopic] = useState<StudioContactTopic | null>(null)

  async function handleContact(topic: StudioContactTopic) {
    if (!vkGroupId) {
      onNotice?.('Напишите нам в сообщения сообщества VK — кнопка появится после настройки группы.')
      return
    }

    setLoadingTopic(topic)
    try {
      const message = buildStudioContactMessage(topic, context)
      await openStudioContactChat(vkGroupId, message)
      onNotice?.('Текст скопирован — вставьте его в сообщение студии.')
    } catch {
      onNotice?.('Не удалось открыть диалог со студией.')
    } finally {
      setLoadingTopic(null)
    }
  }

  return (
    <section className="studio-contact" aria-label="Написать в студию">
      <h3 className="lotos-section-title">Написать в студию</h3>
      <p className="studio-contact__hint">
        Готовый текст с вашими данными — останется дописать вопрос и отправить.
      </p>
      <div className="studio-contact__grid">
        {STUDIO_CONTACT_TOPICS.map((topic) => (
          <button
            key={topic.id}
            type="button"
            className="studio-contact__btn lotos-btn lotos-btn--secondary"
            disabled={loadingTopic !== null}
            onClick={() => void handleContact(topic.id)}
          >
            {loadingTopic === topic.id ? 'Открываем…' : topic.label}
          </button>
        ))}
      </div>
    </section>
  )
}
