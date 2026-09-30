# -*- coding: utf-8 -*-
"""
Obsidian 知识库 CLI —— 让任意 Agent 读写 Obsidian vault
========================================================
用法:
    python obs.py list                    # 列出全部笔记
    python obs.py search "关键词"          # 搜索笔记（文件名+内容）
    python obs.py read "笔记名"            # 读取笔记内容
    python obs.py write "笔记名" "内容"     # 新建/覆盖笔记
    python obs.py append "笔记名" "追加内容" # 追加内容到笔记末尾

QClaw / WorkBuddy 的 Agent 均可直接调用本工具读写知识库。
"""
import argparse
import os
import re
import sys

VAULT = r"D:/daima/obsidian-vault"


def _read_text(path):
    raw = open(path, "rb").read()
    # utf-8-sig 先试：能剥离 BOM，避免 \ufeff 输出到 GBK 控制台崩溃
    for enc in ("utf-8-sig", "utf-8", "gbk"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def _resolve(name):
    """笔记名 -> 文件路径（支持模糊：不含 .md 自动补，全库唯一匹配）"""
    if name.endswith(".md"):
        name = name[:-3]
    exact = os.path.join(VAULT, name + ".md")
    if os.path.exists(exact):
        return exact
    hits = []
    for root, _, files in os.walk(VAULT):
        for f in files:
            if f == name + ".md":
                hits.append(os.path.join(root, f))
    if len(hits) == 1:
        return hits[0]
    if len(hits) > 1:
        print(f"笔记「{name}」有多个同名（{len(hits)}），请用更具体路径")
        return None
    return exact  # 不存在则按新建处理


def main():
    # Windows 控制台中文输出：保持默认编码（GBK），但允许无法编码的字符（emoji等）降级为 ?，避免崩溃
    try:
        sys.stdout.reconfigure(errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="Obsidian 知识库 CLI")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="列出全部笔记")
    p_s = sub.add_parser("search", help="搜索笔记")
    p_s.add_argument("query")
    p_r = sub.add_parser("read", help="读取笔记")
    p_r.add_argument("name")
    p_w = sub.add_parser("write", help="新建/覆盖笔记")
    p_w.add_argument("name")
    p_w.add_argument("content")
    p_a = sub.add_parser("append", help="追加内容")
    p_a.add_argument("name")
    p_a.add_argument("content")

    args = ap.parse_args()

    if args.cmd == "list":
        for root, _, files in os.walk(VAULT):
            for f in sorted(files):
                if f.endswith(".md"):
                    rel = os.path.relpath(os.path.join(root, f), VAULT)
                    print(rel)
        return

    if args.cmd == "search":
        q = args.query.lower()
        for root, _, files in os.walk(VAULT):
            for f in sorted(files):
                if not f.endswith(".md"):
                    continue
                p = os.path.join(root, f)
                rel = os.path.relpath(p, VAULT)
                try:
                    txt = _read_text(p)
                except Exception:
                    continue
                if q in rel.lower() or q in txt.lower():
                    # 找命中片段
                    idx = txt.lower().find(q)
                    snippet = txt[max(0, idx - 40): idx + 60].replace("\n", " ") if idx >= 0 else ""
                    print(f"{rel} :: ...{snippet}...")
        return

    if args.cmd == "read":
        p = _resolve(args.name)
        if not p:
            return
        if not os.path.exists(p):
            print(f"笔记不存在: {args.name}")
            return
        print(_read_text(p))
        return

    if args.cmd == "write":
        p = _resolve(args.name)
        if not p:
            return
        os.makedirs(os.path.dirname(p) or VAULT, exist_ok=True)
        open(p, "w", encoding="utf-8").write(args.content)
        print(f"已写入: {os.path.relpath(p, VAULT)}")
        return

    if args.cmd == "append":
        p = _resolve(args.name)
        if not p:
            return
        if not os.path.exists(p):
            print(f"笔记不存在: {args.name}")
            return
        with open(p, "a", encoding="utf-8") as f:
            f.write("\n\n" + args.content)
        print(f"已追加: {os.path.relpath(p, VAULT)}")
        return


if __name__ == "__main__":
    main()
