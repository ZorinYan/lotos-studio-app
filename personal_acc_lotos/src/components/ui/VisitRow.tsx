import type { CabinetVisit } from '../../types/cabinet'
import './VisitRow.css'

type VisitRowProps = {
  visit: CabinetVisit
}

export function VisitRow({ visit }: VisitRowProps) {
  return (
    <div className="visit-row">
      <div className="visit-row__marker" aria-hidden="true" />
      <div className="visit-row__content">
        <div className="visit-row__head">
          <span className="visit-row__date">{visit.date}</span>
          <span className="visit-row__check" aria-label="Посещение состоялось">✓</span>
        </div>
        <p className="visit-row__service">{visit.service}</p>
        <p className="visit-row__staff">{visit.staff}</p>
      </div>
    </div>
  )
}
