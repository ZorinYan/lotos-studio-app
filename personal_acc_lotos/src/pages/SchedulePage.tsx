import { ScreenSpinner, Snackbar } from '@vkontakte/vkui'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { fetchSchedule, fetchScheduleFilters } from '../api/schedule'
import { ApiError } from '../api/client'
import { AppHeader } from '../components/AppHeader'
import { ScheduleClassCard } from '../components/ui/ScheduleClassCard'
import { ScheduleClassModal } from '../components/ui/ScheduleClassModal'
import type { ScheduleClass, ScheduleData, ScheduleFilterOptions } from '../types/schedule'
import './SchedulePage.css'

type SchedulePageProps = {
  vkUserId: number
  studioName: string
  onBack: () => void
}

function todayIso() {
  return new Date().toISOString().slice(0, 10)
}

function serviceFilterKey(id: number | null, title: string) {
  return id != null ? `id:${id}` : `title:${title.toLowerCase()}`
}

export function SchedulePage({ vkUserId, studioName, onBack }: SchedulePageProps) {
  const [selectedDate, setSelectedDate] = useState(todayIso)
  const [data, setData] = useState<ScheduleData | null>(null)
  const [filterOptions, setFilterOptions] = useState<ScheduleFilterOptions | null>(null)
  const [trainerId, setTrainerId] = useState<number | null>(null)
  const [serviceKey, setServiceKey] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedClass, setSelectedClass] = useState<ScheduleClass | null>(null)

  const load = useCallback(async (date: string, isRefresh = false) => {
    if (isRefresh) setRefreshing(true)
    else setLoading(true)
    setError(null)

    try {
      const schedule = await fetchSchedule(date)
      setData(schedule)
      setSelectedDate(schedule.date)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Не удалось загрузить расписание')
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [])

  useEffect(() => {
    void load(selectedDate)
  }, [load, selectedDate])

  useEffect(() => {
    void fetchScheduleFilters()
      .then(setFilterOptions)
      .catch(() => setFilterOptions(null))
  }, [])

  const filteredClasses = useMemo(() => {
    if (!data) return []
    return data.classes.filter((item) => {
      if (trainerId != null && item.staffId !== trainerId) {
        return false
      }
      if (serviceKey) {
        if (serviceKey.startsWith('id:')) {
          const id = Number(serviceKey.slice(3))
          if (item.serviceId !== id) return false
        } else if (serviceKey.startsWith('title:')) {
          const title = serviceKey.slice(6)
          if (item.serviceTitle.toLowerCase() !== title) return false
        }
      }
      return true
    })
  }, [data, trainerId, serviceKey])

  const hasActiveFilters = trainerId != null || serviceKey != null
  const dayLabel = data?.dayLabel ?? 'Расписание'

  return (
    <div className="schedule-page">
      <AppHeader title="Расписание" showCabinetButton={false} onBack={onBack} />

      <div className="schedule-page__content">
        <section className="schedule-hero">
          <p className="schedule-hero__eyebrow">Lotos Studio</p>
          <h2 className="schedule-hero__title">{dayLabel}</h2>
          {data?.dateLabel && (
            <p className="schedule-hero__subtitle">{data.dateLabel}</p>
          )}
        </section>

        {data && data.days.length > 0 && (
          <div className="schedule-days" role="tablist" aria-label="Выбор дня">
            {data.days.map((day) => (
              <button
                key={day.date}
                type="button"
                role="tab"
                aria-selected={day.date === selectedDate}
                className={`schedule-days__chip${
                  day.date === selectedDate ? ' schedule-days__chip--active' : ''
                }`}
                onClick={() => setSelectedDate(day.date)}
              >
                {day.label}
              </button>
            ))}
          </div>
        )}

        {filterOptions && (filterOptions.trainers.length > 0 || filterOptions.services.length > 0) && (
          <section className="schedule-filters" aria-label="Фильтры расписания">
            <div className="schedule-filters__group">
              <p className="schedule-filters__label">Тренер</p>
              <div className="schedule-filters__chips">
                <button
                  type="button"
                  className={`schedule-filters__chip${
                    trainerId == null ? ' schedule-filters__chip--active' : ''
                  }`}
                  onClick={() => setTrainerId(null)}
                >
                  Все
                </button>
                {filterOptions.trainers.map((trainer) => (
                  <button
                    key={trainer.id}
                    type="button"
                    className={`schedule-filters__chip${
                      trainerId === trainer.id ? ' schedule-filters__chip--active' : ''
                    }`}
                    onClick={() => setTrainerId(trainer.id)}
                  >
                    {trainer.name}
                  </button>
                ))}
              </div>
            </div>

            {filterOptions.services.length > 0 && (
              <div className="schedule-filters__group">
                <p className="schedule-filters__label">Занятие</p>
                <div className="schedule-filters__chips">
                  <button
                    type="button"
                    className={`schedule-filters__chip${
                      serviceKey == null ? ' schedule-filters__chip--active' : ''
                    }`}
                    onClick={() => setServiceKey(null)}
                  >
                    Все
                  </button>
                  {filterOptions.services.map((service) => {
                    const key = serviceFilterKey(service.id, service.title)
                    return (
                      <button
                        key={key}
                        type="button"
                        className={`schedule-filters__chip${
                          serviceKey === key ? ' schedule-filters__chip--active' : ''
                        }`}
                        onClick={() => setServiceKey(key)}
                      >
                        {service.title}
                      </button>
                    )
                  })}
                </div>
              </div>
            )}

            {hasActiveFilters && (
              <button
                type="button"
                className="schedule-filters__reset"
                onClick={() => {
                  setTrainerId(null)
                  setServiceKey(null)
                }}
              >
                Сбросить фильтры
              </button>
            )}
          </section>
        )}

        {loading ? (
          <div className="schedule-page__loading">
            <ScreenSpinner />
          </div>
        ) : !data || filteredClasses.length === 0 ? (
          <div className="lotos-empty lotos-card schedule-page__empty">
            <p className="schedule-page__empty-title">
              {hasActiveFilters ? 'Нет занятий по фильтру' : 'Занятий нет'}
            </p>
            <p>
              {hasActiveFilters
                ? 'Попробуйте другой день или сбросьте фильтры.'
                : 'На этот день в расписании пока ничего не запланировано.'}
            </p>
          </div>
        ) : (
          <div className="schedule-page__list">
            {filteredClasses.map((item) => (
              <ScheduleClassCard
                key={item.id}
                item={item}
                onClick={() => setSelectedClass(item)}
              />
            ))}
          </div>
        )}

        {!loading && (
          <button
            type="button"
            className="lotos-btn lotos-btn--secondary lotos-btn--stretched"
            disabled={refreshing}
            onClick={() => void load(selectedDate, true)}
          >
            {refreshing ? 'Обновляем…' : 'Обновить расписание'}
          </button>
        )}
      </div>

      {selectedClass && data && (
        <ScheduleClassModal
          item={selectedClass}
          dayLabel={data.dayLabel}
          vkUserId={vkUserId}
          studioName={studioName}
          onClose={() => setSelectedClass(null)}
          onBooked={() => void load(selectedDate, true)}
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
