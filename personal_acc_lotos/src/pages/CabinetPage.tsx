import { Snackbar } from '@vkontakte/vkui'
import { useCallback, useEffect, useState } from 'react'
import { fetchAbonements } from '../api/abonement'
import { fetchCabinet } from '../api/cabinet'
import { ApiError } from '../api/client'
import { AppHeader } from '../components/AppHeader'
import { AbonementCard } from '../components/ui/AbonementCard'
import { AbonementModal } from '../components/ui/AbonementModal'
import { PullToRefresh } from '../components/ui/PullToRefresh'
import { RecordCard } from '../components/ui/RecordCard'
import { RecordModal } from '../components/ui/RecordModal'
import { StatTile } from '../components/ui/StatTile'
import { VisitActivityChart } from '../components/ui/VisitActivityChart'
import { VisitRhythmCard } from '../components/ui/VisitRhythmCard'
import { VisitRow } from '../components/ui/VisitRow'
import { CabinetPageSkeleton } from '../components/ui/skeletons/PageSkeletons'
import type { CabinetAbonement, CabinetData } from '../types/cabinet'
import type { UserRecord } from '../types/records'
import { formatMoney } from '../utils/format'
import {
  buildMonthlyVisitBuckets,
  collectVisitDateIsos,
  computeVisitRhythm,
} from '../utils/visitAnalytics'
import './CabinetPage.css'

type CabinetPageProps = {
  vkUserId: number
  studioName: string
  onBack?: () => void
  onOpenRecords: () => void
}

