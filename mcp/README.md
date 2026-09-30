# 配套 MCP 服务端

本目录是上面这个技能配套的 MCP（Model Context Protocol）服务端源码。

## 目录结构

- `mcp/mem0-shared-memory/memory_mcp_server.py`
- `mcp/mem0-shared-memory/mem.py`
- `mcp/mem0-shared-memory/README.md`
- `mcp/Agent接入提示词.md`
- `mcp/obsidian-vault/obsidian_vault_mcp.py`
- `mcp/obsidian-vault/obs.py`

## 接入方式

在 `~/.workbuddy/mcp.json`（或 Claude 的 MCP 配置）的 `mcpServers` 里加入：

```json
{
  "mcpServers": {
    "mem0-shared-memory": {
      "command": "<你的 python 解释器路径>",
      "args": [
        "<本仓库路径>/mcp/mem0-shared-memory/memory_mcp_server.py"
      ],
      "env": {
        "MEM0_LLM_API_KEY": "<你的 LLM 密钥>",
        "MEM0_LLM_BASE_URL": "<你的 LLM 网关地址>",
        "MEM0_LLM_MODEL": "<模型名>"
      }
    },
    "obsidian-vault": {
      "command": "<你的 python 解释器路径>",
      "args": [
        "<本仓库路径>/mcp/obsidian-vault/obsidian_vault_mcp.py"
      ]
    }
  }
}
```

把路径替换成你自己机器上的实际位置，然后重启会话即可加载。

## 依赖说明

- `mem0-shared-memory`：依赖 `mem0ai`，需要设置环境变量 `MEM0_LLM_API_KEY`、`MEM0_LLM_BASE_URL`、`MEM0_LLM_MODEL`（源码里不存明文密钥）
- `obsidian-vault`：纯标准库实现，只依赖 Python 3.10+，直接读本地 Obsidian 库的 `.md` 文件
- 数据文件（记忆数据库、向量索引）不随仓库分发，首次运行会自动创建
