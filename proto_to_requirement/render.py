"""Output rendering for PRD and intermediate prototype analysis artifacts."""

import json
import re
from collections import Counter
from pathlib import Path


def render_outputs(structured_data: dict, output_dir: str) -> None:
    """Write PRD, intermediate analysis, and machine-readable outputs."""
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    _render_requirements_md(structured_data, out_path / "requirements.md")
    _render_prototype_analysis_md(structured_data, out_path / "prototype-analysis.md")
    _render_structured_json(structured_data, out_path / "structured-data.json")
    _render_completeness_report(structured_data, out_path / "completeness-report.json")


def compute_completeness(structured_data: dict) -> dict:
    """Compute completeness scores from extracted data."""
    pages = structured_data.get("pages", [])
    interactions = structured_data.get("interactions", [])
    texts = structured_data.get("texts", [])
    business_rules = structured_data.get("business_rules", [])
    unresolved = structured_data.get("unresolved", [])

    total_interactions = len(interactions)
    resolved = sum(
        1 for i in interactions if i.get("confidence") in ("fact", "inferred")
    )

    page_coverage = 1.0 if pages else 0.0
    interaction_mapping = resolved / total_interactions if total_interactions > 0 else 0.0
    text_extraction = min(1.0, len(texts) / max(1, len(pages) * 2))
    business_rule_extraction = min(1.0, len(business_rules) / max(1, len(pages) * 0.5))
    unknown_rate = 1.0 - (len(unresolved) / max(1, total_interactions + len(unresolved)))

    overall = (
        page_coverage * 0.20
        + interaction_mapping * 0.25
        + text_extraction * 0.20
        + business_rule_extraction * 0.10
        + unknown_rate * 0.25
    )

    return {
        "page_coverage": round(page_coverage, 2),
        "interaction_mapping": round(interaction_mapping, 2),
        "text_extraction": round(text_extraction, 2),
        "business_rule_extraction": round(business_rule_extraction, 2),
        "unknown_rate": round(unknown_rate, 2),
        "overall_implementability": round(overall, 2),
    }


