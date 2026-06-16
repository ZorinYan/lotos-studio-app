import { ScreenSpinner, Snackbar, Switch } from '@vkontakte/vkui'
import { useCallback, useEffect, useState } from 'react'
import { fetchStaffSettings, updateStaffSettings } from '../api/staff'
import { clearBootCache } from '../api/auth'
import { ApiError } from '../api/client'
import { AppHeader } from '../components/AppHeader'
import { useLotosTheme } from '../hooks/useLotosTheme'
import './SettingsPage.css'

type StaffSettingsPageProps = {
  vkUserId: number
}

export function StaffSettingsPage({ vkUserId }: StaffSettingsPageProps) {
  const { isDark, setColorScheme } = useLotosTheme()
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const settings = await fetchStaffSettings(vkUserId)
      setColorScheme(settings.colorScheme as 'light' | 'dark')
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Не удалось загрузить настройки')
    } finally {
      setLoading(false)
    }
  }, [vkUserId, setColorScheme])

  useEffect(() => {
    void load()
  }, [load])

  function handleThemeChange(enabled: boolean) {
    const scheme: 'light' | 'dark' = enabled ? 'dark' : 'light'
    const previousScheme = enabled ? 'light' : 'dark'

    setColorScheme(scheme)
    clearBootCache(vkUserId)
    setError(null)

    setSaving(true)
    void updateStaffSettings(vkUserId, { colorScheme: scheme })
      .catch((err) => {
        setColorScheme(previousScheme)
        setError(err instanceof ApiError ? err.message : 'Не удалось сохранить тему')
      })
      .finally(() => setSaving(false))
  }

  return (
    <div className="settings-page">
      <AppHeader title="Настройки" showCabinetButton={false} />

      <main className="settings-page__content">
        {loading ? (
          <div className="settings-page__loading">
            <ScreenSpinner />
          </div>
        ) : (
          <>
            <section className="settings-section lotos-card">
              <div className="settings-toggle">
                <div>
                  <h2 className="settings-section__title">Тёмная тема</h2>
                  <p className="settings-section__hint">
                    Переключите тему для интерфейса сотрудника. Хранится в БД.
                  </p>
                </div>
                <Switch checked={isDark} onChange={(event) => handleThemeChange(event.target.checked)} disabled={saving} />
              </div>
            </section>
          </>
        )}
      </main>

      {error && (
        <Snackbar onClose={() => setError(null)} duration={5000}>
          {error}
        </Snackbar>
      )}
    </div>
  )
}

