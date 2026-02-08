import { apiFetch } from './client'
import type { ProjectVersion } from '../types/version'

export function getVersions(projectId: string) {
  return apiFetch<ProjectVersion[]>(`/projects/${projectId}/versions`)
}

export function rollbackVersion(projectId: string, versionId: number) {
  return apiFetch<ProjectVersion>(`/projects/${projectId}/versions/${versionId}/rollback`, {
    method: 'POST',
  })
}
