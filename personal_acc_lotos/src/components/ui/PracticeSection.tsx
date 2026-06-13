import type { PracticeDashboardData } from '../../utils/practiceAnalytics'
import { ProgressRing } from './ProgressRing'
import { VisitActivityChart } from './VisitActivityChart'
import { VisitRhythmCard } from './VisitRhythmCard'
import './PracticeSection.css'

type PracticeSectionProps = {
  data: PracticeDashboardData
}

function Heatmap({ data }: { data: PracticeDashboardData['heatmap'] }) {
  return (
    <div className="practice-card lotos-card practice-heatmap">
      <p className="practice-card__eyebrow">Регулярность</p>
      <h4 className="practice-card__title">Карта активности</h4>
      <div className="practice-heatmap__grid" role="img" aria-label="Тепловая карта посещений за 16 недель">
        <div className="practice-heatmap__day-labels" aria-hidden="true">
          {data.dayLabels.map((label, index) => (
            <span
              key={label}
              className={`practice-heatmap__day-label${index % 2 === 1 ? ' practice-heatmap__day-label--muted' : ''}`}
            >
              {index % 2 === 0 ? label : ''}
            </span>
          ))}
        </div>
        <div className="practice-heatmap__weeks">
          {data.weeks.map((week) => (
            <div key={week.key} className="practice-heatmap__week">
              {week.days.map((level, dayIndex) => (
                <span
                  key={`${week.key}-${dayIndex}`}
                  className={`practice-heatmap__cell practice-heatmap__cell--l${level}`}
                />
              ))}
            </div>
          ))}
        </div>
      </div>
      <div className="practice-heatmap__legend" aria-hidden="true">
        <span>Меньше</span>
        <span className="practice-heatmap__cell practice-heatmap__cell--l0" />
        <span className="practice-heatmap__cell practice-heatmap__cell--l1" />
        <span className="practice-heatmap__cell practice-heatmap__cell--l2" />
        <span className="practice-heatmap__cell practice-heatmap__cell--l3" />
        <span>Больше</span>
      </div>
    </div>
  )
}

function ServiceChart({ buckets }: { buckets: PracticeDashboardData['serviceBuckets'] }) {
  if (buckets.length === 0) return null
  const max = Math.max(1, ...buckets.map((item) => item.count))

  return (
    <div className="practice-card lotos-card practice-services">
      <p className="practice-card__eyebrow">Направления</p>
      <h4 className="practice-card__title">Чем вы занимаетесь</h4>
      <div className="practice-services__list">
        {buckets.map((item) => (
          <div key={item.title} className="practice-services__row">
            <div className="practice-services__meta">
              <span className="practice-services__name">{item.title}</span>
              <span className="practice-services__count">{item.count}</span>
            </div>
            <div className="practice-services__track">
              <div
                className="practice-services__fill"
                style={{ width: `${Math.max(8, (item.count / max) * 100)}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function WeeklyStrip({ buckets }: { buckets: PracticeDashboardData['weeklyStrip'] }) {
  return (
    <div className="practice-card lotos-card practice-weekly-strip">
      <p className="practice-card__eyebrow">8 недель</p>
      <h4 className="practice-card__title">Недавний ритм</h4>
      <div className="practice-weekly-strip__chart" role="img" aria-label="Посещения по неделям">
        {buckets.map((item) => (
          <div key={item.key} className="practice-weekly-strip__col">
            <div className="practice-weekly-strip__shell">
              <div className={`practice-weekly-strip__bar practice-weekly-strip__bar--l${item.level}`} />
            </div>
            <span className="practice-weekly-strip__count">{item.count > 0 ? item.count : '·'}</span>
            <span className="practice-weekly-strip__label">{item.label}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

function MonthlyGoalRing({ goal }: { goal: NonNullable<PracticeDashboardData['monthlyGoal']> }) {
  return (
    <div className="practice-card lotos-card practice-month-goal">
      <div className="practice-month-goal__content">
        <div>
          <p className="practice-card__eyebrow">Этот месяц</p>
          <h4 className="practice-card__title">Ваш темп</h4>
          <p className="practice-month-goal__text">
            {goal.current} из {goal.goal} визитов
          </p>
        </div>
        <div className="practice-month-goal__ring-wrap">
          <ProgressRing
            progress={goal.progress}
            size={84}
            strokeWidth={7}
            label={`${goal.current} из ${goal.goal} визитов в этом месяце`}
          >
            <span className="practice-month-goal__ring-num">{goal.current}</span>
            <span className="practice-month-goal__ring-label">из {goal.goal}</span>
          </ProgressRing>
        </div>
      </div>
    </div>
  )
}

function WeeklyTrend({ points }: { points: PracticeDashboardData['weeklyTrend'] }) {
  const max = Math.max(1, ...points.map((item) => item.count))
  const width = 280
  const height = 88
  const padding = 8
  const step = points.length > 1 ? (width - padding * 2) / (points.length - 1) : 0

  const coords = points.map((point, index) => {
    const x = padding + index * step
    const y = height - padding - (point.count / max) * (height - padding * 2)
    return { x, y, point }
  })

  const polyline = coords.map((item) => `${item.x},${item.y}`).join(' ')

  return (
    <div className="practice-card lotos-card practice-trend">
      <p className="practice-card__eyebrow">Динамика</p>
      <h4 className="practice-card__title">12 недель</h4>
      <svg
        className="practice-trend__svg"
        viewBox={`0 0 ${width} ${height}`}
        role="img"
        aria-label="Линейный тренд посещений за 12 недель"
      >
        <polyline className="practice-trend__line" points={polyline} />
        {coords.map((item) => (
          <circle
            key={item.point.key}
            className="practice-trend__dot"
            cx={item.x}
            cy={item.y}
            r={item.point.count > 0 ? 3.5 : 2.5}
          />
        ))}
      </svg>
      <div className="practice-trend__labels">
        <span>{points[0]?.label}</span>
        <span>{points[points.length - 1]?.label}</span>
      </div>
    </div>
  )
}

export function PracticeSection({ data }: PracticeSectionProps) {
  if (!data.hasActivity) {
    return (
      <section className="cabinet-section practice-section">
        <h3 className="lotos-section-title">Моя практика</h3>
        <div className="practice-empty lotos-card">
          <p className="practice-empty__title">Пока мало данных</p>
          <p className="practice-empty__text">
            После нескольких визитов здесь появятся графики, карта активности и ваш ритм.
          </p>
        </div>
      </section>
    )
  }

  return (
    <section className="cabinet-section practice-section">
      <h3 className="lotos-section-title">Моя практика</h3>

      {data.tenureLine && (
        <p className="practice-tenure">{data.tenureLine}</p>
      )}

      {data.rhythm && (
        <div className="practice-section__rhythm">
          <VisitRhythmCard rhythm={data.rhythm} />
        </div>
      )}

      <div className="practice-section__grid">
        <VisitActivityChart
          buckets={data.monthlyBuckets}
          comparison={data.monthComparison}
        />

        {data.monthlyGoal && (
          <MonthlyGoalRing goal={data.monthlyGoal} />
        )}

        <WeeklyStrip buckets={data.weeklyStrip} />
        <WeeklyTrend points={data.weeklyTrend} />
        <ServiceChart buckets={data.serviceBuckets} />
        <Heatmap data={data.heatmap} />
      </div>
    </section>
  )
}
