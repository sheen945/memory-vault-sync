【AI Agent 共享知识库与记忆接入说明】

你正在运行的用户环境（Windows）已部署两套数据系统，接入后你可以直接读写用户的历史知识与跨工具记忆。请先读完本说明，然后按最后一步完成自检。

────────────────────────────
一、Obsidian 知识库（用户的个人知识沉淀）
────────────────────────────
- 库位置：D:\daima\obsidian-vault\（206 篇 Markdown 笔记，2026-08-28 已深度整理）
- 目录结构（整理后，文件名保持唯一不变，靠目录分类）：
  - 00-收件箱/        新笔记暂存区
  - 01-长期记忆/      用户身份与偏好（先读 00-导读.md 了解红线）
  - 02-日记/          按年-月归档（索引：00-日记索引-MOC.md）
  - 03-项目记录/      6 个分类子目录（索引：00-索引-MOC.md）
    - 03a-短视频创作 / 03b-闲鱼运营 / 03c-技能与工具开发
    - 03d-项目与客户 / 03e-AI调研与对比 / 03f-系统与运维
  - 04-技能档案/      已安装技能说明
  - 05-codex-archive/  Codex 会话自动归档（命名固定勿改名，导读见 00-导读.md）
- 总导航：README.md（所有 Agent 接入后先读这个）
- 项目笔记顶部有 frontmatter（tags/category/date），可用标签筛选
- 调用方式（注意 obs.py 用 D:/ 正斜杠路径）：
  "C:/Users/Administrator/.workbuddy/binaries/python/versions/3.13.12/python.exe" D:/daima/shared-memory/obs.py <命令>
- 命令：
  list                    列出全部笔记
  search "关键词"          搜索笔记内容（文件名+正文）
  read "笔记名"            读取笔记全文
  write "笔记名" "内容"     新建或覆盖笔记
  append "笔记名" "内容"    追加内容到笔记末尾
- 示例：查用户的闲鱼红线：
  "C:/Users/Administrator/.workbuddy/binaries/python/versions/3.13.12/python.exe" D:/daima/shared-memory/obs.py search "闲鱼"

────────────────────────────
二、共享记忆库（Mem0，跨 Agent 共享记忆）
────────────────────────────
- 位置：D:\daima\shared-memory\（本地部署的 Mem0 记忆层，ChromaDB 向量存储）
- 调用方式：
  "C:/Users/Administrator/.workbuddy/binaries/python/envs/mem0/Scripts/python.exe" D:/daima/shared-memory/mem.py <命令>
- 命令：
  add "记忆内容" --agent <你的名字> --tags 标签1,标签2   写入一条记忆
  search "关键词"          搜索记忆（全 Agent 共享，谁写的都能搜到）
  list                    列出记忆（--agent xxx 可只看某 Agent 的）
  delete <memory_id>      删除记忆
  update <memory_id> "新内容"  更新记忆
- 示例：写入用户偏好：
  "C:/Users/Administrator/.workbuddy/binaries/python/envs/mem0/Scripts/python.exe" D:/daima/shared-memory/mem.py add "用户喜欢直接简洁的回答" --agent codex
- 重要：user_id 默认是 shen（用户的共享空间），不要改动。所有 Agent 写在这同一个空间里，彼此互通。

────────────────────────────
三、使用规则
────────────────────────────
1. 用户提到历史、偏好、项目经验、之前做过的事时，先用共享记忆库搜索（mem.py search），再用知识库搜索（obs.py search），有相关内容优先引用。
2. 用户告诉你的新偏好、新事实、重要决策，用 mem.py add 写入共享记忆（--agent 填你自己的名字），让其他 Agent 也能知道。
3. 值得长期沉淀的知识、方法论、踩坑经验，用 obs.py write / append 写入知识库。
4. 写入前先搜索查重，不要重复记录同一条内容。

────────────────────────────
四、接入自检（粘贴后立即执行）
────────────────────────────
请依次运行以下两条命令，并把结果告诉我：
1. "C:/Users/Administrator/.workbuddy/binaries/python/versions/3.13.12/python.exe" D:/daima/shared-memory/obs.py list
2. "C:/Users/Administrator/.workbuddy/binaries/python/envs/mem0/Scripts/python.exe" D:/daima/shared-memory/mem.py search "闲鱼"
如果第 1 条能列出笔记、第 2 条能返回记忆，说明接入成功；如果报错，把错误信息发出来排查。
