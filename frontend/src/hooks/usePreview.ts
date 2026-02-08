import { useMemo } from 'react'
import { useStore } from '../store'

export function usePreview(projectId: string | undefined) {
  const previewKey = useStore((s) => s.previewKey)

  const previewUrl = useMemo(() => {
    if (!projectId) return ''
    return `/api/v1/projects/${projectId}/preview/index.html?v=${previewKey}`
  }, [projectId, previewKey])

  return { previewUrl, previewKey }
}
