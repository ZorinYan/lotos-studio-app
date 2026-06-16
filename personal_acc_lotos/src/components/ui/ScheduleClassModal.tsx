import { FormItem, Input } from '@vkontakte/vkui'
import { useRef, useState } from 'react'
import {
  bookScheduleClass,
  checkBookingEligibility,
  checkGuestBooking,
} from '../../api/schedule'
import { ApiError } from '../../api/client'
import { useModalOverlay } from '../../hooks/useModalOverlay'
import type { BookScheduleResult, BookingEligibility, ScheduleClass } from '../../types/schedule'
import { formatMoney } from '../../utils/format'
import { AddToCalendarButton } from './AddToCalendarButton'
import './ScheduleClassModal.css'

type ModalMode = 'details' | 'guest' | 'confirm' | 'success'

type ScheduleClassModalProps = {
  item: ScheduleClass
  dayLabel: string
  vkUserId: number
  studioName: string
  authenticated: boolean
  onClose: () => void
  onBooked: () => void
  onAuthenticated?: () => void
  onError: (message: string) => void
}

function formatClassPrice(item: ScheduleClass, trialHint = false): string | null {
  if (trialHint && item.trialPrice != null) {
    return `Пробное: ${formatMoney(item.trialPrice)}`
  }
  if (item.priceMin != null) {
    return formatMoney(item.priceMin)
  }
  return null
}

