"""Tests for render and completeness modules."""

import json
import os

from proto_to_requirement.render import compute_completeness, render_outputs


def test_requirements_md_has_business_prd_sections(tmp_path):
    data = _make_sample_data()
    output_dir = tmp_path / "output"
    render_outputs(data, str(output_dir))

    md_path = output_dir / "requirements.md"
    assert md_path.exists()
    content = md_path.read_text(encoding="utf-8")

    expected_sections = [
        "## 1. 业务背景",
        "## 2. 用户角色",
        "## 3. 全局布局结构",
        "## 4. 页面详细规格",
        "## 5. 异常流程",
        "## 6. 业务规则",
        "## 7. 数据规则",
        "## 8. 权限规则",
        "## 9. 验收标准",
        "## 10. 影响范围",
        "## 11. 附录",
    ]
    for section in expected_sections:
        assert section in content, f"Missing section: {section}"
    template_subsections = [
        "### 1.1 为什么做这个需求",
        "### 1.2 解决的业务问题",
        "### 3.1 页面框架",
        "### 3.2 模块导航映射",
        "### 10.2 涉及 API 模块（推断）",
        "### 10.3 涉及数据表（推断）",
        "### 11.1 交互类型统计",
    ]
    for subsection in template_subsections:
        assert subsection in content, f"Missing template subsection: {subsection}"
    assert "**业务流程**：" in content
    assert "**状态与异常**：" in content
    assert content.index("**业务流程**：") < content.index("**关键页面/状态**：")
    assert "## 1. Overview" not in content
    assert "Prototype Inventory" not in content


def test_requirements_md_describes_instead_of_listing_prototype_inventory(tmp_path):
    data = _make_sample_data()
    data["pages"] = [
        {"page_id": f"rbp{i:03d}", "page_name": f"保单管理-{i}", "estimated_route": f"/policy/{i}"}
        for i in range(1, 12)
    ]
    data["interactions"] = [
        {
            "source_component": f"Button {i}",
            "interaction_type": "navigate",
            "target_page": f"rbp{i:03d}",
            "target_name": f"保单管理-{i}",
            "confidence": "fact",
        }
        for i in range(1, 12)
    ]
    data["unresolved"] = [
        {"source_component": "Unknown Button", "raw_target_id": "missing_target", "interaction_type": "modal"}
    ]
    data["texts"] = [
        {"component_name": "Layer", "text_content": "FRAME", "field": "name"},
        {"component_name": "Layer", "text_content": "h3", "field": "name"},
        {"component_name": "Layer", "text_content": "矩形 1", "field": "name"},
        {"component_name": "Input", "text_content": "客户姓名", "field": "text"},
    ]
    output_dir = tmp_path / "output"
    render_outputs(data, str(output_dir))

    content = (output_dir / "requirements.md").read_text(encoding="utf-8")
    assert "已解析页面跳转样例" not in content
    assert "未解析交互样例" not in content
    assert "### 9.1 页面清单" not in content
    assert "页面清单" not in content
    assert "| 触发组件 |" not in content
    assert "- 保单管理-1 `事实`" not in content
    assert "详细原型解析明细" in content
    assert "FRAME" not in content
    assert "h3" not in content
    assert "矩形 1" not in content


def test_prototype_analysis_md_is_intermediate_artifact(tmp_path):
    data = _make_sample_data()
    output_dir = tmp_path / "output"
    render_outputs(data, str(output_dir))

    analysis_path = output_dir / "prototype-analysis.md"
    assert analysis_path.exists()
    content = analysis_path.read_text(encoding="utf-8")
    assert "# 原型解析报告（中间产物）" in content
    assert "不是最终 PRD" in content
    assert "最终对用户交付请使用 `requirements.md`" in content


def test_structured_json_contains_required_keys(tmp_path):
    data = _make_sample_data()
    output_dir = tmp_path / "output"
    render_outputs(data, str(output_dir))

    json_path = output_dir / "structured-data.json"
    assert json_path.exists()
    with open(json_path, encoding="utf-8") as f:
        loaded = json.load(f)

    for key in ["tool_info", "pages", "interactions", "texts", "business_rules", "unresolved", "completeness"]:
        assert key in loaded, f"Missing key: {key}"


def test_completeness_report_has_scores(tmp_path):
    data = _make_sample_data()
    output_dir = tmp_path / "output"
    render_outputs(data, str(output_dir))

    report_path = output_dir / "completeness-report.json"
    assert report_path.exists()
    with open(report_path, encoding="utf-8") as f:
        report = json.load(f)

    assert "scores" in report
    scores = report["scores"]
    for key in ["page_coverage", "interaction_mapping", "overall_implementability"]:
        assert key in scores, f"Missing score: {key}"
    assert "details" in report
    assert "assessment" in report


def test_compute_completeness_with_data():
    data = _make_sample_data()
    scores = compute_completeness(data)
    assert scores["page_coverage"] == 1.0
    assert 0 <= scores["interaction_mapping"] <= 1.0
    assert 0 <= scores["overall_implementability"] <= 1.0


def _make_sample_data():
    return {
        "tool_info": {"tool_type": "mockitt", "project_name": "Test"},
        "pages": [
            {"page_id": "rbp001", "page_name": "Login", "estimated_route": "/login"},
            {"page_id": "rbp002", "page_name": "Dashboard", "estimated_route": "/dashboard"},
        ],
        "interactions": [
            {
                "source_component": "Sign In",
                "source_component_id": "V001",
                "interaction_type": "navigate",
                "target_page": "rbp002",
                "target_name": "Dashboard",
                "confidence": "fact",
            },
            {
                "source_component": "Forgot Password",
                "source_component_id": "V002",
                "interaction_type": "modal",
                "target_page": "",
                "target_name": "",
                "raw_target_id": "modal_reset_99",
                "confidence": "unknown",
            },
        ],
        "texts": [
            {"component_name": "Welcome Label", "component_id": "V003", "text_content": "Welcome Back!", "field": "b/#000000"},
        ],
        "business_rules": [
            {"rule_text": "Password must be at least 8 characters", "source": "annotation"},
            {"rule_text": "GDPR consent required", "source": "annotation"},
        ],
        "unresolved": [
            {"source_component": "Forgot Password", "raw_target_id": "modal_reset_99", "interaction_type": "modal"},
        ],
        "completeness": {
            "page_coverage": 1.0,
            "interaction_mapping": 0.5,
            "text_extraction": 0.25,
            "business_rule_extraction": 1.0,
            "unknown_rate": 0.5,
            "overall_implementability": 0.64,
        },
    }
