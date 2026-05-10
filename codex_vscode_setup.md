# VS Code Codex 配置指南

本文用于实验室成员配置 VS Code 中的 Codex/ChatGPT 插件。

每个人需要先从实验室网站http://154.201.92.23领取两项信息：

- `base_url`：模型服务地址，例如 `http://154.201.92.23:8317/v1`
- `token`：个人访问令牌。不要转发给他人，不要提交到 Git 仓库，也不要放进截图或 PDF 文档里。

> 重要：本文只展示 `xxx` 占位模板，不展示真实 token。复制模板后必须把 `xxx` 替换成实验室网站分配给你的个人 token，平常使用不要只用gpt-5.5,合理使用才能节省token和不陷入幻觉，同时推理强度不要一直开超高，很耗token，建议平时使用中等强度，困难问题才用高，解决不了再用超高，后台检测一旦一直用超高强度就关闭使用权一周。

## 1. 安装 VS Code 插件

在 VS Code 里打开扩展市场，搜索并安装 OpenAI 的 Codex/ChatGPT 插件。

也可以在终端中安装 VS Code 插件：

```bash
code --install-extension openai.chatgpt
```

安装完成后，重启 VS Code，左侧边栏或命令面板中应该可以看到 Codex/ChatGPT 相关入口。

## 2. 先用 API 登录

安装插件后，先在 VS Code 插件界面完成 API 登录，让插件初始化本地 Codex 账号状态。完成登录后，再修改配置文件。

推荐顺序：

1. 打开 VS Code。
2. 打开 Codex/ChatGPT 插件入口。
3. 选择使用 API key/token 的登录方式。
4. 粘贴实验室网站分配给你的个人 token。
5. 确认插件已完成登录。

不要在项目文件、聊天记录、Markdown 文档或 PDF 文档中粘贴真实 token。

## 3. 写入个人令牌文件

API 登录完成后，打开 Codex 的令牌文件：

```text
~/.codex/auth.json
```

在 Linux 终端中可以这样打开：

```bash
mkdir -p ~/.codex
code ~/.codex/auth.json
```

把 `~/.codex/auth.json` 原有内容全部替换为下面这段，并把 `xxx` 替换成实验室网站分配给你的个人 token：

```json
{
  "OPENAI_API_KEY": "sk-xxx"
}
```

注意：

- 只替换 `xxx`，不要删除双引号。
- 文件必须是合法 JSON，不能有注释、行号或多余逗号。
- 不要把真实 token 写进项目文件、Markdown 文档、PDF 文档或聊天记录。

## 4. 修改 Codex 配置文件

API 登录完成后，再修改 Codex 的用户配置文件。

配置文件通常位于：

```text
~/.codex/config.toml
```

在 Linux 终端中可以这样打开：

```bash
mkdir -p ~/.codex
code ~/.codex/config.toml
```

如果 `code` 命令不可用，也可以在 VS Code 中使用 `File -> Open File...`，然后打开：

```text
/home/你的用户名/.codex/config.toml
```

把下面模板写入 `~/.codex/config.toml`，并把 `base_url` 改成实验室网站分配给你的地址。

复制配置时，只复制代码块内部内容；不要复制标题、说明文字或行号。

```toml
disable_response_storage = true
model = "gpt-5.5"
model_provider = "PioneerCode"
model_reasoning_effort = "high"
model_verbosity = "high"

[features]
web_search_request = true
multi_agent = true

[model_providers.PioneerCode]
base_url = "把这里替换成你的 base_url"
name = "PioneerCode"
requires_openai_auth = true
wire_api = "responses"
```

示例：

```toml
disable_response_storage = true
model = "gpt-5.5"
model_provider = "PioneerCode"
model_reasoning_effort = "xhigh"
model_verbosity = "high"

[features]
web_search_request = true
multi_agent = true

[model_providers.PioneerCode]
base_url = "http://154.201.92.23:8317/v1"
name = "PioneerCode"
requires_openai_auth = true
wire_api = "responses"
```

