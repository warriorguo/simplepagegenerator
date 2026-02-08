import { apiFetch } from './client'
import type { ProjectFile } from '../types/file'

export function getFiles(projectId: string) {
  return apiFetch<ProjectFile[]>(`/projects/${projectId}/files`)
}
