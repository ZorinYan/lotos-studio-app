import { AppRoot, ConfigProvider, Placeholder, ScreenSpinner } from '@vkontakte/vkui'
import '@vkontakte/vkui/dist/vkui.css'
import './styles/lotos-theme.css'
import { useCallback, useEffect, useState, type ReactNode } from 'react'
import { fetchAuthStatus, fetchPublicConfig, logout, type PublicConfig } from './api/auth'
import { ApiError } from './api/client'
import { AuthPage } from './pages/AuthPage'
import { CabinetPage } from './pages/CabinetPage'
import { HomePage } from './pages/HomePage'
import { RecordsPage } from './pages/RecordsPage'
import { SchedulePage } from './pages/SchedulePage'
import { useVkApp } from './hooks/useVkApp'
import './App.css'

type Screen = 'loading' | 'auth' | 'home' | 'cabinet' | 'schedule' | 'records'

function LotosAppShell({ children }: { children: ReactNode }) {
  return (
    <ConfigProvider colorScheme="light">
      <AppRoot className="lotos-app">{children}</AppRoot>
    </ConfigProvider>
  )
}

function App() {
  const { ready, vkUser, error: vkError } = useVkApp()
  const [screen, setScreen] = useState<Screen>('loading')
  const [config, setConfig] = useState<PublicConfig | null>(null)
  const [phoneDisplay, setPhoneDisplay] = useState<string | null>(null)
  const [clientName, setClientName] = useState<string | null>(null)
  const [bootError, setBootError] = useState<string | null>(null)

  const checkSession = useCallback(async (userId: number) => {
    const [publicConfig, status] = await Promise.all([
      fetchPublicConfig(),
      fetchAuthStatus(userId),
    ])
    setConfig(publicConfig)
    if (status.authenticated) {
      setPhoneDisplay(status.phoneDisplay)
      setClientName(status.clientName)
      setScreen('home')
    } else {
      setPhoneDisplay(null)
      setClientName(null)
      setScreen('auth')
    }
  }, [])

  useEffect(() => {
    if (!ready || !vkUser) return

    let cancelled = false
    void (async () => {
      try {
        await checkSession(vkUser.id)
      } catch (err) {
        if (!cancelled) {
          setBootError(err instanceof ApiError ? err.message : 'Не удалось загрузить приложение')
          setScreen('auth')
        }
      }
    })()

    return () => {
      cancelled = true
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
      setPhoneDisplay(status.phoneDisplay)
      setClientName(status.clientName)
      setScreen('home')
    } catch {
      setScreen('home')
    }
  }, [vkUser])

  const handleLogout = useCallback(async () => {
    if (!vkUser) return
    await logout(vkUser.id)
    setPhoneDisplay(null)
    setClientName(null)
    setScreen('auth')
  }, [vkUser])

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

  return (
    <LotosAppShell>
        {screen === 'loading' && <ScreenSpinner />}

        {screen === 'auth' && (
          <AuthPage
            vkUser={vkUser}
            bootError={bootError}
            onAuthenticated={handleAuthenticated}
          />
        )}

        {screen === 'home' && (
          <HomePage
            vkUserId={vkUser.id}
            clientName={clientName}
            studioName={config?.studioName ?? 'Lotos Studio'}
            phoneDisplay={phoneDisplay}
            onOpenCabinet={() => setScreen('cabinet')}
            onOpenSchedule={() => setScreen('schedule')}
            onOpenRecords={() => setScreen('records')}
            onLogout={() => void handleLogout()}
          />
        )}

        {screen === 'cabinet' && (
          <CabinetPage
            vkUserId={vkUser.id}
            studioName={config?.studioName ?? 'Lotos Studio'}
            onBack={() => setScreen('home')}
            onOpenRecords={() => setScreen('records')}
          />
        )}

        {screen === 'schedule' && (
          <SchedulePage
            vkUserId={vkUser.id}
            studioName={config?.studioName ?? 'Lotos Studio'}
            onBack={() => setScreen('home')}
          />
        )}

        {screen === 'records' && (
          <RecordsPage
            vkUserId={vkUser.id}
            studioName={config?.studioName ?? 'Lotos Studio'}
            onBack={() => setScreen('home')}
          />
        )}
    </LotosAppShell>
  )
}

export default App
