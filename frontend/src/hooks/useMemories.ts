import { useEffect } from 'react'
import { listMemories } from '../api/memories'
import { useStore } from '../store'

export function useMemories(projectId: string | undefined) {
  const { setMemories } = useStore()

  useEffect(() => {
    if (!projectId) return
    let cancelled = false
    listMemories(projectId).then((m) => {
      if (!cancelled) setMemories(m)
    })
    return () => {
      cancelled = true
    }
  }, [projectId, setMemories])
}
