import { useEffect, useRef } from 'react'
import { getActiveSession } from '../api/exploration'
import { useStore } from '../store'
import type { ExplorationState } from '../types/exploration'

/**
 * On mount, fetch the most recent active exploration session from the backend
 * and hydrate the Zustand store so exploration state survives page refreshes.
 */
export function useExplorationSession(projectId: string | undefined) {
  const didRun = useRef(false)
  const {
    setSessionId,
    setExplorationState,
    setExplorationOptions,
    setAmbiguity,
    setSelectedOptionId,
    setHypothesisLedger,
    setIterationCount,
    setActiveTab,
    explorationState,
  } = useStore()

  useEffect(() => {
    if (!projectId || didRun.current) return
    // Only hydrate when the store is in default idle state
    if (explorationState !== 'idle') return
    didRun.current = true

    getActiveSession(projectId)
      .then((data) => {
        setSessionId(data.session_id)
        setAmbiguity(data.ambiguity)
        setExplorationOptions(data.options)
        setSelectedOptionId(data.selected_option_id)
        setHypothesisLedger(data.hypothesis_ledger)
        setIterationCount(data.iteration_count)

        // Map backend state to frontend ExplorationState
        const stateMap: Record<string, ExplorationState> = {
          explore_options: 'explore_options',
          previewing: 'explore_options',
          committed: 'committed',
          iterating: 'iterating',
          memory_writing: 'memory_writing',
        }
        setExplorationState(stateMap[data.state] || 'explore_options')

        // Switch to iterate tab for post-commit states
        if (data.state === 'committed' || data.state === 'iterating') {
          setActiveTab('iterate')
        }
      })
      .catch(() => {
        // 404 = no active session, stay idle
      })
  }, [projectId]) // eslint-disable-line react-hooks/exhaustive-deps
}
