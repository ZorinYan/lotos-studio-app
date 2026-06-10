import type { ScheduleClass } from '../../types/schedule'
import './ScheduleClassCard.css'

type ScheduleClassCardProps = {
  item: ScheduleClass
  onClick: () => void
}

export function ScheduleClassCard({ item, onClick }: ScheduleClassCardProps) {
  const spotsText = item.isFull
    ? 'Нет мест'
    : item.freeSpots != null && item.capacity > 0
      ? `${item.freeSpots} из ${item.capacity} свободно`
      : 'Есть места'

  return (
    <article
      className={`schedule-card${item.isFull ? ' schedule-card--full' : ''}`}
      role="button"
      tabIndex={0}
      onClick={onClick}
      onKeyDown={(event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault()
          onClick()
        }
      }}
    >
      <div className="schedule-card__time-col">
        <span className="schedule-card__time">{item.time}</span>
        {item.durationMinutes != null && item.durationMinutes > 0 && (
          <span className="schedule-card__duration">{item.durationMinutes} мин</span>
        )}
      </div>

      <div className="schedule-card__body">
        <h3 className="schedule-card__title">{item.serviceTitle}</h3>
        <p className="schedule-card__trainer">{item.trainer}</p>
        <span
          className={`schedule-card__spots schedule-card__spots--${
            item.isFull ? 'full' : 'free'
          }`}
        >
          {spotsText}
        </span>
      </div>

      <span className="schedule-card__arrow" aria-hidden="true">→</span>
    </article>
  )
}
