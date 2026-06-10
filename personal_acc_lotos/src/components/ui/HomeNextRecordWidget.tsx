import type { UserRecord } from '../../types/records'
import { AddToCalendarButton } from './AddToCalendarButton'
import './HomeNextRecordWidget.css'

type HomeNextRecordWidgetProps = {
  record: UserRecord
  studioName: string
  onOpenRecords: () => void
}

export function HomeNextRecordWidget({
  record,
  studioName,
  onOpenRecords,
}: HomeNextRecordWidgetProps) {
  return (
    <section className="home-next-record lotos-card">
      <div className="home-next-record__header">
        <div>
          <p className="home-next-record__eyebrow">Ближайшее занятие</p>
          <h3 className="home-next-record__title">{record.service}</h3>
          <p className="home-next-record__meta">
            {record.datetime} · {record.staff}
          </p>
        </div>
        {record.time && (
          <div className="home-next-record__time" aria-hidden="true">
            {record.time}
          </div>
        )}
      </div>

      <div className="home-next-record__actions">
        <AddToCalendarButton
          stretched
          event={{
            title: record.service,
            startsAt: record.startsAt!,
            endsAt: record.endsAt!,
            trainer: record.staff,
            studioName,
          }}
        />
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
