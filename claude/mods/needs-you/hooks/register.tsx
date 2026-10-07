import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import type { AskOption, GitFacts, Item, ItemKind, Reply } from '../types'

const items = atom({ plugin: 'needs-you', key: 'items' } as const, [])
const reply = atom({ plugin: 'needs-you', key: 'reply' } as const, null)
const git = atom({ plugin: 'needs-you', key: 'git' } as const, null)
const now = atom({ plugin: 'needs-you', key: 'now' } as const, 0)
const tldr = atom({ plugin: 'needs-you', key: 'tldr' } as const, null)
const shown = atom({ plugin: 'needs-you', key: 'shown' } as const, null)
const laterOpen = atom({ plugin: 'needs-you', key: 'laterOpen' } as const, false)

const KINDS: readonly ItemKind[] = ['answer', 'review', 'do', 'later']
const SHELL_LANGS = /^(bash|sh|zsh|shell|console)$/i
const USER_ORIGINS = ['composer', 'bridge', 'sdk']
const SPAWN_TASK = 'mcp__ccd_session__spawn_task'
const SHOWN = 3
const COMMANDS = ['/implement', '/review-brief', '/review-changes', '/open-pr']
const NO_REPLY: Reply = { done: null, options: [], draft: null }

const CLASSIFY = `You keep the list of things the user of an AI coding assistant still has to act on. You get the open list, the user's latest prompts and the assistant's latest reply.
Answer with JSON only, no prose, in this shape:
{"resolved": number[], "new": [{"kind": "answer" | "review" | "do" | "later", "text": string, "same": number}], "done": string, "options": [{"label": string, "fill": string}], "draft": number, "tldr": string}

resolved: the ids of open items the latest prompts or the reply dealt with: the user answered or decided it, approved or rejected the draft, did the task, or the assistant fixed it, opened an issue for it or dropped it. Also resolve an answer, review or do item that a newer item replaced. A later item stays open while the work moves on. Suggesting an item as a background task does not deal with it. Leave an item the reply asks again out of resolved.

new: everything the reply asks of the user or sets aside, one entry each, new ones first, at most 5. same: the id of the open item the entry repeats, even when worded differently, or -1 when it is new.
- "answer": a question or decision for the user.
- "review": a draft (comment, PR text, message) or commits for the user to check or approve.
- "do": something the user must do themselves (test a UI, run a command, restart a device, log in).
- "later": a problem or follow-up the reply leaves out of the current work ("found a bug, but it does not belong in this PR"). Not the assistant's own next steps in the current work.
text: under 80 characters and clear without reading the reply, so name what it is about. For "later", a noun phrase naming the problem and where it is ("Race in queue reload in the player provider"). Otherwise start with a verb ("Answer: fix needs-you duplicates now or log first?").

done: when the reply asks nothing, what was done, under 60 characters. Otherwise "".

options: buttons that answer the reply's main question, at most 4. label is one to three words. fill is the answer the user would type, under 100 characters, naming what it answers so it reads clearly on its own ("Yes, add setup-notes to the mod list in settings.json").
- A yes/no question: a "Yes" and a "No" entry.
- A choice between named alternatives: one entry per alternative, labeled with it ("Fix now", "Measure first").
- Numbered options to pick from: one entry per number, labeled with the number, even when the options also have names.
- Several numbered questions: one entry per number, labeled with the number, fill "<number> - " for the user to finish.
Otherwise [].

draft: the index of the candidate below that is a draft for the user to copy and post, or -1 when none is.

tldr: what the whole session is working on, under 70 characters, as a noun phrase ("Building a band mod that shows what the session needs"). Start from the previous TLDR and change it only when the latest prompts moved the work somewhere new.
`

function extractCandidates(text: string): string[] {
  const found: string[] = []
  const fence = /```(\w*)\n([\s\S]*?)```/g
  for (const m of text.matchAll(fence)) {
    if (!SHELL_LANGS.test(m[1] ?? '')) found.push(m[2]!.trimEnd())
  }
  let quote: string[] = []
  for (const line of [...text.split('\n'), '']) {
    if (line.startsWith('>')) {
      quote.push(line.replace(/^>\s?/, ''))
    } else if (quote.length > 0) {
      found.push(quote.join('\n').trim())
      quote = []
    }
  }

  return found
}

