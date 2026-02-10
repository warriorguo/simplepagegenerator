import { useState, useEffect, useCallback } from 'react'
import { fetchDebugLog, clearDebugLog } from '../../api/exploration'

interface DebugEntry {
  label: string
  timestamp: number
  model: string
  messages: Array<{ role: string; content: string }>
  raw_response: string | null
  parsed: any
  error: string | null
  duration_ms: number
  usage?: { prompt_tokens: number; completion_tokens: number; total_tokens: number }
}

export default function DebugPanel() {
  const [entries, setEntries] = useState<DebugEntry[]>([])
  const [expanded, setExpanded] = useState<Set<number>>(new Set())
  const [autoRefresh, setAutoRefresh] = useState(false)

  const load = useCallback(async () => {
    try {
      const data = await fetchDebugLog()
      setEntries(data)
    } catch (e) {
      console.error('Failed to fetch debug log:', e)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  useEffect(() => {
    if (!autoRefresh) return
    const id = setInterval(load, 3000)
    return () => clearInterval(id)
  }, [autoRefresh, load])

  const toggle = (idx: number) => {
    setExpanded((prev) => {
      const next = new Set(prev)
      if (next.has(idx)) next.delete(idx)
      else next.add(idx)
      return next
    })
  }

  const handleClear = async () => {
    await clearDebugLog()
    setEntries([])
  }

  const fmtTime = (ts: number) => {
    const d = new Date(ts * 1000)
    return d.toLocaleTimeString()
  }

  return (
    <div className="debug-panel">
      <div className="debug-toolbar">
        <button className="debug-btn" onClick={load}>Refresh</button>
        <label className="debug-auto-label">
          <input
            type="checkbox"
            checked={autoRefresh}
            onChange={(e) => setAutoRefresh(e.target.checked)}
          />
          Auto (3s)
        </label>
        <span className="debug-count">{entries.length} calls</span>
        <button className="debug-btn debug-btn-clear" onClick={handleClear}>Clear</button>
      </div>

      {entries.length === 0 && (
        <div className="debug-empty">No OpenAI calls recorded yet. Try exploring!</div>
      )}

      {[...entries].reverse().map((entry, i) => {
        const idx = entries.length - 1 - i
        const isOpen = expanded.has(idx)
        const systemMsg = entry.messages.find((m) => m.role === 'system')?.content || ''
        const userMsg = entry.messages.find((m) => m.role === 'user')?.content || ''

        return (
          <div
            key={idx}
            className={`debug-entry ${entry.error ? 'debug-entry-error' : ''}`}
          >
            <div className="debug-entry-header" onClick={() => toggle(idx)}>
              <span className={`debug-arrow ${isOpen ? 'open' : ''}`}>&#9654;</span>
              <span className="debug-label">{entry.label || 'unknown'}</span>
              <span className="debug-model">{entry.model}</span>
              <span className="debug-duration">{entry.duration_ms}ms</span>
              {entry.usage && (
                <span className="debug-tokens">{entry.usage.total_tokens} tok</span>
              )}
              <span className="debug-time">{fmtTime(entry.timestamp)}</span>
              {entry.error && <span className="debug-error-badge">ERR</span>}
            </div>

            {isOpen && (
              <div className="debug-entry-body">
                <div className="debug-section">
                  <div className="debug-section-title">System Prompt</div>
                  <pre className="debug-pre">{systemMsg}</pre>
                </div>
                <div className="debug-section">
                  <div className="debug-section-title">User Message</div>
                  <pre className="debug-pre">{userMsg}</pre>
                </div>
                {entry.raw_response && (
                  <div className="debug-section">
                    <div className="debug-section-title">Raw Response</div>
                    <pre className="debug-pre">{entry.raw_response}</pre>
                  </div>
                )}
                {entry.parsed && (
                  <div className="debug-section">
                    <div className="debug-section-title">Parsed JSON</div>
                    <pre className="debug-pre">{JSON.stringify(entry.parsed, null, 2)}</pre>
                  </div>
                )}
                {entry.error && (
                  <div className="debug-section">
                    <div className="debug-section-title debug-section-error">Error</div>
                    <pre className="debug-pre debug-pre-error">{entry.error}</pre>
                  </div>
                )}
                {entry.usage && (
                  <div className="debug-section">
                    <div className="debug-section-title">Usage</div>
                    <div className="debug-usage">
                      <span>Prompt: {entry.usage.prompt_tokens}</span>
                      <span>Completion: {entry.usage.completion_tokens}</span>
                      <span>Total: {entry.usage.total_tokens}</span>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
