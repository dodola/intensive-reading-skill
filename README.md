# intensive-reading

一个 Claude Code skill：把一篇英文原文做成中英双语深度精读讲义，并导出为可打印的 Word / PDF。

**范围：只做「读」这一侧。** 教材侧是重点词汇、短语与固定搭配、长难句、语法点；
外刊侧是论证分析与「这个表达能不能搬进自己作文」的迁移判断。
写作产出（写作素材库、读后续写素材、单元写作专题）不在这个 skill 里。

体例与排版从两份《外刊精读》讲义原件（The Atlantic / The New Yorker）逆向提取——
分析方法见 `references/method.md`，样式规格见 `references/style-spec.md`
（从原件 OOXML 逐项提取，是排版的唯一权威）。

**两条主线，各一套骨架和靶子。** 雅思考能力、高考考知识点，两侧不是"另一侧减几块"：

| | 外刊文章（雅思） | 教材课文（高考） |
|---|---|---|
| 骨架 | `references/template-ielts.md` | `references/template.md` |
| 靶子 | `references/ielts-targets.md` | `references/gaokao-targets.md` |
| 主线 | 论证分析 + 写作迁移 | 知识点 |
| 每块必做 | 词条内的 `外刊写作赏析` / `🎓 IELTS 使用提醒` | `🔗 短语与固定搭配` / `🔍 长难句拆解` / `🧩 语法聚焦` |
| 词条末尾 | 迁移分级 ✓✓/✓/✧/⚠️（能不能搬进作文） | 掌握分级 ✓✓✓/✓✓/✓/⚠️（要不要背） |

外刊侧的正主是那句「这个表达能不能搬进我自己的作文」——判据是**语域**而不是难度
（新闻评论修辞、文学隐喻、隐含褒贬、网络俚语、夸张调侃这五类一律不迁移，
Lexical Resource 看的是恰当不是罕见），⚠️ 档必须给替代表达，✧ 档要把修辞层与学术层切开。
往上还有两块：`🎓 IELTS 写作迁移`（把几个表达串成一条完整论证链）、
`📈 Task 1 迁移`（数据之间关系的变化）。

教材侧的正主是三个每块必做的知识点模块，论证分析降为支线（靠精读末尾的 `⇢ 题型对接` 变现）。

文件分工：`method.md` 讲**怎么读**，两份 targets 讲**读出来的东西对准哪儿**，
两份 template 是**照抄的骨架**，`style-spec.md` 讲**怎么排**。

## 产出

一篇原文 → 一份 Markdown 讲义，连同同名的 `.docx` 与 `.pdf`：

- 教材课文 `<册次>_Unit<N>_<课文名>_精读讲义.md`（如 `选必二_Unit1_John Snow_精读讲义.md`）
- 外刊文章 `外刊精读<NN>_<文章简称>_精读讲义.md`（如 `外刊精读02_Harvard Writing Center_精读讲义.md`）

文件名里的字段会在缺 front matter 时用来推页脚，所以按上面的形状起名。

**教材课文**的段落块内固定七个模块：双语对照 / ✦ 表达清单 / 📖 词汇注释 /
🔗 短语与固定搭配 / 🔍 长难句拆解 / 🧩 语法聚焦 / 📖 精读，文末附
📐 语法填空考点扫描与 ✅ 学完自测。

**外刊文章**的段落块是四件套（双语对照 / ✦ 表达清单 / 📖 词汇注释 / 📖 精读，🔗 可选），
不做 🔍 / 🧩 / 📐 / ✅——那几块对着高考知识点；但每个词条内部多两块
（`外刊写作赏析` + `🎓 IELTS 使用提醒`），精读末尾挂 `⇢ 能力对接` 而不是题型对接。

## 安装

```bash
git clone git@github.com:dodola/intensive-reading-skill.git
ln -s "$PWD/intensive-reading-skill/intensive-reading" ~/.claude/skills/intensive-reading
```

