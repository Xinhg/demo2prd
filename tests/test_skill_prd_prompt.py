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


def test_prd_writing_prompt_has_incremental_interviewer_contract():
    content = PROMPT_PATH.read_text(encoding="utf-8")

    required_interviewer_rules = [
        "需求访谈模式",
        "访谈记录",
        "问题清单",
        "每轮只问一个问题",
        "不得一次性抛出全部问题",
        "回答后更新访谈记录",
        "所有 P0 级别问题确认完毕",
        "达到进入下一步的阈值",
        "允许用户继续访谈",
    ]
    for rule in required_interviewer_rules:
        assert rule in content


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