注意：`model_provider = "PioneerCode"` 必须和 `[model_providers.PioneerCode]` 完全一致，大小写也要一致。如果一个写成 `PIONEER`，另一个写成 `PioneerCode`，Codex 会报 provider 找不到。

## 5. 关闭 VS Code 后再重新打开

`auth.json` 和 `config.toml` 都保存后，需要完全关闭 VS Code，再重新打开。

建议这样做：

1. 保存 `~/.codex/auth.json` 和 `~/.codex/config.toml`。
2. 关闭所有 VS Code 窗口。
3. 确认 VS Code 后台进程已经退出。
4. 重新打开 VS Code。
5. 重新打开 Codex/ChatGPT 插件并创建任务。

如果只关闭当前聊天面板而没有关闭 VS Code，插件可能仍然使用旧配置。

## 6. 在 VS Code 插件里验证

VS Code 插件用户不需要执行 Codex CLI 命令来验证配置。

验证方式：

1. 在 VS Code 中打开 Codex/ChatGPT 插件。
2. 新建一个 Codex 任务。
3. 发送一句简单测试，例如“你好，确认一下当前模型是否可用”。
4. 如果能正常回复，说明 API 登录、`auth.json` 和 `config.toml` 基本可用。

如果创建任务失败，先检查：

- `base_url` 是否正确，尤其是否包含 `/v1`
- `model_provider` 是否和 `[model_providers.PioneerCode]` 完全一致
- 是否已经用插件完成 API 登录
- `~/.codex/auth.json` 是否已替换为 `OPENAI_API_KEY` 模板，并把 `xxx` 换成个人 token
- 保存配置后是否完全关闭并重新打开 VS Code

## 7. 必须：让 Codex 自动安装推荐 Skills

下面这一步是必须配置项。它会让 Codex 帮你安装一组适合 VS Code/Codex 插件工作流的 skills，并写入全局路由规则。没有这一步，后续“gstack 负责想、Superpowers 负责做”的工作流不会自动生效。

推荐思路：

- gstack 只负责决策层：想清楚需求、范围、方案和架构。
- Superpowers 只负责执行层：TDD、调试、执行计划、验证、代码 review 和收尾。
- `planning-with-files` 负责长任务的文件化记忆。
- `qmd` 负责搜索本地 Markdown 知识库。
- `find-skills` 负责发现和评估新的 skills。
- 文档类 skills 只处理真实的 PDF、Word、PPT、Excel 文件。
- `shuorenhua` 只负责“说人话”“去 AI 味”和文本自然化。

### 发给 Codex 的安装提示词

打开 VS Code 的 Codex 插件，新建任务，然后把下面整段发给 Codex。

```text
请使用 gpt-5.5，并使用最高强度推理 xhigh。

目标：为当前用户配置 VS Code/Codex 插件使用的全局 skills 和路由规则。不要按 OpenClaw/Clawdbot 专用方案安装。不要安装 memory-hygiene。

请完成这些事：

1. 检查 ~/.codex/config.toml，确保包含：
   - model = "gpt-5.5"
   - model_reasoning_effort = "xhigh"
   - [features] 下有 web_search_request = true 和 multi_agent = true

2. 安装 find-skills：
   DISABLE_TELEMETRY=1 npx skills add vercel-labs/skills --skill find-skills -g -a codex -y

3. 安装 qmd skill：
   DISABLE_TELEMETRY=1 npx skills add tobi/qmd --skill qmd -g -a codex -y

4. QMD CLI 是可选运行时依赖。只有当用户需要真正搜索本地 Markdown 知识库时，才安装 @tobilu/qmd。安装前先检查 Node 版本；如果默认 Node 低于 20，请使用本机已有的 Node 20+，或者创建 wrapper，不要破坏用户默认 Node。

5. 安装文档类 skills：
   - pdf
   - docx
   - pptx
   - xlsx
   优先使用可信来源，例如 openai/skills 或 anthropics/skills。

6. 安装 shuorenhua：
   来源：https://github.com/MrGeDiao/shuorenhua
   安装为 ~/.codex/skills/shuorenhua。

7. 安装 planning-with-files：
   来源：https://github.com/OthmanAdi/planning-with-files
   skill 路径：.codex/skills/planning-with-files

8. 安装 gstack，但只暴露决策层 skills：
   - gstack-office-hours
   - gstack-plan-ceo-review
   - gstack-plan-eng-review
   - gstack-upgrade
   使用 prefix 模式，避免和其他 skills 冲突。隐藏其他 gstack 执行层 skills，不要删除 gstack 源仓库。

9. 安装 Superpowers，但只暴露执行层 skills：
   - test-driven-development
   - systematic-debugging
   - executing-plans
   - verification-before-completion
   - requesting-code-review
   - receiving-code-review
   - finishing-a-development-branch
   - dispatching-parallel-agents
   - subagent-driven-development
   - using-git-worktrees
   不要暴露 using-superpowers、brainstorming、writing-plans、writing-skills。

10. 写入或更新 ~/.codex/AGENTS.md，加入：
    - 默认中文回复
    - 编码前先说明方法并等待批准
    - 需求模糊时先问澄清问题
    - 修改超过 3 个文件时先拆小任务
    - 修 bug 时先写复现测试
    - 写完代码后列出边缘案例和建议测试
    - 被用户纠正时反思错因并制定避免再犯的规则
    - gstack 负责决策层，Superpowers 负责执行层，planning-with-files 负责长任务记忆，qmd 负责 Markdown 知识检索，find-skills 负责 skill 发现

11. 完成后列出最终可见 skills，并提醒我重启 VS Code/Codex 插件。
```

