import type { Register } from 'claude-code'

// ponytail: only Write/Edit; a bash redirect is invisible until a real chore needs it.
const MAX_PATHS = 30

export const register: Register = on => {
  const touched = new Set<string>()

  on('tool.call', { tool: ['Write', 'Edit'] }, async ($, e, next) => {
    const result = await next(e)
    if (!result.deny && !result.isError && e.file_path) touched.add(e.file_path)
    return result
  }).catch(($, e, next) => next(e))

  on('turn.complete', async ($, e, next) => {
    if (e.agentId) return next(e)
    if (e.isAborted) {
      touched.clear()
      return next(e)
    }
    const paths = [...touched].slice(0, MAX_PATHS)
    touched.clear()
    if (paths.length === 0) return next(e)
    const root = $.plugin.root.replace(/\/$/, '')
    let run: { exitCode: number; stdout: string }
    try {
      run = await $.process.run([`${root}/pytho-inator`, 'glance', ...paths])
    } catch {
      return next(e)
    }
    const hint = run.exitCode === 0 ? run.stdout.trim() : ''
    if (!hint) return next(e)
    await next(e)
    return { text: `${hint}\nQuer que eu construa esse CLI?` }
  }).catch(($, e, next) => next(e))
}
