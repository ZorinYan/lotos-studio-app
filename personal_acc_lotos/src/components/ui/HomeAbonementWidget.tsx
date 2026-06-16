import type { CabinetAbonement } from '../../types/cabinet'
import { parseAbonementStatus, pluralizeLessons } from '../../utils/format'
import { estimateAbonementProgress } from '../../utils/visitAnalytics'
import { ProgressRing } from './ProgressRing'
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
        <h3 className="home-abonement__title">Нет абонемента</h3>
        <p className="home-abonement__hint">Откройте кабинет, чтобы посмотреть детали</p>
      </section>
    )
  }

  const status = parseAbonementStatus(abonement.status)
  const remaining = abonement.balanceRemaining
  const previewServices = abonement.services.filter((service) => service.remaining > 0).slice(0, 2)
  const progress = estimateAbonementProgress(remaining, abonement.balanceTotal ?? null)

  return (
    <section
      className="home-abonement lotos-card"
      onClick={onOpenCabinet}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === 'Enter' && onOpenCabinet()}
    >
      <div className="home-abonement__header">
        <div className="home-abonement__info">
          <p className="home-abonement__eyebrow">Ваш абонемент</p>
          <h3 className="home-abonement__title">{abonement.title}</h3>
          <span className={`home-abonement__status home-abonement__status--${status.tone}`}>
            {status.label}
          </span>
        </div>
        {remaining != null && (
          <div className="home-abonement__ring-wrap" aria-label={`Осталось ${remaining} занятий`}>
            <ProgressRing
              progress={progress}
              size={78}
              strokeWidth={6}
              label={`Осталось ${remaining} ${pluralizeLessons(remaining)}`}
            >
              <span className="home-abonement__ring-num">{remaining}</span>
              <span className="home-abonement__ring-label">{pluralizeLessons(remaining)}</span>
            </ProgressRing>
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
