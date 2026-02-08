import { useParams } from 'react-router-dom'

export default function PublishedPage() {
  const { id } = useParams<{ id: string }>()

  if (!id) return <div>Invalid project ID</div>

  return (
    <div className="published-page">
      <iframe
        src={`/published/${id}/index.html`}
        sandbox="allow-scripts"
        className="published-frame"
        title="Published App"
      />
    </div>
  )
}
