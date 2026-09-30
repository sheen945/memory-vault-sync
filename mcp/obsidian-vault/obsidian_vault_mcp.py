# -*- coding: utf-8 -*-
"""
Obsidian 主知识库 MCP 服务器
============================
把唯一主库 D:\\daima\\obsidian-vault 暴露给所有 AI Agent（WorkBuddy / QClaw / Codex 等）。

存在的意义：本机曾有三个 Obsidian 仓库，AI 经常写错地方。本服务把主库路径硬编码，
AI 通过 MCP 调用时不需要猜路径，也不会写去副本库。

启动方式（stdio）：
    python obsidian_vault_mcp.py

接入配置（~/.workbuddy/mcp.json）：
    "obsidian-vault": {
        "command": "C:/Users/Administrator/.workbuddy/binaries/python/envs/mem0/Scripts/python.exe",
        "args": ["D:/daima/shared-memory/obsidian_vault_mcp.py"]
    }
"""
import os
import re
import sys
from pathlib import Path

from fastmcp import FastMCP

# ===== 唯一主库路径（不要改成其他仓库）=====
VAULT = Path("D:/daima/obsidian-vault")

# 需要忽略的目录
IGNORE_DIRS = {".obsidian", ".git", ".trash", "__pycache__", ".obsidian-backup"}

# 各目录用途说明，写笔记时按这个归类
FOLDER_GUIDE = {
    "00-收件箱": "新笔记暂存区，整理后再归档",
    "01-长期记忆": "用户身份、偏好、红线铁律（Agent 必读 00-导读.md）",
    "02-日记": "工作日记，按年-月归档",
    "03-项目记录": "项目任务，含 03a~03f 六个分类子目录",
    "04-技能档案": "已安装的 AI 技能说明",
    "05-codex-archive": "Codex 会话自动归档（命名固定勿改名）",
    "06-梦境记录": "梦境日记（deep / light / rem）",
    "07-技术笔记": "可复用的技术干货（前端、工具、方法论）",
}

mcp = FastMCP("obsidian-vault")


def _all_notes():
    """遍历全库 md 文件，返回相对路径列表。"""
    out = []
    for p in VAULT.rglob("*.md"):
        if any(part in IGNORE_DIRS for part in p.parts):
            continue
        out.append(p.relative_to(VAULT).as_posix())
    return sorted(out)


def _resolve(name: str):
    """
    模糊解析笔记名 → 绝对路径。
    优先级：完整相对路径 > 文件名精确匹配 > 唯一包含匹配。
    """
    name = (name or "").strip().strip("/\\")
    if not name:
        return None, "笔记名不能为空"

    if not name.endswith(".md"):
        name += ".md"

    # 1) 完整相对路径
    direct = VAULT / name
    if direct.is_file():
        return direct, None

    # 2) 文件名精确匹配（全库唯一）
    hits = [p for p in _all_notes() if Path(p).name == name]
    if len(hits) == 1:
        return VAULT / hits[0], None
    if len(hits) > 1:
        return None, f"文件名不唯一（{len(hits)} 处）：\n" + "\n".join("  - " + h for h in hits)

    # 3) 包含匹配（去掉 .md 后比对，全库唯一）
    stem = name[:-3]
    hits = [p for p in _all_notes() if stem in Path(p).stem]
    if len(hits) == 1:
        return VAULT / hits[0], None
    if len(hits) > 1:
        return None, f"匹配到多个笔记（{len(hits)} 个），请给更精确的名字：\n" + "\n".join("  - " + h for h in hits[:10])

    return None, f"没找到笔记：{name}"


@mcp.tool()
def vault_info() -> str:
    """返回主库路径、目录结构说明和笔记统计。调用任何读写操作前先看这个。"""
    notes = _all_notes()
    by_top = {}
    for n in notes:
        top = n.split("/")[0]
        by_top[top] = by_top.get(top, 0) + 1

    lines = [
        f"主库路径：{VAULT.as_posix()}",
        f"笔记总数：{len(notes)} 篇",
        "",
        "目录结构（写笔记请按用途归类）：",
    ]
    for folder, desc in FOLDER_GUIDE.items():
        cnt = by_top.get(folder, 0)
        lines.append(f"  {folder:<18} {cnt:>4} 篇  {desc}")

    others = {k: v for k, v in by_top.items() if k not in FOLDER_GUIDE}
    if others:
        lines.append("")
        lines.append("其他目录：")
        for k, v in sorted(others.items()):
            lines.append(f"  {k:<18} {v:>4} 篇")

    lines.append("")
    lines.append("注意：本机另有两个仓库（Documents\\Obsidian Vault 已合并停用、")
    lines.append("Documents\\cyber-bookhouse 为赛博书屋抓取区），读写笔记一律走本库。")
    return "\n".join(lines)


