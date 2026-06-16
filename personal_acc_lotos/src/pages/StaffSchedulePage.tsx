import { Snackbar } from '@vkontakte/vkui'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { fetchSchedule, fetchScheduleFilters } from '../api/schedule'
import { ApiError } from '../api/client'
import { AppHeader } from '../components/AppHeader'
import { PullToRefresh } from '../components/ui/PullToRefresh'
import { ScheduleClassCard } from '../components/ui/ScheduleClassCard'
import { StaffScheduleClassModal } from '../components/ui/StaffScheduleClassModal'
import { SchedulePageSkeleton } from '../components/ui/skeletons/PageSkeletons'
import type { ScheduleClass, ScheduleData, ScheduleFilterOptions } from '../types/schedule'
import { localTodayIso } from '../utils/format'
import './SchedulePage.css'

type StaffSchedulePageProps = {
  vkUserId: number
  staffId: number | null
  studioName: string
  onBack?: () => void
}

function serviceFilterKey(id: number | null, title: string) {
  return id != null ? `id:${id}` : `title:${title.toLowerCase()}`
}

export function StaffSchedulePage({
  vkUserId,
  staffId,
  studioName,
  onBack,
}: StaffSchedulePageProps) {
  const [selectedDate, setSelectedDate] = useState(localTodayIso)
  const [data, setData] = useState<ScheduleData | null>(null)
  const [filterOptions, setFilterOptions] = useState<ScheduleFilterOptions | null>(null)
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
      const [schedule, filters] = await Promise.all([
        fetchSchedule(date, isRefresh),
        isRefresh ? fetchScheduleFilters(true) : Promise.resolve(null),
      ])

      setData(schedule)
      if (filters) setFilterOptions(filters)
    } catch (err) {
      const message = err instanceof ApiError ? err.message : 'Не удалось загрузить расписание'
      setError(message)
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
    const currentStaffId = staffId
    return data.classes.filter((item) => {
      if (currentStaffId != null && item.staffId !== currentStaffId) return false
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
  }, [data, staffId, serviceKey])

  const hasActiveFilters = serviceKey != null
  const dayLabel = data?.dayLabel ?? 'Расписание'

  return (
    <div className="schedule-page">
      <AppHeader title="Расписание" showCabinetButton={false} onBack={onBack} />

      <PullToRefresh onRefresh={() => load(selectedDate, true)} refreshing={refreshing}>
        <div className="schedule-page__content">
          <section className="schedule-hero">
            <p className="schedule-hero__eyebrow">Lotos Studio</p>
            <h2 className="schedule-hero__title">{dayLabel}</h2>
            {data?.dateLabel && <p className="schedule-hero__subtitle">{data.dateLabel}</p>}
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

          {filterOptions && filterOptions.services.length > 0 && (
            <section className="schedule-filters" aria-label="Фильтры расписания">
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

              {hasActiveFilters && (
                <button
                  type="button"
                  className="schedule-filters__reset"
                  onClick={() => setServiceKey(null)}
                >
                  Сбросить фильтры
                </button>
              )}
            </section>
          )}

          {loading ? (
            <SchedulePageSkeleton />
          ) : !data || filteredClasses.length === 0 ? (
            <div className="lotos-empty lotos-card schedule-page__empty">
              <p className="schedule-page__empty-title">
                {hasActiveFilters ? 'Нет занятий по фильтру' : 'Занятий нет'}
              </p>
              <p>
                {hasActiveFilters
                  ? 'Попробуйте другой день или сбросьте фильтры.'
                  : 'На этот день у вашего тренера в расписании пока ничего не запланировано.'}
              </p>
            </div>
          ) : (
            <div className="schedule-page__list">
              {filteredClasses.map((item) => (
                <ScheduleClassCard key={item.id} item={item} onClick={() => setSelectedClass(item)} />
              ))}
            </div>
          )}
        </div>
      </PullToRefresh>

      {error && (
        <Snackbar onClose={() => setError(null)} duration={5000}>
          {error}
        </Snackbar>
      )}

      {selectedClass && data && (
        <StaffScheduleClassModal
          item={selectedClass}
          dayLabel={dayLabel}
          vkUserId={vkUserId}
          studioName={studioName}
          onClose={() => setSelectedClass(null)}
        />
      )}
    </div>
  )
}

