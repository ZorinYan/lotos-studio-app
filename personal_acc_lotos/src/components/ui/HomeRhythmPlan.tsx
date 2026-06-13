import type { RhythmPlan } from '../../types/home'
import './HomeRhythmPlan.css'

type HomeRhythmPlanProps = {
  plan: RhythmPlan
  onBook: () => void
  loading?: boolean
}

export function HomeRhythmPlan({ plan, onBook, loading = false }: HomeRhythmPlanProps) {
  const canBook = plan.slotsCount > 0

  return (
    <section className="home-rhythm lotos-card">
      <p className="home-rhythm__eyebrow">Ваш ритм</p>
      <h3 className="home-rhythm__title">{plan.message}</h3>
      {plan.detail && <p className="home-rhythm__detail">{plan.detail}</p>}
      {plan.serviceTitle && plan.staffName && (
        <p className="home-rhythm__meta">
          {plan.serviceTitle} · {plan.staffName}
        </p>
      )}
      {canBook && (
        <button
          type="button"
          className="lotos-btn lotos-btn--primary home-rhythm__btn"
          disabled={loading}
          onClick={onBook}
        >
          {loading ? 'Ищем…' : 'Выбрать время'}
        </button>
      )}
    </section>
  )
}
