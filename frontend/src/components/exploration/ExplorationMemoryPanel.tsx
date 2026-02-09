import { useEffect, useState } from 'react'
import { useStore } from '../../store'
import { listMemoryNotes } from '../../api/exploration'
import type { MemoryNote } from '../../types/exploration'

interface Props {
  projectId: string
}

export default function ExplorationMemoryPanel({ projectId }: Props) {
  const { memoryNotes, setMemoryNotes } = useStore()
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    setLoading(true)
    listMemoryNotes(projectId)
      .then(setMemoryNotes)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [projectId, setMemoryNotes])

  if (loading) {
    return <div className="exploration-memory-panel"><p className="memory-loading">Loading memories...</p></div>
  }

  return (
    <div className="exploration-memory-panel">
      <h3>Exploration Memory</h3>
      {memoryNotes.length === 0 && (
        <div className="memory-empty">
          No exploration memories yet. Complete an exploration to save structured conclusions.
        </div>
      )}
      {memoryNotes.map((note) => (
        <MemoryNoteCard key={note.id} note={note} />
      ))}
    </div>
  )
}

function MemoryNoteCard({ note }: { note: MemoryNote }) {
  const [expanded, setExpanded] = useState(false)
  const c = note.content_json

  return (
    <div className="memory-note-card" onClick={() => setExpanded(!expanded)}>
      <div className="note-header">
        <h5 className="note-title">{c.title}</h5>
        <span className="note-confidence">{Math.round(c.confidence * 100)}%</span>
      </div>
      <p className="note-summary">{c.summary}</p>

      {note.tags && (
        <div className="note-tags">
          {note.tags.map((t) => (
            <span key={t} className="note-tag">{t}</span>
          ))}
        </div>
      )}

      {expanded && (
        <div className="note-expanded">
          <div className="note-section">
            <h6>Preferences</h6>
            <div className="pref-grid">
              {Object.entries(c.user_preferences).map(([k, v]) => (
                <div key={k} className="pref-item">
                  <span className="pref-key">{k}</span>
                  <span className="pref-val">{v}</span>
                </div>
              ))}
            </div>
          </div>

          {c.final_choice && (
            <div className="note-section">
              <h6>Final Choice</h6>
              <p>{c.final_choice.option_id}: {c.final_choice.why}</p>
            </div>
          )}

          {c.validated_hypotheses.length > 0 && (
            <div className="note-section">
              <h6>Validated</h6>
              {c.validated_hypotheses.map((h, i) => (
                <span key={i} className="hypothesis validated">{h}</span>
              ))}
            </div>
          )}

          {c.rejected_hypotheses.length > 0 && (
            <div className="note-section">
              <h6>Rejected</h6>
              {c.rejected_hypotheses.map((h, i) => (
                <span key={i} className="hypothesis rejected">{h}</span>
              ))}
            </div>
          )}

          {c.key_decisions.length > 0 && (
            <div className="note-section">
              <h6>Key Decisions</h6>
              {c.key_decisions.map((d, i) => (
                <div key={i} className="decision-item">
                  <strong>{d.decision}</strong>
                  <p>{d.reason}</p>
                  {d.evidence && <small>Evidence: {d.evidence}</small>}
                </div>
              ))}
            </div>
          )}

          {c.pitfalls_and_guards.length > 0 && (
            <div className="note-section">
              <h6>Pitfalls & Guards</h6>
              {c.pitfalls_and_guards.map((p, i) => (
                <span key={i} className="pitfall-item">{p}</span>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
