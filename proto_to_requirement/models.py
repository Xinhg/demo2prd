"""Data models for the proto-to-requirement pipeline."""

from dataclasses import dataclass, field


@dataclass
class ToolInfo:
    tool_type: str = "unknown"
    tool_version: str = ""
    project_name: str = ""


@dataclass
class PageInfo:
    page_id: str = ""
    page_name: str = ""
    state_variants: list = field(default_factory=list)
    estimated_route: str = ""
    components_count: int = 0


@dataclass
class InteractionInfo:
    source_component: str = ""
    source_component_id: str = ""
    interaction_type: str = ""
    target_page: str = ""
    target_name: str = ""
    raw_target_id: str = ""
    confidence: str = "unknown"


@dataclass
class TextInfo:
    page: str = ""
    component_name: str = ""
    component_id: str = ""
    text_content: str = ""
    field: str = ""


@dataclass
class BusinessRule:
    rule_text: str = ""
    source_page: str = ""
    source_component: str = ""
    source_component_id: str = ""
    source: str = "annotation"


@dataclass
class CompletenessScores:
    page_coverage: float = 0.0
    interaction_mapping: float = 0.0
    text_extraction: float = 0.0
    business_rule_extraction: float = 0.0
    unknown_rate: float = 0.0
    overall_implementability: float = 0.0


@dataclass
class ProbeResult:
    tool_type: str = "unknown"
    data_files: list = field(default_factory=list)
    primary_file: str = ""
    config_file: str = ""
    wrapper: str = ""
    encoding: str = ""
    compression: str = ""
    warnings: list = field(default_factory=list)
