import { AppRoot, ConfigProvider, Placeholder, ScreenSpinner } from '@vkontakte/vkui'
import '@vkontakte/vkui/dist/vkui.css'
import './styles/lotos-theme.css'
import { useCallback, useEffect, useState, type ReactNode } from 'react'
import { fetchAuthStatus, fetchPublicConfig, logout, type PublicConfig } from './api/auth'
import { fetchSettings } from './api/settings'
import { ApiError } from './api/client'
import { AppTabShell } from './components/AppTabShell'
import { WelcomeBanner } from './components/WelcomeBanner'
import type { AppTab } from './components/BottomNav'
import { AuthPage } from './pages/AuthPage'
import { CabinetPage } from './pages/CabinetPage'
import { HomePage } from './pages/HomePage'
import { RecordsPage } from './pages/RecordsPage'
import { SchedulePage } from './pages/SchedulePage'
import { SettingsPage } from './pages/SettingsPage'
import { LotosThemeProvider, useLotosTheme } from './hooks/useLotosTheme'
import { useVkApp } from './hooks/useVkApp'
import { hasSeenWelcomeBanner, markWelcomeBannerSeen } from './utils/welcomeBanner'
import './App.css'

type Screen = 'loading' | 'auth' | AppTab

const TAB_SCREENS: AppTab[] = ['home', 'schedule', 'cabinet', 'records', 'settings']

function LotosAppShell({ children }: { children: ReactNode }) {
  const { colorScheme } = useLotosTheme()

  return (
    <ConfigProvider colorScheme={colorScheme}>
      <AppRoot className="lotos-app">{children}</AppRoot>
    </ConfigProvider>
  )
}

