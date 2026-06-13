import { Snackbar } from '@vkontakte/vkui'
import { useCallback, useEffect, useState } from 'react'
import { fetchRecords } from '../api/records'
import { ApiError } from '../api/client'
import { AppHeader } from '../components/AppHeader'
import { PullToRefresh } from '../components/ui/PullToRefresh'
import { RecordsPageSkeleton } from '../components/ui/skeletons/PageSkeletons'
import { RecordCard } from '../components/ui/RecordCard'
import { RecordModal } from '../components/ui/RecordModal'
import type { RecordFilter, RecordsData, UserRecord } from '../types/records'
import './RecordsPage.css'

type RecordsPageProps = {
  vkUserId: number
  studioName: string
  onBack?: () => void
}

const FILTERS: { id: RecordFilter; label: string }[] = [
  { id: 'all', label: 'Все' },
  { id: 'upcoming', label: 'Предстоящие' },
  { id: 'past', label: 'Прошедшие' },
]

export function RecordsPage({ vkUserId, studioName, onBack }: RecordsPageProps) {
  const [filter, setFilter] = useState<RecordFilter>('all')
  const [data, setData] = useState<RecordsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedRecord, setSelectedRecord] = useState<UserRecord | null>(null)

  const load = useCallback(async (nextFilter: RecordFilter, isRefresh = false) => {
    if (isRefresh) setRefreshing(true)
    else setLoading(true)
    setError(null)

    try {
      const records = await fetchRecords(vkUserId, nextFilter, isRefresh)
      setData(records)
      setFilter(records.filter)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Не удалось загрузить записи')
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [vkUserId])

  useEffect(() => {
    void load(filter)
  }, [filter, load])

  const emptyText =
    filter === 'upcoming'
      ? 'Нет предстоящих занятий'
      : filter === 'past'
        ? 'История записей пока пуста'
        : 'Записей пока нет'

  return (
    <div className="records-page">
      <AppHeader title="Записи" showCabinetButton={false} onBack={onBack} />

      <PullToRefresh
        onRefresh={() => load(filter, true)}
        refreshing={refreshing}
      >
      <div className="records-page__content">
        <section className="records-hero">
          <p className="records-hero__eyebrow">Lotos Studio</p>
          <h2 className="records-hero__title">Мои записи</h2>
          {data && (
            <p className="records-hero__subtitle">
              {data.counts.upcoming} предстоящих · {data.counts.past} прошедших
            </p>
          )}
        </section>

        <div className="records-filters" role="tablist" aria-label="Фильтр записей">
          {FILTERS.map((item) => (
            <button
              key={item.id}
              type="button"
              role="tab"
              aria-selected={filter === item.id}
              className={`records-filters__chip${
                filter === item.id ? ' records-filters__chip--active' : ''
              }`}
              onClick={() => setFilter(item.id)}
            >
              {item.label}
              {data && (
                <span className="records-filters__count">
                  {data.counts[item.id]}
                </span>
              )}
            </button>
          ))}
        </div>

        {loading ? (
          <RecordsPageSkeleton />
        ) : !data || data.records.length === 0 ? (
          <div className="lotos-empty lotos-card records-page__empty">
            <p className="records-page__empty-title">{emptyText}</p>
            <p>Запишитесь на занятие через расписание студии.</p>
          </div>
        ) : (
          <div className="records-page__list">
            {data.records.map((record) => (
              <RecordCard
                key={record.id}
                record={record}
                onClick={() => setSelectedRecord(record)}
              />
            ))}
          </div>
        )}
      </div>
      </PullToRefresh>

      {selectedRecord && (
        <RecordModal
          record={selectedRecord}
          vkUserId={vkUserId}
          studioName={studioName}
          onClose={() => setSelectedRecord(null)}
          onCancelled={() => void load(filter, true)}
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
