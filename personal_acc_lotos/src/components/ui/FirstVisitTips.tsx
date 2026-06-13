import { FIRST_VISIT_TIPS } from '../../content/studioGuide'
import './FirstVisitTips.css'

type FirstVisitTipsProps = {
  onOpenHelp?: () => void
}

export function FirstVisitTips({ onOpenHelp }: FirstVisitTipsProps) {
  return (
    <section className="first-visit lotos-card" aria-label="Перед первым визитом">
      <p className="first-visit__eyebrow">Первый раз у нас</p>
      <h3 className="first-visit__title">Что нужно знать</h3>
      <ul className="first-visit__list">
        {FIRST_VISIT_TIPS.map((item) => (
          <li key={item.title} className="first-visit__item">
            <span className="first-visit__item-title">{item.title}</span>
            <span className="first-visit__item-text">{item.text}</span>
          </li>
        ))}
      </ul>
      {onOpenHelp && (
        <button type="button" className="lotos-btn lotos-btn--secondary lotos-btn--stretched" onClick={onOpenHelp}>
          Вопросы и ответы
        </button>
      )}
    </section>
  )
}
