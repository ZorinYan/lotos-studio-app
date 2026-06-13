import { Snackbar } from '@vkontakte/vkui'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { fetchAbonements } from '../api/abonement'
import { fetchHome } from '../api/home'
import { fetchRebookSlots } from '../api/schedule'
import { fetchStudioFeed } from '../api/studio'
import { ApiError } from '../api/client'
import { AppHeader } from '../components/AppHeader'
import { FirstVisitTips } from '../components/ui/FirstVisitTips'
import { HomeAbonementWidget } from '../components/ui/HomeAbonementWidget'
import { HomeNextRecordWidget } from '../components/ui/HomeNextRecordWidget'
import { HomeRhythmPlan } from '../components/ui/HomeRhythmPlan'
import { HomeStudioPlace } from '../components/ui/HomeStudioPlace'
import { HomeVkPosts } from '../components/ui/HomeVkPosts'
import { HomeVkStories } from '../components/ui/HomeVkStories'
import { PullToRefresh } from '../components/ui/PullToRefresh'
import { RebookModal } from '../components/ui/RebookModal'
import { RevealStack } from '../components/ui/RevealStack'
import { SmartHintsBanner } from '../components/ui/SmartHintsBanner'
import { HomePageSkeleton } from '../components/ui/skeletons/PageSkeletons'
import {
  buildStudioContactMessage,
  type StudioContactTopic,
} from '../content/studioGuide'
import type { HomeData, HomeHint, HomeHintAction } from '../types/home'
import type { RebookData } from '../types/schedule'
import type { StudioFeed } from '../types/studio'
import { buildStudioRouteUrl } from '../utils/studioRoute'
import { openStudioContactChat } from '../vkBridge'
import './HomePage.css'

type HomePageProps = {
  vkUserId: number
  clientName: string | null
  studioName: string
  phoneDisplay: string | null
  vkGroupId?: number
  onOpenCabinet: () => void
  onOpenRecords: () => void
  onOpenSchedule: () => void
  onOpenSettings: () => void
}

export function HomePage({
  vkUserId,
  clientName,
  studioName,
  phoneDisplay,
  vkGroupId,
  onOpenCabinet,
  onOpenRecords,
  onOpenSchedule,
  onOpenSettings,
}: HomePageProps) {
  const [homeData, setHomeData] = useState<HomeData | null>(null)
  const [studioFeed, setStudioFeed] = useState<StudioFeed | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [rebookData, setRebookData] = useState<RebookData | null>(null)
  const [rebookLoading, setRebookLoading] = useState(false)

  const load = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true)
    else setLoading(true)
    setError(null)

    const [homeResult, feedResult, abonementResult] = await Promise.allSettled([
      fetchHome(vkUserId, isRefresh),
      fetchStudioFeed(vkUserId, isRefresh),
      fetchAbonements(vkUserId),
    ])

    if (homeResult.status === 'fulfilled') {
      let home = homeResult.value
      if (abonementResult.status === 'fulfilled') {
        home = {
          ...home,
          abonement: abonementResult.value.primary,
        }
      }
      setHomeData(home)
    } else {
      setHomeData(null)
      if (isRefresh) {
        const reason = homeResult.reason
        setError(reason instanceof ApiError ? reason.message : 'Не удалось обновить данные')
      }
    }

    if (feedResult.status === 'fulfilled') {
      setStudioFeed(feedResult.value)
    } else {
      setStudioFeed(null)
    }

    setLoading(false)
    setRefreshing(false)
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

  const contactContext = useMemo(
    () => ({
      clientName,
      phoneDisplay,
      abonementTitle: homeData?.abonement?.title ?? null,
      abonementRemaining: homeData?.abonement?.balanceRemaining ?? null,
    }),
    [clientName, phoneDisplay, homeData?.abonement],
  )

  const openContact = useCallback(
    async (topic: StudioContactTopic) => {
      if (!vkGroupId) {
        setNotice('Напишите нам в сообщения сообщества VK.')
        return
      }

      try {
        const message = buildStudioContactMessage(topic, contactContext)
        await openStudioContactChat(vkGroupId, message)
        setNotice('Текст скопирован — вставьте его в сообщение студии.')
      } catch {
        setNotice('Не удалось открыть диалог со студией.')
      }
    },
    [contactContext, vkGroupId],
  )

  const handleHintAction = useCallback(
    (action: HomeHintAction, _hint: HomeHint) => {
      if (action === 'schedule') {
        onOpenSchedule()
        return
      }
      if (action === 'rebook') {
        void handleBookAgain()
        return
      }
      if (action === 'contact_renew') {
        void openContact('renew')
      }
    },
    [handleBookAgain, onOpenSchedule, openContact],
  )

  const firstName = clientName?.split(' ')[0]
  const greeting = firstName
    ? `${firstName}, добро пожаловать`
    : 'Добро пожаловать'
  const displayStudio = homeData?.studioName ?? studioName
  const routeUrl = useMemo(
    () => buildStudioRouteUrl(studioFeed?.place),
    [studioFeed?.place],
  )

  return (
    <div className="home-page">
      <AppHeader showCabinetButton={false} />

      <PullToRefresh onRefresh={() => load(true)} refreshing={refreshing}>
        <main className="home-page__content">
          <section className="home-hero lotos-reveal">
            <div className="home-hero__orb" aria-hidden="true" />
            <p className="home-hero__eyebrow">Lotos Studio</p>
            <h2 className="home-hero__greeting">{greeting}</h2>
            {phoneDisplay && (
              <span className="home-hero__badge">{phoneDisplay}</span>
            )}
          </section>

          {loading ? (
            <HomePageSkeleton />
          ) : (
            <RevealStack>
              <SmartHintsBanner
                hints={homeData?.alerts ?? []}
                onAction={handleHintAction}
              />

              {homeData?.isFirstVisit && (
                <FirstVisitTips onOpenHelp={onOpenSettings} />
              )}

              <HomeAbonementWidget
                abonement={homeData?.abonement ?? null}
                onOpenCabinet={onOpenCabinet}
              />

              {homeData?.nextRecord && (
                <HomeNextRecordWidget
                  record={homeData.nextRecord}
                  studioName={displayStudio}
                  routeUrl={routeUrl}
                  onOpenRecords={onOpenRecords}
                />
              )}

              {homeData?.rhythmPlan && (
                <HomeRhythmPlan
                  plan={homeData.rhythmPlan}
                  loading={rebookLoading}
                  onBook={() => void handleBookAgain()}
                />
              )}

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
            </RevealStack>
          )}

          {!loading && studioFeed && (
            <RevealStack className="home-page__feed">
              <HomeVkStories
                stories={studioFeed.stories}
                storiesAvailable={studioFeed.storiesAvailable}
                groupUrl={studioFeed.place?.groupUrl ?? null}
              />
              <HomeVkPosts posts={studioFeed.posts} />
              <HomeStudioPlace place={studioFeed.place} />
            </RevealStack>
          )}
        </main>
      </PullToRefresh>

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

      {notice && (
        <Snackbar onClose={() => setNotice(null)} duration={5000}>
          {notice}
        </Snackbar>
      )}
    </div>
  )
}
