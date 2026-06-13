import type { VisitRhythm } from '../../utils/visitAnalytics'
import './VisitRhythmCard.css'

type VisitRhythmCardProps = {
  rhythm: VisitRhythm
}

export function VisitRhythmCard({ rhythm }: VisitRhythmCardProps) {
  return (
    <div className="visit-rhythm lotos-card">
      <div className="visit-rhythm__icon" aria-hidden="true">
        ◦
      </div>
      <div className="visit-rhythm__text">
        <p className="visit-rhythm__message">{rhythm.message}</p>
        {rhythm.detail && <p className="visit-rhythm__detail">{rhythm.detail}</p>}
      </div>
    </div>
  )
}
