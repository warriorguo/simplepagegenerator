import { useState } from 'react'
import { useStore } from '../../store'
import { iterate, finishExploration } from '../../api/exploration'

interface Props {
  projectId: string
}

export default function IteratePanel({ projectId }: Props) {
  const {
    sessionId,
    hypothesisLedger,
    setHypothesisLedger,
    iterationCount,
    setIterationCount,
    setExplorationState,
    refreshPreview,
    setActiveTab,
    selectedOptionId,
  } = useStore()
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [logs, setLogs] = useState<Array<{ type: string; text: string; time: string }>>([])

  const handleIterate = async () => {
    if (!input.trim() || !sessionId || loading) return
    setLoading(true)
    const timestamp = new Date().toLocaleTimeString()
    setLogs((prev) => [...prev, { type: 'user', text: input.trim(), time: timestamp }])
    try {
      const result = await iterate(projectId, sessionId, input.trim())
      setIterationCount(result.iteration_count)
      setHypothesisLedger(result.hypothesis_ledger)
      setExplorationState(result.state as any)
      refreshPreview()
      setLogs((prev) => [
        ...prev,
        { type: 'system', text: `Version created (iteration #${result.iteration_count})`, time: new Date().toLocaleTimeString() },
      ])
      setInput('')
    } catch (err) {
      setLogs((prev) => [
        ...prev,
        { type: 'error', text: `Error: ${err}`, time: new Date().toLocaleTimeString() },
      ])
    } finally {
      setLoading(false)
    }
  }

  const handleFinish = async () => {
    if (!sessionId) return
    setLoading(true)
    try {
      const result = await finishExploration(projectId, sessionId)
      setExplorationState('stable')
      setActiveTab('memory')
    } catch (err) {
      console.error('Finish failed:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="iterate-panel">
      <div className="iterate-header">
        <h3>Iterate</h3>
        <div className="iterate-meta">
          <span className="iterate-badge">v{iterationCount + 1}</span>
          {selectedOptionId && <span className="iterate-option">Option: {selectedOptionId}</span>}
        </div>
        <button
          className="finish-btn"
          onClick={handleFinish}
          disabled={loading}
        >
          Finish Exploration
        </button>
      </div>

      {hypothesisLedger && (
        <div className="hypothesis-ledger">
          <h4>Hypothesis Ledger</h4>
          <div className="ledger-sections">
            {hypothesisLedger.validated.length > 0 && (
              <div className="ledger-section validated">
                <span className="ledger-label">Validated</span>
                {hypothesisLedger.validated.map((h, i) => (
                  <span key={i} className="ledger-item">{h}</span>
                ))}
              </div>
            )}
            {hypothesisLedger.rejected.length > 0 && (
              <div className="ledger-section rejected">
                <span className="ledger-label">Rejected</span>
                {hypothesisLedger.rejected.map((h, i) => (
                  <span key={i} className="ledger-item">{h}</span>
                ))}
              </div>
            )}
            {hypothesisLedger.open_questions.length > 0 && (
              <div className="ledger-section open">
                <span className="ledger-label">Open</span>
                {hypothesisLedger.open_questions.map((h, i) => (
                  <span key={i} className="ledger-item">{h}</span>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      <div className="iterate-logs">
        {logs.map((log, i) => (
          <div key={i} className={`iterate-log ${log.type}`}>
            <span className="log-time">{log.time}</span>
            <span className="log-text">{log.text}</span>
          </div>
        ))}
      </div>

      <div className="iterate-input-area">
        <textarea
          className="iterate-input"
          placeholder="Describe what to change... (e.g., make the player faster, add enemies)"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          rows={2}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) handleIterate()
          }}
        />
        <button
          className="btn-primary iterate-btn"
          onClick={handleIterate}
          disabled={loading || !input.trim()}
        >
          {loading ? 'Applying...' : 'Apply Change'}
        </button>
      </div>
    </div>
  )
}
