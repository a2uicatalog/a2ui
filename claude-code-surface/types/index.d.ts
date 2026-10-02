export type Block = { type: string; [field: string]: unknown }

export type Gate = {
  process: string
  isOk: boolean
  phase: string
  cmd: string
  durationS: number | null
  at: number
}

export type ToolRow = {
  id: string
  label: string
  state: 'running' | 'ok' | 'error'
  startedAt: number
  endedAt: number
}

export type Progress = {
  id: string
  label: string
  caption: string
  value: number
  shown: number
  updatedAt: number
  state: 'running' | 'done' | 'stalled'
}

export type Limit = { kind: string; percentUsed: number; resetsAt?: string }

export type Job = {
  isActive: boolean
  turnId: string
  prompt: string
  startedAt: number
  endedAt: number
  ctxStart: number
  ctxTokens: number
  ctxPercent: number | null
  costUsd: number | null
  tools: ToolRow[]
  outcome: string
  limits: Limit[]
}

declare module 'claude-code' {
  interface PluginState {
    'a2ui-claude-code': {
      title: string
      blocks: Block[]
      error: string
      job: Job
      gate: Gate | null
      now: number
      progress: Progress[]
    }
  }
}
