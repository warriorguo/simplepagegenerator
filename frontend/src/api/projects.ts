import { apiFetch } from './client'
import type { Project, ProjectCreate } from '../types/project'

export function createProject(data: ProjectCreate) {
  return apiFetch<Project>('/projects', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export function listProjects() {
  return apiFetch<Project[]>('/projects')
}

export function getProject(id: string) {
  return apiFetch<Project>(`/projects/${id}`)
}

export function updateProject(id: string, data: Partial<ProjectCreate>) {
  return apiFetch<Project>(`/projects/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  })
}

export function deleteProject(id: string) {
  return apiFetch<void>(`/projects/${id}`, { method: 'DELETE' })
}