function parseJson(text: string) {
  const start = text.indexOf('{')
  const end = text.lastIndexOf('}')
  if (start < 0 || end <= start) return null
  try {
    return JSON.parse(text.slice(start, end + 1))
  } catch {
    return null
  }
}

function parseNew(raw: unknown, openIds: number[]): Pick<Item, 'kind' | 'text'>[] {
  if (!Array.isArray(raw)) return []

  return raw
    .filter(n => KINDS.includes(n?.kind) && typeof n?.text === 'string' && n.text.trim() !== '')
    .filter(n => !openIds.includes(n.same))
    .slice(0, 5)
    .map(n => ({ kind: n.kind, text: n.text.trim().slice(0, 100) }))
}

function parseReply(raw: any, candidates: string[]): Reply {
  const options: AskOption[] = Array.isArray(raw.options)
    ? raw.options
        .filter((o: unknown): o is AskOption =>
          typeof (o as AskOption)?.label === 'string' &&
          typeof (o as AskOption)?.fill === 'string',
        )
        .slice(0, 4)
    : []
  const draft = Number.isInteger(raw.draft) ? (candidates[raw.draft] ?? null) : null
  const done = typeof raw.done === 'string' && raw.done.trim() !== '' ? raw.done.trim().slice(0, 80) : null

  return { done, options, draft }
}

async function changeItems(
  $: EngineInterface,
  resolved: number[],
  added: Pick<Item, 'kind' | 'text'>[],
) {
  const at = await $.clock.now()
  await update($, items, (list: Item[]) => {
    let id = list.reduce((max, i) => Math.max(max, i.id), 0)
    const kept = list.filter(i => !resolved.includes(i.id))

    return [...kept, ...added.map(a => ({ ...a, id: ++id, at }))]
  })
}

async function runGit($: EngineInterface, cwd: string, args: string[]) {
  const ran = await $.process.run(['git', ...args], { cwd, timeoutMs: 5000 })

  return ran.exitCode === 0 ? ran.stdout.trim() : null
}

async function refreshGit($: EngineInterface) {
  const cwd = await $.session.cwd()
  const branch = await runGit($, cwd, ['rev-parse', '--abbrev-ref', 'HEAD'])
  if (branch === null) {
    await update($, git, () => null)
    return
  }
  const upstream = await runGit($, cwd, ['rev-list', '--count', '@{u}..HEAD'])
  const ahead = await runGit($, cwd, ['rev-list', '--count', 'origin/HEAD..HEAD'])
  const status = (await runGit($, cwd, ['status', '--porcelain'])) ?? ''
  const facts: GitFacts = {
    branch,
    unpushed: Number(upstream ?? ahead ?? 0),
    ahead: ahead === null ? null : Number(ahead),
    hasUpstream: upstream !== null,
    uncommitted: status === '' ? 0 : status.split('\n').length,
  }
  await update($, git, () => facts)
}

async function classify(
  $: EngineInterface,
  prompt: string,
  answer: string,
  isCurrent: () => boolean,
) {
  const candidates = extractCandidates(answer)
  const listed = candidates.map((c, i) => `[${i}]\n${c}`).join('\n\n') || '(none)'
  const current = await read($, items)
  const open = current.map(i => `[${i.id}] ${i.kind}: ${i.text}`).join('\n')
  const previous = (await read($, tldr)) ?? '(none yet)'
  const completed = await $.model.complete({
    model: 'sonnet',
    effort: 'low',
    prompt: `${CLASSIFY}\nOpen items:\n${open || '(none)'}\n\nCandidates:\n${listed}\n\nPrevious TLDR:\n${previous}\n\nLatest prompts:\n${prompt}\n\nReply:\n${answer}`,
  })
  const raw = completed.isAnswered ? parseJson(completed.text) : null
  if (raw === null) {
    if (isCurrent()) await update($, reply, () => NO_REPLY)
    return
  }
  const resolved = Array.isArray(raw.resolved) ? raw.resolved.filter(Number.isInteger) : []
  await changeItems($, resolved, parseNew(raw.new, current.map(i => i.id).filter(id => !resolved.includes(id))))
  if (typeof raw.tldr === 'string' && raw.tldr.trim() !== '') {
    await update($, tldr, () => raw.tldr.trim().slice(0, 90))
  }
  if (isCurrent()) await update($, reply, () => parseReply(raw, candidates))
}

