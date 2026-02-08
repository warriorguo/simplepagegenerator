import { useState } from 'react'
import { buildProject, publishProject } from '../../api/build'

interface Props {
  projectId: string
  onRefresh: () => void
}

export default function PreviewToolbar({ projectId, onRefresh }: Props) {
  const [publishing, setPublishing] = useState(false)

  const handleBuild = async () => {
    await buildProject(projectId)
    onRefresh()
  }

  const handlePublish = async () => {
    setPublishing(true)
    try {
      await publishProject(projectId)
      alert('Published! View at /published/' + projectId + '/index.html')
    } finally {
      setPublishing(false)
    }
  }

  return (
    <div className="preview-toolbar">
      <span className="preview-toolbar-label">Preview</span>
      <div className="preview-toolbar-actions">
        <button onClick={onRefresh} title="Refresh">Refresh</button>
        <button onClick={handleBuild} title="Rebuild">Build</button>
        <button onClick={handlePublish} disabled={publishing} title="Publish">
          {publishing ? 'Publishing...' : 'Publish'}
        </button>
      </div>
    </div>
  )
}