### 推荐的 AGENTS.md 路由规则

如果你想手动写，也可以把下面内容保存到：

```text
~/.codex/AGENTS.md
```

```markdown
## Default Language

Reply in Chinese by default unless the user asks for another language, or unless the output is code, logs, config, commit text, or documentation that should stay in its existing language.

## Coding Guardrails

Before writing or editing any code, first describe the intended approach in plain language and wait for the user's approval.

If the user's requirement is ambiguous, incomplete, or could reasonably produce different behavior, ask clarifying questions before writing code.

If the task appears likely to modify more than three files, stop before editing and split the work into smaller tasks.

When fixing a bug, first write or identify a test that reproduces the bug, then fix the code until that test passes. If a reproduction test is impractical, say why before changing code.

After any code writing, list relevant edge cases and suggest tests that should cover them.

Whenever the user corrects the assistant, explicitly reflect on what was wrong, why it happened, and what rule or habit will prevent the same mistake from recurring.

## Skill Routing

Use installed skills by stage, not by enthusiasm.

gstack thinks. Superpowers executes. planning-with-files remembers. qmd searches Markdown knowledge. find-skills discovers new skills. document skills handle actual documents. shuorenhua cleans writing style.

### Active Skill Whitelist

- gstack decision layer: `gstack-office-hours`, `gstack-plan-ceo-review`, `gstack-plan-eng-review`, `gstack-upgrade`.
- Superpowers execution layer: `test-driven-development`, `systematic-debugging`, `executing-plans`, `verification-before-completion`, `requesting-code-review`, `receiving-code-review`, `finishing-a-development-branch`, `dispatching-parallel-agents`, `subagent-driven-development`, `using-git-worktrees`.
- Skill discovery: `find-skills`.
- Memory and retrieval: `planning-with-files`, `qmd`.
- Documents: `pdf`, `docx`, `pptx`, `xlsx`.
- Writing style: `shuorenhua`.

Do not rely on hidden or unlisted gstack execution skills or Superpowers planning skills unless the user explicitly asks to restore or use them.

### Habitual Dispatch

The user should not need to explicitly name a skill every time. Infer the stage:

- Fuzzy, strategic, product-shaped, architectural, risky, or scope-changing work: do a lightweight gstack decision pass first.
- Clear implementation work: skip gstack and move to execution.
- Long-running or multi-file work: also use planning-with-files.
- Explicitly named skill: use that skill.

### Decision Layer: gstack

Use gstack before implementation when the main uncertainty is what to build, why it matters, how to scope it, whether the plan is sound, or which architecture is worth committing to.

### Execution Layer: Superpowers

Use Superpowers after the direction is clear and the task has moved into coding, debugging, verification, review, or delivery.

### Knowledge Search: qmd

Use qmd when the task is to search local Markdown knowledge bases, notes, project docs, research notes, or long-lived documentation. Do not use qmd for ordinary code search; use rg for code and file search.

### Skill Discovery: find-skills

Use find-skills when the user asks whether there is a skill for a task, wants to extend Codex with a new capability, asks to compare/install skills, or asks which skill source is appropriate.

### Documents

Use pdf/docx/pptx/xlsx only when a real document file of that type is involved.

### Writing Style

Use shuorenhua only when the user asks to make text more natural, remove AI tone, say it like a person, reduce template language, review writing style, or produce a less staged version.
```