def _render_requirements_md(data: dict, filepath: Path) -> None:
    """Render the business PRD Markdown document."""
    tool_info = data.get("tool_info", {})
    pages = data.get("pages", [])
    interactions = data.get("interactions", [])
    texts = data.get("texts", [])
    business_rules = data.get("business_rules", [])
    unresolved = data.get("unresolved", [])
    completeness = data.get("completeness", {})

    out: list[str] = []

    def w(line: str = "") -> None:
        out.append(line + "\n")

    page_names = _unique_page_names(pages)
    module_counts = _module_counts(page_names)
    parsed_interactions = [
        ix for ix in interactions if ix.get("confidence") in ("fact", "inferred")
    ]
    resolved_page_interactions = [ix for ix in parsed_interactions if ix.get("target_page")]
    meaningful_rules = _meaningful_business_rules(business_rules)
    field_candidates = _field_candidates(texts)
    field_summary_rows = _field_summary_rows(field_candidates)
    roles = _infer_roles(page_names)
    domain_summary = _infer_domain_summary(page_names)

    project_name = tool_info.get("project_name", "未知项目")

    w(f"# {project_name} — 需求规格说明书")
    w()
    w(f"> 本文档基于 {tool_info.get('tool_type', 'unknown')} 交互原型（{len(pages)} 个页面状态，{len(interactions)} 个交互点，{len(texts)} 条文本/字段线索）逆向分析生成。")
    w("> “原型未提供”表示原型数据中未体现该信息，需通过需求评审、视觉稿或业务规则补充确认。解析明细见 `prototype-analysis.md`，不作为最终 PRD 正文。")
    w()

    w("## 1. 业务背景")
    w()
    w("### 1.1 为什么做这个需求")
    w()
    w(f"{project_name} 是基于原型识别出的业务管理系统。{domain_summary}。该需求的核心目标是把原型中的工作入口、业务流程、数据对象、权限边界和异常处理沉淀为可评审、可开发、可验收的需求规格说明书。`推断`")
    w()
    w("核心定位：")
    for line in _positioning_lines(page_names):
        w(f"- **{line[0]}**：{line[1]}")
    w()
    w("### 1.2 解决的业务问题")
    w()
    w("| 业务痛点 | 解决方案 |")
    w("|---------|---------|")
    for pain, solution in _business_problem_rows(page_names):
        w(f"| {pain} | {solution} |")
    w()
    w(f"> 原型来源：{tool_info.get('tool_type', 'unknown')} 离线导出包；当前解析不包含视觉识别、后端接口或数据库真实结构。`事实`")
    w()

    w("## 2. 用户角色")
    w()
    w("| 用户/角色 | 原型依据 | 权限边界 | 置信度 |")
    w("|-----------|----------|----------|--------|")
    for role, evidence, boundary, confidence in roles:
        w(f"| {role} | {evidence} | {boundary} | {confidence} |")
    w("| 未明确角色 | 原型未提供登录用户类型、组织层级和岗位权限配置 | 需补充角色清单、数据范围、审批职责和菜单权限 | 未知 |")
    w()

    w("## 3. 全局布局结构")
    w()
    w("### 3.1 页面框架")
    w()
    w("```text")
    w("┌──────────────────────────────────────────────┐")
    w("│ 头部：系统标识 / 用户信息 / 语言或账号入口     │")
    w("├────────┬─────────────────────────────────────┤")
    w("│ 菜单栏  │ 内容区域：列表、详情、表单、弹窗、流程 │")
    w("│        │                                     │")
    for module in _navigation_modules(page_names)[:10]:
        w(f"│ {module[:6].ljust(6)} │                                     │")
    w("└────────┴─────────────────────────────────────┘")
    w("```")
    w()
    w("### 3.2 模块导航映射")
    w()
    w("| 模块 | 入口/页面依据 | 主要能力 |")
    w("|------|---------------|----------|")
    for module, evidence, capability in _navigation_rows(page_names):
        w(f"| {module} | {evidence} | {capability} |")
    w()
    w("### 3.3 全局交互约定")
    w()
    w(f"- {_interaction_summary(interactions, parsed_interactions)}")
    w("- 页面跳转用于模块进入和详情切换；弹窗/浮层用于新增、编辑、审核、确认等短流程；状态切换用于 Tab、步骤、折叠展开或组件状态变化。`推断`")
    w("- 返回/关闭动作需保持上下文，避免丢失已填写表单和当前筛选条件。`推断`")
    w()

    w("## 4. 页面详细规格")
    w()
    for idx, spec in enumerate(_module_specs(pages, parsed_interactions), start=1):
        w(f"### 4.{idx} {spec['module']}")
        w()
        w(f"**模块定位**：{spec['description']}")
        w()
        w("**业务流程**：")
        for step in spec["flow"]:
            w(f"- {step}")
        w()
        w("**关键页面/状态**：")
        w()
        w("| 页面 | 页面 ID | 路由/说明 |")
        w("|------|---------|-----------|")
        for page in spec["pages"]:
            w(f"| {_escape_table(page['name'])} | `{_escape_table(page['id'])}` | {_escape_table(page['route'])} |")
        w()
        w("**页面结构**：")
        for item in spec["structure"]:
            w(f"- {item}")
        w()
        w("**关键交互**：")
        if spec["interactions"]:
            w()
            w("| 交互类型 | 目标/结果 | 数量 |")
            w("|----------|-----------|-----:|")
            for interaction_type, target, count in spec["interactions"]:
                w(f"| {interaction_type} | {_escape_table(target)} | {count} |")
        else:
            w("- 原型未解析出该模块的明确交互；需人工补充入口、提交、返回和异常处理。`未知`")
        w()
        w("**状态与异常**：")
        for item in spec["states"]:
            w(f"- {item}")
        w()
        w("**数据来源**：")
        for source in spec["data_sources"]:
            w(f"- {source}")
        w()

    w("### 4.99 主流程摘要")
    w()
    for line in _main_flow_lines(page_names):
        w(f"- {line}")
    if not resolved_page_interactions:
        w("- 原型数据中未解析出可靠的页面跳转链路，需人工按原型补充主流程。`未知`")
    w()

    w("## 5. 异常流程")
    w()
    w("| 场景 | 原型体现 | 说明 |")
    w("|------|---------|------|")
    w("| 审核失败 | 若存在审核失败、驳回、失败弹窗等页面/状态，仅能证明失败态入口存在 | 需补充失败原因、驳回后状态、重新提交和通知规则 |")
    w("| 操作失败 | 原型未提供接口失败码、错误态和错误文案 | 开发前需补充失败原因、提示文案、是否允许重试 |")
    w("| 撤回/撤销 | 原型未提供完整状态机 | 需补充哪些状态允许撤回、撤回后数据流向、操作记录 |")
    w("| 重复提交 | 原型未提供幂等规则 | 提交类按钮应明确防重复策略、重复提交提示和后端幂等键 |")
    w("| 超时处理 | 原型未提供会话超时、接口超时或审批超时策略 | 需补充超时阈值、前端提示、任务回收或重试机制 |")
    w("| 返回/关闭 | 解析到返回和弹窗类交互 | 关闭弹窗、返回上级时需保留必要上下文 |")
    w(f"| 无法解析的交互目标 | 当前存在 {len(unresolved)} 个未解析交互目标 | 需逐项确认是否为弹窗、状态切换、页面跳转或无效交互 |")
    if unresolved:
        w()
        w(f"- {_unresolved_summary(unresolved)}")
    w()

    w("## 6. 业务规则")
    w()
    w("### 6.1 状态流转")
    w()
    for line in _state_rule_lines(page_names):
        w(f"- {line}")
    w()
    w("### 6.2 计算规则")
    w()
    w("| 计算项 | 规则 | 来源 |")
    w("|--------|------|------|")
    for item, rule, source in _calculation_rows(page_names):
        w(f"| {item} | {rule} | {source} |")
    w()
    w("> 具体计算公式、舍入规则、币种、税费口径和边界条件未在原型中完整展示。")
    w()
    w("### 6.3 可确认规则")
    w()
    if meaningful_rules:
        for rule in meaningful_rules[:80]:
            w(f"- {rule} `事实`")
    else:
        w("- 未从批注中提取到明确业务规则；当前批注多为“批注 1/打点批注”等占位名，不足以作为业务规则。`未知`")
    w("- 限制条件：原型未提供提交次数、文件大小、产品选择范围、审批时限等限制；实现前需补充。`未知`")
    w()

    w("## 7. 数据规则")
    w()
    w("### 7.1 核心字段")
    w()
    w("| 数据分组 | 字段含义 | 数据来源 | 校验规则 | 置信度 |")
    w("|----------|----------|----------|----------|--------|")
    for group, meaning, source, validation, confidence in field_summary_rows:
        w(f"| {_escape_table(group)} | {_escape_table(meaning)} | {_escape_table(source)} | {_escape_table(validation)} | {confidence} |")
    if not field_summary_rows:
        w("| 未识别 | 原型数据中未提取到稳定字段分组 | 需人工补充字段清单 | 需补充必填、格式、枚举、长度和唯一性 | 未知 |")
    w()
    w("### 7.2 校验规则")
    w()
    w("- 数据来源：当前仅能确认字段/文案来自原型组件；接口来源、数据库表、外部系统来源未提供。`未知`")
    w("- 数据去向：保存、提交、审批、结算等动作涉及的数据表和消息任务未在原型中定义。`未知`")
    w("- 文件类数据：如页面包含文件、资料、计划书等线索，需补充文件类型、大小限制、存储位置和访问权限。`未知`")
    w("- 前后端需统一必填、格式、枚举、长度、唯一性、金额精度和文件限制规则。`推断`")
    w()

    w("## 8. 权限规则")
    w()
    w("| 权限对象 | 查看权限 | 操作权限 | 审批权限 | 置信度 |")
    w("|----------|----------|----------|----------|--------|")
    for role, evidence, boundary, confidence in roles:
        w(f"| {role} | 需按角色开放相关菜单和页面 | {boundary} | 原型未提供审批矩阵 | {confidence} |")
    w("| 页面级权限 | 原型提供页面集合但未提供菜单授权配置 | 需补充页面与角色的授权关系 | 需补充审批节点和审批人规则 | 未知 |")
    w("| 数据级权限 | 原型未提供组织、团队、本人/全部数据范围 | 需补充数据范围规则 | 需补充跨角色查看和审批边界 | 未知 |")
    w()

    w("## 9. 验收标准")
    w()
    w("### 9.1 功能验收")
    w()
    w("- 页面范围：影响范围内的页面均可访问，页面标题、主要文本、主要按钮与原型一致。`事实`")
    w("- 主流程：主流程章节列出的正常业务路径可完成端到端操作；已解析交互应按目标页面或弹窗实现。`推断`")
    for line in _acceptance_lines(page_names):
        w(f"- {line}")
    w()
    w("### 9.2 交互验收")
    w()
    w("- 所有页面跳转、弹窗/浮层、返回/关闭、状态切换交互均按解析目标实现；未解析交互必须在评审中确认后实现。`事实/推断`")
    w("- 弹窗可正常打开和关闭；返回操作不丢失必要上下文；步骤条、Tab、分页、筛选、表单状态随流程正确更新。`推断`")
    w("- 异常流程：失败、撤回、重复提交、超时等场景需有明确提示、状态回滚或重试策略；未确认项不得静默上线。`未知`")
    w("- 业务规则：已确认规则必须实现；未知计算公式、状态机、限制条件必须在评审后补齐并形成测试用例。`未知`")
    w("- 数据规则：字段含义、来源、校验、枚举、必填和唯一性规则经产品/业务确认后，前后端校验一致。`未知`")
    w("- 权限规则：角色可见菜单、可操作按钮、可审批任务与补充权限矩阵一致，并覆盖越权访问测试。`未知`")
    w(f"- 文档完整性：当前可实现度评分为 {completeness.get('overall_implementability', 0):.0%}；低于 75% 时，不建议直接进入完整开发，应先补齐未知项。`事实`")
    w()

    w("## 10. 影响范围")
    w()
    w(f"### 10.1 涉及页面与模块（{len(pages)} 个页面状态）")
    w()
    w("| 模块 | 估计页面数 | 关键页面 |")
    w("|------|:-------:|---------|")
    for module, count, key_pages in _impact_module_rows(pages):
        w(f"| {module} | {count} | {_escape_table(key_pages)} |")
    w(f"- {_module_summary(module_counts, len(pages))}")
    w("- 实现范围按业务区域和系统边界确认；详细原型解析明细见 `prototype-analysis.md` 与 `structured-data.json`。`事实`")
    w()
    w("### 10.2 涉及 API 模块（推断）")
    w()
    w("| API 模块 | 主要端点/能力 |")
    w("|----------|---------------|")
    for api, capability in _api_module_rows(page_names):
        w(f"| `{api}` | {capability} |")
    w()
    w("### 10.3 涉及数据表（推断）")
    w()
    w("| 数据表 | 关键字段/用途 |")
    w("|--------|--------------|")
    for table, fields in _data_table_rows(page_names):
        w(f"| `{table}` | {fields} |")
    w()
    w("### 10.4 外部系统依赖")
    w()
    w("| 系统 | 用途 |")
    w("|------|------|")
    for system, usage in _external_dependency_rows(page_names):
        w(f"| {system} | {usage} |")
    w()

    w("## 11. 附录")
    w()
    w("### 11.1 交互类型统计")
    w()
    w("| 类型 | 数量 | 说明 |")
    w("|------|:----:|------|")
    for interaction_type, count, description in _interaction_type_rows(interactions):
        w(f"| {interaction_type} | {count} | {description} |")
    w(f"| **总计** | **{len(interactions)}** | 已解析 {len(parsed_interactions)}，未解析 {len(unresolved)} |")
    w()
    w("### 11.2 完整性评估")
    w()
    w("| 维度 | 分数 |")
    w("|------|-----:|")
    w(f"| 页面覆盖 | {completeness.get('page_coverage', 0):.0%} |")
    w(f"| 交互解析 | {completeness.get('interaction_mapping', 0):.0%} |")
    w(f"| 文本提取 | {completeness.get('text_extraction', 0):.0%} |")
    w(f"| 业务规则提取 | {completeness.get('business_rule_extraction', 0):.0%} |")
    w(f"| 未知项控制 | {completeness.get('unknown_rate', 0):.0%} |")
    w(f"| **整体可实现度** | **{completeness.get('overall_implementability', 0):.0%}** |")
    w()
    w("### 11.3 待补充信息")
    w()
    w("- 后端 API、请求/响应结构、错误码、鉴权方式和幂等策略。")
    w("- 数据表结构、索引、枚举、审计日志和数据迁移策略。")
    w("- 完整权限矩阵、组织/岗位/角色/数据范围边界。")
    w("- 计算公式、状态机、超时策略、失败提示和通知规则。")
    w("- 完整交互映射、页面库存和组件级证据详见 `prototype-analysis.md`。")
    w()

    filepath.write_text("".join(out), encoding="utf-8")


