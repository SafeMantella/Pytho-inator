import type { Register } from 'claude-code'

// ponytail: Write/Edit paths + Bash commands; a bash redirect is invisible until a real chore needs it.
const MAX_PATHS = 30
const MAX_CMDS = 40

export const register: Register = on => {
  const touched = new Set<string>()
  const cmds: string[] = []

  on('tool.call', { tool: ['Write', 'Edit', 'Bash'] }, async ($, e, next) => {
    const result = await next(e)
    if (!result.deny && !result.isError) {
      if (e.file_path) touched.add(e.file_path)
      else if (e.command && cmds.length < MAX_CMDS) cmds.push(String(e.command))
    }
    return result
  }).catch(($, e, next) => next(e))

  on('turn.complete', async ($, e, next) => {
    if (e.agentId) return next(e)
    if (e.isAborted) {
      touched.clear()
      cmds.length = 0
      return next(e)
    }
    const paths = [...touched].slice(0, MAX_PATHS)
    const ran = cmds.splice(0).map(c => `--cmd=${c}`)
    touched.clear()
    if (paths.length === 0 && ran.length < 2) return next(e)
    const root = $.plugin.root.replace(/\/$/, '')
    let run: { exitCode: number; stdout: string }
    try {
      run = await $.process.run([`${root}/pytho-inator`, 'turn', ...ran, ...paths])
    } catch {
      return next(e)
    }
    const hint = run.exitCode === 0 ? run.stdout.trim() : ''
    if (!hint) return next(e)
    await next(e)
    return { text: `${hint}\nQuer que eu construa esse CLI?` }
  }).catch(($, e, next) => next(e))
}
