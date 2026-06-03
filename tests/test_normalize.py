"""Tests for ID normalization module."""

from proto_to_requirement.normalize import build_id_map, normalize_id


def test_strip_trailing_dot_space():
    assert normalize_id("V001 .") == "V001"
    assert normalize_id("rbp001 .") == "rbp001"


def test_strip_trailing_comma():
    assert normalize_id("V002 ,") == "V002"


def test_strip_mockitt_page_key_suffixes():
    assert normalize_id("rbpV8k4y1ArLAneS6 6") == "rbpV8k4y1ArLAneS6"
    assert normalize_id("rbpV8paxt7Wz9JQ82 *") == "rbpV8paxt7Wz9JQ82"
    assert normalize_id("rbpV8pk5bGIasnJwf )") == "rbpV8pk5bGIasnJwf"


def test_no_change_on_normal_id():
    assert normalize_id("V003") == "V003"
    assert normalize_id("rbp001") == "rbp001"


def test_empty_string():
    assert normalize_id("") == ""


def test_build_id_map():
    raw_ids = ["V001 .", "V002 ,", "V003"]
    mapping = build_id_map(raw_ids)
    assert mapping["V001"] == "V001 ."
    assert mapping["V002"] == "V002 ,"
    assert mapping["V003"] == "V003"
