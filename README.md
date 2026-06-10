# proto-to-requirement Skill Suite 用法

本项目是一组三段式需求工程 skill，用于把墨刀/Mockitt 原型证据、产品经理人工确认和辅助材料整理成可交给 coding agent 开发的 BDD 工程版 PRD。

## 工作流

```text
墨刀/Mockitt 原型导出
  -> Stage 1: proto-to-requirement
  -> Stage 2: proto-pm-interviewer
  -> Stage 3: bdd-engineering-prd-writer
  -> BDD 工程版 PRD
```

三段职责必须分开：

| 阶段 | Skill | 作用 | 输出 |
|------|-------|------|------|
| Stage 1 | `proto-to-requirement` | 解析原型页面、交互、文本、批注和不确定项 | `prototype-analysis.md`, `structured-data.json`, `completeness-report.json`, `requirements.md` 草稿 |
| Stage 2 | `proto-pm-interviewer` | 根据解析证据采访产品经理，确认权限、修改边界、业务逻辑和缺失决策 | 采访问题清单、PM 采访报告 |
| Stage 3 | `bdd-engineering-prd-writer` | 整合解析证据、PM 确认、人工 PRD 和辅助材料，编写最终 BDD 工程 PRD | `bdd-engineering-prd.md` |

## Stage 1: 解析墨刀原型

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

解析完成后重点查看：

- `prototype-analysis.md`：给后续采访和 PRD 编写使用的解析报告。
- `structured-data.json`：机器可读的页面、交互、文本、业务规则和未解析项。
- `completeness-report.json`：完整度和可开发性评估。
- `requirements.md`：基于原型生成的需求草稿，不是最终 BDD 工程 PRD。

注意：Stage 1 只负责提取事实和标注不确定性，不负责补全权限矩阵、后端接口、数据库字段、审批链、业务计算公式等原型中没有的内容。

## Stage 2: 采访产品经理

当 Stage 1 输出存在权限、修改边界、业务逻辑、状态流转、异常流程、数据归属或缺失材料时，使用 `proto-pm-interviewer`。

输入材料：

- `prototype-analysis.md`
- `structured-data.json`
- `completeness-report.json`
- Stage 1 生成的 `requirements.md` 草稿
- 人工 PRD、截图、流程图、会议纪要、现有系统资料等辅助材料

产出内容：

- 采访问题清单：按 P0/P1/P2 分级。
- PM 采访报告：记录已确认决策、被否定假设、未回答问题、缺失背景资料和后续负责人。

采访重点：

- 权限：谁能看、建、改、删、审核、撤回。
- 修改边界：哪些字段在什么状态可编辑，哪些不可改。
- 业务逻辑：主流程、计算、校验、跨实体规则。
- 状态流转：合法状态、触发条件、不可逆流转。
- 异常流程：重复提交、超时、并发编辑、撤销、回滚。
- 数据归属：数据所有者、转移、跨组织可见性。
- 审批/撤回：审批链、委托、升级、召回、撤回后状态。
- 缺失材料：外部接口、模板、合规约束、上下游系统说明。

规则：不要替 PM 编答案。没有回答就标记为 `Unanswered`，缺资料就标记为 `Missing context`。

## Stage 3: 编写 BDD 工程版 PRD

当 Stage 1 解析证据和 Stage 2 PM 采访报告都准备好后，使用 `bdd-engineering-prd-writer`。

输入材料：

- Stage 1 的解析报告和结构化 JSON
- Stage 2 的 PM 采访报告
- 人工 PRD 或需求说明
- 其他辅助材料，如截图、系统文档、流程图、会议纪要、代码仓库线索

最终输出：

- `bdd-engineering-prd.md`

文档必须包含：

- 开发入口摘要
- 必须交付的 Epic
- P0/P1/P2 待确认项
- 证据映射
- 人工确认映射
- Feature / Rule / Scenario
- Given / When / Then 验收场景
- 领域模型与数据结构说明
- 接口与后端能力说明
- 工程实施拆解建议
- coding agent 仓库检查守则

关键规则：

- 未确认的 P0 不能写成验收标准。
- 每条确定需求都要有来源：原型解析、PM 确认、人工 PRD、辅助材料或仓库证据。
- 不要把页面清单、组件清单、交互表直接当 PRD 正文。
- 不要虚构 API、数据库字段、枚举、权限矩阵、外部服务、消息模板或定时任务。
- coding agent 开发前必须先查目标仓库已有字段、表、接口、枚举、权限和任务实现。

## 推荐使用顺序

1. 准备 Mockitt/MoDao 原型导出目录和辅助材料。
2. 运行 `proto-to-requirement` 生成解析报告。
3. 检查 `completeness-report.json`，找出证据薄弱点。
4. 使用 `proto-pm-interviewer` 生成采访问题并采访 PM。
5. 整理 PM 采访报告，关闭所有 P0 或明确标记阻塞。
6. 使用 `bdd-engineering-prd-writer` 编写最终 BDD 工程 PRD。
7. 交给 coding agent 前，确认 PRD 中的 P0、证据映射、仓库检查项都已明确。

## 验证命令

```bash
uv run python3 -m proto_to_requirement.cli --help
uv run pytest
```

当前 MVP 不支持 Axure、Figma、在线原型 URL、浏览器渲染或视觉模型分析。这些能力需要作为后续任务单独扩展。
