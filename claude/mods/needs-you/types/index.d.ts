export type ItemKind = 'answer' | 'do' | 'later'

export type Item = {
  id: number
  kind: ItemKind
  text: string
  at: number
  detail?: string
  expanding?: boolean
  failed?: boolean
  fromTask?: boolean
}

export type AskOption = { label: string; fill: string; send?: boolean }

export type Reply = {
  question: string | null
  done: string | null
  options: AskOption[]
}

export type GitFacts = {
  branch: string
  unpushed: number
  ahead: number | null
  hasUpstream: boolean
  uncommitted: number
}

declare module 'claude-code' {
  interface PluginState {
    'needs-you': {
      items: Item[]
      reply: Reply | null
      git: GitFacts | null
      now: number
      tldr: string | null
      shown: string | null
      laterOpen: boolean
      lastCall: number
      keepWarm: boolean
    }
  }
}
