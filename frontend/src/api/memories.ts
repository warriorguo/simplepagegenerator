import { apiFetch } from './client'
import type { Memory } from '../types/memory'

export function listMemories(projectId: string) {
  return apiFetch<Memory[]>(`/projects/${projectId}/memories`)
}

export function createMemory(projectId: string, content: string) {
  return apiFetch<Memory>(`/projects/${projectId}/memories`, {
    method: 'POST',
    body: JSON.stringify({ content }),
  })
}

export function updateMemory(projectId: string, memoryId: number, content: string) {
  return apiFetch<Memory>(`/projects/${projectId}/memories/${memoryId}`, {
    method: 'PUT',
    body: JSON.stringify({ content }),
  })
}

export function deleteMemory(projectId: string, memoryId: number) {
  return apiFetch<void>(`/projects/${projectId}/memories/${memoryId}`, {
    method: 'DELETE',
  })
}
