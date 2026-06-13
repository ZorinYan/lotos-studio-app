import './Skeleton.css'

function Bone({ className = '', style }: { className?: string; style?: React.CSSProperties }) {
  return <div className={`lotos-skeleton ${className}`} style={style} />
}

export function HomePageSkeleton() {
  return (
    <div className="lotos-skeleton-block" aria-hidden="true">
      <div className="home-skeleton__hero">
        <Bone style={{ width: 120, height: 12 }} />
        <Bone style={{ width: 220, height: 28 }} />
        <Bone style={{ width: 140, height: 28, borderRadius: 999 }} />
      </div>
      <Bone className="lotos-skeleton--card home-skeleton__card" />
      <Bone className="lotos-skeleton--card home-skeleton__card--tall" />
      <Bone className="lotos-skeleton--card home-skeleton__carousel" />
      <Bone className="lotos-skeleton--card home-skeleton__carousel" />
    </div>
  )
}

export function SchedulePageSkeleton() {
  return (
    <div className="lotos-skeleton-block" aria-hidden="true">
      <div className="schedule-skeleton__chip-row">
        {Array.from({ length: 5 }).map((_, index) => (
          <Bone key={index} className="schedule-skeleton__chip" />
        ))}
      </div>
      {Array.from({ length: 4 }).map((_, index) => (
        <Bone key={index} className="lotos-skeleton--card schedule-skeleton__card" />
      ))}
    </div>
  )
}

export function CabinetPageSkeleton() {
  return (
    <div className="lotos-skeleton-block" aria-hidden="true">
      <Bone className="cabinet-skeleton__hero" />
      <div className="cabinet-skeleton__stat-row">
        <Bone className="lotos-skeleton--card cabinet-skeleton__stat" />
        <Bone className="lotos-skeleton--card cabinet-skeleton__stat" />
      </div>
      <Bone className="lotos-skeleton--card cabinet-skeleton__chart" />
      <Bone className="lotos-skeleton--card home-skeleton__card" />
      <Bone className="lotos-skeleton--card home-skeleton__card" />
    </div>
  )
}

export function RecordsPageSkeleton() {
  return (
    <div className="lotos-skeleton-block" aria-hidden="true">
      {Array.from({ length: 4 }).map((_, index) => (
        <Bone key={index} className="lotos-skeleton--card schedule-skeleton__card" />
      ))}
    </div>
  )
}
