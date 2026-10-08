# memory-vault-sync

> A skill for syncing, verifying, and slimming a personal memory vault across QClaw / WorkBuddy / Obsidian — plus two companion MCP servers (Mem0 shared memory and Obsidian vault access).

## Introduction

This is a Skill repository for WorkBuddy / CodeBuddy / Claude Code. It solves the multi-device consistency problem for personal AI memory files: core profiles (MEMORY.md / USER.md / SOUL.md), daily journals, and "dreaming" records live in three places at once — QClaw, WorkBuddy, and an Obsidian vault — and need syncing, verification, and occasional slimming.

The skill distills a real acceptance session: a migration that was *reported* as done turned out to have 3 bugs when actually tested (one journal entry missing, the Obsidian half never executed at all, the index file nonexistent). Afterwards, a bloated 57KB MEMORY.md was split by topic into 5 files, bringing the main file down to 15.8KB. The core rule: **a report is not a result — verify everything yourself**.

**Trigger words**: 同步记忆, 迁移记忆, 检查迁移, 记忆库验收, MEMORY.md 太大, 记忆拆分, 瘦身记忆, 同步到 Obsidian (sync memory, migrate memory, verify migration, memory vault acceptance, MEMORY.md too large, split memory, slim memory, sync to Obsidian).

## Features

- **Three-way sync with md5 verification** — the standard move: `cp` files to the QClaw workspace, `.workbuddy`, and Obsidian's `01-长期记忆`, then run a three-way md5 comparison. Copying without verifying doesn't count.
- **Four-step migration acceptance** — ① `ls` the target directory first to confirm it actually exists (the most commonly faked step); ② count files (list *all* `.md` files and eyeball the total — a regex like `^2026-.*\.md$` silently skips non-standard names such as `20260628.md`); ③ compare content by md5, never by file size; ④ confirm index files exist and their entry counts match reality.
- **MEMORY.md topic-based slimming** — the system auto-loads MEMORY.md into every session; beyond ~40KB it gets truncated (`user memory truncated`, so trailing sections may as well not exist). Keep persona/identity/preferences/red-lines in the main file; split project logs, pitfalls, and deployment records into satellite files. The main file must open with a navigation table stating *when to read* each satellite — otherwise everything gets loaded at once and the split was pointless.
- **Line-number precise slicing** — matching Chinese headings with regex is error-prone. Read the full file, capture line numbers, print boundary lines for confirmation, then slice (`slc(a, b)`, 1-indexed, inclusive). After splitting, run a zero-loss check: every non-empty line of the backup must appear in the merged result; missing lines must be exactly 0.
- **Mandatory backups before touching anything** — keep a `.bak-<timestamp>` copy in each of the three locations before splitting or overwriting. If the user later asks to delete a satellite file, first prove its content exists 100% in the backup, then annotate the navigation table with where it was archived.
- **Dreaming-record migration** — QClaw's sleep-cycle memory jobs generate deep/light/rem entries daily. When migrating to Obsidian, create a numbered `03-梦境\` directory and generate an index; afterwards, scan for dead wikilinks (write dates as plain text — date columns pointing at nonexistent root-level files become dead links).
- **Unified encoding discipline** — memory files carry a UTF-8 BOM; always read/write with `utf-8-sig` (reading strips the BOM so summary extraction doesn't break; writing keeps it for Windows compatibility).

## How It Works / Tech Stack

- **Skill mechanics**: the core is `SKILL.md` (trigger words plus the full operating procedure). On a trigger match, the AI follows the spec: locate paths, back up, sync, md5-verify, slice by line numbers, and run zero-loss checks.
- **Obsidian vault location**: never guess the path — find it with `find ~ -maxdepth 6 -type d -name ".obsidian"`; the `.obsidian` directory is the definitive vault marker.
- **Companion MCP servers** (`mcp/` directory, two stdio servers):
  - **mem0-shared-memory** — a multi-agent shared memory layer built on `mem0ai`: an LLM (via a custom gateway) extracts memories, a local bge-small-zh-v1.5 Chinese embedding model provides vectors, and ChromaDB stores them locally. `user_id` defines the shared space (all agents under the same user_id share everything); `agent_id` records provenance without isolating reads. Secrets live only in environment variables (`MEM0_LLM_API_KEY` / `MEM0_LLM_BASE_URL` / `MEM0_LLM_MODEL`) — never in source. Exposes MCP tools `remember` / `recall` / `list_memories` / `forget` / `update_memory`, plus a `mem.py` CLI (add / search / list / delete / update).
  - **obsidian-vault** — pure standard library (Python 3.10+, zero dependencies); reads and writes the local Obsidian vault's `.md` files directly.

## Installation & Usage

**Skill install**: copy this repository's contents into your skills directory, keeping the folder name `memory-vault-sync`:

- WorkBuddy / CodeBuddy: `~/.workbuddy/skills/memory-vault-sync/`
- Claude Code: `~/.claude/skills/memory-vault-sync/`

Restart your session and the skill will match via its trigger words.

**MCP setup**: add two stdio server entries under `mcpServers` in `~/.workbuddy/mcp.json` (or your Claude MCP config), pointing at `mcp/mem0-shared-memory/memory_mcp_server.py` and `mcp/obsidian-vault/obsidian_vault_mcp.py` — full JSON examples are in `mcp/README.md`. Restart the session to load them. The mem0 server requires your own LLM gateway credentials via environment variables.

## Project Structure

```
memory-vault-sync/
├── README.md                        # Chinese documentation
├── README_EN.md                     # This file
├── SKILL.md                         # Skill core: paths, acceptance flow, splitting & zero-loss checks, pitfalls
├── .gitignore
└── mcp/                             # Companion MCP server sources
    ├── README.md                    # MCP setup and dependency notes
    ├── Agent接入提示词.md            # Agent-side onboarding prompt (Chinese)
    ├── mem0-shared-memory/          # Mem0 shared memory (MCP server + CLI)
    │   ├── memory_mcp_server.py
    │   ├── mem.py
    │   └── README.md
    └── obsidian-vault/              # Obsidian vault MCP (pure stdlib)
        ├── obsidian_vault_mcp.py
        └── obs.py
```

## Notes

- Data files (memory database, vector indexes) are not distributed with the repo; mem0 creates them on first run and downloads the ~95MB Chinese embedding model (via a HuggingFace mirror).
- During acceptance, never trust a report: `ls` the target directory, count files, md5-compare, then audit the index entry count — in that order.
- Regex-based filtering of journal filenames is unreliable (non-hyphenated names exist); always list everything and confirm the total manually.
- Keep the UTF-8 BOM — do not convert to BOM-less files (consistency with existing behavior and Windows compatibility).
- After splitting, the system only auto-loads the main file; satellite files are not loaded automatically — the navigation table is not optional.

## License

MIT

## Author

sheen945
