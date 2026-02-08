import { useNavigate } from 'react-router-dom'
import type { Project } from '../../types/project'

interface Props {
  project: Project
  onDelete: (id: string) => void
}

export default function ProjectCard({ project, onDelete }: Props) {
  const nav = useNavigate()

  return (
    <div className="project-card" onClick={() => nav(`/project/${project.id}`)}>
      <div className="project-card-header">
        <h3>{project.title}</h3>
        <span className={`status-badge status-${project.status}`}>{project.status}</span>
      </div>
      {project.description && <p className="project-card-desc">{project.description}</p>}
      <div className="project-card-footer">
        <span className="project-card-date">
          {new Date(project.created_at).toLocaleDateString()}
        </span>
        <button
          className="project-card-delete"
          onClick={(e) => {
            e.stopPropagation()
            onDelete(project.id)
          }}
        >
          Delete
        </button>
      </div>
    </div>
  )
}
