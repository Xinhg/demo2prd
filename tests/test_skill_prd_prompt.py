"""Tests for the PRD writing skill prompt reference."""

from pathlib import Path


PROMPT_PATH = Path("proto-to-requirement/references/prd-writing-prompt.md")


def test_prd_writing_prompt_has_engineering_prd_contract():
    content = PROMPT_PATH.read_text(encoding="utf-8")

    required_sections = [
        "开发入口摘要",
        "P0 待确认清单",
        "必须先查仓库的对象",
        "领域模型与数据结构说明",
        "按 Feature 重写业务需求",
        "接口与后端能力",
        "工程实施拆解建议",
        "Sub-agent 审查结果",
    ]
    for section in required_sections:
        assert section in content


def test_prd_writing_prompt_is_generic_not_business_specific():
    content = PROMPT_PATH.read_text(encoding="utf-8")

    removed_business_terms = [
        "主附计划",
        "顾问在线预约",
        "缴费功能优化",
        "保司计划编码",
        "OCR",
        "RPA",
    ]
    for term in removed_business_terms:
        assert term not in content
