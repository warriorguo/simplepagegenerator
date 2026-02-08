import { useNavigate } from 'react-router-dom'
import type { Project } from '../../types/project'

interface Props {
  project?: Project | null
}

export default function TopBar({ project }: Props) {
  const nav = useNavigate()

  return (
    <header className="topbar">
      <button className="topbar-back" onClick={() => nav('/')}>
        &larr;
      </button>
      <h1 className="topbar-title">{project?.title || 'SimplePageGenerator'}</h1>
      <div className="topbar-status">
        {project && <span className={`status-badge status-${project.status}`}>{project.status}</span>}
      </div>
    </header>
  )
}
