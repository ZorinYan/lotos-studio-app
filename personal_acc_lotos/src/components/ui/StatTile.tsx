import './StatTile.css'

type StatTileProps = {
  label: string
  value: string
  accent?: boolean
}

export function StatTile({ label, value, accent }: StatTileProps) {
  return (
    <div className={`stat-tile${accent ? ' stat-tile--accent' : ''}`}>
      <span className="stat-tile__value">{value}</span>
      <span className="stat-tile__label">{label}</span>
    </div>
  )
}
