import {
  Icon24CalendarOutline,
  Icon24Home,
  Icon24List,
  Icon24Settings,
  Icon24UserCircleOutline,
} from '@vkontakte/icons'
import './BottomNav.css'

export type AppTab = 'home' | 'schedule' | 'cabinet' | 'records' | 'settings'

type BottomNavProps = {
  active: AppTab
  onSelect: (tab: AppTab) => void
}

const TABS: { id: AppTab; label: string }[] = [
  { id: 'home', label: 'Главная' },
  { id: 'schedule', label: 'Расписание' },
  { id: 'cabinet', label: 'ЛК' },
  { id: 'records', label: 'Записи' },
  { id: 'settings', label: 'Настройки' },
]

const NAV_ICON_PROPS = {
  className: 'bottom-nav__icon',
  width: 24,
  height: 24,
  'aria-hidden': true as const,
}

function TabIcon({ tab }: { tab: AppTab }) {
  switch (tab) {
    case 'home':
      return <Icon24Home {...NAV_ICON_PROPS} />
    case 'schedule':
      return <Icon24CalendarOutline {...NAV_ICON_PROPS} />
    case 'cabinet':
      return <Icon24UserCircleOutline {...NAV_ICON_PROPS} />
    case 'records':
      return <Icon24List {...NAV_ICON_PROPS} />
    case 'settings':
      return <Icon24Settings {...NAV_ICON_PROPS} />
  }
}

export function BottomNav({ active, onSelect }: BottomNavProps) {
  return (
    <nav className="bottom-nav" aria-label="Основное меню">
      {TABS.map(({ id, label }) => {
        const isActive = active === id
        return (
          <button
            key={id}
            type="button"
            className={`bottom-nav__item${isActive ? ' bottom-nav__item--active' : ''}`}
            aria-current={isActive ? 'page' : undefined}
            onClick={() => onSelect(id)}
          >
            <TabIcon tab={id} />
            <span className="bottom-nav__label">{label}</span>
          </button>
        )
      })}
    </nav>
  )
}
