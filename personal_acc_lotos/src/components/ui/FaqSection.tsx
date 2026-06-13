import { useState } from 'react'
import { STUDIO_FAQ } from '../../content/studioGuide'
import './FaqSection.css'

type FaqSectionProps = {
  compact?: boolean
}

export function FaqSection({ compact = false }: FaqSectionProps) {
  const [openId, setOpenId] = useState<string | null>(compact ? null : STUDIO_FAQ[0]?.id ?? null)

  return (
    <section className={`faq-section${compact ? ' faq-section--compact' : ''}`} aria-label="Вопросы и ответы">
      {!compact && <h3 className="lotos-section-title">Частые вопросы</h3>}
      <div className="faq-section__list">
        {STUDIO_FAQ.map((item) => {
          const isOpen = openId === item.id
          return (
            <article key={item.id} className={`faq-section__item${isOpen ? ' faq-section__item--open' : ''}`}>
              <button
                type="button"
                className="faq-section__question"
                aria-expanded={isOpen}
                onClick={() => setOpenId(isOpen ? null : item.id)}
              >
                <span>{item.question}</span>
                <span className="faq-section__chevron" aria-hidden="true">{isOpen ? '−' : '+'}</span>
              </button>
              {isOpen && <p className="faq-section__answer">{item.answer}</p>}
            </article>
          )
        })}
      </div>
    </section>
  )
}
