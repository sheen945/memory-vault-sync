# -*- coding: utf-8 -*-
"""
共享记忆 CLI（基于 Mem0）
=========================
用法:
    python mem.py add "内容" [--agent qclaw] [--tags a,b,c]
    python mem.py search "关键词" [--limit 5]
    python mem.py list [--agent qclaw] [--limit 20]
    python mem.py delete <memory_id>
    python mem.py update <memory_id> "新内容"
"""
import argparse
import json
import os
import sys

os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")  # 国内下载模型必须走镜像

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from memory_mcp_server import CONFIG, DEFAULT_USER

from mem0 import Memory

_memory = None


def get_memory():
    global _memory
    if _memory is None:
        _memory = Memory.from_config(CONFIG)
    return _memory


def main():
    ap = argparse.ArgumentParser(description="共享记忆 CLI")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_add = sub.add_parser("add", help="写入记忆")
    p_add.add_argument("content")
    p_add.add_argument("--agent", default="default")
    p_add.add_argument("--tags", default="")
    p_add.add_argument("--user", default=DEFAULT_USER)

    p_search = sub.add_parser("search", help="搜索记忆")
    p_search.add_argument("query")
    p_search.add_argument("--limit", type=int, default=5)
    p_search.add_argument("--user", default=DEFAULT_USER)

    p_list = sub.add_parser("list", help="列出记忆")
    p_list.add_argument("--agent", default="")
    p_list.add_argument("--limit", type=int, default=20)
    p_list.add_argument("--user", default=DEFAULT_USER)

    p_del = sub.add_parser("delete", help="删除记忆")
    p_del.add_argument("memory_id")
    p_del.add_argument("--user", default=DEFAULT_USER)

    p_upd = sub.add_parser("update", help="更新记忆")
    p_upd.add_argument("memory_id")
    p_upd.add_argument("content")
    p_upd.add_argument("--user", default=DEFAULT_USER)

    args = ap.parse_args()

    try:
        m = get_memory()
        if args.cmd == "add":
            metadata = {"agent": args.agent}
            if args.tags:
                metadata["tags"] = [t.strip() for t in args.tags.split(",") if t.strip()]
            r = m.add(args.content, user_id=args.user, agent_id=args.agent, metadata=metadata)
            print(json.dumps(r, ensure_ascii=False, indent=2))

        elif args.cmd == "search":
            r = m.search(args.query, filters={"user_id": args.user}, top_k=args.limit)
            print(json.dumps(r, ensure_ascii=False, indent=2))

        elif args.cmd == "list":
            r = m.get_all(filters={"user_id": args.user}, top_k=args.limit)
            if args.agent:
                r = [x for x in r if x.get("metadata", {}).get("agent") == args.agent]
            print(json.dumps(r, ensure_ascii=False, indent=2))

        elif args.cmd == "delete":
            m.delete(memory_id=args.memory_id)
            print("已删除")

        elif args.cmd == "update":
            m.update(memory_id=args.memory_id, text=args.content)
            print("已更新")
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
