import { AppRoot, ConfigProvider, Placeholder, ScreenSpinner } from '@vkontakte/vkui'
import '@vkontakte/vkui/dist/vkui.css'
import './styles/lotos-theme.css'
import { useCallback, useEffect, useState, type ReactNode } from 'react'
import { clearBootCache, fetchBoot, fetchPublicConfig, logout, type AuthSessionPayload, type AuthStatus, type PublicConfig, type UserPrefs } from './api/auth'
import { fetchSettings } from './api/settings'
import { ApiError } from './api/client'
import { registerSessionExpiredHandler } from './api/session'
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
import { markWelcomeBannerSeen } from './utils/welcomeBanner'
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
  const { setColorScheme } = useLotosTheme()
  const [screen, setScreen] = useState<Screen>('loading')
  const [config, setConfig] = useState<PublicConfig | null>(null)
  const [phoneDisplay, setPhoneDisplay] = useState<string | null>(null)
  const [clientName, setClientName] = useState<string | null>(null)
  const [favoriteTrainerId, setFavoriteTrainerId] = useState<number | null>(null)
  const [bootError, setBootError] = useState<string | null>(null)
  const [sessionChecking, setSessionChecking] = useState(true)
  const [guestSchedule, setGuestSchedule] = useState(false)
  const [authenticated, setAuthenticated] = useState(false)
  const [welcomeOpen, setWelcomeOpen] = useState(false)

  const applyUserPrefs = useCallback(
    (prefs: UserPrefs, options?: { showWelcome?: boolean }) => {
      setColorScheme(prefs.colorScheme)
      if (options?.showWelcome && !prefs.welcomeBannerSeen) {
        setWelcomeOpen(true)
      }
    },
    [setColorScheme],
  )

  const loadUserSettings = useCallback(async (userId: number) => {
    try {
      const settings = await fetchSettings(userId)
      setFavoriteTrainerId(settings.favoriteTrainer?.id ?? null)
      return settings
    } catch {
      setFavoriteTrainerId(null)
      return null
    }
  }, [])

  const applySession = useCallback((status: AuthStatus) => {
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
    const boot = await fetchBoot(userId)
    setConfig(boot.config)
    applySession(boot.auth)
    setColorScheme(boot.prefs.colorScheme)
    if (boot.auth.authenticated) {
      setScreen('home')
      if (!boot.prefs.welcomeBannerSeen) {
        setWelcomeOpen(true)
      }
      void loadUserSettings(userId)
    } else {
      setScreen('auth')
    }
  }, [applySession, loadUserSettings, setColorScheme])

  useEffect(() => {
    if (!ready || !vkUser) return

    let cancelled = false
    setScreen('auth')
    setSessionChecking(true)
    setBootError(null)

    const unlockFormTimer = window.setTimeout(() => {
      if (!cancelled) {
        setSessionChecking(false)
      }
    }, 8_000)

    void (async () => {
      try {
        await checkSession(vkUser.id)
      } catch (err) {
        if (!cancelled) {
          const message =
            err instanceof ApiError
              ? err.message
              : err instanceof Error
                ? err.message
                : 'Не удалось загрузить приложение'
          setBootError(message)
          setScreen('auth')
        }
      } finally {
        window.clearTimeout(unlockFormTimer)
        if (!cancelled) {
          setSessionChecking(false)
        }
      }
    })()

    return () => {
      cancelled = true
      window.clearTimeout(unlockFormTimer)
    }
  }, [ready, vkUser, checkSession])

  const handleAuthenticated = useCallback(async (session?: AuthSessionPayload) => {
    if (!vkUser) return

    if (session) {
      setAuthenticated(true)
      setPhoneDisplay(session.phoneDisplay)
      setClientName(session.clientName ?? null)
      setGuestSchedule(false)
      setBootError(null)
      setScreen('home')
      void loadUserSettings(vkUser.id).then((settings) => {
        if (settings && !settings.welcomeBannerSeen) {
          setWelcomeOpen(true)
        }
      })
      return
    }

    try {
      const boot = await fetchBoot(vkUser.id)
      setConfig(boot.config)
      applySession(boot.auth)
      if (!boot.auth.authenticated) {
        setBootError('Сессия не сохранилась. Попробуйте войти снова.')
        setScreen('auth')
        return
      }
      await loadUserSettings(vkUser.id)
      applyUserPrefs(boot.prefs, { showWelcome: true })
      setScreen('home')
    } catch (err) {
      setBootError(
        err instanceof ApiError ? err.message : 'Не удалось завершить вход',
      )
      setScreen('auth')
    }
  }, [vkUser, applySession, loadUserSettings, applyUserPrefs])

  const handleWelcomeClose = useCallback(() => {
    if (vkUser) {
      void markWelcomeBannerSeen(vkUser.id)
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

  const handleLogout = useCallback(() => {
    if (!vkUser) return
    clearBootCache(vkUser.id)
    setPhoneDisplay(null)
    setClientName(null)
    setFavoriteTrainerId(null)
    setAuthenticated(false)
    setGuestSchedule(false)
    setWelcomeOpen(false)
    setBootError(null)
    setScreen('auth')
    void logout(vkUser.id).catch(() => {
      // UI уже на экране входа; повторный logout не критичен
    })
  }, [vkUser])

  const forceLogout = useCallback(
    async (message?: string) => {
      if (!vkUser) return
      try {
        await logout(vkUser.id)
      } catch {
        // локально сбрасываем сессию даже если API недоступен
      }
      setPhoneDisplay(null)
      setClientName(null)
      setFavoriteTrainerId(null)
      setAuthenticated(false)
      setGuestSchedule(false)
      setWelcomeOpen(false)
      setBootError(
        message ?? 'Сессия завершена. Войдите снова по номеру телефона.',
      )
      setScreen('auth')
    },
    [vkUser],
  )

  useEffect(() => {
    return registerSessionExpiredHandler((message) => {
      void forceLogout(message)
    })
  }, [forceLogout])

  const handleTabNavigate = useCallback((tab: AppTab) => {
    setGuestSchedule(false)
    setScreen(tab)
  }, [])

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
    if (screen === 'auth') {
      return (
        <AuthPage
          vkUser={user}
          bootError={bootError}
          initialConfig={config}
          sessionChecking={sessionChecking}
          onAuthenticated={handleAuthenticated}
          onOpenSchedule={() => void handleOpenGuestSchedule()}
        />
      )
    }

    if (screen === 'loading') {
      return <ScreenSpinner />
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
