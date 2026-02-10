import { create } from 'zustand'
import type { Project } from '../types/project'
import type { ChatMessage } from '../types/chat'
import type { ProjectVersion } from '../types/version'
import type { Memory } from '../types/memory'
import type { ExplorationOption, ExplorationState, HypothesisLedger, Ambiguity, MemoryInfluence, MemoryNote } from '../types/exploration'

interface StreamingMessage {
  tokens: string
  stage: string
  toolCalls: Array<{ tool: string; args: Record<string, string> }>
  buildStatus: { success: boolean; errors: string[] } | null
  done: boolean
}

interface AppState {
  // Project
  currentProject: Project | null
  setCurrentProject: (p: Project | null) => void

  // Chat
  messages: ChatMessage[]
  setMessages: (msgs: ChatMessage[]) => void
  addMessage: (msg: ChatMessage) => void

  // Streaming
  streaming: StreamingMessage
  resetStreaming: () => void
  appendToken: (token: string) => void
  setStage: (stage: string) => void
  addToolCall: (tool: string, args: Record<string, string>) => void
  setBuildStatus: (success: boolean, errors: string[]) => void
  setStreamDone: () => void

  // Versions
  versions: ProjectVersion[]
  setVersions: (v: ProjectVersion[]) => void

  // Memories
  memories: Memory[]
  setMemories: (m: Memory[]) => void

  // Preview
  previewKey: number
  refreshPreview: () => void

  // Sending state
  isSending: boolean
  setIsSending: (v: boolean) => void

  // Exploration
  explorationState: ExplorationState
  setExplorationState: (s: ExplorationState) => void
  sessionId: number | null
  setSessionId: (id: number | null) => void
  explorationOptions: ExplorationOption[]
  setExplorationOptions: (opts: ExplorationOption[]) => void
  selectedOptionId: string | null
  setSelectedOptionId: (id: string | null) => void
  previewingTemplateId: string | null
  setPreviewingTemplateId: (id: string | null) => void
  hypothesisLedger: HypothesisLedger | null
  setHypothesisLedger: (h: HypothesisLedger | null) => void
  iterationCount: number
  setIterationCount: (n: number) => void
  memoryNotes: MemoryNote[]
  setMemoryNotes: (notes: MemoryNote[]) => void
  ambiguity: Ambiguity | null
  setAmbiguity: (a: Ambiguity | null) => void
  memoryInfluence: MemoryInfluence | null
  setMemoryInfluence: (m: MemoryInfluence | null) => void
  isExploring: boolean
  setIsExploring: (v: boolean) => void
  activeTab: 'explore' | 'iterate' | 'memory' | 'debug'
  setActiveTab: (tab: 'explore' | 'iterate' | 'memory' | 'debug') => void
  resetExploration: () => void
}

const initialStreaming: StreamingMessage = {
  tokens: '',
  stage: '',
  toolCalls: [],
  buildStatus: null,
  done: false,
}

export const useStore = create<AppState>((set) => ({
  currentProject: null,
  setCurrentProject: (p) => set({ currentProject: p }),

  messages: [],
  setMessages: (msgs) => set({ messages: msgs }),
  addMessage: (msg) => set((s) => ({ messages: [...s.messages, msg] })),

  streaming: { ...initialStreaming },
  resetStreaming: () => set({ streaming: { ...initialStreaming } }),
  appendToken: (token) =>
    set((s) => ({ streaming: { ...s.streaming, tokens: s.streaming.tokens + token } })),
  setStage: (stage) =>
    set((s) => ({ streaming: { ...s.streaming, stage } })),
  addToolCall: (tool, args) =>
    set((s) => ({
      streaming: { ...s.streaming, toolCalls: [...s.streaming.toolCalls, { tool, args }] },
    })),
  setBuildStatus: (success, errors) =>
    set((s) => ({ streaming: { ...s.streaming, buildStatus: { success, errors } } })),
  setStreamDone: () =>
    set((s) => ({ streaming: { ...s.streaming, done: true } })),

  versions: [],
  setVersions: (v) => set({ versions: v }),

  memories: [],
  setMemories: (m) => set({ memories: m }),

  previewKey: 0,
  refreshPreview: () => set((s) => ({ previewKey: s.previewKey + 1 })),

  isSending: false,
  setIsSending: (v) => set({ isSending: v }),

  // Exploration
  explorationState: 'idle',
  setExplorationState: (s) => set({ explorationState: s }),
  sessionId: null,
  setSessionId: (id) => set({ sessionId: id }),
  explorationOptions: [],
  setExplorationOptions: (opts) => set({ explorationOptions: opts }),
  selectedOptionId: null,
  setSelectedOptionId: (id) => set({ selectedOptionId: id }),
  previewingTemplateId: null,
  setPreviewingTemplateId: (id) => set({ previewingTemplateId: id }),
  hypothesisLedger: null,
  setHypothesisLedger: (h) => set({ hypothesisLedger: h }),
  iterationCount: 0,
  setIterationCount: (n) => set({ iterationCount: n }),
  memoryNotes: [],
  setMemoryNotes: (notes) => set({ memoryNotes: notes }),
  ambiguity: null,
  setAmbiguity: (a) => set({ ambiguity: a }),
  memoryInfluence: null,
  setMemoryInfluence: (m) => set({ memoryInfluence: m }),
  isExploring: false,
  setIsExploring: (v) => set({ isExploring: v }),
  activeTab: 'explore',
  setActiveTab: (tab) => set({ activeTab: tab }),
  resetExploration: () =>
    set({
      explorationState: 'idle',
      sessionId: null,
      explorationOptions: [],
      selectedOptionId: null,
      previewingTemplateId: null,
      hypothesisLedger: null,
      iterationCount: 0,
      ambiguity: null,
      memoryInfluence: null,
      isExploring: false,
      activeTab: 'explore',
    }),
}))
