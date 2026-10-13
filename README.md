# Pytho-inator

An agent skill that turns a repeated, deterministic chore into one free local Python CLI. The agent runs one command and reads the last line. It does not re-think the steps.

Portuguese: [README.pt-BR.md](README.pt-BR.md).

The procedure the agent follows is [`skills/pytho-inator/SKILL.md`](skills/pytho-inator/SKILL.md). This page is the human contract.

## Why

A skill that spells five shell commands spends tokens every time an agent reads it, and the agent can still drop a step. A CLI that finishes the task spends one command. That is the whole point of this repo. If one command can do the job, the skill shrinks to that command.

The scanner does not make that decision. It prints a short hint. The agent drops menus (`fan-out`) and anything that is taste, approval, voice, or strategy (`judgment=keep`).

## End of an answer

**Claude Code.** Install the mod in the section below. After a turn that saved a file with Write or Edit, it runs `glance` and shows the hint under the answer. That text is not another model turn. Empty `glance` stays silent. An aborted turn drops the paths. A subagent stays quiet; the main answer sees the files it wrote.

**Every other agent** runs:

```bash
./pytho-inator glance path/to/file.md
```

Empty stdout means silence. A hit is at most three lines and the question "do you want this built?". It does not build in that same turn. When the Claude Code mod is on, do not run `glance` again.

Wire that sentence into the project's always-on instructions (for this social project, `CLAUDE.md`). A skill description alone will not fire after every answer.

## Commands

| Command | What the agent does |
|---|---|
| `/map-automation-opportunities` | `pytho-inator map`. Where a new CLI can replace a chain. |
| `/check-skills` | `pytho-inator check`. Where an existing skill can shrink to one command. |

Both commands stop before writing code. Building starts only after a yes, and then follows [`skills/pytho-inator/references/gates.md`](skills/pytho-inator/references/gates.md).

## The CLI

Stdlib only. No API key. `uv` runs it; `python3` is the fallback.

```bash
./pytho-inator map [root]       # ranked hints, default 5
./pytho-inator check [root]     # per-skill insertion points
./pytho-inator glance [files]   # silent unless a touched file hides a chain
./pytho-inator vet name [name]  # license, version, date from the PyPI JSON API
./pytho-inator self-check       # offline asserts
```

`map` and `check` look at `.claude/skills`, `.claude/commands`, `skills/`, and `commands/`. They do not walk the rest of the tree. `glance` with no paths uses `git status` and only changed skill or command files. It prints nothing when there is no repo, or no such change. Pass paths when the chore lives in another file.

`vet` prints `ok` or `check`. `quiet-Nd` means the latest upload is older than 24 months; a known license is still `ok`. `check` means a missing license, a yanked release, or a PyPI error. Look before depending.

## Rules for anything it builds

- **Ponytail ultra** at the moment the CLI is written. Read the installed ponytail skill and set intensity to ultra (`/ponytail ultra` on Claude Code) before the first line. Standard library first. One file. No framework. The short ladder in `gates.md` is only the fallback when that skill is missing.
- **uv** for the interpreter and for third-party installs, in that tool's own venv. Never the system Python.
- **Free and open source.** Prefer MIT, Apache, or BSD when two libraries fit.
- **Ask before any paid API**, keyed service, or account that can bill. Free tier with a credit card counts as paid. Wait for a yes.
- **Ask before testing** what was just written, including its self-check.
- **Automate the Boring Stuff with Python** (Al Sweigart, free edition) is the catalog of chores: files, text, CSV, JSON, spreadsheets, PDF, Word, images, web pages, time, email, GUI. The book names the chore. It is not a dependency list, and its text is not copied here. The map is in [`gates.md`](skills/pytho-inator/references/gates.md).
- Library lookup is a free web search plus `vet`. Do not spend a paid research pipeline to pick a package name.

## Install

```bash
git clone https://github.com/SafeMantella/Pytho-inator.git
chmod +x Pytho-inator/pytho-inator
```

From the project the agent works in, symlink the skill and the two commands (one copy, no drift):

```bash
ln -s /path/to/Pytho-inator/skills/pytho-inator .claude/skills/pytho-inator
ln -s /path/to/Pytho-inator/commands/map-automation-opportunities.md .claude/commands/
ln -s /path/to/Pytho-inator/commands/check-skills.md .claude/commands/
```

Opening this repo on its own also loads them: `.claude/` inside the repo points at the same files.

### Claude Code mod

The plugin root is this repo. The hook calls `./pytho-inator glance`. Installing it edits Claude Code's project settings, so do that only when you want it on.

From a local clone:

```bash
claude plugin marketplace add ./Pytho-inator --scope project
claude plugin install pytho-inator@pytho-inator --scope project
```

Once this repo is on GitHub, Claude Code 2.1.275 or later also accepts:

```
/plugin install pytho-inator --marketplace SafeMantella/Pytho-inator
```

Check without installing, from inside the repo: `claude plugin validate . && claude plugin test .`.

## Layout

```
pytho-inator          wrapper (uv, then python3)
pytho_inator.py       the scanner
hooks/register.ts     Claude Code mod
.claude-plugin/       plugin and marketplace manifests
skills/pytho-inator/  the agent skill
commands/             /map-automation-opportunities and /check-skills
```

## License

MIT. See [LICENSE](LICENSE).
