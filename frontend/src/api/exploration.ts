import { apiFetch } from './client'
import type {
  ExploreResponse,
  SelectOptionResponse,
  IterateResponse,
  FinishExplorationResponse,
  MemoryNote,
  ExplorationSessionState,
  ActiveSessionResponse,
} from '../types/exploration'

export function explore(projectId: string, userInput: string) {
  return apiFetch<ExploreResponse>(`/projects/${projectId}/explore`, {
    method: 'POST',
    body: JSON.stringify({ user_input: userInput }),
  })
}

export function selectOption(projectId: string, sessionId: number, optionId: string) {
  return apiFetch<SelectOptionResponse>(`/projects/${projectId}/select_option`, {
    method: 'POST',
    body: JSON.stringify({ session_id: sessionId, option_id: optionId }),
  })
}

export function iterate(projectId: string, sessionId: number, userInput: string) {
  return apiFetch<IterateResponse>(`/projects/${projectId}/iterate`, {
    method: 'POST',
    body: JSON.stringify({ session_id: sessionId, user_input: userInput }),
  })
}

export function finishExploration(projectId: string, sessionId: number) {
  return apiFetch<FinishExplorationResponse>(`/projects/${projectId}/finish_exploration`, {
    method: 'POST',
    body: JSON.stringify({ session_id: sessionId }),
  })
}

export function getActiveSession(projectId: string) {
  return apiFetch<ActiveSessionResponse>(`/projects/${projectId}/exploration/active`)
}

export function getExplorationState(projectId: string, sessionId: number) {
  return apiFetch<ExplorationSessionState>(`/projects/${projectId}/exploration/state/${sessionId}`)
}

export function listMemoryNotes(projectId: string) {
  return apiFetch<MemoryNote[]>(`/projects/${projectId}/exploration/memory_notes`)
}

export function getTemplatePreviewUrl(projectId: string, templateId: string) {
  return `/api/v1/projects/${projectId}/exploration/preview/${templateId}`
}

export function fetchDebugLog() {
  return apiFetch<any[]>('/debug/openai_log')
}

export function clearDebugLog() {
  return apiFetch<{ status: string }>('/debug/openai_log', { method: 'DELETE' })
}
