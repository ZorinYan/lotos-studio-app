import type { HomeAlert } from '../../types/home'
import './HomeAlertsBanner.css'

type HomeAlertsBannerProps = {
  alerts: HomeAlert[]
}

export function HomeAlertsBanner({ alerts }: HomeAlertsBannerProps) {
  if (alerts.length === 0) {
    return null
  }

  return (
    <div className="home-alerts">
      {alerts.map((alert) => (
        <div
          key={`${alert.type}-${alert.message}`}
          className={`home-alerts__item home-alerts__item--${alert.type}`}
          role="status"
        >
          <span className="home-alerts__icon" aria-hidden="true">
            {alert.type === 'expiring' ? '⏳' : '◆'}
          </span>
          <p className="home-alerts__text">{alert.message}</p>
        </div>
      ))}
    </div>
  )
}
