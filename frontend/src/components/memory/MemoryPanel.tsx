import { useState } from 'react'
import { useStore } from '../../store'
import { createMemory, updateMemory, deleteMemory, listMemories } from '../../api/memories'

interface Props {
  projectId: string
}

export default function MemoryPanel({ projectId }: Props) {
  const { memories, setMemories } = useStore()
  const [newContent, setNewContent] = useState('')
  const [editingId, setEditingId] = useState<number | null>(null)
  const [editContent, setEditContent] = useState('')
  const [adding, setAdding] = useState(false)

  const refresh = async () => {
    const updated = await listMemories(projectId)
    setMemories(updated)
  }

  const handleAdd = async () => {
    if (!newContent.trim()) return
    setAdding(true)
    try {
      await createMemory(projectId, newContent.trim())
      setNewContent('')
      await refresh()
    } finally {
      setAdding(false)
    }
  }

  const handleUpdate = async (memoryId: number) => {
    if (!editContent.trim()) return
    await updateMemory(projectId, memoryId, editContent.trim())
    setEditingId(null)
    setEditContent('')
    await refresh()
  }

  const handleDelete = async (memoryId: number) => {
    await deleteMemory(projectId, memoryId)
    await refresh()
  }

  const startEdit = (memoryId: number, content: string) => {
    setEditingId(memoryId)
    setEditContent(content)
  }

  return (
    <div className="memory-panel">
      <h3>Memories</h3>

      <div className="memory-add">
        <textarea
          className="memory-input"
          placeholder="Add a memory..."
          value={newContent}
          onChange={(e) => setNewContent(e.target.value)}
          rows={2}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) handleAdd()
          }}
        />
        <button
          className="memory-add-btn"
          onClick={handleAdd}
          disabled={adding || !newContent.trim()}
        >
          {adding ? 'Adding...' : 'Add'}
        </button>
      </div>

      {memories.length === 0 && (
        <div className="memory-empty">
          No memories yet. Memories are auto-extracted from conversations or can be added manually.
        </div>
      )}

      {memories.map((m) => (
        <div key={m.id} className="memory-item">
          {editingId === m.id ? (
            <div className="memory-edit">
              <textarea
                className="memory-input"
                value={editContent}
                onChange={(e) => setEditContent(e.target.value)}
                rows={2}
              />
              <div className="memory-edit-actions">
                <button onClick={() => handleUpdate(m.id)}>Save</button>
                <button onClick={() => setEditingId(null)}>Cancel</button>
              </div>
            </div>
          ) : (
            <>
              <div className="memory-content">{m.content}</div>
              <div className="memory-meta">
                <span className={`memory-source ${m.source}`}>{m.source}</span>
                <span className="memory-date">{new Date(m.created_at).toLocaleDateString()}</span>
                <div className="memory-actions">
                  <button onClick={() => startEdit(m.id, m.content)}>Edit</button>
                  <button onClick={() => handleDelete(m.id)}>Del</button>
                </div>
              </div>
            </>
          )}
        </div>
      ))}
    </div>
  )
}
