import type { CabinetAbonement } from '../../types/cabinet'
import { parseAbonementStatus, pluralizeLessons } from '../../utils/format'
import './HomeAbonementWidget.css'

type HomeAbonementWidgetProps = {
  abonement: CabinetAbonement | null
  onOpenCabinet: () => void
}

export function HomeAbonementWidget({ abonement, onOpenCabinet }: HomeAbonementWidgetProps) {
  if (!abonement) {
    return (
      <section
        className="home-abonement lotos-card home-abonement--empty"
        onClick={onOpenCabinet}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => e.key === 'Enter' && onOpenCabinet()}
      >
        <p className="home-abonement__eyebrow">Абонемент</p>
        <h3 className="home-abonement__title">Нет активного абонемента</h3>
        <p className="home-abonement__hint">Откройте кабинет, чтобы посмотреть детали</p>
      </section>
    )
  }

  const status = parseAbonementStatus(abonement.status)
  const remaining = abonement.balanceRemaining
  const previewServices = abonement.services.slice(0, 2)

  return (
    <section
      className="home-abonement lotos-card"
      onClick={onOpenCabinet}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === 'Enter' && onOpenCabinet()}
    >
      <div className="home-abonement__header">
        <div>
          <p className="home-abonement__eyebrow">Ваш абонемент</p>
          <h3 className="home-abonement__title">{abonement.title}</h3>
          <span className={`home-abonement__status home-abonement__status--${status.tone}`}>
            {status.label}
          </span>
        </div>
        {remaining != null && (
          <div className="home-abonement__balance" aria-label={`Осталось ${remaining} занятий`}>
            <span className="home-abonement__balance-num">{remaining}</span>
            <span className="home-abonement__balance-label">{pluralizeLessons(remaining)}</span>
          </div>
        )}
      </div>

      {previewServices.length > 0 && (
        <div className="home-abonement__services">
          {previewServices.map((service) => (
            <div key={service.title} className="home-abonement__service">
              <span>{service.title}</span>
              <strong>{service.remaining}</strong>
            </div>
          ))}
        </div>
      )}

      {abonement.expiry && (
        <p className="home-abonement__expiry">Действует до {abonement.expiry}</p>
      )}
    </section>
  )
}
