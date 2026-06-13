import './ConfirmModal.css'

type ConfirmModalProps = {
  title: string
  message: string
  confirmLabel: string
  cancelLabel?: string
  onConfirm: () => void
  onClose: () => void
  danger?: boolean
  loading?: boolean
}

export function ConfirmModal({
  title,
  message,
  confirmLabel,
  cancelLabel = 'Отмена',
  onConfirm,
  onClose,
  danger = false,
  loading = false,
}: ConfirmModalProps) {
  return (
    <div
      className="confirm-modal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="confirm-modal-title"
    >
      <button
        type="button"
        className="confirm-modal__backdrop"
        aria-label="Закрыть"
        disabled={loading}
        onClick={onClose}
      />
      <div className="confirm-modal__card lotos-card">
        <h2 id="confirm-modal-title" className="confirm-modal__title">
          {title}
        </h2>
        <p className="confirm-modal__message">{message}</p>
        <div className="confirm-modal__actions">
          <button
            type="button"
            className="lotos-btn lotos-btn--secondary lotos-btn--stretched"
            disabled={loading}
            onClick={onClose}
          >
            {cancelLabel}
          </button>
          <button
            type="button"
            className={`lotos-btn lotos-btn--stretched${
              danger ? ' confirm-modal__confirm--danger' : ' lotos-btn--primary'
            }`}
            disabled={loading}
            onClick={onConfirm}
          >
            {loading ? 'Выходим…' : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  )
}
