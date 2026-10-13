#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Point at workflow steps one local Python CLI can finish.

The scanner is a hint. It does not decide, install, or run the user's task.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

SKIP_MARKER = "pytho-inator: skip"
SKIP_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    "downloads",
    "transcripts",
    "site-packages",
    ".ruff_cache",
}
TEXT_SUFFIXES = {".md", ".txt", ".py", ".sh", ".bash"}
# ponytail: skip files over 200k chars; raise this if a real skill is larger.
MAX_CHARS = 200_000
QUIET_DAYS = 730
UA = "pytho-inator/0.1 (+https://github.com/SafeMantella/Pytho-inator)"

FENCE_RE = re.compile(r"```(?:bash|sh|shell|zsh|console)\s*\n(.*?)```", re.I | re.S)
INLINE_RE = re.compile(r"`((?:python3?|uv|ffmpeg|ffprobe|yt-dlp|git|sox|magick)\b[^`]*)`")
JUDGMENT_RE = re.compile(
    r"aprova|julg|tom de voz|entrevist|criativ|estrat[eé]gi|approv|judgment|judgement",
    re.I,
)
FILE_RE = re.compile(
    r"[\w./@+-]+\.(?:py|md|mp4|json|txt|wav|csv|png|jpg|jpeg|srt|mp3|tsv|html|xml|yaml|yml)"
)
LICENSE_TOKENS = (
    "mit",
    "apache",
    "bsd",
    "isc",
    "mpl",
    "gpl",
    "lgpl",
    "psf",
    "hpnd",
    "unlicense",
    "zlib",
    "artistic",
    "python",
    "0bsd",
    "agpl",
)
PREFERRED = (".claude/skills", ".claude/commands", "skills", "commands")


@dataclass
class Opp:
    path: Path
    cmds: list[str]
    judgment: bool
    heading: str
    shape: str


SHELL_WORDS = {"if", "then", "else", "elif", "fi", "do", "done", "esac", "in", "case"}
HEREDOC_RE = re.compile(r"<<-?\s*['\"]?(\w+)['\"]?")


def is_command(line: str) -> bool:
    parts = line.split()
    while parts and "=" in parts[0] and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", parts[0]):
        parts.pop(0)
    if not parts:
        return False
    word = parts[0]
    if word in SHELL_WORDS:
        return False
    if word.startswith(("./", "/", "~/", "../")):
        return " " in line or "/" in word
    if "@" in word or not re.match(r"^[a-z][\w.+-]*$", word):
        return False
    return " " in line


def command_lines(block: str) -> list[str]:
    out: list[str] = []
    buf = ""
    heredoc_end: str | None = None
    for raw in block.splitlines():
        if heredoc_end is not None:
            if raw.strip() == heredoc_end:
                heredoc_end = None
            continue
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        if s.startswith("$"):
            s = s[1:].strip()
        if not s:
            continue
        marker = HEREDOC_RE.search(s)
        if "<<" in s and marker:
            heredoc_end = marker.group(1)
        if s.endswith("\\"):
            buf += s[:-1].rstrip() + " "
            continue
        buf += s
        line = " ".join(buf.split())
        buf = ""
        if is_command(line):
            out.append(line)
    if buf.strip():
        line = " ".join(buf.split())
        if is_command(line):
            out.append(line)
    return out


def heading_for(text: str, index: int) -> str:
    prev = ""
    for line in text[:index].splitlines():
        if line.startswith("#"):
            prev = line.lstrip("#").strip()
    return prev or "(top)"


PLACEHOLDER_RE = re.compile(r"<[^>\s]+>")


def shape_of(cmds: list[str]) -> str:
    sets: list[set[str]] = []
    for cmd in cmds:
        parts = cmd.split()
        while parts and "=" in parts[0] and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", parts[0]):
            parts.pop(0)
        args = " ".join(parts[1:]) if len(parts) > 1 else ""
        tokens = {item.lower() for item in FILE_RE.findall(cmd) if len(item) >= 5}
        tokens.update(item.lower() for item in PLACEHOLDER_RE.findall(args))
        sets.append(tokens)
    linked = sum(1 for left, right in zip(sets, sets[1:]) if left & right)
    return "chain" if linked else "fan-out"