链接的是**仓库里的 `intensive-reading/` 子目录**（装的是 skill 本体，不是仓库根）。
符号链接让仓库成为唯一副本：改完直接 `git commit`，不必再往 `~/.claude/skills/` 同步一次。
想要独立副本就把 `ln -s` 换成 `cp -r`。

验证装好了：

```bash
ls -l ~/.claude/skills/intensive-reading/SKILL.md   # 能看到文件即生效
```

**技能清单是会话启动时加载的**，装完要新开一个 Claude Code 会话才认得它。

## 使用

skill 是 model-invoked 的，不必打命令：把原文交给它，说一句要做精读讲义就会触发
（「把这篇文章做成精读讲义」「Unit 2 也做一份」）。

### 切换两种模式

两条主线靠你话里的信号分流（SKILL.md 顶部那张路由表）。**说清目标考试，模式就不会错：**

| 你说 | 走哪一侧 |
|---|---|
| 把人教版选必二 Unit 1 这篇课文做成精读讲义 | 教材 / 高考 |
| 把这篇 The Atlantic 的文章做成外刊精读讲义 | 外刊 / 雅思 |
| 按教材体例做，要 🔗 / 🔍 / 🧩 和文末两个附录 | 强制教材侧 |
| 走雅思侧，用 `template-ielts.md` 那套骨架 | 强制外刊侧 |

- **触发教材侧的信号**：教材版本名（人教版 / 外研版）、册次、`Unit N`、
  课本板块名（Reading and Thinking / Learning About Language）、高考、课标、语法填空
- **触发外刊侧的信号**：刊物名（The Atlantic / The New Yorker / The Economist）、
  外刊、期号、雅思 / IELTS / Task 1 / Task 2

想强制覆盖就**直接点骨架文件名**，那是路由表里唯一的分叉点。

### 只丢一篇文章、不说目标时它按「来源」猜，可能猜反

决定体例的是**考什么**，不是文章来自哪里。两者大多数时候重合，不重合时要明说一句：

| 场景 | 该走 | 不说就会走 |
|---|---|---|
| 拿 The Economist 文章给高三练高考阅读 | 教材侧（要 🔗 / 🔍 / 🧩 / 📐） | 外刊侧 ✗ |
| 拿雅思真题 Passage 做精读 | 外刊侧 | 不确定 |
| 教材课文给要考雅思的学生用 | 外刊侧 | 教材侧 ✗ |

> 这篇 The Economist 的文章，**按教材/高考体例**做，给高三用

### 长讲义中途断了

教材课文这类通常 15~30 页，skill 会先落一个骨架文件再逐块 Edit 追加（避免超长单次响应
中断把整篇工作清零）。中断后说「接着写」即可——它会先读现有文件判断写到哪一步再续，
不会清空重写。

## 单独导出

已有讲义 Markdown 时，直接跑构建脚本：

```bash
bash ~/.claude/skills/intensive-reading/scripts/build.sh 讲义.md
# → 讲义.docx  讲义.pdf
```

页眉页脚取自讲义的 YAML front matter（缺省时按文件名推）：

```yaml
---
header: 人教版 选择性必修 第二册  ·  双语深度精读讲义   # 教材侧
footer: 选必二 Unit 1  ·  John Snow
---
```

```yaml
---
header: THE ATLANTIC  ·  外刊双语深度精读讲义          # 外刊侧
footer: 外刊精读 02  ·  Harvard Writing Center
---
```

依赖：`pandoc`、`libreoffice`（`soffice`）、`python3`（仅标准库）、
`poppler-utils`（`pdftotext` / `pdfinfo`，用于门禁与页数统计）。
字体：Georgia、Noto Serif CJK SC（需 Medium 与 SemiBold 两个字重）、Microsoft YaHei、Carlito。

## 构建管线

