# MT Syntax Skill

让 AI 帮你编写、修改和排查 MT 管理器使用的 `.mtsx` 语法文件，并通过实际样例检查高亮效果。

支持 Codex 和 Claude Code。

## 能做什么

- **编写语法**：根据语言说明和代码样例，生成 `.mtsx` 文件。
- **修复高亮**：排查字符串、注释、关键字或嵌入语言的高亮问题。
- **查看效果**：生成 HTML 预览，在浏览器中检查高亮结果。
- **验证修改**：用样例检查修改是否符合预期，也可以比较修改前后的高亮和性能。

## 安装前准备

电脑需要安装 Java 和 Python：

| 系统 | Java | Python |
| --- | --- | --- |
| macOS / Linux | 17 或以上 | 3.6 或以上 |
| Windows | 17 或以上 | 3.8 或以上 |

在终端运行 `java -version`，确认 Java 版本。macOS / Linux 用 `python3 --version` 检查 Python；Windows 用 `py -3 --version`，也可以使用已配置好的 `python --version`。

AI 助手需要能够在本机调用这两个命令。校验工具已随仓库提供，无需自行编译或安装额外的 Python 包。

## 安装

### 让 AI 帮你安装

如果你的 AI 助手可以访问仓库并操作本机文件，直接把下面这句话发给它：

> 请从 https://github.com/L-JINBIN/mt-syntax-skill 安装 MT Syntax Skill，并检查运行环境是否就绪。

也可以按下面的步骤手动安装。

### Codex

1. 从[仓库页面](https://github.com/L-JINBIN/mt-syntax-skill)下载 ZIP 并解压，或克隆本仓库。
2. 将包含 `SKILL.md` 的文件夹命名为 `mt-syntax`，完整放入 `~/.agents/skills/`。Windows 对应用户目录下的 `.agents/skills/`。
3. 确认 `~/.agents/skills/mt-syntax/SKILL.md` 和 `~/.agents/skills/mt-syntax/lib/mt-syntax.jar` 都存在。
4. 在 Codex 中选择或输入 `$mt-syntax`。如果没有出现，重新启动 Codex。

如果你现有的 Codex 环境已使用 `~/.codex/skills/` 安装技能，沿用该目录即可。只安装一份，保留整个文件夹，不要单独复制 jar。

Codex 的目录说明见[官方文档](https://learn.chatgpt.com/docs/build-skills#where-codex-loads-local-skills)。

### Claude Code

在终端执行：

```text
claude plugin marketplace add L-JINBIN/mt-syntax-skill
claude plugin install mt-syntax@mt-syntax
```

重新启动 Claude Code，在对话中输入 `/mt-syntax` 使用。安装后可以在 `/plugin` 中查看和管理插件。

如果已经下载或克隆到本机，也可以在仓库目录执行 `claude plugin marketplace add .` 添加安装源，再运行上面的安装命令。只想先试用时，执行 `claude --plugin-dir .` 即可在本次会话加载，调用方式相同。

安装方式详见 [Claude Code 插件文档](https://code.claude.com/docs/en/plugin-marketplaces)。

## 如何使用

先选择对应的技能，再向 AI 说明需求：

| 安装方式 | 调用方式 |
| --- | --- |
| Codex | `$mt-syntax` |
| Claude Code 插件 | `/mt-syntax` |

建议同时提供代码样例；修改已有语法时，再提供对应的 `.mtsx` 文件。

**创建新语法**

> 为这个语言编写 MT 语法文件。附件是语言说明和代码样例，请生成高亮预览。

**修复现有语法**

> 修复这个语法文件中的字符串高亮。样例第 8 行的转义引号导致字符串提前结束，请检查并验证。

**检查修改效果**

> 比较这两个版本的语法在同一份样例上的高亮差异，检查是否影响了注释和嵌入语言。

描述问题时，指出具体位置、目前的效果和你期望的效果。涉及自定义子语法时，将主语法和子语法一并提供。

AI 会按任务需要调用校验工具，并给出语法文件、预览或验证结果。生成的 HTML 可以直接在浏览器中打开，便于检查实际效果。

## 常见问题

**提示找不到 Java 或 Python**

确认安装完成，并能在 AI 工具所使用的终端中运行上述版本检查命令。修改环境变量后，可能需要重新启动 AI 工具。

**提示 Java 版本过低**

需要 Java 17 或以上。若电脑安装了多个版本，以 `java -version` 显示的版本为准。

**提示找不到校验工具**

检查 `lib/mt-syntax.jar` 是否存在。更新时替换完整的 skill 文件夹，保持脚本、资料与 jar 来自同一版本。

**怎样让验证更可靠？**

提供能复现问题的小样例，并保留正常情况供对照。除了查看 AI 的说明，也打开高亮预览，确认结果符合预期。
