import { expect, test } from 'claude-code/testing'

const turn = (extra = {}) => ({
  turnId: 't',
  answer: 'feito',
  durationMs: 1,
  isAborted: false,
  usage: null,
  ...extra,
})

test('turno sem arquivo não chama o scanner', async ($, on) => {
  let ran = false
  on('tool.call', () => ({ result: 'ok' }))
  on('process.run', () => {
    ran = true
    return { value: { exitCode: 0, stdout: '', stderr: '' } }
  })
  on('turn.complete', () => ({ text: 'feito' }))
  const done = await $.turn.complete(turn())
  expect(ran).toBe(false)
  expect(done.text).toBe('feito')
})

test('Write gravado: a linha debaixo da resposta é a saída do glance', async ($, on) => {
  const argv: string[][] = []
  on('tool.call', () => ({ result: 'ok' }))
  on('process.run', (_$, e) => {
    argv.push(e.argv)
    return { value: { exitCode: 0, stdout: 'demo  cmds=2  chain\n', stderr: '' } }
  })
  on('turn.complete', () => ({ text: 'feito' }))
  await $.tool.call({ tool: 'Write', file_path: '/work/skills/demo/SKILL.md' })
  const done = await $.turn.complete(turn())
  expect(argv).toHaveLength(1)
  expect(argv[0][1]).toBe('glance')
  expect(argv[0]).toContain('/work/skills/demo/SKILL.md')
  expect(done.text).toContain('demo  cmds=2  chain')
  expect(done.text).toContain('Quer que eu construa esse CLI?')
})

test('Write recusado e turno abortado ficam calados', async ($, on) => {
  let ran = false
  on('tool.call', () => ({ deny: 'não' }))
  on('process.run', () => {
    ran = true
    return { value: { exitCode: 0, stdout: 'x', stderr: '' } }
  })
  on('turn.complete', () => ({ text: 'feito' }))
  await $.tool.call({ tool: 'Write', file_path: '/work/a.md' })
  await $.turn.complete(turn())
  await $.turn.complete(turn({ isAborted: true }))
  expect(ran).toBe(false)
})

test('Write gravado e turno abortado não varre no turno seguinte', async ($, on) => {
  let ran = false
  on('tool.call', () => ({ result: 'ok' }))
  on('process.run', () => {
    ran = true
    return { value: { exitCode: 0, stdout: 'x', stderr: '' } }
  })
  on('turn.complete', () => ({ text: '' }))
  await $.tool.call({ tool: 'Write', file_path: '/work/a.md' })
  await $.turn.complete(turn({ isAborted: true }))
  await $.turn.complete(turn())
  expect(ran).toBe(false)
})

test('subagente não fala; o turno principal vê o arquivo que ele gravou', async ($, on) => {
  const argv: string[][] = []
  on('tool.call', () => ({ result: 'ok' }))
  on('process.run', (_$, e) => {
    argv.push(e.argv)
    return { value: { exitCode: 0, stdout: '', stderr: '' } }
  })
  on('turn.complete', () => ({ text: '' }))
  await $.tool.call({ tool: 'Edit', file_path: '/work/b.md' })
  await $.turn.complete(turn({ agentId: 'sub' }))
  expect(argv).toHaveLength(0)
  await $.turn.complete(turn())
  expect(argv).toHaveLength(1)
  expect(argv[0]).toContain('/work/b.md')
})
