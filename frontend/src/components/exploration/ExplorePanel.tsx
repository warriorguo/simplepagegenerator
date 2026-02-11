import { useState } from 'react'
import { useStore } from '../../store'
import OptionCard from './OptionCard'
import { explore, selectOption, triggerPreviewOption } from '../../api/exploration'
import type { Decomposition } from '../../types/exploration'

interface Props {
  projectId: string
}

const CONFIDENCE_COLORS: Record<string, string> = {
  high: 'conf-high',
  med: 'conf-med',
  low: 'conf-low',
}

export default function ExplorePanel({ projectId }: Props) {
  const {
    explorationOptions,
    setExplorationOptions,
    setSessionId,
    sessionId,
    setExplorationState,
    setSelectedOptionId,
    setPreviewingOptionId,
    setIsPreviewLoading,
    setPreviewError,
    setPreviewFixAttempts,
    previewingOptionId,
    isPreviewLoading,
    setAmbiguity,
    setMemoryInfluence,
    setIsExploring,
    isExploring,
    refreshPreview,
    setActiveTab,
    ambiguity,
    memoryInfluence,
  } = useStore()
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleExplore = async () => {
    if (!input.trim() || loading) return
    setLoading(true)
    setIsExploring(true)
    setError(null)
    try {
      const result = await explore(projectId, input.trim())
      setSessionId(result.session_id)
      setExplorationOptions(result.options)
      setAmbiguity(result.ambiguity)
      setMemoryInfluence(result.memory_influence)
      setExplorationState('explore_options')
    } catch (err: any) {
      const msg = err?.response?.data?.detail || err?.message || 'Explore failed'
      setError(msg)
      console.error('Explore failed:', err)
    } finally {
      setLoading(false)
    }
  }

  const handlePreview = async (optionId: string) => {
    if (!sessionId) return
    setPreviewingOptionId(optionId)
    setIsPreviewLoading(true)
    setPreviewError(null)
    setPreviewFixAttempts(0)
    setExplorationState('previewing')
    refreshPreview()

    try {
      // Trigger AI generation (Stage D+E)
      await triggerPreviewOption(projectId, sessionId, optionId)
      // Stale guard: check the option hasn't changed while we waited
      if (useStore.getState().previewingOptionId !== optionId) return
      // Switch to AI preview
      setIsPreviewLoading(false)
      refreshPreview()
    } catch (err: any) {
      if (useStore.getState().previewingOptionId !== optionId) return
      const msg = err?.message || 'Preview generation failed'
      setPreviewError(msg)
      setIsPreviewLoading(false)
      console.error('Preview generation failed:', err)
    }
  }

  const handleSelect = async (optionId: string) => {
    if (!sessionId) return
    setLoading(true)
    setError(null)
    try {
      const result = await selectOption(projectId, sessionId, optionId)
      setSelectedOptionId(optionId)
      setExplorationState('committed')
      setActiveTab('iterate')
      refreshPreview()
    } catch (err: any) {
      const msg = err?.response?.data?.detail || err?.message || 'Select failed'
      setError(msg)
      console.error('Select failed:', err)
    } finally {
      setLoading(false)
    }
  }

  // Try to use new Decomposition structure, fallback for old format
  const decomp = ambiguity as Decomposition | null
  const hasDimensions = decomp && decomp.dimensions && typeof decomp.dimensions === 'object'

  return (
    <div className="explore-panel">
      <div className="explore-input-area">
        <textarea
          className="explore-input"
          placeholder="Describe your game idea, e.g. a simple mobile game where you tap to jump over obstacles..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          rows={4}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) handleExplore()
          }}
        />
        <div className="explore-input-footer">
          <span className="explore-input-hint">
            {navigator.platform.includes('Mac') ? '⌘' : 'Ctrl'}+Enter
          </span>
          <button
            className="btn-primary explore-btn"
            onClick={handleExplore}
            disabled={loading || !input.trim()}
          >
            {loading ? 'Analyzing...' : 'Explore Options'}
          </button>
        </div>
      </div>

      {error && (
        <div className="explore-error">
          <span className="explore-error-icon">!</span>
          <span className="explore-error-msg">{error}</span>
          <button className="explore-error-close" onClick={() => setError(null)}>&times;</button>
        </div>
      )}

      {hasDimensions && (
        <div className="explore-decomposition">
          {decomp.summary && (
            <div className="decomp-summary">{decomp.summary}</div>
          )}

          {decomp.locked && decomp.locked.items && decomp.locked.items.length > 0 && (
            <div className="decomp-locked">
              <h5>Already Decided</h5>
              <div className="locked-items">
                {decomp.locked.items.map((item, i) => (
                  <span key={i} className="locked-tag">{item}</span>
                ))}
              </div>
            </div>
          )}

          <h4>Implementation Dimensions</h4>
          <div className="decomp-grid">
            {Object.entries(decomp.dimensions).map(([key, dim]) => (
              <div key={key} className="decomp-dim">
                <div className="decomp-dim-header">
                  <span className="decomp-dim-name">{key.replace(/_/g, ' ')}</span>
                  <span className={`decomp-confidence ${CONFIDENCE_COLORS[dim.confidence] || ''}`}>
                    {dim.confidence}
                  </span>
                </div>
                <div className="decomp-candidates">
                  {dim.candidates.map((c: string) => (
                    <span key={c} className="decomp-candidate">{c}</span>
                  ))}
                </div>
                {dim.signals && dim.signals.length > 0 && (
                  <div className="decomp-signals">
                    {dim.signals.map((s: string, i: number) => (
                      <span key={i} className="decomp-signal">{s}</span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>

          {decomp.hard_constraints && decomp.hard_constraints.length > 0 && (
            <div className="decomp-constraints">
              <h5>Hard Constraints</h5>
              {decomp.hard_constraints.map((c, i) => (
                <span key={i} className="constraint-tag">{c}</span>
              ))}
            </div>
          )}

          {decomp.open_questions && decomp.open_questions.length > 0 && (
            <div className="decomp-questions">
              <h5>Open Questions</h5>
              {decomp.open_questions.map((q, i) => (
                <div key={i} className="open-question">
                  <span className="oq-dim">{q.dimension}</span>
                  <span className="oq-text">{q.question}</span>
                  <span className="oq-why">{q.why_it_matters}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {memoryInfluence && Object.keys(memoryInfluence).length > 0 && (
        <div className="memory-influence-banner">
          Options influenced by your past preferences
        </div>
      )}

      {explorationOptions.length > 0 && (
        <div className="explore-options">
          <h4>Choose a Direction ({explorationOptions.length} options)</h4>
          <div className="option-cards">
            {explorationOptions.map((opt) => (
              <OptionCard
                key={opt.option_id}
                option={opt}
                onPreview={() => handlePreview(opt.option_id)}
                onSelect={() => handleSelect(opt.option_id)}
                disabled={loading}
                isPreviewing={previewingOptionId === opt.option_id}
                isPreviewLoading={previewingOptionId === opt.option_id && isPreviewLoading}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
