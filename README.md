# memory-vault-sync

> 跨 QClaw / WorkBuddy / Obsidian 三处的个人记忆库同步、验收与 MEMORY.md 主题拆分瘦身技能，附带两个配套 MCP 服务端（Mem0 共享记忆、Obsidian 仓库读写）。

## 简介

这是一个 WorkBuddy / CodeBuddy / Claude Code 技能（Skill）仓库，解决个人 AI 记忆档案的多端一致性问题：记忆文件（MEMORY.md / USER.md / SOUL.md 等核心档案 + 每日日记 + 梦境记录）同时存在于 QClaw、WorkBuddy、Obsidian 三处，需要同步、验收和瘦身。

技能沉淀自一次实战验收：一次"号称完成"的迁移，实测发现 3 个 bug（漏 1 篇日记、Obsidian 部分完全未执行、索引不存在）；随后把 57KB 的 MEMORY.md 按主题拆成 5 个文件，主文件降到 15.8KB。核心铁律：**汇报不等于完成，必须逐项实测**。

**触发词**：同步记忆、迁移记忆、检查迁移、记忆库验收、MEMORY.md 太大、记忆拆分、瘦身记忆、同步到 Obsidian。

## 功能特性

- **三处同步与 md5 三方比对**——标准动作：`cp` 到 QClaw workspace、`.workbuddy`、Obsidian `01-长期记忆` 三处后，必须跑 md5 三方比对，不能只 copy 就完事。
- **迁移验收四步法**——① 先 `ls` 确认目标目录真的存在（最容易被谎报的环节）；② 数量对比（先列全部 `.md` 人工确认总数，正则 `^2026-.*\.md$` 会漏掉 `20260628.md` 这类无连字符文件）；③ 内容一致性用 md5 而非看文件大小；④ 验证索引文件真实存在且收录数对得上。
- **MEMORY.md 主题拆分瘦身**——系统每次会话自动读入 MEMORY.md，超过约 40KB 会被截断（`user memory truncated`，末尾章节等于白写）。拆分原则：人设/身份/偏好/红线留主文件，项目流水账/踩坑/部署记录拆出去；主文件开头必须加导航表标明每个分文件"什么时候读"，避免以后一次性全读。
- **按行号精确切片**——中文标题用正则匹配极易切错位置；先 Read 全文拿行号，打印边界行核对后再切（`slc(a, b)`，1-indexed 含两端）。拆完必须做零丢失校验：备份全文逐行比对，丢失行数必须为 0。
- **动手前强制备份**——拆分/覆盖前三处各留 `.bak-时间戳` 副本，回滚直接 `cp` 回来；用户要求删除分文件时，先验证待删内容 100% 存在于备份，删完在主文件导航里注明归档去向。
- **梦境记录（dreaming）迁移**——QClaw 睡眠周期每天生成 deep/light/rem 三类记忆整理，迁移到 Obsidian 时建 `03-梦境\` 目录并生成索引；索引生成后必须查死链（日期列直接写文本，不做 `[[wikilink]]`）。
- **编码规范统一**——记忆文件带 UTF-8 BOM，读写一律用 `utf-8-sig`（读时自动剥离 BOM 避免摘要提取异常，写时保持 BOM 兼容 Windows）。

## 工作原理 / 技术栈

- **技能机制**：核心为 `SKILL.md`（含触发词与完整操作规范）。AI 匹配触发词后，按规范执行路径定位、备份、同步、md5 校验、行号切片、零丢失校验等动作。
- **Obsidian vault 定位**：不靠猜路径，用 `find ~ -maxdepth 6 -type d -name ".obsidian"` 查找，`.obsidian` 目录是 vault 的唯一标识。
- **配套 MCP 服务端**（`mcp/` 目录，两个 stdio server）：
  - **mem0-shared-memory**——基于 `mem0ai` 的多 Agent 共享记忆层：LLM 提取记忆（走自定义网关，密钥只走环境变量 `MEM0_LLM_API_KEY` / `MEM0_LLM_BASE_URL` / `MEM0_LLM_MODEL`，源码不存明文）、本地 bge-small-zh-v1.5 中文向量模型、ChromaDB 本地存储。`user_id` 即共享空间（同 user_id 下所有 Agent 共享全部记忆），`agent_id` 只记录来源不隔离读取。提供 MCP 工具 `remember` / `recall` / `list_memories` / `forget` / `update_memory`，另附 `mem.py` 命令行工具（add / search / list / delete / update）。
  - **obsidian-vault**——纯标准库实现（Python 3.10+，零依赖），直接读写本地 Obsidian 库的 `.md` 文件。

## 安装与使用

**技能安装**：把本仓库目录内容复制到技能目录，文件夹名保持 `memory-vault-sync`：

- WorkBuddy / CodeBuddy：`~/.workbuddy/skills/memory-vault-sync/`
- Claude Code：`~/.claude/skills/memory-vault-sync/`

重启会话后即可通过触发词自动匹配。

**配套 MCP 接入**：在 `~/.workbuddy/mcp.json`（或 Claude 的 MCP 配置）的 `mcpServers` 中加入两个 stdio server 定义，指向 `mcp/mem0-shared-memory/memory_mcp_server.py` 和 `mcp/obsidian-vault/obsidian_vault_mcp.py`（完整 JSON 配置示例见 `mcp/README.md`），重启会话加载。mem0 服务需自行配置 LLM 网关环境变量。

## 项目结构

```
memory-vault-sync/
├── README.md                        # 本文件（中文说明）
├── README_EN.md                     # English version
├── SKILL.md                         # 技能主文件：三处路径、验收流程、拆分与零丢失校验、踩坑清单
├── .gitignore
└── mcp/                             # 配套 MCP 服务端源码
    ├── README.md                    # MCP 接入方式与依赖说明
    ├── Agent接入提示词.md            # Agent 侧接入提示词
    ├── mem0-shared-memory/          # Mem0 共享记忆（MCP server + CLI）
    │   ├── memory_mcp_server.py
    │   ├── mem.py
    │   └── README.md
    └── obsidian-vault/              # Obsidian 仓库读写 MCP（纯标准库）
        ├── obsidian_vault_mcp.py
        └── obs.py
```

## 注意事项

- 数据文件（记忆数据库、向量索引）不随仓库分发，mem0 首次运行会自动创建，并会下载约 95MB 的中文向量模型（走 HuggingFace 镜像）。
- 验收时永远不要只看汇报：先 `ls` 目标目录，再数文件，再 md5，最后核对索引收录数。
- 正则筛选日记文件名不可靠（存在无连字符命名），必须先列全量人工确认总数。
- 保持 UTF-8 BOM，不要改成无 BOM（与原有行为一致、兼容 Windows）。
- 拆分后系统只自动读主文件，分文件不会被自动加载——主文件导航表不是可选项。

## License

MIT

## 作者

sheen945
