# proto-to-requirement Skill Suite 用法

本项目是一组四段式需求工程 skill，用于把墨刀/Mockitt 原型证据、字段分析、产品经理人工确认和辅助材料整理成可交给 coding agent 开发的 BDD 工程版 PRD。

## 工作流

```text
墨刀/Mockitt 原型导出
  -> Stage 1: proto-to-requirement（原型解析 + 字段/页面结构解析）
  -> Stage 2: proto-pm-interviewer（PM 提问清单生成）
  -> Stage 3: 用户会议（PM 解答收集）
  -> Stage 4: bdd-engineering-prd-writer（BDD 工程 PRD 编写）
  -> BDD 工程版 PRD
```

四段职责必须分开：

| 阶段 | Skill | 作用 | 输出 |
|------|-------|------|------|
| Stage 1 | `proto-to-requirement` | 解析原型页面、交互、文本、批注，自动执行字段解析和页面结构分析 | `prototype-analysis.md`, `structured-data.json`, `completeness-report.json`, `requirements.md` 草稿, `field-analysis.md` |
| Stage 2 | `proto-pm-interviewer` | 根据解析证据和字段分析生成高可读性 PM 提问清单（选择题为主） | `pm-question-checklist.md`, `pm-answer-template.md` |
| Stage 3 | 用户手动 | 带清单参加 PM 会议，收集解答，将会议记录交给 AI 自动填写解答模板 | 填写后的 `pm-answer-template.md` |
| Stage 4 | `bdd-engineering-prd-writer` | 整合解析证据、字段分析、PM 解答、人工 PRD 和辅助材料，编写最终 BDD 工程 PRD | `bdd-engineering-prd.md` |

## Stage 1: 解析墨刀原型 + 字段分析

适用于本地已解压的 Mockitt/MoDao 导出目录。目录需要包含：

- `mb-proto2/`
- `extra/data.*.js`

运行：

```bash
uv run python3 -m proto_to_requirement.cli <prototype_dir> --output <output_dir>
```

如果 skill 已安装到 Codex，注意 skill 目录本身通常只包含 `SKILL.md` 和参考材料；解析器 Python 包不一定在 skill 目录内。当前推荐的 runtime 位置是：

```text
~/.codex/skill-runtimes/proto-to-requirement-skill-suite
```

因此在 Codex 上运行 Stage 1 时，先进入 runtime 目录：

```bash
cd ~/.codex/skill-runtimes/proto-to-requirement-skill-suite
uv run python3 -m proto_to_requirement.cli <prototype_dir> --output <output_dir>
```

示例：

```bash
uv run python3 -m proto_to_requirement.cli /path/to/mockitt-export --output output/mockitt-export
```

解析完成后，**字段分析自动执行**，产出以下文件：

- `prototype-analysis.md`：给后续清单生成和 PRD 编写使用的解析报告。
- `structured-data.json`：机器可读的页面、交互、文本、业务规则和未解析项。
- `completeness-report.json`：完整度和可开发性评估。
- `requirements.md`：基于原型生成的需求草稿，不是最终 BDD 工程 PRD。
- `field-analysis.md`：**字段与页面结构分析报告**，包含：
  - 页面结构（层级、区域、导航）
  - 18 维度字段说明表（字段名称、所属页面、所属区域、业务含义、是否前端展示、是否后端字段、是否可搜索、是否可新增、是否可编辑、是否必填、填写形式、格式要求、枚举值或数据来源、默认值、依赖关系、权限规则、置信度、信息来源）
  - 操作逻辑（CRUD、按钮行为、批量操作）
  - 字段与操作依赖关系
  - 初步 Given-When-Then 场景
  - 待产品确认问题（仅低置信度/高风险/有冲突的项目，选择题格式）

**注意**：字段分析只描述原型 UI 中出现的字段，**不映射到数据库字段名或后端 schema**。这是为了防止下游 coding agent 误将字段描述当作数据库迁移指令，破坏已有数据结构。

## Stage 2: 生成 PM 提问清单

当 Stage 1 输出存在低置信度字段、权限未明确、修改边界不清、业务逻辑缺失等问题时，使用 `proto-pm-interviewer` 生成 **会议用提问清单**。

