import type { CabinetAbonement } from '../../types/cabinet'
import { parseAbonementStatus, pluralizeLessons } from '../../utils/format'
import './AbonementCard.css'

type AbonementCardProps = {
  item: CabinetAbonement
  onClick: () => void
}

export function AbonementCard({ item, onClick }: AbonementCardProps) {
  const status = parseAbonementStatus(item.status)
  const remaining = item.balanceRemaining
  const previewServices = item.services.slice(0, 2)
  const moreCount = item.services.length - previewServices.length

  return (
    <article
      className="abonement-card abonement-card--clickable"
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
      <div className="abonement-card__top">
        <div className="abonement-card__info">
          <h3 className="abonement-card__title">{item.title}</h3>
          <span className={`abonement-card__status abonement-card__status--${status.tone}`}>
            {status.label}
          </span>
        </div>
        {remaining != null && remaining > 0 && (
          <div className="abonement-card__balance">
            <span className="abonement-card__balance-num">{remaining}</span>
            <span className="abonement-card__balance-label">
              {pluralizeLessons(remaining)}
              <br />
              осталось
            </span>
          </div>
        )}
      </div>

      {previewServices.length > 0 && (
        <div className="abonement-card__services-preview">
          {previewServices.map((service) => (
            <div key={service.title} className="abonement-card__service-chip">
              <span className="abonement-card__service-name">{service.title}</span>
              <span className="abonement-card__service-left">{service.remaining}</span>
            </div>
          ))}
          {moreCount > 0 && (
            <span className="abonement-card__more">ещё {moreCount}</span>
          )}
        </div>
      )}

      <div className="abonement-card__footer">
        {item.expiry ? (
          <span className="abonement-card__expiry">до {item.expiry}</span>
        ) : (
          <span className="abonement-card__expiry abonement-card__expiry--muted">Подробнее</span>
        )}
        <span className="abonement-card__arrow" aria-hidden="true">→</span>
      </div>
    </article>
  )
}
