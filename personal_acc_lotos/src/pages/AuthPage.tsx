import { FormItem, Input, ScreenSpinner, Snackbar } from '@vkontakte/vkui'
import { useEffect, useState } from 'react'
import {
  fetchPublicConfig,
  resendOtp,
  submitPhone,
  verifyName,
  verifyOtp,
  type AuthStep,
  type PublicConfig,
} from '../api/auth'
import { ApiError } from '../api/client'
import type { VkUser } from '../hooks/useVkApp'
import { requestVkNotificationsPermission } from '../vkBridge'
import './AuthPage.css'

const OTP_WAIT_SEC = 60

type AuthPageProps = {
  vkUser: VkUser
  bootError: string | null
  onAuthenticated: () => void
  onOpenSchedule?: () => void
}

export function AuthPage({ vkUser, bootError, onAuthenticated, onOpenSchedule }: AuthPageProps) {
  const [step, setStep] = useState<'phone' | AuthStep>('phone')
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [config, setConfig] = useState<PublicConfig | null>(null)
  const [phoneInput, setPhoneInput] = useState('')
  const [nameInput, setNameInput] = useState('')
  const [otpInput, setOtpInput] = useState('')
  const [verifiedPhone, setVerifiedPhone] = useState('')
  const [requiresSurname, setRequiresSurname] = useState(false)
  const [messagesAllowed, setMessagesAllowed] = useState(false)
  const [messagesPermissionPending, setMessagesPermissionPending] = useState(true)
  const [otpSecondsLeft, setOtpSecondsLeft] = useState(OTP_WAIT_SEC)
  const [otpSession, setOtpSession] = useState(0)
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

      try {
        const allowed = await requestVkNotificationsPermission()
        if (!cancelled) {
          setMessagesAllowed(allowed)
          setMessagesPermissionPending(false)
        }
      } catch {
        if (!cancelled) {
          setMessagesAllowed(false)
          setMessagesPermissionPending(false)
        }
      }
    }

    void load()

    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    if (step !== 'otp') return

    setOtpSecondsLeft(OTP_WAIT_SEC)
    const intervalId = window.setInterval(() => {
      setOtpSecondsLeft((prev) => {
        if (prev <= 1) {
          window.clearInterval(intervalId)
          return 0
        }
        return prev - 1
      })
    }, 1000)

    const timeoutId = window.setTimeout(() => {
      setStep('name')
      setError('Код не пришёл за минуту. Войдите по имени, как в студии.')
    }, OTP_WAIT_SEC * 1000)

    return () => {
      window.clearInterval(intervalId)
      window.clearTimeout(timeoutId)
    }
  }, [step, verifiedPhone, otpSession])

  function goToNameStep(message?: string) {
    setStep('name')
    if (message) setError(message)
  }

  async function handlePhoneSubmit() {
    setSubmitting(true)
    setError(null)
    try {
      const result = await submitPhone(
        vkUser.id,
        phoneInput,
        !messagesPermissionPending && messagesAllowed,
      )
      setVerifiedPhone(result.phone)
      setRequiresSurname(result.requiresSurname)
      if (result.step === 'otp') {
        setOtpInput('')
        setOtpSession((value) => value + 1)
        setStep('otp')
      } else {
        goToNameStep(
          messagesAllowed
            ? 'Не удалось отправить код в VK. Войдите по имени, как в студии.'
            : undefined,
        )
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Не удалось проверить номер')
    } finally {
      setSubmitting(false)
    }
  }

  async function handleOtpSubmit() {
    setSubmitting(true)
    setError(null)
    try {
      await verifyOtp(vkUser.id, verifiedPhone, otpInput)
      onAuthenticated()
    } catch (err) {
      if (err instanceof ApiError && err.code === 'otp_verification_failed') {
        setError(err.message)
        return
      }
      setError(err instanceof ApiError ? err.message : 'Не удалось проверить код')
    } finally {
      setSubmitting(false)
    }
  }

  async function handleOtpResend() {
    setSubmitting(true)
    setError(null)
    try {
      await resendOtp(vkUser.id, verifiedPhone)
      setOtpInput('')
      setOtpSession((value) => value + 1)
      setStep('otp')
    } catch (err) {
      goToNameStep(
        err instanceof ApiError
          ? err.message
          : 'Не удалось отправить код. Войдите по имени, как в студии.',
      )
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
          <p className="auth-page__step">Шаг 1</p>
          <h2 className="auth-page__section-title">Вход по номеру</h2>
          <p className="auth-page__hint">
            Введите телефон, указанный при записи в студию.
            {messagesAllowed
              ? ' Мы отправим код в сообщения VK.'
              : ' Подтверждение — по имени, как в студии.'}
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

      {step === 'otp' && (
        <section className="auth-page__card lotos-card">
          <p className="auth-page__step">Шаг 2 — код из VK</p>
          <h2 className="auth-page__section-title">Проверка по сообщению</h2>
          <p className="auth-page__hint">
            Код отправлен в личные сообщения от сообщества студии.
            {otpSecondsLeft > 0
              ? ` Осталось ${otpSecondsLeft} сек до входа по имени.`
              : ''}
          </p>
          <FormItem top="Код из VK" htmlFor="otp-code">
            <Input
              id="otp-code"
              type="text"
              inputMode="numeric"
              maxLength={6}
              placeholder="123456"
              value={otpInput}
              onChange={(event) => setOtpInput(event.target.value.replace(/\D/g, ''))}
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
                setOtpInput('')
              }}
            >
              Назад
            </button>
            <button
              type="button"
              className="lotos-btn lotos-btn--primary"
              style={{ flex: 1 }}
              disabled={submitting || otpInput.length !== 6}
              onClick={() => void handleOtpSubmit()}
            >
              {submitting ? 'Проверяем…' : 'Войти'}
            </button>
          </div>
          <button
            type="button"
            className="auth-page__link-btn"
            disabled={submitting}
            onClick={() => goToNameStep()}
          >
            Не пришёл код? Войти по имени
          </button>
          <button
            type="button"
            className="auth-page__link-btn"
            disabled={submitting}
            onClick={() => void handleOtpResend()}
          >
            Отправить код ещё раз
          </button>
        </section>
      )}

      {step === 'name' && (
        <section className="auth-page__card lotos-card">
          <p className="auth-page__step">Подтверждение личности</p>
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