def _render_prototype_analysis_md(data: dict, filepath: Path) -> None:
    """Render an intermediate parsing report for a fresh PRD-writing subagent."""
    tool_info = data.get("tool_info", {})
    pages = data.get("pages", [])
    interactions = data.get("interactions", [])
    texts = data.get("texts", [])
    business_rules = data.get("business_rules", [])
    unresolved = data.get("unresolved", [])
    completeness = data.get("completeness", {})

    out: list[str] = []

    def w(line: str = "") -> None:
        out.append(line + "\n")

    resolved = [
        ix for ix in interactions if ix.get("confidence") in ("fact", "inferred")
    ]
    page_names = _unique_page_names(pages)

    w("# 原型解析报告（中间产物）")
    w()
    w("> 本文件不是最终 PRD。它面向一个全新上下文的 PRD 写作 subagent，用于说明原型中实际提取到了什么、哪些内容可靠、哪些内容缺失。最终对用户交付请使用 `requirements.md`。")
    w()

    w("## 1. 解析概览")
    w()
    w(f"- 工具类型：{tool_info.get('tool_type', 'unknown')}")
    w(f"- 项目名称：{tool_info.get('project_name', 'Unknown Project')}")
    w(f"- 页面数：{len(pages)}")
    w(f"- 交互数：{len(interactions)}")
    w(f"- 已解析交互：{len(resolved)}")
    w(f"- 未解析交互：{len(unresolved)}")
    w(f"- 文本条目：{len(texts)}")
    w(f"- 批注候选：{len(business_rules)}")
    w("- 置信度：`fact` 为直接提取，`inferred` 为结构推断，`unknown` 为原型未提供或未解析。")
    w()

    w("## 2. 页面清单")
    w()
    w("| 页面ID | 页面名称 | 估算路由 |")
    w("|--------|----------|----------|")
    for page in pages[:300]:
        w(f"| {_escape_table(page.get('page_id', ''))} | {_escape_table(page.get('page_name', ''))} | {_escape_table(page.get('estimated_route', ''))} |")
    if len(pages) > 300:
        w(f"| ... | 其余 {len(pages) - 300} 个页面见 structured-data.json | ... |")
    w()

    w("## 3. 页面组统计")
    w()
    w("| 页面组 | 页面数 |")
    w("|--------|-------:|")
    for module, count in _module_counts(page_names):
        w(f"| {_escape_table(module)} | {count} |")
    w()

    w("## 4. 已解析交互")
    w()
    w("| 触发组件 | 类型 | 目标页面 | 置信度 |")
    w("|----------|------|----------|--------|")
    for ix in resolved[:300]:
        source = ix.get("source_component") or ix.get("source_component_id") or "未命名组件"
        target = ix.get("target_name") or ix.get("target_page") or ix.get("target_id") or ""
        w(f"| {_escape_table(source)} | {_escape_table(ix.get('interaction_type', ''))} | {_escape_table(target)} | {_escape_table(ix.get('confidence', ''))} |")
    if len(resolved) > 300:
        w(f"| ... | ... | 其余 {len(resolved) - 300} 条见 structured-data.json | ... |")
    w()

    w("## 5. 未解析交互")
    w()
    w("| 触发组件 | 类型 | 原始目标ID |")
    w("|----------|------|------------|")
    for item in unresolved[:300]:
        source = item.get("source_component") or item.get("source_component_id") or "未命名组件"
        w(f"| {_escape_table(source)} | {_escape_table(item.get('interaction_type', ''))} | {_escape_table(item.get('raw_target_id', ''))} |")
    if len(unresolved) > 300:
        w(f"| ... | ... | 其余 {len(unresolved) - 300} 条见 structured-data.json |")
    w()

    w("## 6. 文本与字段线索")
    w()
    w("| 文本/字段候选 | 来源组件 | 字段来源 |")
    w("|---------------|----------|----------|")
    for item in texts[:300]:
        w(f"| {_escape_table(item.get('text_content', ''))} | {_escape_table(item.get('component_name', ''))} | {_escape_table(item.get('field', ''))} |")
    if len(texts) > 300:
        w(f"| ... | 其余 {len(texts) - 300} 条见 structured-data.json | ... |")
    w()

    w("## 7. 批注与业务规则线索")
    w()
    meaningful_rules = _meaningful_business_rules(business_rules)
    if meaningful_rules:
        for rule in meaningful_rules[:200]:
            w(f"- {rule}")
    else:
        w("- 未提取到明确业务规则；批注多为占位名。")
    w()

    w("## 8. PRD 写作提示")
    w()
    w("- 最终 PRD 必须使用模板章节：业务背景、用户角色、全局布局结构、页面详细规格、异常流程、业务规则、数据规则、权限规则、验收标准、影响范围、附录。")
    w("- 不要把本解析报告直接交付给用户。")
    w("- 对接口、数据表、权限矩阵、状态机、计算公式等原型未提供的信息，必须标注为“原型未提供/需补充”，不能编造成事实。")
    w("- 页面名称和已解析交互用于推断模块流程、入口、状态和关键操作；不要把页面清单或交互表直接复制成 PRD 正文。")
    w()

    w("## 9. 完整性评分")
    w()
    w("| 维度 | 分数 |")
    w("|------|-----:|")
    w(f"| 页面覆盖 | {completeness.get('page_coverage', 0):.0%} |")
    w(f"| 交互解析 | {completeness.get('interaction_mapping', 0):.0%} |")
    w(f"| 文本提取 | {completeness.get('text_extraction', 0):.0%} |")
    w(f"| 业务规则提取 | {completeness.get('business_rule_extraction', 0):.0%} |")
    w(f"| 未知项控制 | {completeness.get('unknown_rate', 0):.0%} |")
    w(f"| 整体可实现度 | {completeness.get('overall_implementability', 0):.0%} |")
    w()

    filepath.write_text("".join(out), encoding="utf-8")


