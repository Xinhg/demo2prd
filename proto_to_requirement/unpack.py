"""Data unpacking: read, unwrap, decode, decompress, and parse data files."""

import base64
import gzip
import json
import re
import zlib
from pathlib import Path


def read_and_unpack(filepath: str) -> dict:
    """Read a data file and unpack into a component index dict keyed by component ID."""
    content = Path(filepath).read_text(encoding="utf-8")

    # Try hzv5.flpk chunked gzip/base64 format first
    result = _try_unpack_flpk(content)
    if result:
        return result

    content = _unwrap_js_assignment(content)

    # Try parsing directly first — covers raw JSON and JS-unwrapped inline JSON
    result = _parse_content(content)
    if result:
        return result

    # Try base64 decode, then parse
    decoded = _try_base64_decode(content)
    if decoded != content:
        result = _parse_content(decoded)
        if result:
            return result

    # Try decompression on the decoded content, then parse
    decompressed = _try_decompress(decoded)
    if decompressed != decoded:
        result = _parse_content(decompressed)
        if result:
            return result

    return {}


def _try_unpack_flpk(content: str) -> dict | None:
    """Handle hzv5.flpk chunked gzip/base64 format.

    Format: window["hzv5"]["flpk"] = [[num, num, "gzip_base64"], ...]
    Each inner array carries a gzip-compressed, base64-encoded string payload.
    Decompressed chunks are concatenated and parsed as line-delimited records.
    Returns None if the content does not match this format.
    """
    flpk_match = re.search(r'window\["hzv5"\]\["flpk"\]\s*=\s*', content)
    if not flpk_match:
        return None

    remaining = content[flpk_match.end():]
    b64_strings = re.findall(r'"([A-Za-z0-9+/=]{50,})"', remaining)
    if not b64_strings:
        return None

    all_text_parts: list[str] = []
    for b64_str in b64_strings:
        try:
            raw = base64.b64decode(b64_str)
            decompressed = gzip.decompress(raw)
            all_text_parts.append(decompressed.decode("utf-8"))
        except Exception:
            pass

    if not all_text_parts:
        return None

    combined = "".join(all_text_parts)
    return _parse_line_delimited(combined)


def _unwrap_js_assignment(content: str) -> str:
    """Remove JS assignment wrapper like window["key"] = <value>;"""
    patterns = [
        r'window\["[^"]*"\]\s*=\s*',
        r"window\['[^']*'\]\s*=\s*",
    ]
    for pattern in patterns:
        m = re.match(pattern, content)
        if m:
            content = content[m.end():]
            content = content.rstrip().rstrip(";").rstrip()
            break

    # If the value is a quoted JS string literal, unwrap it
    content = _unwrap_js_string(content)
    return content


def _unwrap_js_string(content: str) -> str:
    """If content is a JS string literal, extract its value with basic unescaping."""
    content = content.strip()
    if (content.startswith('"') and content.endswith('"')) or \
       (content.startswith("'") and content.endswith("'")):
        inner = content[1:-1]
        inner = inner.replace('\\"', '"').replace("\\'", "'")
        inner = inner.replace('\\n', '\n').replace('\\t', '\t')
        inner = inner.replace('\\\\', '\\')
        return inner
    return content


def _try_base64_decode(content: str) -> str:
    """Try to decode as base64. Returns decoded text or original string."""
    content_stripped = content.strip()
    try:
        decoded = base64.b64decode(content_stripped)
        try:
            return decoded.decode("utf-8")
        except UnicodeDecodeError:
            return decoded.decode("latin-1")
    except Exception:
        return content


def _try_decompress(content: str) -> str:
    """Try gzip, zlib, and raw deflate decompression. Returns decompressed text or original."""
    try:
        raw = content.encode("latin-1")
    except UnicodeEncodeError:
        return content

    for decompressor, name in [
        (lambda b: gzip.decompress(b), "gzip"),
        (lambda b: zlib.decompress(b), "zlib"),
        (lambda b: zlib.decompress(b, -15), "raw_deflate"),
    ]:
        try:
            decoded = decompressor(raw)
            try:
                return decoded.decode("utf-8")
            except UnicodeDecodeError:
                return decoded.decode("latin-1")
        except Exception:
            continue

    return content


def _parse_content(content: str) -> dict:
    """Parse content into a component index dict."""
    content = content.strip()

    # Try JSON first
    try:
        data = json.loads(content)
        if isinstance(data, dict):
            return data
        elif isinstance(data, list):
            return _array_to_index(data)
    except (json.JSONDecodeError, ValueError):
        pass

    # Try line-delimited: component_id\t{json}
    try:
        return _parse_line_delimited(content)
    except Exception:
        pass

    return {}


def _array_to_index(arr: list) -> dict:
    """Convert a JSON array to a component index dict."""
    index: dict = {}
    for i, item in enumerate(arr):
        if isinstance(item, dict):
            cid = item.get("id") or item.get("component_id") or str(i)
            index[cid] = item
    return index


def _parse_line_delimited(content: str) -> dict:
    """Parse line-delimited component records: component_id\\t{json}"""
    index: dict = {}
    for line in content.split("\n"):
        line = line.strip()
        if not line:
            continue
        parts = line.split("\t", 1)
        if len(parts) == 2:
            cid, json_str = parts
            try:
                index[cid] = json.loads(json_str)
            except json.JSONDecodeError:
                pass
        else:
            try:
                obj = json.loads(line)
                if isinstance(obj, dict):
                    cid = obj.get("id") or obj.get("component_id") or ""
                    index[cid] = obj
            except json.JSONDecodeError:
                pass
    return index
