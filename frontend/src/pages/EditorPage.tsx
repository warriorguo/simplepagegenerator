import { useParams } from 'react-router-dom'
import { useState } from 'react'
import TopBar from '../components/layout/TopBar'
import EditorLayout from '../components/layout/EditorLayout'
import PreviewPanel from '../components/preview/PreviewPanel'
import ChatPanel from '../components/chat/ChatPanel'
import VersionList from '../components/version/VersionList'
import { useProject } from '../hooks/useProject'
import '../styles/editor.css'

export default function EditorPage() {
  const { id } = useParams<{ id: string }>()
  const project = useProject(id)
  const [showVersions, setShowVersions] = useState(false)

  if (!id) return <div>Invalid project ID</div>

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
      </div>
      <div className="editor-main">
        {showVersions && (
          <div className="editor-sidebar">
            <VersionList projectId={id} />
          </div>
        )}
        <EditorLayout
          preview={<PreviewPanel projectId={id} />}
          chat={<ChatPanel projectId={id} />}
        />
      </div>
    </div>
  )
}
