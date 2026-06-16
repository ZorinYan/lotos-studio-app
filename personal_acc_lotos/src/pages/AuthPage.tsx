import { FormItem, Input, ScreenSpinner, Snackbar } from '@vkontakte/vkui'
import { useEffect, useState } from 'react'
import {
  fetchBoot,
  setPassword,
  submitPhone,
  verifyName,
  verifyPassword,
  type AuthStep,
  type AuthSessionPayload,
  type PublicConfig,
  type VerifyResponse,
} from '../api/auth'
import { ApiError } from '../api/client'
import type { VkUser } from '../hooks/useVkApp'
import './AuthPage.css'

type FlowStep = 'phone' | AuthStep | 'setPassword'

type AuthPageProps = {
  vkUser: VkUser
  bootError: string | null
  initialConfig?: PublicConfig | null
  sessionChecking?: boolean
  onAuthenticated: (session?: AuthSessionPayload) => void | Promise<void>
  onOpenSchedule?: () => void
}

export function AuthPage({
  vkUser,
  bootError,
  initialConfig = null,
  sessionChecking = false,
  onAuthenticated,
  onOpenSchedule,
}: AuthPageProps) {
  const [step, setStep] = useState<FlowStep>('phone')
  const [submitting, setSubmitting] = useState(false)
  const [config, setConfig] = useState<PublicConfig | null>(initialConfig)
  const [phoneInput, setPhoneInput] = useState('')
  const [nameInput, setNameInput] = useState('')
  const [passwordInput, setPasswordInput] = useState('')
  const [passwordConfirmInput, setPasswordConfirmInput] = useState('')
  const [verifiedPhone, setVerifiedPhone] = useState('')
  const [requiresSurname, setRequiresSurname] = useState(false)
  const [error, setError] = useState<string | null>(bootError ?? null)

  useEffect(() => {
    if (initialConfig) {
      setConfig(initialConfig)
    }
  }, [initialConfig])

  useEffect(() => {
    setError(bootError ?? null)
  }, [bootError])

  function resetPasswordFields() {
    setPasswordInput('')
    setPasswordConfirmInput('')
  }

  async function handlePhoneSubmit() {
    setSubmitting(true)
    setError(null)
    try {
      const result = await submitPhone(vkUser.id, phoneInput)
      setVerifiedPhone(result.phone)
      setRequiresSurname(result.requiresSurname)
      resetPasswordFields()
      setStep(result.step)
    } catch (err) {
      const message =
        err instanceof ApiError
          ? err.message
          : 'Не удалось проверить номер. Убедитесь, что API запущен (npm run dev:api).'
      setError(message)
    } finally {
      setSubmitting(false)
    }
  }

  async function handleNameSubmit() {
    setSubmitting(true)
    setError(null)
    try {
      const result = await verifyName(vkUser.id, verifiedPhone, nameInput)
      if (result.needsPassword) {
        resetPasswordFields()
        setStep('setPassword')
      } else {
        await onAuthenticated(sessionFromVerify(result))
      }
    } catch (err) {
      if (err instanceof ApiError && err.code === 'session_expired') {
        setStep('phone')
        setVerifiedPhone('')
      }
      setError(err instanceof ApiError ? err.message : 'Не удалось подтвердить имя')
    } finally {
      setSubmitting(false)
    }
  }

  function sessionFromVerify(result: VerifyResponse): AuthSessionPayload {
    return {
      phone: result.phone,
      phoneDisplay: result.phoneDisplay,
      clientName: result.clientName ?? null,
    }
  }

  async function handlePasswordSubmit() {
    setSubmitting(true)
    setError(null)
    try {
      const result = await verifyPassword(vkUser.id, verifiedPhone, passwordInput)
      await onAuthenticated(sessionFromVerify(result))
    } catch (err) {
      if (err instanceof ApiError && err.code === 'password_not_set') {
        setStep('name')
      }
      setError(err instanceof ApiError ? err.message : 'Не удалось проверить пароль')
    } finally {
      setSubmitting(false)
    }
  }

  async function handleSetPasswordSubmit() {
    setSubmitting(true)
    setError(null)
    try {
      const result = await setPassword(
        vkUser.id,
        verifiedPhone,
        passwordInput,
        passwordConfirmInput,
      )
      await onAuthenticated(sessionFromVerify(result))
    } catch (err) {
      if (err instanceof ApiError && err.code === 'timeout') {
        try {
          const boot = await fetchBoot(vkUser.id)
          if (boot.auth.authenticated) {
            await onAuthenticated({
              phone: boot.auth.phone ?? verifiedPhone,
              phoneDisplay: boot.auth.phoneDisplay ?? verifiedPhone,
              clientName: boot.auth.clientName,
            })
            return
          }
        } catch {
          // пароль мог сохраниться, но boot недоступен
        }
      }
      setError(err instanceof ApiError ? err.message : 'Не удалось сохранить пароль')
    } finally {
      setSubmitting(false)
    }
  }

  if (submitting && step !== 'phone') {
    return (
      <div className="auth-page">
        <div className="auth-page__hero">
          <ScreenSpinner />
        </div>
      </div>
    )
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
          <p className="auth-page__step">Шаг 1</p>
          <h2 className="auth-page__section-title">Вход по номеру</h2>
          {sessionChecking && (
            <p className="auth-page__hint auth-page__hint--status">
              Проверяем сессию… Форма откроется через несколько секунд.
            </p>
          )}
          <p className="auth-page__hint">
            Введите телефон, указанный при записи в студию.
            {submitting ? ' Проверяем номер в студии — это может занять до минуты.' : ''}
          </p>
          {error && (
            <p className="auth-page__hint auth-page__hint--error" role="alert">
              {error}
            </p>
          )}
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
            disabled={submitting || sessionChecking || !phoneInput.trim()}
            onClick={() => void handlePhoneSubmit()}
          >
            {sessionChecking ? 'Подключаемся…' : submitting ? 'Проверяем…' : 'Продолжить'}
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

      {step === 'password' && (
        <section className="auth-page__card lotos-card">
          <p className="auth-page__step">Шаг 2</p>
          <h2 className="auth-page__section-title">Ваш пароль</h2>
          <p className="auth-page__hint">
            Введите пароль, который вы задавали при первом входе.
          </p>
          <FormItem top="Пароль" htmlFor="login-password">
            <Input
              id="login-password"
              type="password"
              placeholder="Пароль"
              value={passwordInput}
              onChange={(event) => setPasswordInput(event.target.value)}
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
                resetPasswordFields()
              }}
            >
              Назад
            </button>
            <button
              type="button"
              className="lotos-btn lotos-btn--primary"
              style={{ flex: 1 }}
              disabled={submitting || passwordInput.length < 6}
              onClick={() => void handlePasswordSubmit()}
            >
              {submitting ? 'Входим…' : 'Войти'}
            </button>
          </div>
          <button
            type="button"
            className="auth-page__link-btn"
            disabled={submitting}
            onClick={() => {
              setStep('name')
              setNameInput('')
              resetPasswordFields()
            }}
          >
            Забыли пароль? Войти по имени
          </button>
        </section>
      )}

      {step === 'name' && (
        <section className="auth-page__card lotos-card">
          <p className="auth-page__step">Подтверждение</p>
          <h2 className="auth-page__section-title">Имя в студии</h2>
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
              {submitting ? 'Проверяем…' : 'Продолжить'}
            </button>
          </div>
        </section>
      )}

      {step === 'setPassword' && (
        <section className="auth-page__card lotos-card">
          <p className="auth-page__step">Регистрация</p>
          <h2 className="auth-page__section-title">Придумайте пароль</h2>
          <p className="auth-page__hint">
            Задайте пароль для следующих входов. Минимум 6 символов.
          </p>
          <FormItem top="Пароль" htmlFor="new-password">
            <Input
              id="new-password"
              type="password"
              placeholder="Не короче 6 символов"
              value={passwordInput}
              onChange={(event) => setPasswordInput(event.target.value)}
              disabled={submitting}
            />
          </FormItem>
          <FormItem top="Повторите пароль" htmlFor="new-password-confirm">
            <Input
              id="new-password-confirm"
              type="password"
              placeholder="Ещё раз"
              value={passwordConfirmInput}
              onChange={(event) => setPasswordConfirmInput(event.target.value)}
              disabled={submitting}
            />
          </FormItem>
          <button
            type="button"
            className="lotos-btn lotos-btn--primary lotos-btn--stretched"
            disabled={
              submitting
              || passwordInput.length < 6
              || passwordConfirmInput.length < 6
            }
            onClick={() => void handleSetPasswordSubmit()}
          >
            {submitting ? 'Сохраняем…' : 'Сохранить и войти'}
          </button>
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