def _unique_page_names(pages: list[dict]) -> list[str]:
    names: list[str] = []
    seen = set()
    for page in pages:
        name = str(page.get("page_name") or page.get("page_id") or "").strip()
        if not name or name in seen:
            continue
        seen.add(name)
        names.append(name)
    return names


def _module_counts(page_names: list[str]) -> list[tuple[str, int]]:
    counter: Counter[str] = Counter()
    for name in page_names:
        module = re.split(r"[-（(]", name, maxsplit=1)[0].strip() or name
        if module.startswith("rbp"):
            module = "未命名页面"
        counter[module] += 1
    return counter.most_common()


def _module_blueprints() -> list[dict]:
    return [
        {
            "module": "工作台",
            "keywords": ["工作台", "Dashboard", "首页", "待办", "快捷入口"],
            "description": "作为登录后的统一入口，聚合统计、待办和常用业务入口。",
            "capability": "展示经营概览、待办任务和核心模块快捷入口",
            "flow": [
                "用户登录后进入工作台，系统加载统计指标、待办事项和快捷入口。`推断`",
                "用户从快捷入口进入产品、预约、保单、用户等业务模块。`推断`",
                "用户点击待办项进入对应业务列表或处理页面，并带入待办状态筛选。`推断`",
            ],
            "structure": ["顶部统计/指标区", "快捷入口区", "待办事项区", "趋势或日历辅助区"],
            "states": ["统计和待办加载失败时需展示可重试提示；原型未提供具体错误态。`未知`"],
            "data_sources": ["统计数据来自后端聚合接口；具体 API 未提供。`未知`", "待办数量来自各业务模块状态汇总。`推断`"],
        },
        {
            "module": "产品管理",
            "keywords": ["产品库", "产品管理", "产品详情", "产品资料", "AI产品", "新增产品", "编辑产品"],
            "description": "集中管理和查询保险产品、产品资料、计划书及相关销售资料。",
            "capability": "产品查询、详情查看、资料维护、上下架、AI 分析或文件解析",
            "flow": [
                "用户进入产品库或产品管理后，通过分类、关键字等条件筛选产品。`推断`",
                "用户查看产品详情，切换基本信息、官方资料、优惠信息、内部资料、保司介绍等内容。`推断`",
                "具备维护权限的用户新增或编辑产品资料，并按规则保存、上架或下架。`推断`",
            ],
            "structure": ["筛选区", "产品列表/卡片区", "产品详情与资料 Tab", "新增/编辑/资料弹窗"],
            "states": ["产品上架/下架应有二次确认；AI 解析失败需允许重新解析。`推断`"],
            "data_sources": ["产品基础资料、分类、文件和上下架状态来自产品服务；具体 API 未提供。`未知`", "AI 分析依赖文件解析或外部 AI 服务。`推断`"],
        },
        {
            "module": "保单管理",
            "keywords": ["保单管理", "全部保单", "保单详情", "新增保单", "保单文件", "投保跟进", "缴费信息", "保全"],
            "description": "覆盖保单新增、详情维护、缴费信息、文件资料和投保跟进。",
            "capability": "保单列表、详情 Tab、新增多步骤表单、缴费维护、文件管理、投保跟进",
            "flow": [
                "用户从保单列表进入新增保单或保单详情。`推断`",
                "新增保单按基本信息、被保人、受益人、缴费、文件、其他信息等步骤录入。`推断`",
                "用户在保单详情中查看和维护不同 Tab 信息，并进入缴费、文件或投保跟进处理。`推断`",
            ],
            "structure": ["筛选区", "保单列表表格", "保单详情多 Tab", "新增保单多步骤表单", "缴费/文件/跟进子页面"],
            "states": ["草稿、待提交资料、待缴费、已生效、待续期等状态需形成状态机。`推断`"],
            "data_sources": ["保单主体、投保人/被保人/受益人、缴费、文件和跟进记录来自保单服务。`推断`"],
        },
        {
            "module": "预约管理",
            "keywords": ["预约", "双录", "健康信息", "声明", "保单持有人", "受保人资料", "计划书文件"],
            "description": "支持投保前预约、资料填写、双录处理和预约详情跟踪。",
            "capability": "在线预约、多步骤资料填写、预约列表、处理预约、预约详情",
            "flow": [
                "用户从在线预约入口发起预约，按步骤填写基本资料、持有人、受保人、受益人、健康声明和计划书文件。`推断`",
                "预约提交后进入预约列表或详情，业务人员可查看状态并处理预约。`推断`",
                "处理过程中应记录操作日志，并在预约完成或失败后更新状态。`推断`",
            ],
            "structure": ["步骤条", "多步骤表单", "预约列表", "预约详情", "处理记录"],
            "states": ["草稿、已提交、处理中、预约成功/失败、取消等状态需补充确认。`推断`"],
            "data_sources": ["预约主体资料、人员资料、健康声明、计划书文件和操作记录来自预约服务。`推断`"],
        },
        {
            "module": "服务费与结算",
            "keywords": ["服务费", "结算", "账单", "收入", "扣减", "费率", "审核", "缴费申请"],
            "description": "管理服务费配置、审核、账单、扣减、结算记录和收入信息。",
            "capability": "服务费配置、审核流、账单管理、扣减管理、发起结算、收入查看",
            "flow": [
                "财务或管理角色查看账单、收入、服务费配置和结算记录。`推断`",
                "用户发起缴费、扣减或结算相关操作后进入审核或确认流程。`推断`",
                "审核通过后更新账单、结算或收入状态；审核失败需记录原因并允许后续处理。`推断`",
            ],
            "structure": ["账单列表", "结算记录", "扣减管理", "服务费配置", "审核弹窗/状态页"],
            "states": ["待审核、审核中、审核成功、审核失败等状态需明确流转条件。`推断`"],
            "data_sources": ["账单、服务费费率、扣减、审核记录和收入明细来自财务/结算服务。`推断`"],
        },
        {
            "module": "续期与投保跟进",
            "keywords": ["续期", "待续期", "投保跟进", "核保", "跟进"],
            "description": "跟踪续期提醒、续期处理、投保进度和后续跟进事项。",
            "capability": "续期提醒、续期列表、投保跟进、核保单跟进",
            "flow": [
                "系统按保单到期或业务状态生成续期提醒和跟进任务。`推断`",
                "用户进入续期或投保跟进模块，查看待处理事项并更新跟进状态。`推断`",
                "跟进完成后应更新保单或预约相关状态，并保留操作记录。`推断`",
            ],
            "structure": ["提醒列表", "跟进列表", "详情/处理页", "状态记录"],
            "states": ["待跟进、跟进中、已完成、已取消等状态原型未完整提供。`未知`"],
            "data_sources": ["续期提醒来自保单到期信息；投保跟进来自保单/预约流程状态。`推断`"],
        },
        {
            "module": "系统管理",
            "keywords": ["用户", "角色", "岗位", "部门", "机构", "租户", "账号", "设置", "银行", "保险公司"],
            "description": "维护组织、用户、角色、岗位、部门、账号设置、保险公司等基础资料。",
            "capability": "组织与用户配置、角色权限、基础资料、银行账号和保险公司维护",
            "flow": [
                "管理员进入系统管理后维护组织、部门、岗位、角色和用户。`推断`",
                "用户进入账号与设置维护个人资料、银行账号或安全配置。`推断`",
                "管理员维护保险公司等基础资料，为产品、保单和结算提供引用数据。`推断`",
            ],
            "structure": ["组织/机构列表", "用户列表", "角色/岗位/部门配置", "账号设置", "保险公司列表"],
            "states": ["新增、编辑、删除、启用/停用等配置状态需补充权限和审计规则。`未知`"],
            "data_sources": ["组织、用户、角色、保险公司和账号配置来自系统管理服务。`推断`"],
        },
        {
            "module": "登录与账号",
            "keywords": ["登录"],
            "description": "提供系统登录、账号进入和基础会话能力。",
            "capability": "登录认证、账号入口、语言或用户信息展示",
            "flow": [
                "用户输入账号凭证完成登录，登录成功后进入工作台或默认业务入口。`推断`",
                "登录失败时应提示失败原因，支持重新输入或找回流程；原型未提供具体错误态。`未知`",
            ],
            "structure": ["登录表单", "账号信息区", "语言/用户入口"],
            "states": ["登录成功、登录失败、会话超时和退出登录规则需补充。`未知`"],
            "data_sources": ["认证、用户资料和会话状态来自认证服务。`推断`"],
        },
    ]