export function ScheduleClassModal({
  item,
  dayLabel,
  vkUserId,
  studioName,
  authenticated,
  onClose,
  onBooked,
  onAuthenticated,
  onError,
}: ScheduleClassModalProps) {
  const sheetRef = useRef<HTMLDivElement>(null)
  const [mode, setMode] = useState<ModalMode>('details')
  const [booking, setBooking] = useState(false)
  const [result, setResult] = useState<BookScheduleResult | null>(null)
  const [phoneInput, setPhoneInput] = useState('')
  const [nameInput, setNameInput] = useState('')
  const [surnameInput, setSurnameInput] = useState('')
  const [guestError, setGuestError] = useState<string | null>(null)
  const [eligibility, setEligibility] = useState<BookingEligibility | null>(null)
  const [checking, setChecking] = useState(false)

  const isFull = item.isFull
  const canBook = !isFull
  const showTrialPrice = item.hasTrial && item.trialPrice != null
  const regularPrice = formatClassPrice(item)
  const trialPriceLabel = formatClassPrice(item, true)

  const handleClose = () => {
    if (booking) return
    if (mode === 'success') {
      onBooked()
      if (!authenticated) {
        onAuthenticated?.()
      }
    }
    onClose()
  }

  useModalOverlay(handleClose, sheetRef)

  const guestFormComplete =
    phoneInput.trim().length > 0
    && nameInput.trim().length > 0
    && surnameInput.trim().length > 0

  const handleBook = async () => {
    setBooking(true)
    try {
      const guest =
        !authenticated && guestFormComplete
          ? {
              phone: phoneInput.trim(),
              name: nameInput.trim(),
              surname: surnameInput.trim(),
            }
          : undefined
      const response = await bookScheduleClass(
        vkUserId,
        item.id,
        item.date,
        guest,
      )
      setResult(response)
      setMode('success')
    } catch (err) {
      onError(err instanceof ApiError ? err.message : 'Не удалось записаться на занятие')
      setMode(authenticated ? 'details' : 'guest')
    } finally {
      setBooking(false)
    }
  }

  const startBooking = async () => {
    if (authenticated) {
      setChecking(true)
      setEligibility(null)
      try {
        const result = await checkBookingEligibility(vkUserId, item.id, item.date)
        setEligibility(result)
        setMode('confirm')
      } catch (err) {
        onError(err instanceof ApiError ? err.message : 'Не удалось проверить возможность записи')
      } finally {
        setChecking(false)
      }
      return
    }
    setGuestError(null)
    setMode('guest')
  }

  const handleGuestNext = async () => {
    if (!guestFormComplete) {
      setGuestError('Заполните телефон, имя и фамилию.')
      return
    }
    setChecking(true)
    setGuestError(null)
    try {
      const result = await checkGuestBooking(phoneInput.trim())
      if (!result.allowed) {
        setGuestError(result.message ?? 'Войдите по номеру телефона, чтобы записаться.')
        return
      }
      setMode('confirm')
    } catch (err) {
      onError(err instanceof ApiError ? err.message : 'Не удалось проверить номер телефона')
    } finally {
      setChecking(false)
    }
  }

  return (
    <div className="schedule-modal lotos-modal" role="dialog" aria-modal="true" aria-labelledby="schedule-modal-title">
      <button
        type="button"
        className="schedule-modal__backdrop"
        aria-label="Закрыть"
        onClick={handleClose}
        disabled={booking}
      />
      <div ref={sheetRef} className="schedule-modal__sheet lotos-modal__sheet lotos-card">
        <div className="schedule-modal__handle" aria-hidden="true" />
        <button
          type="button"
          className="schedule-modal__close"
          onClick={handleClose}
          aria-label="Закрыть"
          disabled={booking}
        >
          ×
        </button>

        {mode === 'success' && result ? (
          <div className="schedule-modal__success">
            <div className="schedule-modal__success-icon" aria-hidden="true">✓</div>
            <h2 className="schedule-modal__success-title">Вы записаны!</h2>
            <p className="schedule-modal__success-text">{result.message}</p>
            {result.isTrial && (
              <p className="schedule-modal__trial-note">
                Запись оформлена как пробное занятие по цене студии.
              </p>
            )}
            <dl className="schedule-modal__success-summary">
              <div className="schedule-modal__detail">
                <dt>Занятие</dt>
                <dd>{result.class.serviceTitle}</dd>
              </div>
              <div className="schedule-modal__detail">
                <dt>Дата и время</dt>
                <dd>
                  {result.class.dateLabel}, {result.class.time}
                </dd>
              </div>
              <div className="schedule-modal__detail">
                <dt>Тренер</dt>
                <dd>{result.class.trainer}</dd>
              </div>
              <div className="schedule-modal__detail">
                <dt>Телефон</dt>
                <dd>{result.phoneDisplay}</dd>
              </div>
            </dl>
            <p className="schedule-modal__hint">До встречи в студии</p>
            <div className="schedule-modal__actions schedule-modal__actions--stacked">
              <AddToCalendarButton
                stretched
                event={{
                  title: result.class.serviceTitle,
                  startsAt: result.class.startsAt,
                  endsAt: result.class.endsAt,
                  trainer: result.class.trainer,
                  studioName,
                }}
              />
              <button
                type="button"
                className="lotos-btn lotos-btn--primary lotos-btn--stretched"
                onClick={handleClose}
              >
                Отлично
              </button>
            </div>
          </div>
        ) : (
          <>
            <header className="schedule-modal__header">
              <p className="schedule-modal__eyebrow">{dayLabel} · {item.time}</p>
              <h2 id="schedule-modal-title" className="schedule-modal__title">
                {item.serviceTitle}
              </h2>
              <span
                className={`schedule-modal__status schedule-modal__status--${
                  isFull ? 'full' : 'free'
                }`}
              >
                {isFull ? 'Нет мест' : 'Есть свободные места'}
              </span>
              {(regularPrice || showTrialPrice) && (
                <div className="schedule-modal__prices">
                  {regularPrice && (
                    <span className="schedule-modal__price">{regularPrice}</span>
                  )}
                  {showTrialPrice && trialPriceLabel && (
                    <span className="schedule-modal__price schedule-modal__price--trial">
                      {trialPriceLabel}
                    </span>
                  )}
                </div>
              )}
            </header>

            {mode === 'guest' ? (
              <section className="schedule-modal__section">
                <h3 className="lotos-section-title">Запись без входа</h3>
                <p className="schedule-modal__confirm-text">
                  Без входа можно записаться только на первое пробное занятие.
                  {showTrialPrice
                    ? ' Если вы ещё не были в студии, запись оформится по пробной цене.'
                    : ' Укажите телефон, имя и фамилию.'}
                </p>
                <FormItem top="Телефон" htmlFor="book-phone" status="default" bottom="Обязательное поле">
                  <Input
                    id="book-phone"
                    type="tel"
                    inputMode="tel"
                    placeholder="8 999 123 45 67"
                    value={phoneInput}
                    onChange={(event) => setPhoneInput(event.target.value)}
                    disabled={booking}
                    required
                  />
                </FormItem>
                <FormItem top="Имя" htmlFor="book-name" status="default" bottom="Обязательное поле">
                  <Input
                    id="book-name"
                    placeholder="Иван"
                    value={nameInput}
                    onChange={(event) => setNameInput(event.target.value)}
                    disabled={booking || checking}
                    required
                  />
                </FormItem>
                <FormItem top="Фамилия" htmlFor="book-surname" status="default" bottom="Обязательное поле">
                  <Input
                    id="book-surname"
                    placeholder="Иванов"
                    value={surnameInput}
                    onChange={(event) => setSurnameInput(event.target.value)}
                    disabled={booking || checking}
                    required
                  />
                </FormItem>
                {guestError && (
                  <div className="schedule-modal__guest-error">
                    <p className="schedule-modal__hint schedule-modal__hint--error" role="alert">
                      {guestError}
                    </p>
                    {onAuthenticated && (
                      <button
                        type="button"
                        className="lotos-btn lotos-btn--secondary lotos-btn--stretched"
                        onClick={() => {
                          onClose()
                          onAuthenticated()
                        }}
                      >
                        Войти по номеру телефона
                      </button>
                    )}
                  </div>
                )}
                <div className="schedule-modal__actions">
                  <button
                    type="button"
                    className="lotos-btn lotos-btn--secondary"
                    disabled={booking || checking}
                    onClick={() => {
                      setGuestError(null)
                      setMode('details')
                    }}
                  >
                    Назад
                  </button>
                  <button
                    type="button"
                    className="lotos-btn lotos-btn--primary"
                    disabled={booking || checking || !guestFormComplete}
                    onClick={() => void handleGuestNext()}
                  >
                    {checking ? 'Проверяем…' : 'Далее'}
                  </button>
                </div>
              </section>
            ) : mode === 'confirm' ? (
              <section className="schedule-modal__section">
                <h3 className="lotos-section-title">Подтвердите запись</h3>
                <p className="schedule-modal__confirm-text">
                  Записать на «{item.serviceTitle}» {item.dateLabel} в {item.time}?
                  Тренер: {item.trainer}.
                  {!authenticated && showTrialPrice && (
                    <> Для новых клиентов — {trialPriceLabel}.</>
                  )}
                  {authenticated && eligibility?.isTrial && showTrialPrice && (
                    <> Запись оформится как пробное занятие — {trialPriceLabel}.</>
                  )}
                  {authenticated && eligibility && !eligibility.isTrial && item.requiresAbonement && (
                    <> Запись по абонементу.</>
                  )}
                </p>
                {eligibility && !eligibility.canBook && eligibility.message && (
                  <p className="schedule-modal__hint schedule-modal__hint--error" role="alert">
                    {eligibility.message}
                  </p>
                )}
                <div className="schedule-modal__actions">
                  <button
                    type="button"
                    className="lotos-btn lotos-btn--secondary"
                    disabled={booking}
                    onClick={() => setMode(authenticated ? 'details' : 'guest')}
                  >
                    Назад
                  </button>
                  <button
                    type="button"
                    className="lotos-btn lotos-btn--primary"
                    disabled={booking || (authenticated && eligibility !== null && !eligibility.canBook)}
                    onClick={() => void handleBook()}
                  >
                    {booking ? 'Записываем…' : 'Подтвердить'}
                  </button>
                </div>
              </section>
            ) : (
              <>
                <section className="schedule-modal__section">
                  <h3 className="lotos-section-title">Детали занятия</h3>
                  <dl className="schedule-modal__details">
                    <div className="schedule-modal__detail">
                      <dt>Тренер</dt>
                      <dd>{item.trainer}</dd>
                    </div>
                    <div className="schedule-modal__detail">
                      <dt>Дата</dt>
                      <dd>{item.dateLabel}</dd>
                    </div>
                    <div className="schedule-modal__detail">
                      <dt>Время</dt>
                      <dd>{item.time}</dd>
                    </div>
                    {item.durationMinutes != null && item.durationMinutes > 0 && (
                      <div className="schedule-modal__detail">
                        <dt>Длительность</dt>
                        <dd>{item.durationMinutes} мин</dd>
                      </div>
                    )}
                    {item.capacity > 0 && (
                      <>
                        <div className="schedule-modal__detail">
                          <dt>Всего мест</dt>
                          <dd>{item.capacity}</dd>
                        </div>
                        <div className="schedule-modal__detail">
                          <dt>Занято</dt>
                          <dd>{item.booked}</dd>
                        </div>
                        <div className="schedule-modal__detail">
                          <dt>Свободно</dt>
                          <dd>{isFull ? '0' : String(item.freeSpots ?? 0)}</dd>
                        </div>
                      </>
                    )}
                  </dl>
                </section>

                {item.comment && (
                  <section className="schedule-modal__section">
                    <h3 className="lotos-section-title">О занятии</h3>
                    <p className="schedule-modal__comment">{item.comment}</p>
                  </section>
                )}

                {showTrialPrice && !authenticated && (
                  <p className="schedule-modal__trial-note">
                    Первый визит — пробное занятие {trialPriceLabel}
                    {regularPrice ? ` вместо ${regularPrice}` : ''}.
                  </p>
                )}

                {isFull ? (
                  <p className="schedule-modal__hint schedule-modal__hint--muted">
                    Группа заполнена. Выберите другое время или напишите администратору студии.
                  </p>
                ) : null}

                <div className="schedule-modal__actions schedule-modal__actions--stacked">
                  {canBook && (
                    <button
                      type="button"
                      className="lotos-btn lotos-btn--primary lotos-btn--stretched"
                      disabled={checking}
                      onClick={() => void startBooking()}
                    >
                      {checking ? 'Проверяем…' : 'Записаться'}
                    </button>
                  )}
                  <button
                    type="button"
                    className={`lotos-btn lotos-btn--${canBook ? 'secondary' : 'primary'} lotos-btn--stretched`}
                    onClick={handleClose}
                  >
                    Закрыть
                  </button>
                </div>
              </>
            )}
          </>
        )}
      </div>
    </div>
  )
}
