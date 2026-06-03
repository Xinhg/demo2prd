"""CLI entry point for proto-to-requirement workflow."""

import argparse
import sys
from pathlib import Path

from .extract import extract_business_rules, extract_interactions, extract_pages, extract_texts
from .probe import probe_directory
from .render import compute_completeness, render_outputs
from .unpack import read_and_unpack


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="proto-to-requirement",
        description="Convert prototype exports into structured requirement documents.",
    )
    parser.add_argument(
        "prototype_dir",
        help="Path to the prototype export directory",
    )
    parser.add_argument(
        "--output", "-o",
        default="./output",
        help="Output directory for generated documents (default: ./output)",
    )

    args = parser.parse_args()

    # Phase 1: Probe
    probe_result = probe_directory(args.prototype_dir)

    if probe_result.tool_type == "unknown":
        print(f"Error: Unrecognized prototype format in {args.prototype_dir}", file=sys.stderr)
        for w in probe_result.warnings:
            print(f"  Warning: {w}", file=sys.stderr)
        sys.exit(1)

    if not probe_result.primary_file:
        print(f"Error: No data file found in {args.prototype_dir}", file=sys.stderr)
        sys.exit(1)

    print(f"Detected: {probe_result.tool_type}")
    print(f"Primary data: {probe_result.primary_file}")

    # Phase 2: Unpack
    try:
        components = read_and_unpack(probe_result.primary_file)
    except Exception as e:
        print(f"Error unpacking data: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Components unpacked: {len(components)}")

    # Phase 3: Extract
    pages = extract_pages(components)
    interactions, unresolved = extract_interactions(components, pages)
    texts = extract_texts(components)
    business_rules = extract_business_rules(components)
    parsed_interactions = sum(
        1 for item in interactions if item.get("confidence") in ("fact", "inferred")
    )
    parse_rate = parsed_interactions / len(interactions) if interactions else 0.0

    print(f"Pages: {len(pages)}")
    print(f"Interactions: {len(interactions)}")
    print(f"Interaction parse rate: {parsed_interactions}/{len(interactions)} ({parse_rate:.0%})")
    print(f"Texts: {len(texts)}")
    print(f"Business Rules: {len(business_rules)}")
    print(f"Unresolved: {len(unresolved)}")

    # Build structured data
    structured_data: dict = {
        "tool_info": {
            "tool_type": probe_result.tool_type,
            "tool_version": "",
            "project_name": Path(args.prototype_dir).name,
        },
        "pages": pages,
        "interactions": interactions,
        "texts": texts,
        "business_rules": business_rules,
        "unresolved": unresolved,
    }
    structured_data["completeness"] = compute_completeness(structured_data)

    # Phase 5: Render
    render_outputs(structured_data, args.output)

    print(f"\nOutput written to: {args.output}/")
    print("  - requirements.md")
    print("  - prototype-analysis.md")
    print("  - structured-data.json")
    print("  - completeness-report.json")


if __name__ == "__main__":
    main()