```
讲义.md
  │
  ├─ make_ref.py        按 tokens.py 生成 Word 参考模板：字体 / 色板 / 页面 / 页眉页脚
  ├─ print_variant.py   符号替换（emoji → CJK 几何符号）+ 字形校验 + 生成实体目录
  ├─ pandoc             md → docx（--reference-doc）
  ├─ postprocess.py     逐段角色排版 + 表格列宽 + 加粗着色 + 页面设置 + 产物校验
  └─ soffice            docx → pdf
```

分工的原因：原件**零命名样式**，1681 个段落全是直接格式化，命名样式表达不了那种粒度。
所以 `make_ref.py` 只定基线，逐段的间距 / 缩进 / 底色 / 竖条由 `postprocess.py` 写进 XML。

`scripts/tokens.py` 是所有取值的唯一源。改样式：先改 `references/style-spec.md`，再改 `tokens.py`。

## 绕过的几个导出缺陷

| 现象 | 处理 |
|---|---|
| LibreOffice 丢彩色 emoji 与 `▶ ⚠ ✔` 字形 | 导出期替换为 CJK 字体内的几何符号，源文件保持 emoji |
| pandoc 对管道表格输出空 `tblGrid` 且 `tblW=0`，表格塌成一列 | 按内容宽度重算列宽并写 `tcW` |
| `--toc` 在 docx 里是需按 F9 才填充的域，导出为空白页 | 生成实体目录列表 |
| pandoc 丢弃参考模板的 `sectPr`，页眉页脚失效 | 导出后重建 `sectPr`，从 rels 里读真实 rId |
| pandoc 把 `---` 渲染成 VML 横线，而原件全篇无横线 | 改成规格里的竖向间隔空段 |
| 紧跟文字行的 `- ` 列表被并进上一段，搭配家族挤成一行连字符 | 开 pandoc `lists_without_preceding_blankline` 扩展 |

## 三处静默失败与对应的门禁

这条管线有三类失败不会自己暴露——产物照样生成、页数照样对，只有逐页看才发现。
三道门禁都是非零退出，`build.sh` 的 `set -e` 会把整条管线停住，
而且**产物在全部门禁通过之后才落盘**，失败时不会留下与 PDF 不同步的半成品：

- **缺字形。** LibreOffice 对 emoji 与 `▶ ⚠ ✔` 无字形，渲染出来是**什么都没有**，
  不是豆腐块。`print_variant.py` 替换完会逐字复查，凡落在 U+2190–U+2BFF 或
  U+1F000 以上而不在 `SAFE_DECOR` 白名单里的字符，报出行号与码位后退出。
- **角色认错。** `postprocess.py` 靠文本特征认封面 / 方框 / `En:` / `译:` / 词条头，
  认不出来只是退回默认排版。所以最后核一遍「必然非零」的计数（`REQUIRED` 里的六个角色），
  缺了就非零退出。
- **字面星号。** 反引号内嵌套 `**加粗**` 时 pandoc 不解析 code span 内部，成品留下字面
  星号，构建却一路成功。`build.sh` 对成品 PDF 跑 `pdftotext … | grep -oP '\*\*[^ ]'`，
  命中就报出带上下文的那几行并退出——这是本项目历史上被漏得最多的一类问题，
  以前靠人肉看渲染截图，现在是硬门禁。

## examples/

- `选必二_Unit1_John Snow_精读讲义` —— 人教版选择性必修第二册 Unit 1 课文的完整讲义（37 页 A4）。
  6 个段落块，含 `🔍 长难句拆解` 与 `🧩 语法聚焦` 的归位表。

  **这份样例出在改版之前**：它还带着已经废弃的 `🖊 续写素材`、`📚 写作素材库` 与
  `🎓 高考迁移` 标签，也还没有 `🔗 短语与固定搭配` 这一块。看排版与词条体例可以照它，
  看模块清单要以 `references/template.md` 为准。

**外刊侧目前没有样例。** 外刊讲义的体例以 `references/template-ielts.md` 的骨架
与末尾那张自检单为准（骨架本身已经跑通过完整管线）。

课文原文版权归人民教育出版社，此处仅作体例样例，请勿分发。