def _active_blueprints(page_names: list[str]) -> list[dict]:
    joined = " ".join(page_names)
    active = [
        blueprint for blueprint in _module_blueprints()
        if any(keyword in joined for keyword in blueprint["keywords"])
    ]
    if active:
        return active
    return [{
        "module": "核心业务流程",
        "keywords": [],
        "description": "原型命名不足以识别明确模块，需按业务评审补充模块边界。",
        "capability": "待补充",
        "flow": ["原型未提供足够命名来推断端到端流程，需人工补充。`未知`"],
        "structure": ["列表/详情/表单/弹窗结构需结合视觉稿补充。`未知`"],
        "states": ["状态流转和异常处理未提供。`未知`"],
        "data_sources": ["数据来源未提供。`未知`"],
    }]


def _positioning_lines(page_names: list[str]) -> list[tuple[str, str]]:
    rows = []
    for blueprint in _active_blueprints(page_names):
        if blueprint["module"] == "登录与账号":
            continue
        rows.append((blueprint["module"], blueprint["capability"]))
    return rows[:8] or [("核心业务流程", "按原型页面和交互整理业务能力，供评审确认")]


def _business_problem_rows(page_names: list[str]) -> list[tuple[str, str]]:
    rows = []
    active_modules = {bp["module"] for bp in _active_blueprints(page_names)}
    if "工作台" in active_modules:
        rows.append(("业务入口分散，待办和统计缺少统一承载", "工作台聚合指标、待办和快捷入口"))
    if "产品管理" in active_modules:
        rows.append(("产品资料、计划书和销售资料难以统一管理", "产品库集中维护产品资料、文件和上下架状态"))
    if "保单管理" in active_modules:
        rows.append(("保单录入、维护和跟进链路较长，容易遗漏资料", "保单列表、详情 Tab 和多步骤新增流程承载全生命周期管理"))
    if "预约管理" in active_modules:
        rows.append(("投保前预约和双录资料线下协调成本高", "在线预约、多步骤资料填写和处理预约流程线上化"))
    if "服务费与结算" in active_modules:
        rows.append(("服务费、账单、扣减和结算口径不透明", "服务费配置、审核、账单和结算记录统一管理"))
    if "系统管理" in active_modules:
        rows.append(("多组织、多角色权限和基础资料缺少统一配置", "系统管理维护组织、用户、角色、岗位和基础资料"))
    return rows or [("原型已表达业务入口，但业务痛点未显式提供", "需在需求评审中补充业务目标、指标和优先级")]


def _navigation_modules(page_names: list[str]) -> list[str]:
    return [blueprint["module"] for blueprint in _active_blueprints(page_names)]


def _navigation_rows(page_names: list[str]) -> list[tuple[str, str, str]]:
    rows = []
    for blueprint in _active_blueprints(page_names):
        evidence = _join_cn(_matching_page_names(page_names, blueprint["keywords"])[:3]) or "原型页面命名"
        rows.append((blueprint["module"], evidence, blueprint["capability"]))
    return rows


def _module_specs(pages: list[dict], interactions: list[dict]) -> list[dict]:
    page_names = _unique_page_names(pages)
    specs = []
    for blueprint in _active_blueprints(page_names):
        matched_pages = _matching_pages(pages, blueprint["keywords"])
        if not matched_pages and blueprint["keywords"]:
            continue
        if not matched_pages:
            matched_pages = pages[:5]
        specs.append({
            "module": blueprint["module"],
            "description": blueprint["description"],
            "flow": blueprint["flow"],
            "pages": _key_page_rows(matched_pages),
            "structure": blueprint["structure"],
            "interactions": _module_interaction_rows(blueprint, interactions),
            "states": blueprint["states"],
            "data_sources": blueprint["data_sources"],
        })
    return specs[:8]


