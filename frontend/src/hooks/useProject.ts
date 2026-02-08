import { useEffect } from 'react'
import { getProject } from '../api/projects'
import { useStore } from '../store'

export function useProject(projectId: string | undefined) {
  const { currentProject, setCurrentProject } = useStore()

  useEffect(() => {
    if (!projectId) return
    let cancelled = false
    getProject(projectId).then((p) => {
      if (!cancelled) setCurrentProject(p)
    })
    return () => {
      cancelled = true
    }
  }, [projectId, setCurrentProject])

  return currentProject
}