@mcp.tool()
def list_notes(prefix: str = "") -> str:
    """列出笔记路径。prefix 可传目录前缀过滤，如 '02-日记' 或 '07-技术笔记'。"""
    notes = _all_notes()
    if prefix:
        prefix = prefix.strip().strip("/\\")
        notes = [n for n in notes if n.startswith(prefix)]

    if not notes:
        return f"没有匹配的笔记（prefix={prefix or '全部'}）"

    lines = [f"共 {len(notes)} 篇：", ""]
    lines.extend("  " + n for n in notes)
    return "\n".join(lines)


@mcp.tool()
def search(query: str, limit: int = 20) -> str:
    """全库搜索，先匹配文件名、再匹配正文。返回命中文件和上下文片段。"""
    query = (query or "").strip()
    if not query:
        return "搜索词不能为空"

    name_hits, body_hits = [], []
    for rel in _all_notes():
        p = VAULT / rel
        try:
            text = p.read_text(encoding="utf-8-sig", errors="ignore")
        except Exception:
            continue

        if query.lower() in rel.lower():
            name_hits.append(rel)
            continue

        idx = text.lower().find(query.lower())
        if idx >= 0:
            start = max(0, idx - 40)
            snippet = text[start:idx + 120].replace("\n", " ")
            body_hits.append(f"{rel}\n      …{snippet}…")

    lines = [f"搜索「{query}」：文件名命中 {len(name_hits)} 篇 / 正文命中 {len(body_hits)} 篇", ""]

    if name_hits:
        lines.append("【文件名命中】")
        lines.extend("  " + h for h in name_hits[:limit])
        lines.append("")

    if body_hits:
        lines.append("【正文命中】")
        lines.extend("  " + h for h in body_hits[:limit])

    if not name_hits and not body_hits:
        lines.append("没有找到。试试更短的关键词，或先用 list_notes 看看有哪些笔记。")

    return "\n".join(lines)


@mcp.tool()
def read_note(name: str) -> str:
    """读取笔记全文。支持模糊名（文件名唯一即可），如 'OYLA-滚动驱动英雄区' 或 '02-日记/2026-08/2026-08-30'。"""
    path, err = _resolve(name)
    if err:
        return err
    try:
        return path.read_text(encoding="utf-8-sig", errors="ignore")
    except Exception as e:
        return f"读取失败：{e}"


@mcp.tool()
def write_note(name: str, content: str, folder: str = "00-收件箱") -> str:
    """
    新建或覆盖笔记。
    folder 用主库的顶层目录名（见 vault_info），默认放 00-收件箱待归档。
    覆盖前请先用 read_note 确认，避免误删内容。
    """
    name = (name or "").strip()
    if not name:
        return "笔记名不能为空"
    if not name.endswith(".md"):
        name += ".md"

    folder = (folder or "00-收件箱").strip().strip("/\\")
    target_dir = VAULT if not folder else VAULT / folder
    target = target_dir / name

    existed = target.is_file()
    if existed:
        backup = target.with_suffix(target.suffix + ".bak")
        try:
            target.rename(backup)
        except Exception:
            pass

    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    except Exception as e:
        return f"写入失败：{e}"

    rel = target.relative_to(VAULT).as_posix()
    if existed:
        return f"已覆盖：{rel}（旧版已备份为同名 .bak）"
    return f"已新建：{rel}"


@mcp.tool()
def append_note(name: str, content: str) -> str:
    """追加内容到笔记末尾，适合写日记、补记录。笔记不存在则报错，不自动新建。"""
    path, err = _resolve(name)
    if err:
        return err

    try:
        old = path.read_text(encoding="utf-8-sig", errors="ignore")
    except Exception as e:
        return f"读取失败：{e}"

    sep = "" if old.endswith("\n") else "\n"
    try:
        path.write_text(old + sep + content + "\n", encoding="utf-8")
    except Exception as e:
        return f"写入失败：{e}"

    return f"已追加到：{path.relative_to(VAULT).as_posix()}"


if __name__ == "__main__":
    if not VAULT.is_dir():
        sys.stderr.write(f"主库不存在：{VAULT}\n")
        sys.exit(1)
    mcp.run()