def _matching_page_names(page_names: list[str], keywords: list[str]) -> list[str]:
    if not keywords:
        return page_names
    return [name for name in page_names if any(keyword in name for keyword in keywords)]


def _matching_pages(pages: list[dict], keywords: list[str]) -> list[dict]:
    if not keywords:
        return pages
    return [
        page for page in pages
        if any(keyword in str(page.get("page_name", "")) for keyword in keywords)
    ]


def _key_page_rows(pages: list[dict]) -> list[dict]:
    rows = []
    for page in pages[:6]:
        rows.append({
            "name": str(page.get("page_name", "")) or str(page.get("page_id", "")),
            "id": str(page.get("page_id", "")),
            "route": str(page.get("estimated_route", "")) or "原型未提供路由",
        })
    return rows


def _module_interaction_rows(blueprint: dict, interactions: list[dict]) -> list[tuple[str, str, int]]:
    keywords = blueprint.get("keywords", [])
    counter: Counter[tuple[str, str]] = Counter()
    for item in interactions:
        target = str(item.get("target_name") or item.get("target_page") or item.get("target_id") or "")
        source = str(item.get("source_component") or "")
        if keywords and not any(keyword in target or keyword in source for keyword in keywords):
            continue
        label = _interaction_label(str(item.get("interaction_type") or "unknown"))
        target_label = target if target else _target_type_label(str(item.get("target_type") or "unknown"))
        counter[(label, target_label)] += 1
    return [(label, target, count) for (label, target), count in counter.most_common(6)]


def _calculation_rows(page_names: list[str]) -> list[tuple[str, str, str]]:
    joined = " ".join(page_names)
    rows = []
    if any(word in joined for word in ["保费", "缴费", "保单"]):
        rows.append(("保费/缴费金额", "原型展示缴费和保单相关信息，但未提供完整计算公式", "保单/缴费信息"))
    if any(word in joined for word in ["服务费", "费率", "佣金"]):
        rows.append(("服务费", "按费率模板或业务配置计算，具体公式未提供", "服务费配置"))
    if any(word in joined for word in ["结算", "账单", "扣减"]):
        rows.append(("结算金额/扣减费用", "由账单、扣减和结算规则汇总，具体口径未提供", "结算管理"))
    if not rows:
        rows.append(("业务金额/统计指标", "原型未提供明确计算公式", "原型未提供"))
    return rows


def _acceptance_lines(page_names: list[str]) -> list[str]:
    lines = []
    for blueprint in _active_blueprints(page_names):
        if blueprint["module"] == "登录与账号":
            lines.append("[ ] 登录成功后进入默认业务入口，登录失败展示明确提示。`推断`")
        else:
            lines.append(f"[ ] {blueprint['module']}支持{blueprint['capability']}。`推断`")
    return lines[:12]


def _impact_module_rows(pages: list[dict]) -> list[tuple[str, str, str]]:
    page_names = _unique_page_names(pages)
    rows = []
    for blueprint in _active_blueprints(page_names):
        matched = _matching_pages(pages, blueprint["keywords"])
        if not matched and blueprint["keywords"]:
            continue
        key_pages = _join_cn([str(page.get("page_name", "")) for page in matched[:4]]) or "原型未提供"
        rows.append((blueprint["module"], str(len(matched)), key_pages))
    return rows or [("未识别模块", str(len(pages)), "详见 prototype-analysis.md")]


def _api_module_rows(page_names: list[str]) -> list[tuple[str, str]]:
    active = {bp["module"] for bp in _active_blueprints(page_names)}
    rows = []
    if "登录与账号" in active:
        rows.append(("/auth/*", "登录认证、会话管理、退出登录"))
    if "工作台" in active:
        rows.append(("/dashboard/*", "统计指标、待办汇总、快捷入口数据"))
    if "产品管理" in active:
        rows.append(("/products/*", "产品查询、详情、资料、上下架、AI 分析"))
    if "保单管理" in active:
        rows.append(("/policies/*", "保单 CRUD、详情 Tab、缴费、文件、跟进"))
    if "预约管理" in active:
        rows.append(("/appointments/*", "预约创建、详情、处理、操作记录"))
    if "服务费与结算" in active:
        rows.extend([
            ("/fees/*", "服务费配置、费率模板、审核记录"),
            ("/settlements/*", "账单、扣减、结算审核、结算记录"),
        ])
    if "续期与投保跟进" in active:
        rows.append(("/renewals/*", "续期提醒、续期处理、跟进任务"))
    if "系统管理" in active:
        rows.extend([
            ("/org/*", "租户、机构、部门、岗位、角色配置"),
            ("/users/*", "用户管理、账号设置、权限分配"),
        ])
    rows.append(("/files/*", "文件上传、预览、下载、删除"))
    return rows


def _data_table_rows(page_names: list[str]) -> list[tuple[str, str]]:
    active = {bp["module"] for bp in _active_blueprints(page_names)}
    rows = []
    if "系统管理" in active:
        rows.extend([
            ("organizations", "id, tenant_id, name, type, status"),
            ("users", "id, org_id, role_id, name, email, status"),
            ("roles", "id, name, permissions, data_scope"),
        ])
    if "产品管理" in active:
        rows.extend([
            ("products", "id, name, category, currency, status, metadata"),
            ("product_documents", "id, product_id, file_name, file_url, ai_parse_status"),
        ])
    if "保单管理" in active:
        rows.extend([
            ("policies", "id, policy_no, product_id, user_id, status"),
            ("policy_payments", "id, policy_id, amount, frequency, status"),
            ("policy_files", "id, policy_id, file_name, file_url"),
        ])
    if "预约管理" in active:
        rows.extend([
            ("appointments", "id, user_id, status, basic_info"),
            ("appointment_records", "id, appointment_id, action, operator, time"),
        ])
    if "服务费与结算" in active:
        rows.extend([
            ("fee_templates", "id, product_id, main_rate, addon_rate"),
            ("settlement_bills", "id, org_id, period, amount, status"),
            ("settlement_deductions", "id, bill_id, reason, amount"),
        ])
    if not rows:
        rows.append(("business_records", "原型未提供，需按业务对象补充"))
    rows.append(("audit_logs", "id, user_id, action, target_type, target_id, created_at"))
    return rows


def _external_dependency_rows(page_names: list[str]) -> list[tuple[str, str]]:
    joined = " ".join(page_names)
    rows = []
    if "AI" in joined or "解析" in joined:
        rows.append(("AI 服务", "产品资料 AI 分析、文件解析、问答辅助"))
    if "银行" in joined or "结算" in joined:
        rows.append(("银行/支付系统", "银行账号绑定、支付或结算对账"))
    if "保险公司" in joined or "保司" in joined:
        rows.append(("保险公司系统", "保险公司、产品、投保或双录资料对接"))
    rows.append(("文件存储服务", "产品资料、保单文件、计划书、图片/PDF 上传下载"))
    return rows