function AppContent() {
  const { ready, vkUser, error: vkError } = useVkApp()
  const [screen, setScreen] = useState<Screen>('loading')
  const [config, setConfig] = useState<PublicConfig | null>(null)
  const [phoneDisplay, setPhoneDisplay] = useState<string | null>(null)
  const [clientName, setClientName] = useState<string | null>(null)
  const [favoriteTrainerId, setFavoriteTrainerId] = useState<number | null>(null)
  const [bootError, setBootError] = useState<string | null>(null)
  const [guestSchedule, setGuestSchedule] = useState(false)
  const [authenticated, setAuthenticated] = useState(false)
  const [welcomeOpen, setWelcomeOpen] = useState(false)

  const loadUserSettings = useCallback(async (userId: number) => {
    try {
      const settings = await fetchSettings(userId)
      setFavoriteTrainerId(settings.favoriteTrainer?.id ?? null)
    } catch {
      setFavoriteTrainerId(null)
    }
  }, [])

  const applySession = useCallback((status: Awaited<ReturnType<typeof fetchAuthStatus>>) => {
    setAuthenticated(status.authenticated)
    if (status.authenticated) {
      setPhoneDisplay(status.phoneDisplay)
      setClientName(status.clientName)
      setGuestSchedule(false)
    } else {
      setPhoneDisplay(null)
      setClientName(null)
      setFavoriteTrainerId(null)
    }
  }, [])

  const checkSession = useCallback(async (userId: number) => {
    const [publicConfig, status] = await Promise.all([
      fetchPublicConfig(),
      fetchAuthStatus(userId),
    ])
    setConfig(publicConfig)
    applySession(status)
    if (status.authenticated) {
      await loadUserSettings(userId)
      setScreen('home')
    } else {
      setScreen('auth')
    }
  }, [applySession, loadUserSettings])

  useEffect(() => {
    if (!ready || !vkUser) return

    let cancelled = false
    const bootTimeoutId = window.setTimeout(() => {
      if (!cancelled) {
        setBootError(
          'Сервер долго не отвечает. На Render первый запуск может занять до минуты — обновите страницу.',
        )
        setScreen('auth')
      }
    }, 30_000)

    void (async () => {
      try {
        await checkSession(vkUser.id)
      } catch (err) {
        if (!cancelled) {
          setBootError(err instanceof ApiError ? err.message : 'Не удалось загрузить приложение')
          setScreen('auth')
        }
      } finally {
        window.clearTimeout(bootTimeoutId)
      }
    })()

    return () => {
      cancelled = true
      window.clearTimeout(bootTimeoutId)
    }
  }, [ready, vkUser, checkSession])

  const handleAuthenticated = useCallback(async () => {
    if (!vkUser) return
    try {
      const [publicConfig, status] = await Promise.all([
        fetchPublicConfig(),
        fetchAuthStatus(vkUser.id),
      ])
      setConfig(publicConfig)
      applySession(status)
      await loadUserSettings(vkUser.id)
      if (!hasSeenWelcomeBanner(vkUser.id)) {
        setWelcomeOpen(true)
      }
      setScreen('home')
    } catch {
      setScreen('home')
    }
  }, [vkUser, applySession, loadUserSettings])

  const handleWelcomeClose = useCallback(() => {
    if (vkUser) {
      markWelcomeBannerSeen(vkUser.id)
    }
    setWelcomeOpen(false)
  }, [vkUser])

  const handleGuestScheduleBack = useCallback(() => {
    setGuestSchedule(false)
    setScreen(authenticated ? 'home' : 'auth')
  }, [authenticated])

  const handleOpenGuestSchedule = useCallback(async () => {
    if (!vkUser) return
    try {
      const publicConfig = await fetchPublicConfig()
      setConfig(publicConfig)
    } catch {
      // расписание доступно и без публичного конфига
    }
    setGuestSchedule(true)
    setScreen('schedule')
  }, [vkUser])

  const handleLogout = useCallback(async () => {
    if (!vkUser) return
    await logout(vkUser.id)
    setPhoneDisplay(null)
    setClientName(null)
    setFavoriteTrainerId(null)
    setAuthenticated(false)
    setGuestSchedule(false)
    setWelcomeOpen(false)
    setScreen('auth')
  }, [vkUser])

  const handleTabNavigate = useCallback((tab: AppTab) => {
    setGuestSchedule(false)
    setScreen(tab)
    if (tab === 'settings' && vkUser) {
      void loadUserSettings(vkUser.id)
    }
  }, [loadUserSettings, vkUser])

  if (!ready) {
    return (
      <LotosAppShell>
        <ScreenSpinner />
      </LotosAppShell>
    )
  }

  if (vkError || !vkUser) {
    return (
      <LotosAppShell>
        <Placeholder title="Ошибка">
          {vkError ?? 'Не удалось определить пользователя VK'}
        </Placeholder>
      </LotosAppShell>
    )
  }

  const user = vkUser
  const showTabShell = authenticated && !guestSchedule && TAB_SCREENS.includes(screen as AppTab)

  function renderScreen() {
    if (screen === 'loading') {
      return <ScreenSpinner />
    }

    if (screen === 'auth') {
      return (
        <AuthPage
          vkUser={user}
          bootError={bootError}
          onAuthenticated={handleAuthenticated}
          onOpenSchedule={() => void handleOpenGuestSchedule()}
        />
      )
    }

    if (screen === 'home') {
      return (
        <HomePage
          vkUserId={user.id}
          clientName={clientName}
          studioName={config?.studioName ?? 'Lotos Studio'}
          phoneDisplay={phoneDisplay}
          vkGroupId={config?.vkGroupId}
          onOpenCabinet={() => setScreen('cabinet')}
          onOpenRecords={() => setScreen('records')}
          onOpenSchedule={() => setScreen('schedule')}
          onOpenSettings={() => setScreen('settings')}
        />
      )
    }

    if (screen === 'cabinet') {
      return (
        <CabinetPage
          vkUserId={user.id}
          studioName={config?.studioName ?? 'Lotos Studio'}
          onOpenRecords={() => setScreen('records')}
        />
      )
    }

    if (screen === 'schedule') {
      return (
        <SchedulePage
          vkUserId={user.id}
          studioName={config?.studioName ?? 'Lotos Studio'}
          guestMode={guestSchedule}
          authenticated={authenticated}
          favoriteTrainerId={favoriteTrainerId}
          onBack={guestSchedule ? handleGuestScheduleBack : undefined}
          onAuthenticated={() => void handleAuthenticated()}
        />
      )
    }

    if (screen === 'records') {
      return <RecordsPage vkUserId={user.id} studioName={config?.studioName ?? 'Lotos Studio'} />
    }

    if (screen === 'settings') {
      return (
        <SettingsPage
          vkUserId={user.id}
          phoneDisplay={phoneDisplay}
          clientName={clientName}
          vkGroupId={config?.vkGroupId}
          onLogout={handleLogout}
        />
      )
    }

    return null
  }

  return (
    <LotosAppShell>
      {showTabShell ? (
        <AppTabShell activeTab={screen as AppTab} onNavigate={handleTabNavigate}>
          {renderScreen()}
        </AppTabShell>
      ) : (
        renderScreen()
      )}
      {welcomeOpen && authenticated && (
        <WelcomeBanner
          clientName={clientName}
          studioName={config?.studioName ?? 'Lotos Studio'}
          onClose={handleWelcomeClose}
        />
      )}
    </LotosAppShell>
  )
}

function App() {
  return (
    <LotosThemeProvider>
      <AppContent />
    </LotosThemeProvider>
  )
}

export default App
