import { ScreenSpinner, Snackbar, Switch } from '@vkontakte/vkui'
import { useCallback, useEffect, useState } from 'react'
import { fetchSettings, updateSettings } from '../api/settings'
import { fetchScheduleFilters } from '../api/schedule'
import { ApiError } from '../api/client'
import { AppHeader } from '../components/AppHeader'
import { useLotosTheme } from '../hooks/useLotosTheme'
import {
  isVkEnvironment,
  resolveInitialNotificationsEnabled,
  setVkNotificationsEnabled,
} from '../vkBridge'
import './SettingsPage.css'

type SettingsPageProps = {
  vkUserId: number
  phoneDisplay: string | null
  onLogout: () => void
}

export function SettingsPage({ vkUserId, phoneDisplay, onLogout }: SettingsPageProps) {
  const { isDark, setColorScheme } = useLotosTheme()
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [favoriteTrainerId, setFavoriteTrainerId] = useState<number | null>(null)
  const [notificationsEnabled, setNotificationsEnabled] = useState(false)
  const [notificationsAvailable, setNotificationsAvailable] = useState(true)
  const [trainers, setTrainers] = useState<{ id: number; name: string }[]>([])

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [settings, filters] = await Promise.all([
        fetchSettings(vkUserId),
        fetchScheduleFilters(),
      ])
      setFavoriteTrainerId(settings.favoriteTrainer?.id ?? null)
      setNotificationsEnabled(
        settings.notificationsEnabled || resolveInitialNotificationsEnabled(),
      )
      setTrainers(filters.trainers)
      setNotificationsAvailable(
        isVkEnvironment() && import.meta.env.VITE_SKIP_VK_BRIDGE !== 'true',
      )
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Не удалось загрузить настройки')
    } finally {
      setLoading(false)
    }
  }, [vkUserId])

  useEffect(() => {
    void load()
  }, [load])

  async function handleTrainerSelect(trainerId: number | null) {
    setSaving(true)
    setError(null)
    try {
      if (trainerId === null) {
        const settings = await updateSettings(vkUserId, { clearFavorite: true })
        setFavoriteTrainerId(settings.favoriteTrainer?.id ?? null)
        return
      }

      const trainer = trainers.find((item) => item.id === trainerId)
      if (!trainer) return

      const settings = await updateSettings(vkUserId, {
        favoriteStaffId: trainer.id,
        favoriteStaffName: trainer.name,
      })
      setFavoriteTrainerId(settings.favoriteTrainer?.id ?? null)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Не удалось сохранить тренера')
    } finally {
      setSaving(false)
    }
  }

  async function handleNotificationsToggle(enabled: boolean) {
    setSaving(true)
    setError(null)
    try {
      const granted = await setVkNotificationsEnabled(enabled)
      const nextValue = enabled ? granted : false
      const settings = await updateSettings(vkUserId, {
        notificationsEnabled: nextValue,
      })
      setNotificationsEnabled(settings.notificationsEnabled)
      if (enabled && !granted) {
        setError('VK не разрешил уведомления. Попробуйте ещё раз или проверьте настройки VK.')
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Не удалось обновить уведомления')
    } finally {
      setSaving(false)
    }
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
            {phoneDisplay && (
              <p className="settings-page__account">Аккаунт: {phoneDisplay}</p>
            )}

            <section className="settings-section lotos-card">
              <h2 className="settings-section__title">Любимый тренер</h2>
              <p className="settings-section__hint">
                В расписании можно быстро смотреть занятия выбранного тренера.
              </p>
              <div className="settings-chips">
                <button
                  type="button"
                  className={`settings-chips__item${
                    favoriteTrainerId === null ? ' settings-chips__item--active' : ''
                  }`}
                  disabled={saving}
                  onClick={() => void handleTrainerSelect(null)}
                >
                  Не выбран
                </button>
                {trainers.map((trainer) => (
                  <button
                    key={trainer.id}
                    type="button"
                    className={`settings-chips__item${
                      favoriteTrainerId === trainer.id ? ' settings-chips__item--active' : ''
                    }`}
                    disabled={saving}
                    onClick={() => void handleTrainerSelect(trainer.id)}
                  >
                    {trainer.name}
                  </button>
                ))}
              </div>
            </section>

            <section className="settings-section lotos-card">
              <div className="settings-toggle">
                <div>
                  <h2 className="settings-section__title">Тёмная тема</h2>
                  <p className="settings-section__hint">
                    Комфортный тёмный режим с теми же фирменными оттенками Lotos.
                  </p>
                </div>
                <Switch
                  checked={isDark}
                  disabled={saving}
                  onChange={(event) =>
                    setColorScheme(event.target.checked ? 'dark' : 'light')
                  }
                />
              </div>
            </section>

            <section className="settings-section lotos-card">
              <div className="settings-toggle">
                <div>
                  <h2 className="settings-section__title">Уведомления VK</h2>
                  <p className="settings-section__hint">
                    Напоминания о занятиях и коды входа от сообщества студии.
                  </p>
                  {!notificationsAvailable && (
                    <p className="settings-section__note">
                      Доступно только при открытии мини-приложения внутри VK.
                    </p>
                  )}
                </div>
                <Switch
                  checked={notificationsEnabled}
                  disabled={saving || !notificationsAvailable}
                  onChange={(event) => void handleNotificationsToggle(event.target.checked)}
                />
              </div>
            </section>

            <div className="settings-logout">
              <button
                type="button"
                className="settings-logout__badge"
                onClick={onLogout}
              >
                Выйти из аккаунта
              </button>
            </div>
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