def _interaction_type_rows(interactions: list[dict]) -> list[tuple[str, int, str]]:
    descriptions = {
        "navigate": "路由跳转到目标页面",
        "modal": "打开弹窗或浮层",
        "back": "返回上一页或关闭当前层",
        "state_change": "Tab、步骤、折叠展开或组件状态变更",
    }
    counter = Counter(str(item.get("interaction_type") or "unknown") for item in interactions)
    return [
        (_interaction_label(interaction_type), count, descriptions.get(interaction_type, "未知交互类型"))
        for interaction_type, count in counter.most_common()
    ]


def _interaction_label(interaction_type: str) -> str:
    labels = {
        "navigate": "页面跳转",
        "modal": "弹窗/浮层",
        "back": "返回/关闭",
        "state_change": "状态切换",
    }
    return labels.get(interaction_type, interaction_type or "未知")


def _target_type_label(target_type: str) -> str:
    labels = {
        "page": "目标页面",
        "modal": "弹窗/浮层",
        "history": "返回上一页/关闭当前层",
        "state_change": "当前组件/页面状态切换",
    }
    return labels.get(target_type, "待确认")


def _module_summary(module_counts: list[tuple[str, int]], total_pages: int) -> str:
    if total_pages == 0:
        return "原型未提供可识别页面/状态，页面范围需产品补充。`未知`"

    generic_modules = {"新增", "编辑", "详情", "弹窗", "复制", "未命名页面"}
    significant = [
        (module, count)
        for module, count in module_counts
        if count > 1 and module and module not in generic_modules
    ][:6]
    single_page_groups = sum(count for _, count in module_counts if count == 1)

    if not significant:
        return (
            f"原型覆盖 {total_pages} 个页面/状态，但页面命名未形成稳定模块聚合；"
            "应按业务流程归纳实现范围，详细解析明细见 `prototype-analysis.md`。`事实/推断`"
        )

    module_text = "、".join(
        f"{module}（约 {count} 个页面/状态）" for module, count in significant
    )
    suffix = ""
    if single_page_groups:
        suffix = f"，另有约 {single_page_groups} 个单页状态、弹窗或详情页"
    if len(module_counts) > len(significant):
        suffix += "；其他低频页面组以解析报告为准"
    return (
        f"原型覆盖 {total_pages} 个页面/状态，主要集中在 {module_text}{suffix}。"
        "详细解析明细保存在 `prototype-analysis.md`。`事实/推断`"
    )


def _interaction_summary(interactions: list[dict], resolved_interactions: list[dict]) -> str:
    if not interactions:
        return "原型未提供可识别交互，主流程需人工补充。`未知`"

    type_labels = {
        "navigate": "页面跳转",
        "modal": "弹窗/浮层",
        "back": "返回",
        "state_change": "状态切换",
        "unknown": "未知交互",
    }
    counter = Counter(
        type_labels.get(str(ix.get("interaction_type") or "unknown"), str(ix.get("interaction_type") or "未知交互"))
        for ix in interactions
    )
    type_text = "、".join(f"{name} {count} 个" for name, count in counter.most_common(5))
    return (
        f"原型共识别 {len(interactions)} 个交互，其中 {len(resolved_interactions)} 个可定位到目标；"
        f"交互类型以 {type_text} 为主，说明系统需要覆盖页面流转、弹窗处理、状态变化和返回路径。`事实`"
    )


def _unresolved_summary(unresolved: list[dict]) -> str:
    counter = Counter(str(item.get("interaction_type") or "unknown") for item in unresolved)
    type_text = "、".join(f"{name} {count} 个" for name, count in counter.most_common(4))
    return (
        f"未解析交互共 {len(unresolved)} 个，类型分布为 {type_text}；"
        "需在原型评审时按业务场景确认其属于弹窗、动态状态、页面跳转还是无效热区，"
        "逐条明细见 `prototype-analysis.md`。`事实`"
    )


def _infer_domain_summary(page_names: list[str]) -> str:
    joined = " ".join(page_names)
    areas = []
    for keyword, label in [
        ("保单", "保单管理"),
        ("预约", "在线预约/投保预约"),
        ("计划书", "计划书"),
        ("产品", "产品库/产品管理"),
        ("账单", "账单"),
        ("结算", "结算"),
        ("续期", "续期管理"),
        ("用户", "用户管理"),
    ]:
        if keyword in joined:
            areas.append(label)
    if areas:
        return "基于页面命名，系统主要覆盖" + "、".join(areas[:8])
    return "原型页面命名不足以判断具体业务域"


def _infer_roles(page_names: list[str]) -> list[tuple[str, str, str, str]]:
    joined = " ".join(page_names)
    roles: list[tuple[str, str, str, str]] = []
    if any(word in joined for word in ["工作台", "保单", "预约", "计划书", "产品"]):
        roles.append(("业务人员/顾问", "工作台、保单、预约、计划书、产品等页面", "查看和维护本人或授权范围内业务数据；具体数据范围未提供", "推断"))
    if any(word in joined for word in ["账单", "结算", "收入", "缴费"]):
        roles.append(("财务/结算人员", "账单、结算、收入、缴费相关页面", "处理账单、结算、缴费申请；审批边界未提供", "推断"))
    if any(word in joined for word in ["审核", "审批"]):
        roles.append(("审批人员", "审核/审批相关页面", "审批业务申请；审批节点、驳回规则和代理审批未提供", "推断"))
    if any(word in joined for word in ["用户管理", "账号与设置", "产品管理"]):
        roles.append(("系统管理员", "用户管理、账号与设置、产品管理相关页面", "维护用户、基础配置或产品资料；具体菜单权限未提供", "推断"))
    if not roles:
        roles.append(("业务用户", "原型页面集合", "具体角色和权限边界未提供", "未知"))
    return roles


def _main_flow_lines(page_names: list[str]) -> list[str]:
    joined = " ".join(page_names)
    lines = []
    if "登录" in joined and "工作台" in joined:
        lines.append("用户登录后进入工作台，查看待办、业务入口或经营概览。`推断`")
    if "在线预约" in joined:
        lines.append("用户从在线预约入口发起预约，填写基本资料、保单持有人、受保人、受益人、计划书文件、健康信息及声明等资料，并进入预约详情查看。`推断`")
    if "保单管理" in joined or "全部保单" in joined:
        lines.append("用户进入保单管理/全部保单，查看保单详情、投被保人信息、受益人信息、保单文件、缴费信息和投保跟进。`推断`")
    if "产品库" in joined or "产品管理" in joined:
        lines.append("用户进入产品库或产品管理，查看产品详情、产品资料，必要时维护产品信息。`推断`")
    if "账单列表" in joined or "结算记录" in joined or "发起结算" in joined:
        lines.append("财务或结算角色查看账单、收入明细、结算记录，并发起结算。`推断`")
    if "用户管理" in joined or "账号与设置" in joined:
        lines.append("管理员或用户进入账号与设置、用户管理，维护账号资料、银行卡绑定或用户配置。`推断`")
    if not lines:
        lines.append("原型未提供足够页面命名来推断端到端主流程，需产品补充。`未知`")
    return lines


