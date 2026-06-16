import { ScreenSpinner } from '@vkontakte/vkui'
import { useEffect, useState } from 'react'
import { fetchStaffHome, type StaffHomeData } from '../api/staff'
import { ApiError } from '../api/client'
import { AppHeader } from '../components/AppHeader'
import './StaffHomePage.css'

type StaffHomePageProps = {
  vkUserId: number
  studioName: string
  staffName: string | null
  phoneDisplay: string | null
  onLogout: () => void
}

export function StaffHomePage({
  vkUserId,
  studioName,
  staffName,
  phoneDisplay,
  onLogout,
}: StaffHomePageProps) {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [data, setData] = useState<StaffHomeData | null>(null)

  useEffect(() => {
    let cancelled = false
    void (async () => {
      setLoading(true)
      setError(null)
      try {
        const home = await fetchStaffHome(vkUserId)
        if (!cancelled) {
          setData(home)
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : 'Не удалось загрузить кабинет сотрудника')
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    })()
    return () => {
      cancelled = true
    }
  }, [vkUserId])

  if (loading) {
    return (
      <div className="staff-home">
        <ScreenSpinner />
      </div>
    )
  }

  const displayName = data?.staffName ?? staffName ?? 'Сотрудник'
  const subtitle = [data?.positionTitle, data?.specialization].filter(Boolean).join(' · ')

  return (
    <div className="staff-home">
      <AppHeader title="Кабинет сотрудника" showCabinetButton={false} />
      <header className="staff-home__hero lotos-card">
        <p className="staff-home__eyebrow">Кабинет сотрудника</p>
        <h1 className="staff-home__title">{displayName}</h1>
        {subtitle && <p className="staff-home__subtitle">{subtitle}</p>}
        <p className="staff-home__meta">
          {studioName}
          {phoneDisplay ? ` · ${phoneDisplay}` : ''}
        </p>
      </header>

      {error && (
        <p className="staff-home__error" role="alert">
          {error}
        </p>
      )}

      <section className="staff-home__sections">
        {(data?.sections ?? []).map((section) => (
          <article key={section.id} className="staff-home__section lotos-card">
            <div className="staff-home__section-head">
              <h2 className="staff-home__section-title">{section.title}</h2>
              {section.status === 'coming_soon' && (
                <span className="staff-home__badge">Скоро</span>
              )}
            </div>
            <p className="staff-home__section-text">{section.description}</p>
          </article>
        ))}
      </section>

      <button
        type="button"
        className="lotos-btn lotos-btn--secondary lotos-btn--stretched staff-home__logout"
        onClick={onLogout}
      >
        Выйти
      </button>
    </div>
  )
}
