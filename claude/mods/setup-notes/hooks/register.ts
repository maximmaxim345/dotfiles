import type { Register } from 'claude-code'

const TOOL = 'mcp__setup-notes__note'

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    const started = await next(e)
    await $.tool.register({
      name: 'note',
      description:
        'Log one thing about the Claude Code setup (CLAUDE.md, project rules, skills, agents, mods, tools) that changed what you did: a rule that was unclear, conflicted with another or was missing for the case at hand, or a tool that got in the way. Write it without reading earlier notes.',
      inputSchema: {
        type: 'object',
        properties: {
          topic: { type: 'string', description: 'The rule, file or tool involved' },
          note: { type: 'string', description: 'One sentence on what happened and what you did' },
        },
        required: ['topic', 'note'],
      },
    })

    return started
  })

  on('tool.call', { tool: TOOL }, async ($, e) => {
    if (typeof e.topic !== 'string' || typeof e.note !== 'string') {
      return { deny: 'topic and note must be strings' }
    }
    const at = new Date(await $.clock.now()).toISOString()
    const entry = {
      at,
      session: await $.session.id(),
      cwd: await $.session.cwd(),
      topic: e.topic,
      note: e.note,
    }
    const home = await $.env.get('HOME')
    // One file per note, since `$.fs` can't append and sessions run in parallel.
    await $.fs.write(
      `${home}/.claude/setup-notes/${at.replace(/[:.]/g, '-')}-${e.tool_use_id}.json`,
      `${JSON.stringify(entry, null, 2)}\n`,
    )

    return { result: 'Noted.' }
  })
}
