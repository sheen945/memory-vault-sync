# -*- coding: utf-8 -*-
"""
共享记忆 MCP 服务器（基于 Mem0）
================================
多 Agent 共享同一份记忆：user_id 区分"人"（如 shen），agent_id 区分"哪个 Agent"。
同一个 user_id 下，QClaw 和 WorkBuddy 两个 Agent 读写同一套记忆。

启动方式（stdio MCP server）：
    python memory_mcp_server.py

WorkBuddy 接入：在 ~/.workbuddy/mcp.json 的 mcpServers 里加：
    "mem0-shared-memory": {
        "command": "C:/Users/Administrator/.workbuddy/binaries/python/envs/mem0/Scripts/python.exe",
        "args": ["D:/daima/shared-memory/memory_mcp_server.py"]
    }
"""
import contextlib
import functools
import io
import json
import os
import sys

os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")  # 国内下载模型必须走镜像
os.environ.setdefault("POSTHOG_DISABLED", "1")  # 关闭 mem0 遥测，避免网络超时噪音

if os.name == "nt":
    try:
        import winreg

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as env_key:
            for env_name in ("MEM0_LLM_API_KEY", "MEM0_LLM_BASE_URL", "MEM0_LLM_MODEL"):
                if os.environ.get(env_name):
                    continue
                try:
                    stored_value, _ = winreg.QueryValueEx(env_key, env_name)
                except FileNotFoundError:
                    continue
                if stored_value:
                    os.environ[env_name] = str(stored_value)
    except OSError:
        pass

MEM0_DIR = r"D:/daima/shared-memory"
LLM_API_KEY = os.environ.get("MEM0_LLM_API_KEY")
if not LLM_API_KEY:
    raise RuntimeError("MEM0_LLM_API_KEY is not configured")
LLM_BASE_URL = os.environ.get("MEM0_LLM_BASE_URL", "https://jojocode.com/v1")
LLM_MODEL = os.environ.get("MEM0_LLM_MODEL", "gpt-5.6-luna")

EMBED_MODEL = os.environ.get(
    "MEM0_EMBED_MODEL",
    r"D:/daima/shared-memory/models/models/BAAI--bge-small-zh-v1.5/snapshots/master",
)

CONFIG = {
    "llm": {
        "provider": "openai",
        "config": {
            "model": LLM_MODEL,
            "api_key": LLM_API_KEY,
            "openai_base_url": LLM_BASE_URL,
        },
    },
    "embedder": {
        "provider": "huggingface",
        "config": {"model": EMBED_MODEL},
    },
    "vector_store": {
        "provider": "chroma",
        "config": {
            "collection_name": "shared_memory",
            "path": os.path.join(MEM0_DIR, "chroma"),
        },
    },
    "history_db_path": os.path.join(MEM0_DIR, "history.db"),
}

DEFAULT_USER = "shen"  # 申总的共享空间

from mem0 import Memory
from fastmcp import FastMCP

mcp = FastMCP("mem0-shared-memory")
_memory = None


def protect_stdout(fn):
    """mem0/sentence-transformers 内部会往 stdout 打印内容，会污染 MCP 协议流。
    执行期间把 stdout 临时捕获到缓冲区（用完立即恢复），保证 JSON-RPC 通道干净。"""

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        with contextlib.redirect_stdout(io.StringIO()):
            return fn(*args, **kwargs)

    return wrapper


def get_memory():
    global _memory
    if _memory is None:
        _memory = Memory.from_config(CONFIG)
    return _memory


# 预热：在主线程完成 mem0 初始化（向量库/模型加载），避免在 MCP 工具线程里初始化导致死锁
try:
    _memory = Memory.from_config(CONFIG)
    print("[mem0] 初始化完成（预热）", file=sys.stderr)
except Exception as e:
    print(f"[mem0] 预热失败（首次工具调用时重试）: {e}", file=sys.stderr)
    _memory = None


@mcp.tool()
@protect_stdout
def remember(content: str, agent_id: str = "default", tags: str = "", user_id: str = DEFAULT_USER) -> str:
    """写入一条记忆到共享库。content=记忆内容, agent_id=来源Agent(qclaw/workbuddy), tags=逗号分隔标签, user_id=共享空间(默认shen)。"""
    metadata = {"agent": agent_id}
    if tags:
        metadata["tags"] = [t.strip() for t in tags.split(",") if t.strip()]
    try:
        result = get_memory().add(
            content,
            user_id=user_id,
            agent_id=agent_id,
            metadata=metadata,
        )
        return json.dumps({"ok": True, "result": result}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False)


@mcp.tool()
@protect_stdout
def recall(query: str, limit: int = 5, user_id: str = DEFAULT_USER) -> str:
    """搜索共享记忆库（不分 Agent，全空间可见）。query=查询内容, limit=返回条数。"""
    try:
        results = get_memory().search(query, filters={"user_id": user_id}, top_k=limit)
        return json.dumps({"ok": True, "results": results}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False)


@mcp.tool()
@protect_stdout
def list_memories(limit: int = 20, agent_id: str = "", user_id: str = DEFAULT_USER) -> str:
    """列出共享记忆。agent_id 留空=全部Agent；填 qclaw 或 workbuddy 只看某个Agent的。"""
    try:
        results = get_memory().get_all(filters={"user_id": user_id}, top_k=limit)
        if agent_id:
            results = [r for r in results if r.get("metadata", {}).get("agent") == agent_id]
        return json.dumps({"ok": True, "count": len(results), "results": results}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False)


@mcp.tool()
@protect_stdout
def forget(memory_id: str) -> str:
    """删除一条记忆（按 memory_id）。"""
    try:
        get_memory().delete(memory_id=memory_id)
        return json.dumps({"ok": True}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False)


@mcp.tool()
@protect_stdout
def update_memory(memory_id: str, new_content: str) -> str:
    """更新一条记忆的内容。"""
    try:
        get_memory().update(memory_id=memory_id, text=new_content)
        return json.dumps({"ok": True}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False)


if __name__ == "__main__":
    mcp.run()
