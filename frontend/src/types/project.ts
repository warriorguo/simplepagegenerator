export interface Project {
  id: string
  title: string
  description: string | null
  status: string
  current_version_id: number | null
  published_version_id: number | null
  created_at: string
  updated_at: string
}

export interface ProjectCreate {
  title: string
  description?: string
}