def unique(cmds: list[str]) -> list[str]:
    seen: list[str] = []
    for cmd in cmds:
        if cmd not in seen:
            seen.append(cmd)
    return seen


def analyze(text: str, path: Path) -> Opp | None:
    if SKIP_MARKER in text:
        return None
    text = text.replace("\r\n", "\n")
    cmds: list[str] = []
    first_at: int | None = None
    for match in FENCE_RE.finditer(text):
        lines = command_lines(match.group(1))
        if lines and first_at is None:
            first_at = match.start()
        cmds.extend(lines)
    cmds = unique(cmds)
    if len(cmds) < 2:
        outside = FENCE_RE.sub("", text)
        inlines = [item for item in unique(cmd.strip() for cmd in INLINE_RE.findall(outside)) if is_command(item)]
        if len(inlines) < 2:
            return None
        cmds = inlines
        first_at = text.find(inlines[0])
    if shape_of(cmds) == "fan-out" and len(cmds) < 3:
        return None
    return Opp(
        path=path,
        cmds=cmds,
        judgment=bool(JUDGMENT_RE.search(text)),
        heading=heading_for(text, first_at or 0),
        shape=shape_of(cmds),
    )


def is_target(path: Path) -> bool:
    if path.name == "SKILL.md":
        return True
    return path.suffix == ".md" and "commands" in path.parts


def walk_files(base: Path, max_depth: int | None):
    base = base.resolve()
    for dirpath, dirnames, filenames in os.walk(base, followlinks=False):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and d != ".git"]
        if max_depth is not None:
            depth = len(Path(dirpath).resolve().relative_to(base).parts)
            if depth >= max_depth:
                dirnames[:] = []
        for name in filenames:
            yield Path(dirpath) / name


def collect(root: Path) -> list[Path]:
    root = root.expanduser().resolve()
    if root.is_file():
        return [root] if root.suffix.lower() in TEXT_SUFFIXES else []
    preferred = [root / rel for rel in PREFERRED if (root / rel).is_dir()]
    bases = preferred or [root]
    max_depth = None if preferred else 3
    found: list[Path] = []
    seen: set[Path] = set()
    for base in bases:
        paths = [base] if base.is_file() else walk_files(base, max_depth)
        for path in paths:
            if not path.is_file() or not is_target(path):
                continue
            if any(part in SKIP_DIRS for part in path.parts):
                continue
            resolved = path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            found.append(path)
    return found


def read_text(path: Path) -> str | None:
    if path.suffix.lower() not in TEXT_SUFFIXES:
        return None
    if path.stat().st_size > MAX_CHARS:
        return None
    return path.read_text(encoding="utf-8", errors="replace")


def scan(paths: list[Path]) -> tuple[list[Opp], int]:
    opps: list[Opp] = []
    scanned = 0
    for path in paths:
        text = read_text(path)
        if text is None:
            continue
        scanned += 1
        opp = analyze(text, path)
        if opp:
            opps.append(opp)
    return opps, scanned


def rank_key(opp: Opp) -> tuple[int, int]:
    return (1 if opp.shape == "chain" else 0, len(opp.cmds))


def show(path: Path, cwd: Path) -> str:
    try:
        return str(path.resolve().relative_to(cwd.resolve()))
    except ValueError:
        return str(path)


def clip(text: str, limit: int = 110) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def format_hit(index: int | None, opp: Opp, cwd: Path) -> str:
    name = opp.path.parent.name if opp.path.name == "SKILL.md" else opp.path.stem
    prefix = f"{index}  " if index else ""
    judgment = "keep" if opp.judgment else "none"
    lines = [
        f"{prefix}{name}  cmds={len(opp.cmds)}  {opp.shape}  judgment={judgment}  {show(opp.path, cwd)}",
        f"   under: {opp.heading}",
    ]
    for cmd in opp.cmds[:3]:
        lines.append(f"   $ {clip(cmd)}")
    extra = len(opp.cmds) - 3
    if extra > 0:
        lines.append(f"   +{extra} more")
    lines.append("   cli: one local command, finished path on the last stdout line, exit 0")
    return "\n".join(lines)


