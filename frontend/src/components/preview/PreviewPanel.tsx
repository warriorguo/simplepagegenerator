import PreviewToolbar from './PreviewToolbar'
import { usePreview } from '../../hooks/usePreview'
import { useStore } from '../../store'

interface Props {
  projectId: string
}

export default function PreviewPanel({ projectId }: Props) {
  const { previewUrl } = usePreview(projectId)
  const refreshPreview = useStore((s) => s.refreshPreview)

  return (
    <div className="preview-panel">
      <PreviewToolbar onRefresh={refreshPreview} projectId={projectId} />
      <div className="preview-frame-container">
        <iframe
          key={previewUrl}
          src={previewUrl}
          sandbox="allow-scripts allow-same-origin"
          className="preview-frame"
          title="Preview"
        />
      </div>
    </div>
  )
}
