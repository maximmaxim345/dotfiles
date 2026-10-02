export type ItemKind = 'answer' | 'review' | 'do' | 'later'

export type Item = { id: number; kind: ItemKind; text: string; at: number }

export type AskOption = { label: string; fill: string }

export type Reply = {
  done: string | null
  options: AskOption[]
  draft: string | null
}

export type GitFacts = {
  branch: string
  unpushed: number
  hasUpstream: boolean
  uncommitted: number
  needsSage: boolean
}

export type Checks = { audit: boolean; sage: boolean }

declare module 'claude-code' {
  interface PluginState {
    'needs-you': {
      items: Item[]
      reply: Reply | null
      git: GitFacts | null
      checks: Checks
      now: number
      tldr: string | null
    }
  }
}