def format_report(kind: str, opps: list[Opp], scanned: int, cwd: Path, limit: int) -> str:
    ranked = sorted(opps, key=rank_key, reverse=True)
    shown = ranked[:limit]
    header = f"{kind}  scanned={scanned}  hits={len(ranked)}"
    if len(ranked) > limit:
        header += f"  showing={limit}"
    lines = [header]
    numbered = kind == "map"
    for i, opp in enumerate(shown, 1):
        lines.append(format_hit(i if numbered else None, opp, cwd))
    return "\n".join(lines) + "\n"


def git_changed(cwd: Path) -> list[Path]:
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain", "-uall"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=8,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    if result.returncode != 0:
        return []
    found: list[Path] = []
    for line in result.stdout.splitlines():
        if len(line) < 4:
            continue
        rel = line[3:].strip()
        if " -> " in rel:
            rel = rel.split(" -> ", 1)[1]
        path = cwd / rel
        if path.is_file() and is_target(path):
            found.append(path)
        if len(found) >= 30:
            break
    return found


def known_license(license_name: str) -> bool:
    low = license_name.lower()
    return any(token in low for token in LICENSE_TOKENS)


def license_of(info: dict) -> str:
    expression = (info.get("license_expression") or "").strip()
    if expression:
        return expression
    classifiers = info.get("classifiers") or []
    osi = [item for item in classifiers if item.startswith("License ::") and "OSI Approved" in item]
    if osi:
        return osi[-1].split("::")[-1].strip()
    raw = (info.get("license") or "").strip()
    if not raw:
        return ""
    return raw if len(raw) <= 60 else raw[:59] + "…"


def verdict(license_name: str, yanked: bool, uploaded: str, today: datetime) -> tuple[str, str]:
    notes: list[str] = []
    if yanked:
        notes.append("yanked")
    if not license_name or not known_license(license_name):
        notes.append("license-unknown")
    if uploaded:
        try:
            age = (today.date() - datetime.fromisoformat(uploaded).date()).days
        except ValueError:
            notes.append("bad-date")
        else:
            if age > QUIET_DAYS:
                notes.append(f"quiet-{age}d")
    else:
        notes.append("no-date")
    status = "ok" if license_name and known_license(license_name) and not yanked else "check"
    return status, ",".join(notes) if notes else "-"


def newest_upload(data: dict) -> str:
    version = data["info"]["version"]
    files = data.get("releases", {}).get(version) or []
    times = [item.get("upload_time") or "" for item in files]
    times = [item for item in times if item]
    return max(times)[:10] if times else ""


def package_name(raw: str) -> str:
    return re.split(r"[<>=!\[]", raw.strip(), maxsplit=1)[0].strip()


def fetch_pypi(name: str) -> dict:
    url = f"https://pypi.org/pypi/{name}/json"
    request = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=15) as response:
        return json.load(response)


def vet_line(raw_name: str, today: datetime) -> str:
    name = package_name(raw_name)
    if not name:
        return "check  (empty)  HTTP 0"
    try:
        data = fetch_pypi(name)
    except urllib.error.HTTPError as exc:
        return f"check  {name}  HTTP {exc.code}"
    except Exception as exc:  # network and JSON failures stay one line
        return f"check  {name}  {type(exc).__name__}"
    info = data["info"]
    files = data.get("releases", {}).get(info["version"]) or []
    yanked = bool(info.get("yanked")) or any(item.get("yanked") for item in files)
    license_name = license_of(info)
    uploaded = newest_upload(data)
    status, notes = verdict(license_name, yanked, uploaded, today)
    urls = info.get("project_urls") or {}
    url = ""
    for key in ("Source", "Homepage", "Repository"):
        if urls.get(key):
            url = urls[key]
            break
    url = url or info.get("home_page") or info.get("project_url") or ""
    return f"{status}  {info['name']}  {info['version']}  {uploaded or '-'}  {license_name or '-'}  {notes}  {url}"


