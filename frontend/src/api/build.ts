import { apiFetch } from './client'

export interface BuildResult {
  success: boolean
  errors: string[]
  warnings: string[]
}

export function buildProject(projectId: string) {
  return apiFetch<BuildResult>(`/projects/${projectId}/build`, { method: 'POST' })
}

export function publishProject(projectId: string) {
  return apiFetch<unknown>(`/projects/${projectId}/publish`, { method: 'POST' })
}
