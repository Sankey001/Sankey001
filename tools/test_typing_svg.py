"""Tests for typing_svg: run with `python3 -m pytest tools` from the repo root."""

import xml.etree.ElementTree as ET

import pytest

from typing_svg import build_timeline, render

SVG = "{http://www.w3.org/2000/svg}"
LINES = ["Hi", "Hello"]


def test_timeline_types_each_character_then_deletes_back_to_zero():
    frames = build_timeline(LINES, type_ms=100, hold_ms=1000, delete_ms=50, gap_ms=200)
    counts = [f.chars for f in frames if f.line == 0]
    assert counts[:3] == [0, 1, 2]  # typed one char at a time
    assert counts[-1] == 0  # fully deleted before the next line
    assert max(counts) == len(LINES[0])


def test_timeline_is_sorted_and_covers_every_line():
    frames = build_timeline(LINES, type_ms=100, hold_ms=1000, delete_ms=50, gap_ms=200)
    times = [f.t_ms for f in frames]
    assert times == sorted(times)
    assert {f.line for f in frames} == {0, 1}


def test_render_is_valid_svg_with_one_text_per_line():
    root = ET.fromstring(render(LINES))
    texts = root.findall(f".//{SVG}text")
    assert [t.text for t in texts] == LINES


def test_render_escapes_xml_special_characters():
    root = ET.fromstring(render(["AI & <security>"]))
    assert root.find(f".//{SVG}text").text == "AI & <security>"


def test_keytimes_are_valid_for_smil():
    root = ET.fromstring(render(LINES))
    for anim in root.iter(f"{SVG}animate"):
        if "keyTimes" not in anim.attrib:
            continue
        kt = [float(x) for x in anim.attrib["keyTimes"].split(";")]
        values = anim.attrib["values"].split(";")
        assert kt[0] == 0 and all(0 <= k <= 1 for k in kt)
        assert kt == sorted(kt)
        assert len(kt) == len(values)


def test_animation_loops_forever():
    root = ET.fromstring(render(LINES))
    anims = list(root.iter(f"{SVG}animate"))
    assert anims and all(a.attrib.get("repeatCount") == "indefinite" for a in anims)


def test_rejects_empty_input():
    with pytest.raises(ValueError):
        render([])
