import { FormItem, Input, ScreenSpinner, Snackbar } from '@vkontakte/vkui'
import { useEffect, useState } from 'react'
import {
  fetchPublicConfig,
  submitPhone,
  verifyName,
  type PublicConfig,
} from '../api/auth'
import { ApiError } from '../api/client'
import type { VkUser } from '../hooks/useVkApp'
import './AuthPage.css'

type AuthPageProps = {
  vkUser: VkUser
  bootError?: string | null
  onAuthenticated: () => void
  onOpenSchedule?: () => void
}

export function AuthPage({ vkUser, bootError, onAuthenticated, onOpenSchedule }: AuthPageProps) {
  const [step, setStep] = useState<'phone' | 'name'>('phone')
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [config, setConfig] = useState<PublicConfig | null>(null)
  const [phoneInput, setPhoneInput] = useState('')
  const [nameInput, setNameInput] = useState('')
  const [verifiedPhone, setVerifiedPhone] = useState('')
  const [requiresSurname, setRequiresSurname] = useState(false)
  const [error, setError] = useState<string | null>(bootError ?? null)

  useEffect(() => {
    let cancelled = false

    async function load() {
      try {
        const publicConfig = await fetchPublicConfig()
        if (!cancelled) setConfig(publicConfig)
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : 'Не удалось загрузить данные')
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    void load()

    return () => {
      cancelled = true
    }
  }, [])

  async function handlePhoneSubmit() {
    setSubmitting(true)
    setError(null)
    try {
      const result = await submitPhone(vkUser.id, phoneInput)
      setVerifiedPhone(result.phone)
      setRequiresSurname(result.requiresSurname)
      setStep('name')
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Не удалось проверить номер')
    } finally {
      setSubmitting(false)
    }
  }

  async function handleNameSubmit() {
    setSubmitting(true)
    setError(null)
    try {
      await verifyName(vkUser.id, verifiedPhone, nameInput)
      onAuthenticated()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Не удалось подтвердить имя')
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) {
    return <ScreenSpinner />
  }

  const greeting = vkUser.first_name
    ? `${vkUser.first_name}, добро пожаловать`
    : 'Добро пожаловать'
  const studioName = config?.studioName ?? 'Lotos Studio'

  return (
    <div className="auth-page">
      <div className="auth-page__hero">
        <div className="auth-page__orb" aria-hidden="true" />
        <span className="auth-page__logo" aria-hidden="true">🪷</span>
        <p className="auth-page__brand">Lotos Studio</p>
        <h1 className="auth-page__title">{greeting}</h1>
        <p className="auth-page__subtitle">Студия растяжки «{studioName}»</p>
      </div>

      {step === 'phone' && (
        <section className="auth-page__card lotos-card">
          <p className="auth-page__step">Шаг 1 из 2</p>
          <h2 className="auth-page__section-title">Вход по номеру</h2>
          <p className="auth-page__hint">
            Введите телефон, указанный при записи в студию
          </p>
          <FormItem top="Телефон" htmlFor="phone">
            <Input
              id="phone"
              type="tel"
              inputMode="tel"
              placeholder="8 999 123 45 67"
              value={phoneInput}
              onChange={(event) => setPhoneInput(event.target.value)}
              disabled={submitting}
            />
          </FormItem>
          <button
            type="button"
            className="lotos-btn lotos-btn--primary lotos-btn--stretched"
            disabled={submitting || !phoneInput.trim()}
            onClick={() => void handlePhoneSubmit()}
          >
            {submitting ? 'Проверяем…' : 'Продолжить'}
          </button>
          {onOpenSchedule && (
            <button
              type="button"
              className="lotos-btn lotos-btn--secondary lotos-btn--stretched auth-page__schedule-btn"
              disabled={submitting}
              onClick={onOpenSchedule}
            >
              Смотреть расписание и записаться
            </button>
          )}
        </section>
      )}

      {step === 'name' && (
        <section className="auth-page__card lotos-card">
          <p className="auth-page__step">Шаг 2 из 2</p>
          <h2 className="auth-page__section-title">Подтверждение</h2>
          <p className="auth-page__hint">
            {requiresSurname
              ? 'Введите имя и фамилию, как в студии'
              : 'Введите имя, как в студии'}
          </p>
          <FormItem
            top={requiresSurname ? 'Имя и фамилия' : 'Имя'}
            htmlFor="client-name"
          >
            <Input
              id="client-name"
              placeholder={requiresSurname ? 'Иван Иванов' : 'Иван'}
              value={nameInput}
              onChange={(event) => setNameInput(event.target.value)}
              disabled={submitting}
            />
          </FormItem>
          <div className="auth-page__actions">
            <button
              type="button"
              className="lotos-btn lotos-btn--secondary"
              disabled={submitting}
              onClick={() => {
                setStep('phone')
                setNameInput('')
              }}
            >
              Назад
            </button>
            <button
              type="button"
              className="lotos-btn lotos-btn--primary"
              style={{ flex: 1 }}
              disabled={submitting || !nameInput.trim()}
              onClick={() => void handleNameSubmit()}
            >
              {submitting ? 'Входим…' : 'Войти'}
            </button>
          </div>
        </section>
      )}

      {error && (
        <Snackbar onClose={() => setError(null)} duration={5000}>
          {error}
        </Snackbar>
      )}
    </div>
  )
}
