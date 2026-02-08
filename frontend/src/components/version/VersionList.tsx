import { useEffect } from 'react'
import { getVersions, rollbackVersion } from '../../api/versions'
import { useStore } from '../../store'
import RollbackConfirm from './RollbackConfirm'
import { useState } from 'react'

interface Props {
  projectId: string
}

export default function VersionList({ projectId }: Props) {
  const { versions, setVersions, refreshPreview } = useStore()
  const [rollbackTarget, setRollbackTarget] = useState<number | null>(null)

  useEffect(() => {
    getVersions(projectId).then(setVersions)
  }, [projectId, setVersions])

  const handleRollback = async (versionId: number) => {
    await rollbackVersion(projectId, versionId)
    const updated = await getVersions(projectId)
    setVersions(updated)
    refreshPreview()
    setRollbackTarget(null)
  }

  return (
    <div className="version-list">
      <h3>Versions</h3>
      {versions.map((v) => (
        <div key={v.id} className="version-item">
          <span className="version-id">v{v.id}</span>
          <span className={`version-status ${v.build_status}`}>{v.build_status}</span>
          <span className="version-date">{new Date(v.created_at).toLocaleTimeString()}</span>
          <button
            className="version-rollback"
            onClick={() => setRollbackTarget(v.id)}
          >
            Rollback
          </button>
        </div>
      ))}

      {rollbackTarget !== null && (
        <RollbackConfirm
          versionId={rollbackTarget}
          onConfirm={() => handleRollback(rollbackTarget)}
          onCancel={() => setRollbackTarget(null)}
        />
      )}
    </div>
  )
}
