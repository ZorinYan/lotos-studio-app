import type { MonthlyVisitBucket } from '../../utils/visitAnalytics'
import type { MonthComparison } from '../../utils/practiceAnalytics'
import './VisitActivityChart.css'

type VisitActivityChartProps = {
  buckets: MonthlyVisitBucket[]
  comparison?: MonthComparison | null
}

export function VisitActivityChart({ buckets, comparison }: VisitActivityChartProps) {
  const max = Math.max(1, ...buckets.map((item) => item.count))
  const total = buckets.reduce((sum, item) => sum + item.count, 0)

  if (total === 0) {
    return (
      <div className="visit-activity lotos-card visit-activity--empty">
        <p className="visit-activity__empty-title">Пока мало данных для графика</p>
        <p className="visit-activity__empty-text">После нескольких визитов здесь появится динамика</p>
      </div>
    )
  }

  return (
    <div className="visit-activity lotos-card">
      <div className="visit-activity__head">
        <div>
          <p className="visit-activity__eyebrow">Активность</p>
          <h4 className="visit-activity__title">Посещения за 3 месяца</h4>
          {comparison && (
            <p className={`visit-activity__comparison${
              comparison.delta > 0
                ? ' visit-activity__comparison--up'
                : comparison.delta < 0
                  ? ' visit-activity__comparison--down'
                  : ''
            }`}
            >
              {comparison.text}
            </p>
          )}
        </div>
        <span className="visit-activity__total">{total}</span>
      </div>

      <div className="visit-activity__chart" role="img" aria-label="График посещений за три месяца">
        {buckets.map((bucket) => {
          const height = bucket.count > 0 ? Math.max(14, (bucket.count / max) * 100) : 6
          return (
            <div key={bucket.key} className="visit-activity__bar-wrap">
              <div className="visit-activity__bar-shell">
                <div
                  className={`visit-activity__bar${bucket.count > 0 ? ' visit-activity__bar--filled' : ''}`}
                  style={{ height: `${height}%` }}
                />
              </div>
              <span className="visit-activity__count">{bucket.count > 0 ? bucket.count : '·'}</span>
              <span className="visit-activity__label">{bucket.label}</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
