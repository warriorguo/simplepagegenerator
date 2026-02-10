import { useParams } from 'react-router-dom'
import { useState } from 'react'
import TopBar from '../components/layout/TopBar'
import PreviewPanel from '../components/preview/PreviewPanel'
import ExplorePanel from '../components/exploration/ExplorePanel'
import IteratePanel from '../components/exploration/IteratePanel'
import ExplorationMemoryPanel from '../components/exploration/ExplorationMemoryPanel'
import DebugPanel from '../components/exploration/DebugPanel'
import VersionList from '../components/version/VersionList'
import MemoryPanel from '../components/memory/MemoryPanel'
import { useProject } from '../hooks/useProject'
import { useMemories } from '../hooks/useMemories'
import { useStore } from '../store'
import '../styles/editor.css'
import '../styles/exploration.css'

export default function EditorPage() {
  const { id } = useParams<{ id: string }>()
  const project = useProject(id)
  useMemories(id)
  const [showVersions, setShowVersions] = useState(false)

  const {
    activeTab,
    setActiveTab,
    explorationState,
    previewingTemplateId,
    selectedOptionId,
    iterationCount,
  } = useStore()

  if (!id) return <div>Invalid project ID</div>

  // Determine preview URL
  const isPreviewingTemplate = explorationState === 'previewing' && previewingTemplateId
  const previewModeLabel = (() => {
    if (explorationState === 'previewing' && previewingTemplateId) {
      return `Exploring: ${previewingTemplateId}`
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
            {isPreviewingTemplate ? (
              <div className="preview-panel">
                <div className="preview-toolbar">
                  <span className="preview-toolbar-label">Template Preview</span>
                  <div className="preview-mode-indicator exploring">
                    {previewingTemplateId}
                  </div>
                </div>
                <div className="preview-frame-container">
                  <iframe
                    src={`/api/v1/projects/${id}/exploration/preview/${previewingTemplateId}`}
                    sandbox="allow-scripts allow-same-origin"
                    className="preview-frame"
                    title="Template Preview"
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
