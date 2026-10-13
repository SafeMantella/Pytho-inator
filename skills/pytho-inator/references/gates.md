<!-- pytho-inator: skip -->

# Gates

Read this only when the user has agreed to a build. Follow this order. Do not skip a step.

## 1. Ponytail, intensity ultra

Before the first line of the CLI, read the installed `ponytail` skill from start to finish and apply intensity **ultra** until the file exists. On Claude Code, `/ponytail ultra`. Ultra is that skill's YAGNI-extremist row: deletion before addition, ship the one-liner, and challenge the rest of the requirement in the same breath. Its ladder, its rules, its `ponytail:` comment, and its one self-check all apply. Do not run the self-check until the user says yes.

The rungs below are only for a machine where that skill is not installed. Say so in one line, then stop at the first rung that holds:

1. Speculative need: do not build it. Say so in one line.
2. A script in this repo already does it: call that.
3. The standard library does it: use it.
4. A dependency already installed in the tool's venv does it: use it.
5. Otherwise one file, argparse, no config, no plugin system, no framework.

Ship that and name what you did not build. Mark a real ceiling with a `ponytail:` comment and the upgrade path. Leave one `--self-check` of asserts in the file. Do not run it until the user says yes.

Do not simplify away validation on untrusted input, or a failure that would destroy data.

## 2. The book is the task list

*Automate the Boring Stuff with Python* (Al Sweigart, https://automatetheboringstuff.com) is the catalog of chores worth a program: files, folders, search-and-replace, CSV, JSON, Excel, PDF, Word, images, web pages, time, email, GUI clicking. Do not copy the book's text. Do not install a library because a chapter imports it. The chapter names the chore. The rung above picks the library.

| Chore (book) | Use this | After `vet`, only if the stdlib loses |
|---|---|---|
| Files, move/copy/rename, zip (ch. 9–10) | `pathlib`, `shutil`, `zipfile` | |
| Find and replace text, patterns (ch. 6–7) | `pathlib`, `re` | |
| CSV, JSON, time (ch. 16–17) | `csv`, `json`, `datetime` | |
| SQLite | `sqlite3` | |
| HTML | `html.parser` | `beautifulsoup4` |
| HTTP fetch | `urllib.request` | |
| Excel (ch. 13) | | `openpyxl` |
| PDF, Word (ch. 15) | | `pypdf`, `python-docx` |
| Images (ch. 19) | | `pillow` |
| Google Sheets, Gmail, SMS (ch. 14, 18) | ask with the paid question in the skill | |
| Schedule, launch a program (ch. 17) | `launchd` or cron | |
| Keyboard and mouse (ch. 20) | ask; prefer a real CLI | `pyautogui` only if they insist |

A quiet library (`quiet-Nd` from `vet`, older than 24 months) with a known license is still fine. Say the age. `check` means stop and look: missing license, yanked, or PyPI error.

## 3. Find a library

1. If the table's first cell is the standard library, stop. No search.
2. Otherwise web-search `<chore> python pypi` and keep two or three names. Use the free web search. Do not run `/pesquisar`, Grok, last30days, or any paid search to pick a package.
3. Run `pytho-inator vet name1 name2 name3`. It calls the public PyPI JSON API. No key.
4. Prefer `ok`, then MIT / Apache / BSD when the fit is equal, then a source URL, then the library that finishes the whole chore.
5. If every option needs an API key or an account that can bill, ask the question in the skill. Do not install it while you ask.
6. Install with uv into that tool's venv only:

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python <package>
```

Never `pip install` into the system Python.

## 4. Then ask to test

Write the file. Do not run it, including `--self-check`, until the user answers the test question in the skill.
