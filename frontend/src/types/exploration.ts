export type ExplorationState =
  | 'idle'
  | 'explore_options'
  | 'previewing'
  | 'committed'
  | 'iterating'
  | 'memory_writing'
  | 'stable'

export interface ExplorationOption {
  option_id: string
  title: string
  core_loop: string
  controls: string
  mechanics: string[]
  engine: string
  template_id: string
  complexity: string
  mobile_fit: string
  assumptions_to_validate: string[]
  is_recommended: boolean
}

export interface HypothesisLedger {
  validated: string[]
  rejected: string[]
  open_questions: string[]
}

export interface AmbiguityDimension {
  candidates: string[]
  detected: string[]
}

export interface Ambiguity {
  [key: string]: AmbiguityDimension
}

export interface MemoryInfluence {
  relevant_preferences: Record<string, unknown>
  recurring_patterns: string[]
  warnings: string[]
  suggested_direction_bias: Record<string, string> | null
}

export interface ExploreResponse {
  session_id: number
  ambiguity: Ambiguity
  options: ExplorationOption[]
  memory_influence: MemoryInfluence | null
}

export interface SelectOptionResponse {
  session_id: number
  option_id: string
  version_id: number
  state: string
}

export interface IterateResponse {
  session_id: number
  version_id: number
  iteration_count: number
  hypothesis_ledger: HypothesisLedger
  state: string
}

export interface MemoryNoteContent {
  title: string
  summary: string
  user_preferences: Record<string, string>
  final_choice: { option_id: string; why: string }
  validated_hypotheses: string[]
  rejected_hypotheses: string[]
  key_decisions: Array<{ decision: string; reason: string; evidence: string }>
  pitfalls_and_guards: string[]
  refs: Record<string, unknown>
  confidence: number
}

export interface MemoryNote {
  id: number
  project_id: string
  content_json: MemoryNoteContent
  tags: string[] | null
  confidence: number
  source_session_id: number | null
  created_at: string
}

export interface FinishExplorationResponse {
  session_id: number
  memory_note: MemoryNote
  state: string
}

export interface ExplorationSessionState {
  session_id: number
  state: ExplorationState
  selected_option_id: string | null
  iteration_count: number
  hypothesis_ledger: HypothesisLedger | null
}