## 8. QMD 说明

`qmd` skill 本身只是告诉 Codex 如何使用 QMD。真正执行本地 Markdown 搜索时，还需要 QMD CLI 或 QMD MCP server。

如果你只是先安装 skill，不需要立刻搜索本地 Markdown，可以暂时不安装 QMD CLI。

如果你需要搜索本地 Markdown 知识库，可以让 Codex 帮你安装 CLI，并添加 collection：

```bash
qmd collection add /path/to/notes --name notes
qmd embed
```

之后就可以让 Codex 使用 QMD 查询本地 Markdown 文档。

## 9. 常见问题

### Model provider not found

报错示例：

```text
Model provider `PIONEER` not found
```

原因通常是 `model_provider` 和 provider 配置块名称不一致。

错误示例：

```toml
model_provider = "PIONEER"

[model_providers.PioneerCode]
base_url = "http://154.201.92.23:8317/v1"
```

正确示例：

```toml
model_provider = "PioneerCode"

[model_providers.PioneerCode]
base_url = "http://154.201.92.23:8317/v1"
```

### 401 或 Unauthorized

这通常表示 token 没配置好、token 写错、token 已过期，或者当前 token 不属于这个 `base_url`。

处理方式：

1. 回到 VS Code 插件。
2. 重新执行 API 登录。
3. 打开 `~/.codex/auth.json`，用下面模板替换原有内容，并把 `xxx` 换成新的个人 token：

```json
{
  "OPENAI_API_KEY": "xxx"
}
```

4. 保存后关闭所有 VS Code 窗口，再重新打开。

不要把真实 token 写进 Markdown 或 PDF。

### 404 或接口不存在

如果服务端返回 404，通常是 `base_url` 写错，或者服务端没有兼容 `wire_api = "responses"` 对应的接口。

检查 `base_url` 是否包含 `/v1`。

正确示例：

```toml
base_url = "http://154.201.92.23:8317/v1"
```

错误示例：

```toml
base_url = "http://154.201.92.23:8317"
```

除非实验室网站明确要求，否则不要省略 `/v1`。

### 修改配置后 VS Code 没反应

VS Code 插件可能还在使用旧配置。处理方式：

1. 保存 `~/.codex/auth.json` 和 `~/.codex/config.toml`。
2. 关闭所有 VS Code 窗口。
3. 确认 VS Code 后台进程已经退出。
4. 重新打开 VS Code。
5. 重新创建 Codex 任务。

### 从 PDF 复制配置后出错

PDF 里的引号、空格、换行有时会被阅读器处理得不一致。

如果从 PDF 复制配置后报错，优先从 Markdown 原文复制代码块内容。复制后检查：

- 引号是否是英文半角双引号 `"`
- `model_provider` 是否和 `[model_providers.PioneerCode]` 一致
- `base_url` 是否包含 `/v1`
- `auth.json` 是否是合法 JSON
- 配置里是否混入了行号、标题或多余说明文字

## 10. 安全提醒

每个人的 token 只给本人使用。

不要把下面内容提交到 Git 仓库，也不要截图公开：

- `~/.codex/auth.json`
- 个人 token
- 包含 token 的完整请求日志
- 包含 token 的报错页面

如果怀疑 token 泄露，请立即在实验室网站重新生成 token，或者联系管理员吊销旧 token。
