import type { HomeHint, HomeHintAction } from '../../types/home'
import './SmartHintsBanner.css'

type SmartHintsBannerProps = {
  hints: HomeHint[]
  onAction: (action: HomeHintAction, hint: HomeHint) => void
}

const HINT_ICONS: Record<HomeHint['type'], string> = {
  low_balance: '◆',
  expiring: '⏳',
  inactive: '↺',
}

export function SmartHintsBanner({ hints, onAction }: SmartHintsBannerProps) {
  if (hints.length === 0) {
    return null
  }

  return (
    <div className="smart-hints">
      {hints.map((hint) => (
        <article
          key={`${hint.type}-${hint.message}`}
          className={`smart-hints__item smart-hints__item--${hint.type}`}
        >
          <div className="smart-hints__body">
            <span className="smart-hints__icon" aria-hidden="true">
              {HINT_ICONS[hint.type]}
            </span>
            <div className="smart-hints__text-wrap">
              <p className="smart-hints__text">{hint.message}</p>
              {hint.detail && <p className="smart-hints__detail">{hint.detail}</p>}
            </div>
          </div>
          <button
            type="button"
            className="lotos-btn lotos-btn--primary smart-hints__btn"
            onClick={() => onAction(hint.action, hint)}
          >
            {hint.actionLabel}
          </button>
        </article>
      ))}
    </div>
  )
}
