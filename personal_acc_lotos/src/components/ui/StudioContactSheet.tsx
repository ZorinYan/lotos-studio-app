import { useMemo, useState } from 'react'
import {
  buildStudioContactMessage,
  STUDIO_CONTACT_TOPICS,
  type StudioContactContext,
  type StudioContactTopic,
} from '../../content/studioGuide'
import { buildVkGroupMessagesUrl, copyVkText, openVkUrl } from '../../vkBridge'
import './StudioContactSheet.css'

type StudioContactSheetProps = {
  topic: StudioContactTopic
  context: StudioContactContext
  vkGroupId: number
  onClose: () => void
  onNotice?: (message: string) => void
}

export function StudioContactSheet({
  topic,
  context,
  vkGroupId,
  onClose,
  onNotice,
}: StudioContactSheetProps) {
  const topicMeta = useMemo(
    () => STUDIO_CONTACT_TOPICS.find((item) => item.id === topic),
    [topic],
  )
  const initialText = useMemo(
    () => buildStudioContactMessage(topic, context),
    [topic, context],
  )
  const [text, setText] = useState(initialText)
  const [copying, setCopying] = useState(false)
  const [opening, setOpening] = useState(false)

  async function handleCopy() {
    setCopying(true)
    try {
      const copied = await copyVkText(text)
      if (copied) {
        onNotice?.('Текст скопирован — вставьте его в чат студии.')
      } else {
        onNotice?.('Не удалось скопировать. Выделите текст и скопируйте вручную.')
      }
    } finally {
      setCopying(false)
    }
  }

  async function handleOpenChat() {
    setOpening(true)
    try {
      await openVkUrl(buildVkGroupMessagesUrl(vkGroupId))
    } catch {
      onNotice?.('Не удалось открыть чат со студией.')
    } finally {
      setOpening(false)
    }
  }

  return (
    <div className="studio-contact-sheet" role="dialog" aria-modal="true" aria-labelledby="studio-contact-sheet-title">
      <button
        type="button"
        className="studio-contact-sheet__backdrop"
        aria-label="Закрыть"
        onClick={onClose}
      />
      <div className="studio-contact-sheet__panel lotos-card">
        <div className="studio-contact-sheet__handle" aria-hidden="true" />
        <button
          type="button"
          className="studio-contact-sheet__close"
          onClick={onClose}
          aria-label="Закрыть"
        >
          ×
        </button>

        <p className="studio-contact-sheet__eyebrow">Сообщение в студию</p>
        <h2 id="studio-contact-sheet-title" className="studio-contact-sheet__title">
          {topicMeta?.label ?? 'Написать в студию'}
        </h2>
        <p className="studio-contact-sheet__hint">
          Проверьте текст, при необходимости допишите вопрос. Скопируйте и вставьте в чат сообщества VK.
        </p>

        <label className="studio-contact-sheet__field" htmlFor="studio-contact-sheet-text">
          <span className="studio-contact-sheet__label">Текст обращения</span>
          <textarea
            id="studio-contact-sheet-text"
            className="studio-contact-sheet__textarea"
            value={text}
            rows={10}
            onChange={(event) => setText(event.target.value)}
          />
        </label>

        <div className="studio-contact-sheet__actions">
          <button
            type="button"
            className="lotos-btn lotos-btn--secondary lotos-btn--stretched"
            disabled={copying || opening}
            onClick={() => void handleCopy()}
          >
            {copying ? 'Копируем…' : 'Скопировать'}
          </button>
          <button
            type="button"
            className="lotos-btn lotos-btn--primary lotos-btn--stretched"
            disabled={copying || opening}
            onClick={() => void handleOpenChat()}
          >
            {opening ? 'Открываем…' : 'Открыть чат'}
          </button>
        </div>
      </div>
    </div>
  )
}
