import { useRef, useState } from 'react'
import { rescheduleRecord } from '../../api/records'
import { ApiError } from '../../api/client'
import { useModalOverlay } from '../../hooks/useModalOverlay'
import type { RescheduleResult, RescheduleSlotsData } from '../../types/records'
import type { ScheduleClass } from '../../types/schedule'
import { ScheduleClassCard } from './ScheduleClassCard'
import './RescheduleModal.css'

type ModalMode = 'pick' | 'confirm' | 'success'

type RescheduleModalProps = {
  data: RescheduleSlotsData
  vkUserId: number
  onClose: () => void
  onRescheduled: () => void
  onError: (message: string) => void
}

export function RescheduleModal({
  data,
  vkUserId,
  onClose,
  onRescheduled,
  onError,
}: RescheduleModalProps) {
  const sheetRef = useRef<HTMLDivElement>(null)
  const [mode, setMode] = useState<ModalMode>('pick')
  const [selectedClass, setSelectedClass] = useState<ScheduleClass | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [result, setResult] = useState<RescheduleResult | null>(null)

  const handleConfirm = async () => {
    if (!selectedClass) return
    setSubmitting(true)
    try {
      const response = await rescheduleRecord(
        vkUserId,
        data.record.id,
        selectedClass.id,
        selectedClass.date,
      )
      setResult(response)
      setMode('success')
    } catch (err) {
      onError(err instanceof ApiError ? err.message : 'Не удалось перенести запись')
      setMode('pick')
    } finally {
      setSubmitting(false)
    }
  }

  const handleClose = () => {
    if (submitting) return
    if (mode === 'success') {
      onRescheduled()
    }
    onClose()
  }

  useModalOverlay(handleClose, sheetRef)

  return (
    <div className="reschedule-modal lotos-modal" role="dialog" aria-modal="true" aria-labelledby="reschedule-modal-title">
      <button
        type="button"
        className="reschedule-modal__backdrop"
        aria-label="Закрыть"
        onClick={handleClose}
        disabled={submitting}
      />
      <div ref={sheetRef} className="reschedule-modal__sheet lotos-modal__sheet lotos-card">
        <div className="reschedule-modal__handle" aria-hidden="true" />
        <button
          type="button"
          className="reschedule-modal__close"
          onClick={handleClose}
          aria-label="Закрыть"
          disabled={submitting}
        >
          ×
        </button>

        {mode === 'success' && result ? (
          <div className="reschedule-modal__success">
            <div className="reschedule-modal__success-icon" aria-hidden="true">✓</div>
            <h2 className="reschedule-modal__success-title">Запись перенесена</h2>
            <p className="reschedule-modal__success-text">{result.message}</p>
            {result.partial && result.warning && (
              <p className="reschedule-modal__warning">{result.warning}</p>
            )}
            <dl className="reschedule-modal__summary">
              <div>
                <dt>Было</dt>
                <dd>{result.oldRecord.datetime}</dd>
              </div>
              <div>
                <dt>Стало</dt>
                <dd>
                  {result.newClass.dateLabel} · {result.newClass.time}
                </dd>
              </div>
            </dl>
            <button
              type="button"
              className="lotos-btn lotos-btn--primary lotos-btn--stretched"
              onClick={handleClose}
            >
              Готово
            </button>
          </div>
        ) : mode === 'confirm' && selectedClass ? (
          <section className="reschedule-modal__confirm">
            <p className="reschedule-modal__eyebrow">Подтверждение</p>
            <h2 id="reschedule-modal-title" className="reschedule-modal__title">Перенести запись?</h2>
            <p className="reschedule-modal__text">
              С {data.record.datetime} на {selectedClass.dateLabel} · {selectedClass.time}.
              Тренер: {data.prefs.staffName}.
            </p>
            <div className="reschedule-modal__actions">
              <button
                type="button"
                className="lotos-btn lotos-btn--secondary"
                disabled={submitting}
                onClick={() => setMode('pick')}
              >
                Назад
              </button>
              <button
                type="button"
                className="lotos-btn lotos-btn--primary"
                disabled={submitting}
                onClick={() => void handleConfirm()}
              >
                {submitting ? 'Переносим…' : 'Да, перенести'}
              </button>
            </div>
          </section>
        ) : (
          <>
            <header className="reschedule-modal__header">
              <p className="reschedule-modal__eyebrow">Быстрый перенос</p>
              <h2 id="reschedule-modal-title" className="reschedule-modal__title">Выберите новое время</h2>
              <p className="reschedule-modal__subtitle">
                {data.prefs.serviceTitle} · {data.prefs.staffName}
              </p>
              <p className="reschedule-modal__current">Сейчас: {data.record.datetime}</p>
            </header>
            <div className="reschedule-modal__list">
              {data.classes.map((item) => (
                <ScheduleClassCard
                  key={`${item.id}-${item.date}-${item.time}`}
                  item={item}
                  onClick={() => {
                    setSelectedClass(item)
                    setMode('confirm')
                  }}
                />
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  )
}