def _state_rule_lines(page_names: list[str]) -> list[str]:
    joined = " ".join(page_names)
    lines = []
    for keyword, text in [
        ("草稿", "存在草稿相关页面，说明至少存在未提交/暂存状态；草稿保存、编辑、删除和提交规则需补充。`推断`"),
        ("提交", "存在提交资料相关页面或弹窗，说明业务存在提交动作；提交后的状态、撤回和驳回规则需补充。`推断`"),
        ("审核", "存在审核相关页面，说明业务可能存在审批状态；审批节点、通过/驳回后状态需补充。`推断`"),
        ("续期", "存在续期相关页面，说明保单续期提醒或续期管理是业务范围；提醒时间和处理状态需补充。`推断`"),
        ("缴费", "存在缴费相关页面或弹窗，说明缴费申请/缴费信息是业务范围；金额校验、支付状态和失败处理需补充。`推断`"),
    ]:
        if keyword in joined:
            lines.append(text)
    if not lines:
        lines.append("未从页面命名中识别到明确状态流转，需补充状态机。`未知`")
    return lines


def _meaningful_business_rules(rules: list[dict]) -> list[str]:
    results: list[str] = []
    seen = set()
    placeholder = re.compile(r"^(?:打点)?批注\s*\d+(?:\s*Copy\s*\d+)?$", re.I)
    for rule in rules:
        text = str(rule.get("rule_text", "")).strip()
        if not text or placeholder.match(text):
            continue
        if text in seen:
            continue
        seen.add(text)
        results.append(text)
    return results


def _field_candidates(texts: list[dict]) -> list[str]:
    skip = {
        "确定", "取消", "保存", "返回", "提交", "搜索", "重置", "新增", "编辑", "删除",
        "查看", "详情", "全部", "更多", "下一步", "上一步", "关闭", "复制", "button", "div",
        "header", "footer", "frame", "group", "h1", "h2", "h3", "h4", "工作台", "个人",
        "快捷入口", "前往使用", "菜单栏",
    }
    fields: list[str] = []
    seen = set()
    for item in texts:
        text = str(item.get("text_content", "")).strip()
        text = re.sub(r"\s+", " ", text)
        normalized = text.lower()
        if not text or text in seen or text in skip or normalized in skip:
            continue
        if len(text) > 40 or re.fullmatch(r"[\d\s:：./-]+", text):
            continue
        if normalized.startswith("rbp"):
            continue
        if re.fullmatch(r"(?:frame|group|header|footer|h[1-6]|image|img|rect|rectangle)\s*\d*", normalized):
            continue
        if re.fullmatch(r"图片\s*\d+", text):
            continue
        seen.add(text)
        fields.append(text)
    return fields


def _field_summary_rows(fields: list[str]) -> list[tuple[str, str, str, str, str]]:
    if not fields:
        return []

    groups = [
        (
            "客户/人员信息",
            ["姓名", "电话", "手机", "邮箱", "证件", "身份证", "性别", "年龄", "生日", "出生", "地址", "国籍", "客户", "持有人", "受保人", "受益人"],
            "描述客户、投保人、受保人、受益人或联系人等主体信息",
            "原型可见文本/组件名称",
            "需补充必填、证件格式、手机号/邮箱格式、年龄范围、主体关系和唯一性规则",
        ),
        (
            "保单/产品信息",
            ["保单", "产品", "计划书", "保险", "投保", "保额", "保费", "险种", "保障"],
            "描述产品选择、计划书、投保资料、保单资料和保障内容",
            "原型可见文本/组件名称",
            "需补充产品枚举、保额/保费边界、计划书文件规则和保单状态约束",
        ),
        (
            "财务/结算信息",
            ["金额", "账单", "结算", "收入", "缴费", "支付", "银行", "账户", "佣金", "手续费", "费用"],
            "描述账单、缴费、收入、结算和收款账户相关信息",
            "原型可见文本/组件名称",
            "需补充金额精度、币种、舍入、支付状态、结算周期和账户校验规则",
        ),
        (
            "时间/状态信息",
            ["日期", "时间", "状态", "期限", "到期", "续期", "审核", "审批", "提交", "生效"],
            "描述业务时间节点、任务状态和流转状态",
            "原型可见文本/组件名称",
            "需补充状态机、时限、超时处理、状态变更触发条件和审计记录",
        ),
        (
            "文件/资料信息",
            ["文件", "附件", "资料", "图片", "上传", "下载", "影像", "凭证"],
            "描述上传、下载、查看和归档的业务资料",
            "原型可见文本/组件名称",
            "需补充文件类型、大小、数量、存储、预览、删除和访问权限规则",
        ),
        (
            "系统配置与权限",
            ["用户", "角色", "权限", "账号", "设置", "菜单", "组织", "团队"],
            "描述账号配置、组织范围、角色授权和系统设置",
            "原型可见文本/组件名称",
            "需补充角色矩阵、菜单权限、数据范围和越权访问校验规则",
        ),
    ]

    matched: set[str] = set()
    rows: list[tuple[str, str, str, str, str]] = []
    for group, keywords, meaning, source, validation in groups:
        examples = [field for field in fields if any(keyword in field for keyword in keywords)]
        if not examples:
            continue
        matched.update(examples)
        sample_text = _join_cn(examples[:3])
        rows.append((
            group,
            f"{meaning}；原型线索包括：{sample_text}",
            source,
            validation,
            "推断",
        ))

    other_fields = [field for field in fields if field not in matched]
    if other_fields:
        rows.append((
            "其他业务字段",
            f"原型存在 {len(other_fields)} 个其他未归类字段线索，需在评审中确认业务含义后再进入字段清单",
            "原型可见文本/组件名称",
            "需由产品按业务含义归类后补充校验、枚举、必填和唯一性规则",
            "推断",
        ))
    return rows


def _join_cn(items: list[str]) -> str:
    if not items:
        return "无"
    return "、".join(items)


def _escape_table(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ").strip()


def _render_structured_json(data: dict, filepath: Path) -> None:
    """Write structured-data.json."""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _render_completeness_report(data: dict, filepath: Path) -> None:
    """Write completeness-report.json."""
    completeness = data.get("completeness", {})
    interactions = data.get("interactions", [])
    parsed_interactions = sum(
        1 for i in interactions if i.get("confidence") in ("fact", "inferred")
    )

    report = {
        "scores": completeness,
        "details": {
            "total_pages": len(data.get("pages", [])),
            "total_interactions": len(interactions),
            "parsed_interactions": parsed_interactions,
            "resolved_interactions": parsed_interactions,
            "fact_interactions": sum(1 for i in interactions if i.get("confidence") == "fact"),
            "inferred_interactions": sum(1 for i in interactions if i.get("confidence") == "inferred"),
            "unresolved_targets": len(data.get("unresolved", [])),
            "text_entries": len(data.get("texts", [])),
            "business_rules": len(data.get("business_rules", [])),
        },
        "assessment": _assessment_label(completeness.get("overall_implementability", 0)),
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)


def _assessment_label(score: float) -> str:
    if score >= 0.90:
        return "independent"
    elif score >= 0.75:
        return "mostly_independent"
    elif score >= 0.60:
        return "partial"
    return "insufficient"
