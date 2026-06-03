"""Format probe: detect prototype tool type and locate data files."""

from pathlib import Path
from .models import ProbeResult


def probe_directory(proto_dir: str) -> ProbeResult:
    """Scan a prototype directory and return format detection results."""
    path = Path(proto_dir)
    result = ProbeResult()

    if not path.exists():
        result.warnings.append(f"Directory does not exist: {proto_dir}")
        return result

    if not path.is_dir():
        result.warnings.append(f"Path is not a directory: {proto_dir}")
        return result

    mb_proto2 = path / "mb-proto2"
    extra_dir = path / "extra"

    if mb_proto2.exists() and extra_dir.exists():
        data_files = sorted(extra_dir.glob("data.*.js"), key=lambda f: f.stat().st_size, reverse=True)
        if data_files:
            result.tool_type = "mockitt"
            result.data_files = [str(f) for f in data_files]
            result.primary_file = str(data_files[0])
            config = extra_dir / "data.0.js"
            if config.exists():
                result.config_file = str(config)

            for f in data_files:
                _probe_file_wrapper(f, result)
            return result

    for w in result.warnings:
        pass  # accumulated above

    result.tool_type = "unknown"
    result.warnings.append("No recognized prototype tool format detected")
    return result


def _probe_file_wrapper(filepath: Path, result: ProbeResult) -> None:
    """Detect wrapper and encoding by reading the first few bytes.

    Only sets wrapper/compression from the first (largest/primary) data file.
    """
    if result.wrapper:
        return  # already detected from primary file

    try:
        head = filepath.read_text(encoding="utf-8")[:500]
    except Exception as e:
        result.warnings.append(f"Could not read {filepath}: {e}")
        return

    if 'hzv5"]["flpk"' in head:
        result.wrapper = "hzv5_flpk"
        result.compression = "gzip"
    elif head.startswith("window["):
        result.wrapper = "js_assignment"
    elif head.startswith("{") or head.startswith("["):
        result.wrapper = "raw_json"
    else:
        result.wrapper = "unknown"
