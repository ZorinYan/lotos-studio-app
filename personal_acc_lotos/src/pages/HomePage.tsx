import { ScreenSpinner, Snackbar } from '@vkontakte/vkui'
import { useCallback, useEffect, useState } from 'react'
import { fetchHome } from '../api/home'
import { fetchRebookSlots } from '../api/schedule'
import { ApiError } from '../api/client'
import { AppHeader } from '../components/AppHeader'
import { HomeAbonementWidget } from '../components/ui/HomeAbonementWidget'
import { HomeAlertsBanner } from '../components/ui/HomeAlertsBanner'
import { HomeNextRecordWidget } from '../components/ui/HomeNextRecordWidget'
import { RebookModal } from '../components/ui/RebookModal'
import type { HomeData } from '../types/home'
import type { RebookData } from '../types/schedule'
import './HomePage.css'

type HomePageProps = {
  vkUserId: number
  clientName: string | null
  studioName: string
  phoneDisplay: string | null
  onOpenCabinet: () => void
  onOpenSchedule: () => void
  onOpenRecords: () => void
  onLogout: () => void
}

export function HomePage({
  vkUserId,
  clientName,
  studioName,
  phoneDisplay,
  onOpenCabinet,
  onOpenSchedule,
  onOpenRecords,
  onLogout,
}: HomePageProps) {
  const [homeData, setHomeData] = useState<HomeData | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [rebookData, setRebookData] = useState<RebookData | null>(null)
  const [rebookLoading, setRebookLoading] = useState(false)

  const load = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true)
    else setLoading(true)
    setError(null)

    try {
      const data = await fetchHome(vkUserId, isRefresh)
      setHomeData(data)
    } catch (err) {
      setHomeData(null)
      if (isRefresh) {
        setError(err instanceof ApiError ? err.message : 'Не удалось обновить данные')
      }
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [vkUserId])

  useEffect(() => {
    void load()
  }, [load])

  const handleBookAgain = async () => {
    setRebookLoading(true)
    setError(null)
    try {
      const data = await fetchRebookSlots(vkUserId)
      setRebookData(data)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Не удалось подобрать занятия')
    } finally {
      setRebookLoading(false)
    }
  }

  const firstName = clientName?.split(' ')[0]
  const greeting = firstName
    ? `${firstName}, добро пожаловать`
    : 'Добро пожаловать'
  const displayStudio = homeData?.studioName ?? studioName

  return (
    <div className="home-page">
      <AppHeader onCabinetClick={onOpenCabinet} />

      <main className="home-page__content">
        <section className="home-hero">
          <div className="home-hero__orb" aria-hidden="true" />
          <p className="home-hero__eyebrow">Lotos Studio</p>
          <h2 className="home-hero__greeting">{greeting}</h2>
          <p className="home-hero__studio">{displayStudio}</p>
          {phoneDisplay && (
            <span className="home-hero__badge">{phoneDisplay}</span>
          )}
        </section>

        {loading ? (
          <div className="home-page__loading">
            <ScreenSpinner />
          </div>
        ) : (
          <>
            <HomeAlertsBanner alerts={homeData?.alerts ?? []} />

            <HomeAbonementWidget
              abonement={homeData?.abonement ?? null}
              onOpenCabinet={onOpenCabinet}
            />

            {homeData?.rebook?.available && homeData.rebook.prefs && (
              <section className="home-rebook lotos-card">
                <div className="home-rebook__body">
                  <p className="home-rebook__eyebrow">Быстрая запись</p>
                  <h3 className="home-rebook__title">Записаться снова</h3>
                  <p className="home-rebook__text">
                    {homeData.rebook.prefs.serviceTitle} · {homeData.rebook.prefs.staffName}
                    {homeData.rebook.slotsCount
                      ? ` · ${homeData.rebook.slotsCount} свободных слотов`
                      : ''}
                  </p>
                </div>
                <button
                  type="button"
                  className="lotos-btn lotos-btn--primary home-rebook__btn"
                  disabled={rebookLoading}
                  onClick={() => void handleBookAgain()}
                >
                  {rebookLoading ? 'Ищем…' : 'Выбрать время'}
                </button>
              </section>
            )}

            {homeData?.nextRecord && (
              <HomeNextRecordWidget
                record={homeData.nextRecord}
                studioName={displayStudio}
                onOpenRecords={onOpenRecords}
              />
            )}
          </>
        )}

        <section className="home-feature lotos-card" onClick={onOpenCabinet} role="button" tabIndex={0} onKeyDown={(e) => e.key === 'Enter' && onOpenCabinet()}>
          <div className="home-feature__icon-wrap">
            <span className="home-feature__icon" aria-hidden="true">✦</span>
          </div>
          <div className="home-feature__body">
            <h3 className="home-feature__title">Личный кабинет</h3>
            <p className="home-feature__text">
              Абонемент, записи, история визитов и статистика
            </p>
          </div>
          <span className="home-feature__arrow" aria-hidden="true">→</span>
        </section>

        <section
          className="home-feature lotos-card"
          onClick={onOpenSchedule}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => e.key === 'Enter' && onOpenSchedule()}
        >
          <div className="home-feature__icon-wrap home-feature__icon-wrap--schedule">
            <span className="home-feature__icon" aria-hidden="true">◷</span>
          </div>
          <div className="home-feature__body">
            <h3 className="home-feature__title">Расписание</h3>
            <p className="home-feature__text">
              Занятия на сегодня и ближайшие дни — время, тренер и свободные места
            </p>
          </div>
          <span className="home-feature__arrow" aria-hidden="true">→</span>
        </section>

        <section
          className="home-feature lotos-card"
          onClick={onOpenRecords}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => e.key === 'Enter' && onOpenRecords()}
        >
          <div className="home-feature__icon-wrap home-feature__icon-wrap--records">
            <span className="home-feature__icon" aria-hidden="true">◎</span>
          </div>
          <div className="home-feature__body">
            <h3 className="home-feature__title">Записи</h3>
            <p className="home-feature__text">
              Предстоящие и прошедшие занятия — детали и отмена записи
            </p>
          </div>
          <span className="home-feature__arrow" aria-hidden="true">→</span>
        </section>

        {!loading && (
          <button
            type="button"
            className="lotos-btn lotos-btn--secondary lotos-btn--stretched"
            disabled={refreshing}
            onClick={() => void load(true)}
          >
            {refreshing ? 'Обновляем…' : 'Обновить данные'}
          </button>
        )}

        <button type="button" className="lotos-btn lotos-btn--ghost lotos-btn--stretched" onClick={onLogout}>
          Выйти из аккаунта
        </button>
      </main>

      {rebookData && (
        <RebookModal
          prefs={rebookData.prefs}
          classes={rebookData.classes}
          vkUserId={vkUserId}
          studioName={displayStudio}
          onClose={() => setRebookData(null)}
          onBooked={() => void load(true)}
          onError={setError}
        />
      )}

      {error && (
        <Snackbar onClose={() => setError(null)} duration={5000}>
          {error}
        </Snackbar>
      )}
    </div>
  )
}
