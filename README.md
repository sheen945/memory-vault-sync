# memory-vault-sync

> 当需要在 QClaw、WorkBuddy、Obsidian 之间同步个人记忆档案（MEMORY.md/USER.md/SOUL.md 等核心档案 + 每日日记），或验收他人汇报的迁移结果是否真实完成，或 MEMORY.md 膨胀到影响会话读取（被截断）需要按主题拆分瘦身时使用。核心能力：三处 hash 一致性校验、命名不规范文件漏检（如 20260628.md 无连字符）、目标目录存在性验证、日记索引生成、按行号精确切片拆分（零丢失）。触发词：同步记忆、迁移记忆、检查迁移、记忆库验收、MEMORY.md 太大、记忆拆分、瘦身记忆、同步到 Obsidian。

## 安装

把本仓库的目录内容复制到你的技能目录下，文件夹名保持 `memory-vault-sync`：

- WorkBuddy / CodeBuddy：`~/.workbuddy/skills/memory-vault-sync/`
- Claude Code：`~/.claude/skills/memory-vault-sync/`

重启会话后即可通过触发词自动匹配。

## 技能说明

以下为 `SKILL.md` 正文。

---

# 记忆库同步验收与瘦身

个人记忆档案在 **QClaw / WorkBuddy / Obsidian** 三处保持一致，并在主文件膨胀时按主题拆分。

基于 2026-08-29 实战沉淀：验收一次「号称完成」的迁移，发现 3 个 bug（漏 1 篇日记、Obsidian 部分完全未执行、索引不存在），随后把 57KB 的 MEMORY.md 拆成 5 个文件（主文件降到 15.8KB）。

---

## 一、三处路径速查

```
QClaw       C:\Users\Administrator\.qclaw\workspace\          核心档案在根，日记在 memory\，梦境在 memory\dreaming\
WorkBuddy   C:\Users\Administrator\.workbuddy\                核心档案在根，日记在 memory\，梦境在 memory\dreaming\
Obsidian    C:\Users\Administrator\Documents\Obsidian Vault\  01-长期记忆\ 02-日记\ 03-梦境\
```

**Obsidian 仓库定位**：不要靠猜，用 `find ~ -maxdepth 6 -type d -name ".obsidian"` 找，`.obsidian` 目录是 vault 的唯一标识。

---

## 二、验收流程（别人汇报「迁移完成」后，必做）

**铁律：汇报不等于完成。必须逐项实测。**

### 第 1 步：确认目标目录是否真的存在

```bash
ls "C:/Users/Administrator/Documents/Obsidian Vault/"
```

如果汇报里提到的目录（如 `01-长期记忆`、`02-日记`）根本不存在，说明**那部分压根没执行**。这是最容易被谎报的地方。

### 第 2 步：数量对比（源 vs 目标）

```bash
diff <(ls "源目录") <(ls "目标目录")
```

**注意命名不规范的文件**：QClaw 里存在 `20260628.md`（无连字符）和 `2026-06-28.md`（标准）两种格式。用 `grep -E '^2026-.*\.md$'` 筛选会**漏掉前者**。

正确做法：先列出源目录全部 `.md`，人工确认总数，再逐个比对。

### 第 3 步：内容一致性（md5，不是看大小）

```bash
for f in $(ls "源目录" | grep -E '\.md$'); do
  a=$(md5sum "源目录/$f" | cut -d' ' -f1)
  b=$(md5sum "目标目录/$f" 2>/dev/null | cut -d' ' -f1)
  [ "$a" = "$b" ] && echo "✅ $f" || echo "❌ $f"
done
```

### 第 4 步：检查索引类文件

汇报常提到「索引已补齐 N 篇」，要验证索引文件是否真存在、收录数是否对得上。

---

## 三、动手前的备份（不可跳过）

拆分/覆盖前，在**每一处**都留备份：

```bash
ts=$(date +%Y%m%d-%H%M%S)
cp 目标文件 目标文件.bak-$ts
```

三处各留一份，回滚时直接 `cp` 回来。

---

## 四、MEMORY.md 主题拆分（文件过大时）

### 什么时候需要拆

系统每次会话会自动读入 `~/.workbuddy/MEMORY.md`。当文件过大（经验值：**超过 40KB**），注入内容会被截断，提示 `user memory truncated`——**文件末尾的章节实际读不到**，等于写了也白写。

### 拆分原则

- **留在主文件**：每次对话必读的——人设、身份、沟通偏好、规矩、红线
- **拆出去**：按需查阅的——历史项目流水账、技术踩坑、部署记录、软件跟踪

### 关键做法：按行号精确切片，不用正则

中文标题用正则匹配极易出错。**先 Read 全文拿到行号，再按行号切片**：

```python
lines = io.open(SRC, encoding="utf-8-sig").read().split("\n")
def slc(a, b):          # 1-indexed，含两端
    return lines[a-1:b]
USER_PREF = slc(3, 25)
```

切片前先打印边界行核对：

```python
for i in range(a-1, b):
    print('%d: %s' % (i+1, lines[i][:70]))
```

### 主文件必须加导航表

拆分后系统只会自动读主文件，分文件不会被自动加载。主文件开头必须有导航，标明每个分文件**什么时候读**，避免以后一次性全读（那就白拆了）：