def self_check() -> int:
    fails: list[str] = []

    def expect(cond: bool, msg: str) -> None:
        if not cond:
            fails.append(msg)

    chain_text = """# Demo

## Run

```bash
python3 a.py clip.mp4 -o audio.wav
python3 b.py audio.wav -o out.json
```

Aprovar o tom antes de publicar.
"""
    chain = analyze(chain_text, Path("skills/demo/SKILL.md"))
    expect(chain is not None and len(chain.cmds) == 2, "two shell commands")
    expect(chain is not None and chain.judgment, "judgment flag")
    expect(chain is not None and chain.heading == "Run", "heading")
    expect(chain is not None and chain.shape == "chain", "shared file is a chain")

    continued = """```bash
python3 a.py clip.mp4 \\
  -o audio.wav
python3 b.py audio.wav -o out.json
```
"""
    joined = analyze(continued, Path("skills/demo/SKILL.md"))
    expect(joined is not None and len(joined.cmds) == 2, "backslash continuation")
    expect(joined is not None and joined.cmds[0].endswith("audio.wav"), "joined argv")

    one = "```bash\npython3 a.py clip.mp4 -o audio.wav\n```\n"
    expect(analyze(one, Path("skills/demo/SKILL.md")) is None, "one command stays")

    prose = "# Notes\n\nDecide the tone and approve it.\n"
    expect(analyze(prose, Path("skills/demo/SKILL.md")) is None, "prose stays")

    skipped = "<!-- pytho-inator: skip -->\n```bash\npython3 a.py x.wav\npython3 b.py x.wav\n```\n"
    expect(analyze(skipped, Path("skills/demo/SKILL.md")) is None, "skip marker")

    fan_text = """```bash
python3 tools/topic.py --topic alpha
ffmpeg -i other.mp4 -vn only.wav
yt-dlp "https://example.test/v"
```
"""
    fan = analyze(fan_text, Path("skills/fan/SKILL.md"))
    expect(fan is not None and fan.shape == "fan-out", "unrelated commands are fan-out")
    expect(chain is not None and fan is not None and rank_key(chain) > rank_key(fan), "chain ranks first")

    inline = "Run `python3 a.py clip.mp4 -o audio.wav` then `python3 b.py audio.wav -o out.json`.\n"
    inline_opp = analyze(inline, Path("skills/demo/SKILL.md"))
    expect(inline_opp is not None and inline_opp.shape == "chain", "inline commands count")

    heredoc = """```bash
python3 ferramentas/a.py clip.mp4 -o audio.wav <<'EOF'
Você é a coleta.
Não escreva RESUMO.
EOF
python3 ferramentas/b.py audio.wav -o out.json
```
"""
    heredoc_opp = analyze(heredoc, Path("skills/demo/SKILL.md"))
    expect(heredoc_opp is not None and len(heredoc_opp.cmds) == 2, "heredoc body is not a command")
    expect(heredoc_opp is not None and all("Você" not in cmd for cmd in heredoc_opp.cmds), "prose dropped")

    scraps = """```bash
git@github.com:SafeMantella/arfux.ai-website-repo.git
ffprobe
```
"""
    expect(analyze(scraps, Path("skills/demo/SKILL.md")) is None, "urls and bare words are not a chain")

    mention = """```bash
ffmpeg -ss 1 -i base.mp4 -frames:v 1 out.png
```
Check `ffprobe` for the duration.
"""
    expect(analyze(mention, Path("skills/demo/SKILL.md")) is None, "a bare mention is not a second step")

    two_fan = """```bash
python3 tools/topic.py --topic alpha
ffmpeg -i other.mp4 -vn only.wav
```
"""
    expect(analyze(two_fan, Path("skills/demo/SKILL.md")) is None, "two unrelated commands are not a chain")

    git_chain = """```bash
git -C <pasta> rev-parse --is-inside-work-tree
git -C <pasta> fetch --quiet
git -C <pasta> pull --ff-only
```
"""
    git_opp = analyze(git_chain, Path("commands/atualizar.md"))
    expect(git_opp is not None and git_opp.shape == "chain", "shared placeholder is a chain")

    expect(known_license("MIT License"), "MIT")
    expect(known_license("Apache-2.0"), "Apache")
    expect(not known_license(""), "empty license")
    status, notes = verdict("MIT", False, "2024-06-28", datetime(2026, 10, 13))
    expect(status == "ok" and notes.startswith("quiet-"), f"quiet MIT stays ok ({status} {notes})")
    status, notes = verdict("", False, "2026-01-01", datetime(2026, 10, 13))
    expect(status == "check" and "license-unknown" in notes, "missing license")
    status, notes = verdict("MIT", True, "2026-01-01", datetime(2026, 10, 13))
    expect(status == "check" and "yanked" in notes, "yanked")

    expect(format_report("glance", [], 0, Path("."), 5).startswith("glance"), "report header")
    expect(not format_glance([], Path(".")), "empty glance is silent")

    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        skill = root / ".claude" / "skills" / "demo" / "SKILL.md"
        skill.parent.mkdir(parents=True)
        skill.write_text(chain_text, encoding="utf-8")
        command = root / ".claude" / "commands" / "noise.md"
        command.parent.mkdir(parents=True)
        command.write_text(fan_text, encoding="utf-8")
        big = root / "downloads" / "skip.md"
        big.parent.mkdir()
        big.write_text(chain_text, encoding="utf-8")
        found = collect(root)
        opps, scanned = scan(found)
        expect(scanned == 2, f"skips downloads ({scanned})")
        expect(len(opps) == 2, "finds skill and command")
        report = format_report("map", opps, scanned, root, 5)
        expect("demo" in report and report.index("demo") < report.index("noise"), "chain listed first")

    if fails:
        print("\n".join(f"FAIL {item}" for item in fails))
        return 1
    print("self-check ok")
    return 0


