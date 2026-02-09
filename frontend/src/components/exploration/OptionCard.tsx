import type { ExplorationOption } from '../../types/exploration'

interface Props {
  option: ExplorationOption
  onPreview: () => void
  onSelect: () => void
  disabled?: boolean
}

export default function OptionCard({ option, onPreview, onSelect, disabled }: Props) {
  return (
    <div className={`option-card ${option.is_recommended ? 'recommended' : ''}`}>
      {option.is_recommended && <div className="option-badge">Recommended</div>}
      <h5 className="option-title">{option.title}</h5>
      <p className="option-loop">{option.core_loop}</p>
      <div className="option-details">
        <div className="option-detail">
          <span className="detail-label">Controls</span>
          <span className="detail-value">{option.controls}</span>
        </div>
        <div className="option-detail">
          <span className="detail-label">Complexity</span>
          <span className={`detail-value complexity-${option.complexity}`}>{option.complexity}</span>
        </div>
        <div className="option-detail">
          <span className="detail-label">Mobile</span>
          <span className={`detail-value mobile-${option.mobile_fit}`}>{option.mobile_fit}</span>
        </div>
      </div>
      <div className="option-mechanics">
        {option.mechanics.map((m) => (
          <span key={m} className="mechanic-tag">{m}</span>
        ))}
      </div>
      {option.assumptions_to_validate.length > 0 && (
        <div className="option-assumptions">
          <span className="assumptions-label">To validate:</span>
          {option.assumptions_to_validate.map((a, i) => (
            <span key={i} className="assumption-item">{a}</span>
          ))}
        </div>
      )}
      <div className="option-actions">
        <button className="option-preview-btn" onClick={onPreview} disabled={disabled}>
          Preview
        </button>
        <button className="btn-primary option-select-btn" onClick={onSelect} disabled={disabled}>
          Select
        </button>
      </div>
    </div>
  )
}
