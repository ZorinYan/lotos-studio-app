import { useEffect, useMemo, useState } from 'react'
import type { UserRecord } from '../../types/records'
import { countdownIntervalMs, formatCountdown } from '../../utils/countdown'
import { openVkUrl } from '../../vkBridge'
import { AddToCalendarButton } from './AddToCalendarButton'
import './HomeNextRecordWidget.css'

type HomeNextRecordWidgetProps = {
  record: UserRecord
  studioName: string
  routeUrl?: string | null
  onOpenRecords: () => void
}

function buildDetails(record: UserRecord): string {
  const parts = [record.service, record.staff]
  if (record.comment) parts.push(record.comment)
  return parts.filter(Boolean).join(' · ')
}

export function HomeNextRecordWidget({
  record,
  studioName,
  routeUrl,
  onOpenRecords,
}: HomeNextRecordWidgetProps) {
  const [now, setNow] = useState(() => Date.now())

  useEffect(() => {
    const intervalMs = countdownIntervalMs(record.startsAt)
    const timer = window.setInterval(() => setNow(Date.now()), intervalMs)
    return () => window.clearInterval(timer)
  }, [record.startsAt])

  const countdown = useMemo(
    () => formatCountdown(record.startsAt, now),
    [record.startsAt, now],
  )

  const details = buildDetails(record)

  return (
    <section className={`home-next-record lotos-card${countdown?.isSoon ? ' home-next-record--soon' : ''}`}>
      <p className="home-next-record__eyebrow">Ближайшее занятие</p>

      {countdown && (
        <p className="home-next-record__countdown" aria-live="polite">
          <span key={countdown.tick} className="countdown-value--tick">
            {countdown.label}
          </span>
        </p>
      )}

      <p className="home-next-record__details">{details}</p>

      {record.dateLabel && record.time && (
        <p className="home-next-record__schedule">
          {record.dateLabel} в {record.time}
        </p>
      )}

      <div className="home-next-record__actions">
        {record.startsAt && record.endsAt && (
          <AddToCalendarButton
            stretched
            event={{
              title: record.service,
              startsAt: record.startsAt,
              endsAt: record.endsAt,
              trainer: record.staff,
              studioName,
            }}
            label="В календарь"
          />
        )}
        {routeUrl && (
          <button
            type="button"
            className="lotos-btn lotos-btn--secondary lotos-btn--stretched"
            onClick={() => void openVkUrl(routeUrl)}
          >
            Маршрут
          </button>
        )}
        <button
          type="button"
          className="lotos-btn lotos-btn--ghost lotos-btn--stretched"
          onClick={onOpenRecords}
        >
          Все записи
        </button>
      </div>
    </section>
  )
}
