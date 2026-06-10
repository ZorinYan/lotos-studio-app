import type { AbonementUsageVisit, CabinetAbonement } from '../../types/cabinet'
import { formatMoney, parseAbonementStatus, pluralizeLessons } from '../../utils/format'
import './AbonementModal.css'

type AbonementModalProps = {
  item: CabinetAbonement
  usageVisits: AbonementUsageVisit[]
  onClose: () => void
}

export function AbonementModal({ item, usageVisits, onClose }: AbonementModalProps) {
  const status = parseAbonementStatus(item.status)

  return (
    <div className="abonement-modal" role="dialog" aria-modal="true" aria-labelledby="abonement-modal-title">
      <button type="button" className="abonement-modal__backdrop" aria-label="Закрыть" onClick={onClose} />
      <div className="abonement-modal__sheet lotos-card">
        <div className="abonement-modal__handle" aria-hidden="true" />
        <button type="button" className="abonement-modal__close" onClick={onClose} aria-label="Закрыть">
          ×
        </button>

        <header className="abonement-modal__header">
          <p className="abonement-modal__eyebrow">Абонемент</p>
          <h2 id="abonement-modal-title" className="abonement-modal__title">
            {item.title}
          </h2>
          <span className={`abonement-modal__status abonement-modal__status--${status.tone}`}>
            {status.label}
          </span>
        </header>

        {item.services.length > 0 && (
          <section className="abonement-modal__section">
            <h3 className="lotos-section-title">
              {item.isUnitedBalance ? 'Общий баланс' : 'Услуги и остаток'}
            </h3>
            <div className="abonement-modal__services">
              {item.services.map((service) => (
                <div key={service.title} className="abonement-modal__service">
                  <span className="abonement-modal__service-title">{service.title}</span>
                  <span className="abonement-modal__service-count">
                    {service.remaining}
                    <span className="abonement-modal__service-unit">
                      {pluralizeLessons(service.remaining)}
                    </span>
                  </span>
                </div>
              ))}
            </div>
          </section>
        )}

        <section className="abonement-modal__section">
          <h3 className="lotos-section-title">Детали</h3>
          <dl className="abonement-modal__details">
            {item.number && item.number !== '—' && (
              <div className="abonement-modal__detail">
                <dt>Номер</dt>
                <dd>{item.number}</dd>
              </div>
            )}
            {item.expiry && (
              <div className="abonement-modal__detail">
                <dt>Действует до</dt>
                <dd>{item.expiry}</dd>
              </div>
            )}
            {item.activatedDate && (
              <div className="abonement-modal__detail">
                <dt>Активирован</dt>
                <dd>{item.activatedDate}</dd>
              </div>
            )}
            {item.createdDate && (
              <div className="abonement-modal__detail">
                <dt>Оформлен</dt>
                <dd>{item.createdDate}</dd>
              </div>
            )}
            {item.typeCost != null && item.typeCost > 0 && (
              <div className="abonement-modal__detail">
                <dt>Стоимость</dt>
                <dd>{formatMoney(item.typeCost)}</dd>
              </div>
            )}
            {item.allowFreeze && (
              <div className="abonement-modal__detail">
                <dt>Заморозка</dt>
                <dd>
                  {item.freezeLimit
                    ? `Доступна, до ${item.freezeLimit} дн.`
                    : 'Доступна'}
                </dd>
              </div>
            )}
          </dl>
        </section>

        {item.freezeLines.length > 0 && (
          <section className="abonement-modal__section">
            <h3 className="lotos-section-title">Заморозка</h3>
            <div className="abonement-modal__freeze-list">
              {item.freezeLines.map((line) => (
                <span key={line} className="abonement-modal__freeze-tag">{line}</span>
              ))}
            </div>
          </section>
        )}

        {usageVisits.length > 0 && (
          <section className="abonement-modal__section">
            <h3 className="lotos-section-title">Последние списания</h3>
            <div className="abonement-modal__usage">
              {usageVisits.map((visit, index) => (
                <div key={`${visit.datetime}-${index}`} className="abonement-modal__usage-row">
                  <span className="abonement-modal__usage-date">{visit.datetime}</span>
                  <span className="abonement-modal__usage-service">{visit.service}</span>
                  <span className="abonement-modal__usage-staff">{visit.staff}</span>
                </div>
              ))}
            </div>
          </section>
        )}

        <button type="button" className="lotos-btn lotos-btn--primary lotos-btn--stretched" onClick={onClose}>
          Закрыть
        </button>
      </div>
    </div>
  )
}
