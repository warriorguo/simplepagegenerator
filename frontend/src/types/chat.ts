export interface ChatMessage {
  id: number
  thread_id: number
  role: 'user' | 'assistant' | 'system' | 'tool'
  content: string
  created_at: string
}

export interface SSEEvent {
  event: string
  data: Record<string, unknown>
}

export interface StageChangeData {
  stage: string
}

export interface TokenData {
  token: string
}

export interface ToolCallData {
  tool: string
  args: Record<string, string>
}

export interface BuildStatusData {
  success: boolean
  errors: string[]
}

export interface DoneData {
  version_id: number | null
}

export interface ErrorData {
  message: string
}
