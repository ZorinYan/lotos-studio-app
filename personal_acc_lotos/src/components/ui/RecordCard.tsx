import type { UserRecord } from '../../types/records'
import { parseAttendance, splitDateTime } from '../../utils/format'
import './RecordCard.css'

type RecordCardData = Pick<UserRecord, 'datetime' | 'service' | 'staff' | 'attendance'> & {
  isUpcoming?: boolean
}

type RecordCardProps = {
  record: RecordCardData
  onClick?: () => void
}

export function RecordCard({ record, onClick }: RecordCardProps) {
  const { date, time } = splitDateTime(record.datetime)
  const attendance = parseAttendance(record.attendance)
  const isInteractive = Boolean(onClick)
  const isUpcoming = 'isUpcoming' in record ? record.isUpcoming : true

  return (
    <article
      className={`record-card${isInteractive ? ' record-card--interactive' : ''}${
        !isUpcoming ? ' record-card--past' : ''
      }`}
      role={isInteractive ? 'button' : undefined}
      tabIndex={isInteractive ? 0 : undefined}
      onClick={onClick}
      onKeyDown={(event) => {
        if (!onClick) return
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault()
          onClick()
        }
      }}
    >
      <div className="record-card__time-block">
        {time && <span className="record-card__time">{time}</span>}
        <span className="record-card__date">{date}</span>
      </div>
      <div className="record-card__body">
        <h4 className="record-card__service">{record.service}</h4>
        <p className="record-card__staff">{record.staff}</p>
        <span className={`record-card__badge record-card__badge--${attendance.tone}`}>
          {attendance.label}
        </span>
      </div>
      {isInteractive && <span className="record-card__arrow" aria-hidden="true">→</span>}
    </article>
  )
}
