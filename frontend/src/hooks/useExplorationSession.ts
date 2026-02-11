import { useEffect, useRef } from 'react'
import { getActiveSession } from '../api/exploration'
import { useStore } from '../store'
import type { ExplorationState } from '../types/exploration'

/**
 * On mount (or when projectId changes), reset exploration state then fetch
 * the most recent active session from the backend to hydrate Zustand.
 * This ensures switching between projects doesn't leak stale state.
 */
export function useExplorationSession(projectId: string | undefined) {
  const prevProjectId = useRef<string | undefined>(undefined)
  const {
    resetExploration,
    setSessionId,
    setExplorationState,
    setExplorationOptions,
    setAmbiguity,
    setSelectedOptionId,
    setHypothesisLedger,
    setIterationCount,
    setActiveTab,
  } = useStore()

  useEffect(() => {
    if (!projectId) return
    // Always reset when project changes (including first mount)
    if (prevProjectId.current !== projectId) {
      resetExploration()
      prevProjectId.current = projectId
    }

    getActiveSession(projectId)
      .then((data) => {
        setSessionId(data.session_id)
        setAmbiguity(data.ambiguity)
        setExplorationOptions(data.options)
        setSelectedOptionId(data.selected_option_id)
        setHypothesisLedger(data.hypothesis_ledger)
        setIterationCount(data.iteration_count)

        const stateMap: Record<string, ExplorationState> = {
          explore_options: 'explore_options',
          previewing: 'explore_options',
          committed: 'committed',
          iterating: 'iterating',
          memory_writing: 'memory_writing',
        }
        setExplorationState(stateMap[data.state] || 'explore_options')

        if (data.state === 'committed' || data.state === 'iterating') {
          setActiveTab('iterate')
        }
      })
      .catch(() => {
        // 404 = no active session, stay idle (already reset above)
      })
  }, [projectId]) // eslint-disable-line react-hooks/exhaustive-deps
}
