import { useState } from 'react'
import { useStore } from '../../store'
import OptionCard from './OptionCard'
import { explore, selectOption } from '../../api/exploration'

interface Props {
  projectId: string
}

export default function ExplorePanel({ projectId }: Props) {
  const {
    explorationOptions,
    setExplorationOptions,
    setSessionId,
    sessionId,
    setExplorationState,
    setSelectedOptionId,
    setPreviewingTemplateId,
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

  const handleExplore = async () => {
    if (!input.trim() || loading) return
    setLoading(true)
    setIsExploring(true)
    try {
      const result = await explore(projectId, input.trim())
      setSessionId(result.session_id)
      setExplorationOptions(result.options)
      setAmbiguity(result.ambiguity)
      setMemoryInfluence(result.memory_influence)
      setExplorationState('explore_options')
    } catch (err) {
      console.error('Explore failed:', err)
    } finally {
      setLoading(false)
    }
  }

  const handlePreview = (templateId: string) => {
    setPreviewingTemplateId(templateId)
    setExplorationState('previewing')
    refreshPreview()
  }

  const handleSelect = async (optionId: string) => {
    if (!sessionId) return
    setLoading(true)
    try {
      const result = await selectOption(projectId, sessionId, optionId)
      setSelectedOptionId(optionId)
      setExplorationState('committed')
      setActiveTab('iterate')
      refreshPreview()
    } catch (err) {
      console.error('Select failed:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="explore-panel">
      <div className="explore-input-area">
        <h3>Describe Your Game</h3>
        <textarea
          className="explore-input"
          placeholder="e.g., I want a simple mobile game where you tap to jump over obstacles..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          rows={3}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) handleExplore()
          }}
        />
        <button
          className="btn-primary explore-btn"
          onClick={handleExplore}
          disabled={loading || !input.trim()}
        >
          {loading ? 'Analyzing...' : 'Explore Options'}
        </button>
      </div>

      {ambiguity && (
        <div className="explore-ambiguity">
          <h4>Detected Dimensions</h4>
          <div className="ambiguity-tags">
            {Object.entries(ambiguity).map(([key, val]) => {
              const detected = (val as any)?.detected
              if (!Array.isArray(detected)) return null
              return (
                <div key={key} className="ambiguity-dimension">
                  <span className="ambiguity-key">{key.replace(/_/g, ' ')}</span>
                  <span className="ambiguity-values">
                    {detected.map((d: string) => (
                      <span key={d} className="ambiguity-tag">{d}</span>
                    ))}
                  </span>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {memoryInfluence && Object.keys(memoryInfluence).length > 0 && (
        <div className="memory-influence-banner">
          <span className="memory-influence-icon">&#9733;</span>
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
                onPreview={() => handlePreview(opt.template_id)}
                onSelect={() => handleSelect(opt.option_id)}
                disabled={loading}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
