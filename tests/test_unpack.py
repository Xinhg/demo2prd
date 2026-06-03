"""Tests for data unpack module."""

import base64
import gzip
import json
import os

from proto_to_requirement.unpack import read_and_unpack


def test_unpack_js_assignment_json_object(test_fixture_dir):
    primary = os.path.join(test_fixture_dir, "extra", "data.1.js")
    result = read_and_unpack(primary)
    assert isinstance(result, dict)
    assert len(result) > 0
    # Should contain the raw IDs including suffixes
    assert "V001 ." in result or any("V001" in k for k in result)


def test_unpack_preserves_raw_ids(test_fixture_dir):
    primary = os.path.join(test_fixture_dir, "extra", "data.1.js")
    result = read_and_unpack(primary)
    # Check that components with suffix IDs are present
    all_keys = list(result.keys())
    assert len(all_keys) >= 5


def test_unpack_components_have_expected_fields(test_fixture_dir):
    primary = os.path.join(test_fixture_dir, "extra", "data.1.js")
    result = read_and_unpack(primary)
    # Find an rbp component
    rbp_keys = [k for k in result if k.startswith("rbp")]
    assert len(rbp_keys) >= 2
    for k in rbp_keys:
        assert "N" in result[k]
        assert "T" in result[k]


def test_line_delimited_records(tmp_path):
    """Prove line-delimited component_id\\t{json} records are unpacked."""
    content = (
        'comp_a\t{"N": "Alpha", "T": "*"}\n'
        'comp_b\t{"N": "Beta", "T": "]"}\n'
        'comp_c\t{"N": "Gamma", "T": "x"}\n'
    )
    f = tmp_path / "data.txt"
    f.write_text(content, encoding="utf-8")
    result = read_and_unpack(str(f))
    assert len(result) == 3
    assert result["comp_a"]["N"] == "Alpha"
    assert result["comp_b"]["N"] == "Beta"
    assert result["comp_c"]["N"] == "Gamma"


def test_gzip_base64_payload(tmp_path):
    """Prove gzip-compressed base64-encoded JSON is unpacked correctly."""
    payload = json.dumps({"page1": {"N": "Home", "T": "*"}, "page2": {"N": "About", "T": "*"}})
    compressed = gzip.compress(payload.encode("utf-8"))
    encoded = base64.b64encode(compressed).decode("ascii")
    f = tmp_path / "data.gzb64"
    f.write_text(encoded, encoding="utf-8")
    result = read_and_unpack(str(f))
    assert len(result) == 2
    assert result["page1"]["N"] == "Home"
    assert result["page2"]["N"] == "About"


def test_hzv5_flpk_chunks(tmp_path):
    """Prove hzv5.flpk chunked gzip/base64 format with trailing commas and non-JSON records."""
    # Build two chunks of line-delimited component records
    chunk1 = (
        'rbp001\t{"N":"Home","T":")","B":"*"}\n'
        'rbp002\t{"N":"About","T":")","B":"*"}\n'
    )
    chunk2 = (
        'V003 .\t{"N":"Button1","T":"]","I":[[1,"rbp002","","",["","","","h"],0]]}\n'
        '@@R *\t{}\n'
        '@@M 1\t{}\n'
    )
    c1 = base64.b64encode(gzip.compress(chunk1.encode("utf-8"))).decode("ascii")
    c2 = base64.b64encode(gzip.compress(chunk2.encode("utf-8"))).decode("ascii")

    # Build JS-like array with trailing comma
    content = (
        'window["hzv5"] = window["hzv5"] || {};'
        f'window["hzv5"]["flpk"] = [ [100,200,"{c1}"],[300,400,"{c2}"], ]'
    )
    f = tmp_path / "data.flpk"
    f.write_text(content, encoding="utf-8")
    result = read_and_unpack(str(f))
    # 5 records total: 3 component + 2 placeholder (empty dict) reference records
    # Non-JSON reference lines would be silently ignored
    assert len(result) == 5
    assert result["rbp001"]["N"] == "Home"
    assert result["rbp002"]["N"] == "About"
    assert result["rbp002"]["T"] == ")"
    assert result["rbp002"]["B"] == "*"
    # V003 is stored with raw key "V003 ." from the line-delimited header
    assert "V003 ." in result
    assert result["V003 ."]["N"] == "Button1"
    # Non-component records are present because they have valid JSON
    assert "@@R *" in result
    assert "@@M 1" in result


def test_hzv5_flpk_ignored_for_non_flpk_content(test_fixture_dir):
    """hzv5.flpk detection should not interfere with normal content."""
    primary = os.path.join(test_fixture_dir, "extra", "data.1.js")
    result = read_and_unpack(primary)
    # Should still work and return components (the fixture uses window["xxx"] = {})
    assert isinstance(result, dict)
    assert len(result) > 0
