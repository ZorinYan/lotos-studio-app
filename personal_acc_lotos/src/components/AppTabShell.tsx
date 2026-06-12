import type { ReactNode } from 'react'
import { BottomNav, type AppTab } from './BottomNav'
import './BottomNav.css'

type AppTabShellProps = {
  activeTab: AppTab
  onNavigate: (tab: AppTab) => void
  children: ReactNode
}

export function AppTabShell({ activeTab, onNavigate, children }: AppTabShellProps) {
  return (
    <div className="app-tab-shell">
      <div className="app-tab-shell__content">{children}</div>
      <BottomNav active={activeTab} onSelect={onNavigate} />
    </div>
  )
}
