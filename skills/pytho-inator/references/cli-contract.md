<!-- pytho-inator: skip -->

# CLI contract

One command in. The task done. The last stdout line is the result the agent needs (a path, a count, or `ok`). Exit 0 means done. Exit 1 means one line on stderr.

The agent does not re-read the inputs, re-decide the middle steps, or paste a transcript back into the prompt. If the CLI cannot finish the task, it is the wrong CLI. Do not split a finished task across a "prepare" command and a "render" command the agent has to chain.

## What gets built

- A chain: the output of one step is the input of the next, and nothing in between needs taste or approval.
- Code lives in one file. Third-party installs go in that tool's own `uv` venv, never in the system interpreter.
- The skill that used to spell the steps shrinks to the command, the inputs, and the line it prints. Judgment stays in the skill as a sentence, not as a second procedure.
- A new chore with no skill gets a short skill whose body is that command. Do not add a README for it unless the user asks.

## What does not

- `shape=fan-out`: a menu of unrelated tools (search here, then search somewhere else). Leave the menu.
- `judgment=keep`: approval, voice, hook, strategy, interview. The CLI may prepare the material. The agent still judges.
- A single shell command that already finishes the job. That is already the CLI.
- Anything that sends, deletes, publishes, pays, or writes outside the project. Default those to a dry-run and ask before a real run.

## Suggestion shape

Three lines, then stop:

1. The repeated chain, in one sentence.
2. The command the agent will run later, and the last stdout line.
3. `Quer que eu construa esse CLI?`

Do not build in the same turn as the suggestion.
