import { useState } from 'react'
import type { RebookPrefs, ScheduleClass } from '../../types/schedule'
import { ScheduleClassCard } from './ScheduleClassCard'
import { ScheduleClassModal } from './ScheduleClassModal'
import './RebookModal.css'

type RebookModalProps = {
  prefs: RebookPrefs
  classes: ScheduleClass[]
  vkUserId: number
  studioName: string
  onClose: () => void
  onBooked: () => void
  onError: (message: string) => void
}

export function RebookModal({
  prefs,
  classes,
  vkUserId,
  studioName,
  onClose,
  onBooked,
  onError,
}: RebookModalProps) {
  const [selectedClass, setSelectedClass] = useState<ScheduleClass | null>(null)

  return (
    <>
      <div className="rebook-modal" role="dialog" aria-modal="true" aria-labelledby="rebook-modal-title">
        <button type="button" className="rebook-modal__backdrop" aria-label="Закрыть" onClick={onClose} />
        <div className="rebook-modal__sheet lotos-card">
          <div className="rebook-modal__handle" aria-hidden="true" />
          <button type="button" className="rebook-modal__close" onClick={onClose} aria-label="Закрыть">
            ×
          </button>

          <header className="rebook-modal__header">
            <p className="rebook-modal__eyebrow">Как в прошлый раз</p>
            <h2 id="rebook-modal-title" className="rebook-modal__title">Записаться снова</h2>
            <p className="rebook-modal__subtitle">
              {prefs.serviceTitle} · {prefs.staffName}
            </p>
          </header>

          <div className="rebook-modal__list">
            {classes.map((item) => (
              <ScheduleClassCard
                key={item.id}
                item={item}
                onClick={() => setSelectedClass(item)}
              />
            ))}
          </div>
        </div>
      </div>

      {selectedClass && (
        <ScheduleClassModal
          item={selectedClass}
          dayLabel={selectedClass.dateLabel}
          vkUserId={vkUserId}
          studioName={studioName}
          authenticated
          onClose={() => setSelectedClass(null)}
          onBooked={() => {
            onBooked()
            onClose()
          }}
          onError={onError}
        />
      )}
    </>
  )
}