export function CabinetPage({ vkUserId, studioName, onBack, onOpenRecords }: CabinetPageProps) {
  const [data, setData] = useState<CabinetData | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedAbonement, setSelectedAbonement] = useState<CabinetAbonement | null>(null)
  const [selectedRecord, setSelectedRecord] = useState<UserRecord | null>(null)

  const load = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true)
    else setLoading(true)
    setError(null)

    try {
      const [cabinetResult, abonementResult] = await Promise.allSettled([
        fetchCabinet(vkUserId, isRefresh),
        fetchAbonements(vkUserId),
      ])

      if (cabinetResult.status === 'fulfilled') {
        let cabinet = cabinetResult.value
        if (abonementResult.status === 'fulfilled') {
          cabinet = {
            ...cabinet,
            abonements: abonementResult.value.abonements,
          }
        }
        setData(cabinet)
      } else {
        setError(
          cabinetResult.reason instanceof ApiError
            ? cabinetResult.reason.message
            : 'Не удалось загрузить кабинет',
        )
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Не удалось загрузить кабинет')
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [vkUserId])

  useEffect(() => {
    void load()
  }, [load])

  if (loading) {
    return (
      <div className="cabinet-page">
        <AppHeader title="Личный кабинет" showCabinetButton={false} onBack={onBack} />
        <div className="cabinet-page__content">
          <CabinetPageSkeleton />
        </div>
      </div>
    )
  }

  if (!data) {
    return (
      <div className="cabinet-page">
        <AppHeader title="Личный кабинет" showCabinetButton={false} onBack={onBack} />
        <div className="cabinet-page__error lotos-card">
          <p className="cabinet-page__error-title">Не удалось загрузить</p>
          <p className="cabinet-page__error-text">{error ?? 'Попробуйте обновить страницу'}</p>
          <button type="button" className="lotos-btn lotos-btn--primary lotos-btn--stretched" onClick={() => void load()}>
            Повторить
          </button>
        </div>
      </div>
    )
  }

  const { profile, abonements, upcomingRecords, recentVisits, abonementUsageVisits, visitHistory } = data
  const firstName = profile.name.split(' ')[0]
  const visitDateIsos = collectVisitDateIsos(
    visitHistory ?? [],
    recentVisits,
    abonementUsageVisits,
  )
  const monthlyBuckets = buildMonthlyVisitBuckets(visitDateIsos, 3)
  const visitRhythm = computeVisitRhythm(visitDateIsos)

  return (
    <div className="cabinet-page">
      <AppHeader title="Личный кабинет" showCabinetButton={false} onBack={onBack} />

      <PullToRefresh onRefresh={() => load(true)} refreshing={refreshing}>
      <div className="cabinet-page__content">
        <section className="cabinet-hero">
          <div className="cabinet-hero__glow" aria-hidden="true" />
          <div className="cabinet-hero__inner">
            <div className="cabinet-hero__avatar">
              <span aria-hidden="true">🪷</span>
            </div>
            <div className="cabinet-hero__text">
              <p className="cabinet-hero__eyebrow">Личный кабинет</p>
              <h2 className="cabinet-hero__name">{profile.name}</h2>
              <p className="cabinet-hero__phone">{profile.phoneDisplay}</p>
            </div>
          </div>
          <p className="cabinet-hero__greeting">
            {firstName ? `${firstName}, рады видеть вас в студии` : 'Рады видеть вас в студии'}
          </p>
        </section>

        <section className="cabinet-section">
          <h3 className="lotos-section-title">Ваша статистика</h3>
          {visitRhythm && (
            <div className="cabinet-section__rhythm">
              <VisitRhythmCard rhythm={visitRhythm} />
            </div>
          )}
          <div className="cabinet-section__chart">
            <VisitActivityChart buckets={monthlyBuckets} />
          </div>
          <div className="cabinet-stats">
            <StatTile label="Визитов в студии" value={String(profile.visits)} accent />
            {profile.spent > 0 && (
              <StatTile label="Оплачено всего" value={formatMoney(profile.spent)} />
            )}
            {profile.discount > 0 && (
              <StatTile label="Персональная скидка" value={`${profile.discount}%`} />
            )}
            {profile.firstVisitDate && (
              <StatTile label="Первый визит" value={profile.firstVisitDate} />
            )}
            {profile.lastVisitDate && (
              <StatTile label="Последний визит" value={profile.lastVisitDate} />
            )}
          </div>
        </section>

        <section className="cabinet-section">
          <h3 className="lotos-section-title">Абонементы</h3>
          {abonements.length === 0 ? (
            <div className="lotos-empty lotos-card">Нет абонементов</div>
          ) : (
            <div className="cabinet-stack">
              {abonements.map((item, index) => (
                <AbonementCard
                  key={`${item.id ?? item.number}-${index}`}
                  item={item}
                  onClick={() => setSelectedAbonement(item)}
                />
              ))}
            </div>
          )}
        </section>

        <section className="cabinet-section">
          <div className="cabinet-section__head">
            <h3 className="lotos-section-title cabinet-section__title">Ближайшие записи</h3>
            {upcomingRecords.length > 0 && (
              <button type="button" className="cabinet-section__link" onClick={onOpenRecords}>
                Все записи
              </button>
            )}
          </div>
          {upcomingRecords.length === 0 ? (
            <div className="lotos-empty lotos-card">Пока нет предстоящих занятий</div>
          ) : (
            <div className="cabinet-stack">
              {upcomingRecords.map((record) => (
                <RecordCard
                  key={record.id}
                  record={record}
                  onClick={() => setSelectedRecord(record)}
                />
              ))}
            </div>
          )}
        </section>

        <section className="cabinet-section">
          <h3 className="lotos-section-title">Недавние посещения</h3>
          {recentVisits.length === 0 ? (
            <div className="lotos-empty lotos-card">История пока пуста</div>
          ) : (
            <div className="cabinet-visits lotos-card">
              {recentVisits.map((visit, index) => (
                <VisitRow key={`${visit.date}-${index}`} visit={visit} />
              ))}
            </div>
          )}
        </section>
      </div>
      </PullToRefresh>

      {selectedAbonement && (
        <AbonementModal
          item={selectedAbonement}
          usageVisits={data.abonementUsageVisits}
          onClose={() => setSelectedAbonement(null)}
        />
      )}

      {selectedRecord && (
        <RecordModal
          record={selectedRecord}
          vkUserId={vkUserId}
          studioName={studioName}
          onClose={() => setSelectedRecord(null)}
          onCancelled={() => void load(true)}
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
