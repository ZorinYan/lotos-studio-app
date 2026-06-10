import { Icon28UserCircleOutline } from '@vkontakte/icons'
import './AppHeader.css'

type AppHeaderProps = {
  title?: string
  onCabinetClick?: () => void
  showCabinetButton?: boolean
  onBack?: () => void
}

export function AppHeader({
  title = 'Lotos Studio',
  onCabinetClick,
  showCabinetButton = true,
  onBack,
}: AppHeaderProps) {
  return (
    <header className="app-header">
      <div className="app-header__left">
        {onBack ? (
          <button type="button" className="app-header__back" onClick={onBack} aria-label="Назад">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
              <path d="M12.5 15L7.5 10L12.5 5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>
        ) : (
          <span className="app-header__mark" aria-hidden="true">🪷</span>
        )}
        <div className="app-header__brand">
          <h1 className="app-header__title">{title}</h1>
          {!onBack && <span className="app-header__tagline">студия растяжки</span>}
        </div>
      </div>
      {showCabinetButton && onCabinetClick && (
        <button
          type="button"
          className="app-header__cabinet"
          onClick={onCabinetClick}
          aria-label="Личный кабинет"
        >
          <Icon28UserCircleOutline />
        </button>
      )}
    </header>
  )
}