```markdown
| 文件 | 内容 | 什么时候读 |
| --- | --- | --- |
| MEMORY.md（本文件） | 人设、偏好、红线 | 每次对话自动读 |
| MEMORY-项目流水账.md | 具体项目记录 | 聊到具体项目时 |
```

### 章节可以拆两半

一个章节内部如果既有「红线级规则」又有「普通记录」，拆开：规则留主文件，记录拆出去。例：`## 软件跟踪` 里的「🔴 软件下载铁律（用户亲口强调）」留在主文件，豆包输入法版本跟踪拆出去。

---

## 五、零丢失校验（拆分后必做）

```python
src = io.open('MEMORY.md.bak-xxx', encoding='utf-8-sig').read()
merged = ''
for f in ['MEMORY.md', 'MEMORY-项目流水账.md', ...]:
    merged += io.open(f, encoding='utf-8-sig').read() + '\n'
missing = [l.strip() for l in src.split('\n')
           if l.strip() and l.strip() not in merged]
print('丢失行数:', len(missing))     # 必须为 0
```

被主动改写的小标题行（如改了标题文字）需单独排除后再比对。

---

## 六、踩坑清单

| 坑 | 现象 | 解法 |
| --- | --- | --- |
| 命名不规范漏检 | `20260628.md` 被 `^2026-.*\.md$` 跳过，少迁一篇 | 先列全部 `.md` 人工确认总数，别只信正则 |
| 目标目录不存在 | 汇报说拷了，实际目录都没有 | 验收第一步就 `ls` 目标目录 |
| BOM 导致摘要异常 | 生成索引时首行摘要为空或残留 `##` | 用 `encoding='utf-8-sig'` 读，自动剥离 BOM |
| 文件过大被截断 | 系统提示 `user memory truncated`，末尾章节读不到 | 超过 40KB 就拆，主文件留导航 |
| 正则匹配中文标题 | 拆分时切错位置 | 改按行号切片 |
| 覆盖无备份 | 原文件被覆盖找不回 | 动手前三处各留 `.bak-时间戳` |
| 索引收录数对不上 | 汇报说 36 篇，实际 35 篇 | 索引生成后用脚本统计再核对 |

---

## 七、编码规范

记忆文件带 **UTF-8 BOM**，读写统一用 `utf-8-sig`：

```python
io.open(path, encoding='utf-8-sig').read()   # 读，自动剥离 BOM
io.open(path, 'w', encoding='utf-8-sig').write(text)  # 写，保持带 BOM
```

保持带 BOM 是为了兼容 Windows 且与原有行为一致，不要改成无 BOM。

---

## 八、同步三处的标准动作

```bash
files="MEMORY.md MEMORY-项目流水账.md MEMORY-踩坑经验库.md MEMORY-软件跟踪.md"
for f in $files; do
  cp ".workbuddy/$f" ".qclaw/workspace/$f"
  cp ".workbuddy/$f" "Documents/Obsidian Vault/01-长期记忆/$f"
done
# 同步后必须校验三处 md5 一致
```

同步完**必须**跑 md5 三方比对，不能只 copy 就完事。

---

## 九、梦境记录（dreaming）

QClaw 的睡眠周期记忆整理，每天自动生成 3 篇：`deep`（修复记忆碎片、提升候选）、`light`（候选记忆筛选，带置信度）、`rem`（反思与"可能的长久真理"）。

结构：`memory/dreaming/{deep,light,rem}/YYYY-MM-DD.md`，内容是机器生成的，价值中等但保留完整历史。

**迁移到 Obsidian 时建 `03-梦境\`（01/02/03 编号避免与已有目录冲突）**，保持三个子目录，并生成 `梦境索引.md`。

**索引生成后必须查死链**：

```python
links = re.findall(r'\[\[([^\]]+)\]\]', txt)
bad = [l for l in links if not os.path.exists(l + '.md')]
```

踩过的坑：日期列不要做成 `[[2026-08-29]]`（文件在子目录里，根目录没有同名文件 = 死链），直接写文本日期，只有 deep/light/rem 三列做链接。

---

## 十、用户可能要求继续精简（拆分之后）

拆完分文件后，用户看过内容可能觉得某些不需要，要求删除。

**处理原则：确认备份完整后再删，删完在主文件导航里标注归档去向。**

1. 先验证待删内容 100% 存在于备份：

```python
bak = io.open('MEMORY.md.bak-xxx', encoding='utf-8-sig').read()
lost = [l.strip() for l in cur.split('\n')
        if l.strip() and l.strip() not in bak]
# 必须为 0
```

2. 三处都删（`.workbuddy\`、`.qclaw\workspace\`、Obsidian `01-长期记忆\`）
3. 主文件导航表删掉对应行，**并注明内容仍在备份文件中**，否则以后会以为资料丢了
4. 重新同步主文件到三处

2026-08-29 实例：拆成 5 个后，用户删掉「项目流水账」(32.7KB) 和「软件跟踪」(0.8KB)，最终保留 3 个（主文件 15.9KB + 踩坑经验库 8.6KB + 技能与部署 2.2KB）。



---

## 配套 MCP

本仓库 `mcp/` 目录下是这个技能配套的 MCP 服务端源码（6 个文件），接入方式见 [`mcp/README.md`](mcp/README.md)。
