export type ItemKind = 'answer' | 'review' | 'do' | 'later'

export type Item = {
  id: number
  kind: ItemKind
  text: string
  at: number
  detail?: string
  expanding?: boolean
  failed?: boolean
}

export type AskOption = { label: string; fill: string }

export type Reply = {
  done: string | null
  options: AskOption[]
  draft: string | null
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
    }
  }
}
