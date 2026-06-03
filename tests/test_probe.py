"""Tests for format probe module."""

import os

from proto_to_requirement.probe import probe_directory


def test_detects_mockitt(test_fixture_dir):
    result = probe_directory(test_fixture_dir)
    assert result.tool_type == "mockitt"
    assert len(result.data_files) >= 1
    assert result.primary_file.endswith("data.1.js")
    assert result.config_file.endswith("data.0.js")


def test_unknown_directory(tmp_path):
    empty = tmp_path / "empty_dir"
    empty.mkdir()
    result = probe_directory(str(empty))
    assert result.tool_type == "unknown"
    assert len(result.warnings) > 0


def test_nonexistent_directory():
    result = probe_directory("/nonexistent/path/12345")
    assert result.tool_type == "unknown"
    assert len(result.warnings) > 0


def test_primary_file_is_largest(test_fixture_dir):
    result = probe_directory(test_fixture_dir)
    data_files = [os.path.basename(f) for f in result.data_files]
    assert "data.1.js" in data_files


def test_data_files_ordered_by_size_descending(tmp_path):
    """Prove candidate ordering by file size, not filename."""
    proto2 = tmp_path / "mb-proto2"
    proto2.mkdir()
    extra = tmp_path / "extra"
    extra.mkdir()

    # Create files with known sizes: a.js small, b.js medium, c.js large
    (extra / "data.a.js").write_text("x" * 10)    # 10 bytes
    (extra / "data.c.js").write_text("x" * 100)   # 100 bytes — largest
    (extra / "data.b.js").write_text("x" * 50)    # 50 bytes

    result = probe_directory(str(tmp_path))
    assert result.tool_type == "mockitt"
    assert len(result.data_files) == 3

    names = [os.path.basename(f) for f in result.data_files]
    # data.c.js (100) must be first, then data.b.js (50), then data.a.js (10)
    assert names[0] == "data.c.js"
    assert names[1] == "data.b.js"
    assert names[2] == "data.a.js"
    assert result.primary_file == result.data_files[0]


def test_detects_hzv5_flpk_wrapper(tmp_path):
    """Prove hzv5.flpk wrapper and gzip compression are detected."""
    proto2 = tmp_path / "mb-proto2"
    proto2.mkdir()
    extra = tmp_path / "extra"
    extra.mkdir()

    header = (
        'window["hzv5"] = window["hzv5"] || {};'
        'window["hzv5"]["flpk"] = [ [1,2,"H4sIA"] ]'
    )
    (extra / "data.1.js").write_text(header + "x" * 200)
    (extra / "data.0.js").write_text('window["hzv5"] = window["hzv5"] || {};window["hzv5"]["init"] = {}')

    result = probe_directory(str(tmp_path))
    assert result.tool_type == "mockitt"
    assert result.wrapper == "hzv5_flpk"
    assert result.compression == "gzip"
