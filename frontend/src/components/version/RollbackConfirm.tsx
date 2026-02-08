interface Props {
  versionId: number
  onConfirm: () => void
  onCancel: () => void
}

export default function RollbackConfirm({ versionId, onConfirm, onCancel }: Props) {
  return (
    <div className="modal-overlay" onClick={onCancel}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h3>Rollback to v{versionId}?</h3>
        <p>This will create a new version with the files from v{versionId}.</p>
        <div className="modal-actions">
          <button onClick={onCancel}>Cancel</button>
          <button onClick={onConfirm}>Rollback</button>
        </div>
      </div>
    </div>
  )
}