def format_glance(opps: list[Opp], cwd: Path) -> str:
    if not opps:
        return ""
    best = max(opps, key=rank_key)
    return format_hit(None, best, cwd) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="pytho-inator",
        description="Find steps one free local Python CLI can finish. Prints a short hint and stops.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    map_cmd = sub.add_parser("map", help="rank skills and commands that can collapse into one CLI")
    map_cmd.add_argument("root", nargs="?", default=".")
    map_cmd.add_argument("--limit", type=int, default=5)

    check_cmd = sub.add_parser("check", help="show where an existing skill can shrink to one CLI")
    check_cmd.add_argument("root", nargs="?", default=".")
    check_cmd.add_argument("--limit", type=int, default=20)

    glance_cmd = sub.add_parser("glance", help="silent unless a touched file hides one CLI")
    glance_cmd.add_argument("paths", nargs="*")

    vet_cmd = sub.add_parser("vet", help="license, version, and age from the PyPI JSON API")
    vet_cmd.add_argument("names", nargs="+")

    sub.add_parser("self-check", help="offline asserts")
    args = parser.parse_args(argv)
    cwd = Path.cwd()

    if args.cmd == "self-check":
        return self_check()

    if args.cmd == "vet":
        today = datetime.now()
        lines = [vet_line(name, today) for name in args.names]
        sys.stdout.write("\n".join(lines) + "\n")
        return 0 if all(line.startswith("ok ") for line in lines) else 1

    if args.cmd == "glance":
        if args.paths:
            files: list[Path] = []
            for raw in args.paths:
                path = Path(raw).expanduser()
                if not path.exists():
                    print(f"missing {raw}", file=sys.stderr)
                    return 1
                files.extend(collect(path) if path.is_dir() else [path.resolve()])
        else:
            files = git_changed(cwd)
        opps, _ = scan(files)
        sys.stdout.write(format_glance(opps, cwd))
        return 0

    root = Path(args.root)
    if not root.exists():
        print(f"missing {args.root}", file=sys.stderr)
        return 1
    files = collect(root)
    opps, scanned = scan(files)
    sys.stdout.write(format_report(args.cmd, opps, scanned, cwd, args.limit))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
