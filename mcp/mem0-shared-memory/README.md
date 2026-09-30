# 共享记忆系统（Mem0）

> 让 QClaw 和 WorkBuddy 两个 Agent 共享同一套记忆 —— Agent 1 写入，Agent 2 立即可见。

## 架构

```
┌─────────────┐     ┌─────────────┐
│  Agent 1     │     │  Agent 2     │
│  QClaw       │     │  WorkBuddy   │
└──────┬──────┘     └──────┬──────┘
       │  MCP / CLI        │  MCP / CLI
       ▼                   ▼
┌──────────────────────────────────┐
│       Mem0 共享记忆层             │
│  LLM: jojocode (claude-opus-4-6) │  ← 复用 QClaw 现有 key
│  向量: 本地 bge-small-zh-v1.5    │  ← 本地中文模型（免费）
│  存储: ChromaDB (本地)           │
│  共享空间: user_id=shen          │
└──────────────────────────────────┘
```

## 多 Agent 共享原理

- `user_id` = 共享空间（默认 `shen`）：同一 user_id 下所有 Agent 共享全部记忆
- `agent_id` = 来源 Agent（`qclaw` / `workbuddy`）：记录"谁写的"，但不隔离读取
- 写入/读取都走同一个 Mem0 实例 → Agent 1 写入后，Agent 2 查询立即可见

## 文件说明

| 文件 | 作用 |
|---|---|
| `memory_mcp_server.py` | MCP 服务器（stdio），WorkBuddy 通过 MCP 接入 |
| `mem.py` | 命令行工具，任何 Agent/人都可调用 |
| `memory.db` 历史记录 | Mem0 记忆历史（自动生成） |
| `chroma/` | 向量库存储（自动生成） |

## 命令行用法

```bash
# 写入一条记忆（来源标记为 qclaw）
python mem.py add "申总的闲鱼主图要遵循闲鱼黄配色" --agent qclaw --tags 闲鱼,设计

# 搜索记忆（不分 Agent，全空间）
python mem.py search "闲鱼主图"

# 列出全部 / 只看某个 Agent 的
python mem.py list
python mem.py list --agent workbuddy

# 删除 / 更新
python mem.py delete <memory_id>
python mem.py update <memory_id> "新内容"
```

## WorkBuddy 接入（MCP）

在 `~/.workbuddy/mcp.json` 的 `mcpServers` 中加入：

```json
"mem0-shared-memory": {
  "command": "C:/Users/Administrator/.workbuddy/binaries/python/envs/mem0/Scripts/python.exe",
  "args": ["D:/daima/shared-memory/memory_mcp_server.py"]
}
```

然后在 WorkBuddy 连接器管理页面对新 MCP 服务器点「信任」启用。

MCP 工具：`remember`（写）、`recall`（搜）、`list_memories`（列）、`forget`（删）、`update_memory`（改）。

## QClaw 接入

QClaw（OpenClaw 系）同样支持 MCP：
- 在 QClaw 的 MCP 配置里加同样的 stdio server 定义
- 或直接在 QClaw 的 agent 提示词里让它调用 `python mem.py ...` 读写共享记忆

## 环境变量（可选覆盖）

| 变量 | 默认值 | 说明 |
|---|---|---|
| `MEM0_LLM_API_KEY` | 复用 QClaw key | LLM 密钥 |
| `MEM0_LLM_BASE_URL` | `https://jojocode.com/v1` | LLM 网关 |
| `MEM0_LLM_MODEL` | `claude-opus-4-6` | 提取记忆用的模型 |

## 注意事项

- 首次运行会下载中文向量模型（约 95MB，走 HuggingFace 镜像）
- 记忆提取消耗少量 LLM token（jojocode 网关计费）
- 记忆数据保存在 `D:\daima\shared-memory\`，可整体备份
