"""Integration tests for the CLI."""

import json
import subprocess
import sys


def test_help_command():
    result = subprocess.run(
        [sys.executable, "-m", "proto_to_requirement.cli", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "proto-to-requirement" in result.stdout


def test_integration_end_to_end(tmp_path, test_fixture_dir):
    output_dir = tmp_path / "output"
    result = subprocess.run(
        [
            sys.executable, "-m", "proto_to_requirement.cli",
            test_fixture_dir,
            "--output", str(output_dir),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"CLI failed: {result.stderr}"
    assert "Interaction parse rate:" in result.stdout

    # All output files exist
    assert (output_dir / "requirements.md").exists()
    assert (output_dir / "prototype-analysis.md").exists()
    assert (output_dir / "structured-data.json").exists()
    assert (output_dir / "completeness-report.json").exists()

    # structured-data.json has required content
    with open(output_dir / "structured-data.json", encoding="utf-8") as f:
        data = json.load(f)

    assert len(data.get("pages", [])) >= 2
    assert len(data.get("interactions", [])) >= 2

    # At least one resolved interaction
    resolved = [i for i in data["interactions"] if i.get("confidence") == "fact"]
    assert len(resolved) >= 1, "Should have at least one fact interaction"

    # unresolved targets are tracked even when the fixture is fully parsed
    assert "unresolved" in data
    assert len(data.get("unresolved", [])) == 0

    # At least one text entry
    assert len(data.get("texts", [])) >= 1

    # At least one business rule
    assert len(data.get("business_rules", [])) >= 1

    # requirements.md has the user-facing PRD sections
    md_content = (output_dir / "requirements.md").read_text(encoding="utf-8")
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
        assert section in md_content, f"Missing section heading {section}"
    for subsection in [
        "### 1.1 为什么做这个需求",
        "### 1.2 解决的业务问题",
        "### 3.1 页面框架",
        "### 10.2 涉及 API 模块（推断）",
        "### 11.1 交互类型统计",
    ]:
        assert subsection in md_content, f"Missing template subsection {subsection}"
    assert "**业务流程**：" in md_content
    assert "**状态与异常**：" in md_content
    assert md_content.index("**业务流程**：") < md_content.index("**关键页面/状态**：")
    assert "已解析页面跳转样例" not in md_content
    assert "未解析交互样例" not in md_content
    assert "### 9.1 页面清单" not in md_content
    assert "页面清单" not in md_content
    assert "| 触发组件 |" not in md_content

    analysis_content = (output_dir / "prototype-analysis.md").read_text(encoding="utf-8")
    assert "中间产物" in analysis_content
    assert "不是最终 PRD" in analysis_content

    # completeness-report.json has numeric scores
    with open(output_dir / "completeness-report.json", encoding="utf-8") as f:
        report = json.load(f)
    assert "overall_implementability" in report.get("scores", {})
    assert isinstance(report["scores"]["overall_implementability"], (int, float))
