import { useParams } from 'react-router-dom'
import { useState, useEffect, useCallback } from 'react'
import TopBar from '../components/layout/TopBar'
import PreviewPanel from '../components/preview/PreviewPanel'
import ExplorePanel from '../components/exploration/ExplorePanel'
import IteratePanel from '../components/exploration/IteratePanel'
import ExplorationMemoryPanel from '../components/exploration/ExplorationMemoryPanel'
import DebugPanel from '../components/exploration/DebugPanel'
import VersionList from '../components/version/VersionList'
import MemoryPanel from '../components/memory/MemoryPanel'
import { getAiPreviewUrl, fixPreview } from '../api/exploration'
import { useProject } from '../hooks/useProject'
import { useMemories } from '../hooks/useMemories'
import { useExplorationSession } from '../hooks/useExplorationSession'
import { useStore } from '../store'
import '../styles/editor.css'
import '../styles/exploration.css'

export default function EditorPage() {
  const { id } = useParams<{ id: string }>()
  const project = useProject(id)
  useMemories(id)
  useExplorationSession(id)
  const [showVersions, setShowVersions] = useState(false)

  const {
    activeTab,
    setActiveTab,
    explorationState,
    previewingOptionId,
    isPreviewLoading,
    previewError,
    previewFixAttempts,
    selectedOptionId,
    iterationCount,
    sessionId,
    previewKey,
    refreshPreview,
    setIsPreviewLoading,
    setPreviewError,
    setPreviewFixAttempts,
  } = useStore()

  // Listen for runtime errors from preview iframe
  const handleIframeMessage = useCallback(
    async (event: MessageEvent) => {
      if (event.data?.type !== 'preview-runtime-error') return
      const state = useStore.getState()
      if (!id || !state.sessionId || !state.previewingOptionId) return
      if (state.isPreviewLoading) return // still generating, ignore
      if (state.previewFixAttempts >= 2) {
        setPreviewError(`Runtime error (auto-fix limit reached): ${event.data.errors?.[0]?.message || 'unknown'}`)
        return
      }

      console.log('[preview-fix] Runtime errors detected, attempting auto-fix...', event.data.errors)
      setIsPreviewLoading(true)
      setPreviewError(null)

      try {
        await fixPreview(id, state.sessionId, state.previewingOptionId, event.data.errors)
        setPreviewFixAttempts(state.previewFixAttempts + 1)
        setIsPreviewLoading(false)
        refreshPreview() // reload iframe with fixed code
      } catch (err: any) {
        setIsPreviewLoading(false)
        setPreviewError(`Auto-fix failed: ${err?.message || 'unknown'}`)
      }
    },
    [id],
  )

  useEffect(() => {
    window.addEventListener('message', handleIframeMessage)
    return () => window.removeEventListener('message', handleIframeMessage)
  }, [handleIframeMessage])

  if (!id) return <div>Invalid project ID</div>

  // Determine preview state
  const isPreviewing = explorationState === 'previewing' && !!previewingOptionId
  const previewModeLabel = (() => {
    if (isPreviewing) {
      return `Exploring: ${previewingOptionId}`
    }
    if (explorationState === 'committed' || explorationState === 'iterating') {
      return `Committed v${iterationCount + 1}${selectedOptionId ? ` (${selectedOptionId})` : ''}`
    }
    if (explorationState === 'stable') {
      return 'Stable'
    }
    return 'Ready'
  })()

  const stateColors: Record<string, string> = {
    initial: '',
    explore_options: 'exploring',
    previewing: 'exploring',
    committed: 'committed',
    iterating: 'iterating',
    memory_writing: 'writing',
    stable: 'stable',
  }

  return (
    <div className="editor-page">
      <TopBar project={project} />
      <div className="editor-toolbar">
        <button
          className={showVersions ? 'active' : ''}
          onClick={() => setShowVersions(!showVersions)}
        >
          Versions
        </button>
        <div className="toolbar-separator" />
        <span className={`state-badge state-${stateColors[explorationState] || ''}`}>
          {previewModeLabel}
        </span>
      </div>
      <div className="editor-main">
        {showVersions && (
          <div className="editor-sidebar">
            <VersionList projectId={id} />
          </div>
        )}
        <div className="editor-layout">
          <div className="editor-preview">
            {isPreviewing ? (
              <div className="preview-panel">
                <div className="preview-toolbar">
                  <span className="preview-toolbar-label">
                    {isPreviewLoading ? 'Generating AI Preview...' : 'AI Preview'}
                  </span>
                  <div className="preview-mode-indicator exploring">
                    {previewingOptionId}
                  </div>
                </div>
                <div className="preview-frame-container">
                  {isPreviewLoading && (
                    <div className="preview-loading-overlay">
                      <div className="preview-spinner" />
                      <span className="preview-loading-text">
                        {previewFixAttempts > 0
                          ? `Fixing runtime errors (attempt ${previewFixAttempts}/2)...`
                          : 'Generating AI game from scratch...'}
                      </span>
                    </div>
                  )}
                  {previewError && (
                    <div className="preview-error-banner">{previewError}</div>
                  )}
                  <iframe
                    src={
                      !isPreviewLoading && previewingOptionId && sessionId
                        ? `${getAiPreviewUrl(id, sessionId, previewingOptionId)}?v=${previewKey}`
                        : 'about:blank'
                    }
                    sandbox="allow-scripts allow-same-origin"
                    className={`preview-frame${isPreviewLoading ? ' preview-loading' : ''}`}
                    title="AI Preview"
                  />
                </div>
              </div>
            ) : (
              <PreviewPanel projectId={id} />
            )}
          </div>
          <div className="editor-chat">
            <div className="explore-tabs">
              <button
                className={`tab-btn ${activeTab === 'explore' ? 'active' : ''}`}
                onClick={() => setActiveTab('explore')}
              >
                Explore
              </button>
              <button
                className={`tab-btn ${activeTab === 'iterate' ? 'active' : ''}`}
                onClick={() => setActiveTab('iterate')}
                disabled={explorationState === 'idle' || explorationState === 'explore_options' || explorationState === 'previewing'}
              >
                Iterate
              </button>
              <button
                className={`tab-btn ${activeTab === 'memory' ? 'active' : ''}`}
                onClick={() => setActiveTab('memory')}
              >
                Memory
              </button>
              <button
                className={`tab-btn tab-btn-debug ${activeTab === 'debug' ? 'active' : ''}`}
                onClick={() => setActiveTab('debug')}
              >
                Debug
              </button>
            </div>
            <div className="tab-content">
              {activeTab === 'explore' && <ExplorePanel projectId={id} />}
              {activeTab === 'iterate' && <IteratePanel projectId={id} />}
              {activeTab === 'memory' && <ExplorationMemoryPanel projectId={id} />}
              {activeTab === 'debug' && <DebugPanel />}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