function keyOf(item: Item) {
  return `${item.id}:${item.at}`
}

async function expand($: EngineInterface, item: Item) {
  const change = (patch: Partial<Item>) =>
    update($, items, (list: Item[]) => list.map(i => (keyOf(i) === keyOf(item) ? { ...i, ...patch } : i)))
  await change({ expanding: true })
  const forked = await $.model.fork({
    prompt: `The user's status band shows this open item from this session (${item.kind}): "${item.text}". Expand it in at most three short sentences of plain text, using what you know from this session: what it is about, what the user needs to know to act on it, and your recommendation if you have one. Don't repeat the item, and don't use lists or headings.`,
  })
  await change({
    expanding: false,
    detail: forked.isAnswered ? forked.text.trim() : `No detail: ${forked.reason}`,
    failed: !forked.isAnswered,
  })
  await update($, shown, () => keyOf(item))
}

function minutesSince(at: number, current: number) {
  const minutes = Math.floor((current - at) / 60000)
  if (minutes < 1) return ''
  if (minutes < 60) return ` · ${minutes} min`

  return ` · ${Math.floor(minutes / 60)} h ${minutes % 60} min`
}

export const register: Register = on => {
  let prompts: string[] = []
  let generation = 0
  let queue: Promise<void> = Promise.resolve()

  on('session.start', async ($, e, next) => {
    const started = await next(e)
    await update($, now, () => Date.now())
    $.clock.every(60000, () => void update($, now, () => Date.now()))
    await refreshGit($)

    return started
  })

  on('prompt.submit', async ($, e, next) => {
    if (USER_ORIGINS.includes(e.origin.kind)) {
      generation += 1
      prompts.push(e.text)
      await update($, reply, () => null)
    }

    return next(e)
  })

  on('tool.call', { tool: 'Bash' }, async ($, e, next) => {
    const ran = await next(e)
    if (typeof e.command === 'string' && /\b(git|gh)\b/.test(e.command)) await refreshGit($)

    return ran
  })

  on('tool.call', { tool: SPAWN_TASK }, async ($, e, next) => {
    const ran = await next(e)
    if (typeof e.title === 'string' && ran.deny === undefined && ran.isError !== true) {
      await changeItems($, [], [{ kind: 'later', text: e.title.slice(0, 80) }])
    }

    return ran
  })

  on('turn.complete', async ($, e, next) => {
    const done = await next(e)
    if (e.agentId === undefined && !e.isAborted && e.answer.trim() !== '') {
      generation += 1
      const mine = generation
      const answer = e.answer
      const prompt = prompts.join('\n\n') || '(none)'
      prompts = []
      const run = () => classify($, prompt, answer, () => generation === mine)
      // Run classifications in order so each one sees the items the previous one added.
      $.clock.after(0, () => {
        queue = queue.then(run, run)
      })
    } else if (e.agentId === undefined) {
      await update($, reply, () => NO_REPLY)
    }
    void refreshGit($)

    return done
  })

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    if (e.props.hasSurvey) return next(e)

    const open = await read($, items)
    const latest = e.props.isWorking ? null : await read($, reply)
    const asks = latest === null ? [] : open.filter(i => i.kind !== 'later')
    const later = open.filter(i => i.kind === 'later')
    const facts = await read($, git)
    const current = await read($, now)
    const topic = await read($, tldr)
    const shownId = await read($, shown)
    const isLaterOpen = await read($, laterOpen)
    if (open.length === 0 && latest === null && facts === null && topic === null) return next(e)

    const { Box, Button, Text } = $.ui.resolve(e)

    const fill = async (text: string) => {
      const box = await $.prompt.read()
      const isEmpty = box.text.trim() === ''
      await $.prompt.fill(
        isEmpty ? { text, mode: 'replace' } : { text: `\n${text}`, mode: 'append' },
      )
    }

    const start = async (command: string) => {
      const typed = (await $.prompt.read()).text.trim()
      const previous = COMMANDS.find(c => typed === c || typed.startsWith(`${c} `))
      const args = previous === undefined ? typed : typed.slice(previous.length).trim()
      await $.prompt.fill({ text: `${command} ${args}`, mode: 'replace' })
    }

    const dismiss = (item: Item) => (
      <Button
        key={`dismiss-${item.id}`}
        label="x"
        plain
        dimColor
        onPress={() => void update($, items, (list: Item[]) => list.filter(i => i.id !== item.id))}
      />
    )

    const more = (item: Item) => (
      <Button
        key={`more-${item.id}`}
        label={item.expanding ? 'expanding' : shownId === keyOf(item) ? 'less' : 'more'}
        plain
        dimColor
        onPress={() => {
          if (item.expanding) return
          if (shownId === keyOf(item)) void update($, shown, () => null)
          else if (item.detail !== undefined && !item.failed) void update($, shown, () => keyOf(item))
          else void expand($, item)
        }}
      />
    )

    const detail = (item: Item) =>
      shownId === keyOf(item) &&
      item.detail !== undefined && (
        <Box paddingLeft={2}>
          <Text dimColor>{item.detail}</Text>
        </Box>
      )

    const replyButtons =
      latest === null
        ? []
        : [
            ...latest.options.map((o, i) => (
              <Button
                key={`opt-${i}`}
                label={o.label}
                hotkey={/^[1-9]$/.test(o.label) ? o.label : undefined}
                onPress={() => void fill(o.fill)}
              />
            )),
            ...(latest.draft === null
              ? []
              : [
                  <Button
                    key="copy"
                    label="Copy draft"
                    hotkey="c"
                    onPress={p => void $.ui.copy({ text: latest.draft!, surface: p.surface })}
                  />,
                ]),
          ]

    const gitParts: string[] = []
    if (facts !== null) {
      gitParts.push(facts.branch)
      if (facts.unpushed > 0) {
        gitParts.push(`${facts.unpushed} unpushed${facts.hasUpstream ? '' : ' (no upstream)'}`)
      }
      if (facts.uncommitted > 0) gitParts.push(`${facts.uncommitted} uncommitted`)
    }

    const hasChanges = facts !== null && (facts.ahead !== 0 || facts.uncommitted > 0)
    const commands = COMMANDS.filter(c => hasChanges || !['/review-brief', '/open-pr'].includes(c))
    const showLater = later.length === 1 || isLaterOpen

    return (
      <Box flexDirection="column">
        {topic !== null && (
          <Text dimColor wrap="truncate-end">
            TLDR: {topic}
          </Text>
        )}
        {asks.slice(-SHOWN).map(item => (
          <Box key={`ask-${item.id}`} flexDirection="column">
            <Box flexDirection="row" gap={1}>
              <Text color="yellow" wrap="truncate-end">
                ● Needs you: {item.text}
                {minutesSince(item.at, current)}
              </Text>
              {more(item)}
              {dismiss(item)}
            </Box>
            {detail(item)}
          </Box>
        ))}
        {asks.length > SHOWN && <Text dimColor>+{asks.length - SHOWN} older asks</Text>}
        {latest?.done != null && (
          <Text dimColor wrap="truncate-end">
            Done: {latest.done}
          </Text>
        )}
        {replyButtons.length > 0 && (
          <Box flexDirection="row" gap={1}>
            {replyButtons}
          </Box>
        )}
        {later.length > 1 && (
          <Box flexDirection="row" gap={1}>
            <Text color="magenta">◆ {later.length} later</Text>
            <Button
              key="later-toggle"
              label={isLaterOpen ? 'hide' : 'show'}
              plain
              dimColor
              onPress={() => void update($, laterOpen, (o: boolean) => !o)}
            />
          </Box>
        )}
        {showLater && later.slice(-SHOWN).map(item => (
          <Box key={`later-${item.id}`} flexDirection="column">
            <Box flexDirection="row" gap={1}>
              <Text color="magenta" wrap="truncate-end">
                ◆ Later: {item.text}
              </Text>
              {more(item)}
              {dismiss(item)}
            </Box>
            {detail(item)}
          </Box>
        ))}
        {showLater && later.length > SHOWN && <Text dimColor>+{later.length - SHOWN} older later</Text>}
        {gitParts.length > 0 && (
          <Text dimColor wrap="truncate-end">
            {gitParts.join(' · ')}
          </Text>
        )}
        {!e.props.isWorking && (
          <Box flexDirection="row" gap={1}>
            {commands.map(command => (
              <Button
                key={`cmd-${command}`}
                label={command}
                dimColor
                onPress={() => void start(command)}
              />
            ))}
          </Box>
        )}
      </Box>
    )
  })
}
