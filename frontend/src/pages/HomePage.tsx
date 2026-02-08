import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { listProjects, createProject, deleteProject } from '../api/projects'
import type { Project } from '../types/project'
import ProjectCard from '../components/project/ProjectCard'
import CreateProjectModal from '../components/project/CreateProjectModal'

export default function HomePage() {
  const [projects, setProjects] = useState<Project[]>([])
  const [showCreate, setShowCreate] = useState(false)
  const nav = useNavigate()

  useEffect(() => {
    listProjects().then(setProjects)
  }, [])

  const handleCreate = async (title: string, description: string) => {
    const project = await createProject({ title, description: description || undefined })
    nav(`/project/${project.id}`)
  }

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this project?')) return
    await deleteProject(id)
    setProjects((prev) => prev.filter((p) => p.id !== id))
  }

  return (
    <div className="home-page">
      <header className="home-header">
        <h1>SimplePageGenerator</h1>
        <p>Build web games & mini-apps with AI</p>
        <button className="btn-primary" onClick={() => setShowCreate(true)}>
          New Project
        </button>
      </header>

      <div className="project-grid">
        {projects.map((p) => (
          <ProjectCard key={p.id} project={p} onDelete={handleDelete} />
        ))}
        {projects.length === 0 && (
          <p className="empty-state">No projects yet. Create one to get started!</p>
        )}
      </div>

      <CreateProjectModal
        open={showCreate}
        onClose={() => setShowCreate(false)}
        onCreate={handleCreate}
      />
    </div>
  )
}
