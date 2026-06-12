import { useEffect } from 'react'
import './WelcomeBanner.css'

type WelcomeBannerProps = {
  clientName: string | null
  studioName: string
  onClose: () => void
}

export function WelcomeBanner({ clientName, studioName, onClose }: WelcomeBannerProps) {
  const firstName = clientName?.split(' ')[0]
  const greeting = firstName ? `${firstName}, добро пожаловать!` : 'Добро пожаловать!'

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose()
      }
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [onClose])

  return (
    <div className="welcome-banner" role="dialog" aria-modal="true" aria-labelledby="welcome-banner-title">
      <button
        type="button"
        className="welcome-banner__backdrop"
        aria-label="Закрыть приветствие"
        onClick={onClose}
      />
      <div className="welcome-banner__card">
        <div className="welcome-banner__glow" aria-hidden="true" />
        <span className="welcome-banner__emoji" aria-hidden="true">🪷</span>
        <p className="welcome-banner__eyebrow">{studioName}</p>
        <h2 id="welcome-banner-title" className="welcome-banner__title">{greeting}</h2>
        <p className="welcome-banner__text">
          Это ваш личный кабинет студии в VK. Здесь можно смотреть расписание,
          записываться на занятия и следить за абонементом.
        </p>
        <ul className="welcome-banner__tips">
          <li>Расписание — свободные места и запись</li>
          <li>ЛК — абонемент и история визитов</li>
          <li>Записи — ваши предстоящие занятия</li>
        </ul>
        <button type="button" className="lotos-btn lotos-btn--primary lotos-btn--stretched" onClick={onClose}>
          Начать
        </button>
      </div>
    </div>
  )
}
