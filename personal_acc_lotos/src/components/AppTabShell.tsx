import type { ReactNode } from 'react'
import { BottomNav, type AppTab } from './BottomNav'
import './BottomNav.css'

type AppTabShellProps = {
  activeTab: AppTab
  onNavigate: (tab: AppTab) => void
  children: ReactNode
  tabs?: AppTab[]
}

export function AppTabShell({ activeTab, onNavigate, children, tabs }: AppTabShellProps) {
  return (
    <div className="app-tab-shell">
      <div className="app-tab-shell__content">{children}</div>
      <BottomNav active={activeTab} onSelect={onNavigate} tabs={tabs} />
    </div>
  )
}