输入材料：

- `prototype-analysis.md`
- `structured-data.json`
- `completeness-report.json`
- `field-analysis.md`（重点参考其中的待确认问题和低置信度字段）
- Stage 1 生成的 `requirements.md` 草稿
- 人工 PRD、截图、流程图、会议纪要、现有系统资料等辅助材料

产出内容：

- `pm-question-checklist.md`：**可打印/投屏的提问清单**
  - 按业务模块分组（不按技术维度）
  - 尽量设计为**选择题**（A/B/C/D），减少 PM 认知负担
  - 每题标注优先级（🔴P0/🟡P1/🔵P2）和工程影响
  - 每题附带证据来源说明
  - 预留备注栏供会上记录补充说明
- `pm-answer-template.md`：**标准解答模板**
  - 预填问题编号和选项
  - 可手动填写，也可将会议记录发给 AI 自动填写

只问低置信度、高风险、存在冲突的问题——不问所有字段。

## Stage 3: PM 会议与解答收集

这是用户手动操作的步骤：

1. 打印或投屏 `pm-question-checklist.md`
2. 在 PM 会议上按清单提问，圈选答案或记录备注
3. 会后将以下任一材料交给 AI：
   - **方式 A**：直接发送会议记录（文字、录音转写、聊天记录均可），AI 自动根据会议记录填写 `pm-answer-template.md`
   - **方式 B**：手动填写 `pm-answer-template.md`
4. AI 自动填写时会标注每个答案的来源：`PM 明确回答` / `会议内容推断` / `未提及`
5. 如果会议中出现了清单外的新需求，AI 会在模板末尾记录

## Stage 4: 编写 BDD 工程版 PRD

当 Stage 1 解析证据、字段分析和 Stage 3 PM 解答文档都准备好后，使用 `bdd-engineering-prd-writer`。

输入材料：

- Stage 1 的解析报告和结构化 JSON
- Stage 1 的字段分析报告 `field-analysis.md`
- Stage 3 的 PM 解答文档 `pm-answer-template.md`
- 人工 PRD 或需求说明
- 其他辅助材料，如截图、系统文档、流程图、会议纪要、代码仓库线索

最终输出：

- `bdd-engineering-prd.md`

文档必须包含：

- 开发入口摘要
- 必须交付的 Epic
- P0/P1/P2 待确认项
- 证据映射（含字段分析置信度参考）
- 人工确认映射
- Feature / Rule / Scenario
- Given / When / Then 验收场景
- 领域模型与数据结构说明（基于字段分析的 18 维度表，不映射数据库）
- 接口与后端能力说明
- 工程实施拆解建议
- coding agent 仓库检查守则

关键规则：

- 未确认的 P0 不能写成验收标准。
- 每条确定需求都要有来源：原型解析、字段分析、PM 确认、人工 PRD、辅助材料或仓库证据。
- 不要把页面清单、组件清单、交互表直接当 PRD 正文。
- 不要虚构 API、数据库字段、枚举、权限矩阵、外部服务、消息模板或定时任务。
- coding agent 开发前必须先查目标仓库已有字段、表、接口、枚举、权限和任务实现。

## 推荐使用顺序

1. 准备 Mockitt/MoDao 原型导出目录和辅助材料。
2. 运行 `proto-to-requirement` 生成解析报告和字段分析。
3. 检查 `completeness-report.json` 和 `field-analysis.md`，找出证据薄弱点和低置信度字段。
4. 使用 `proto-pm-interviewer` 生成 PM 提问清单。
5. 带清单参加 PM 会议，收集解答。
6. 将会议记录发送给 AI，自动填写解答模板。
7. 使用 `bdd-engineering-prd-writer` 编写最终 BDD 工程 PRD。
8. 交给 coding agent 前，确认 PRD 中的 P0、证据映射、仓库检查项都已明确。

## 验证命令

```bash
uv run python3 -m proto_to_requirement.cli --help
uv run pytest
```

当前 MVP 不支持 Axure、Figma、在线原型 URL、浏览器渲染或视觉模型分析。这些能力需要作为后续任务单独扩展。
