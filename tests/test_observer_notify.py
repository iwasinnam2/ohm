"""Slack Block Kit payload shape for observer_notify.

Guards Slack's hard limits so a real alert never fails to render: header blocks
are plain_text and capped at 150 chars, section mrkdwn is capped at 3000.
"""

import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "observer_notify",
    Path(__file__).resolve().parent.parent / "scripts" / "observer_notify.py",
)
observer_notify = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(observer_notify)


def test_blocks_have_header_and_section():
    blocks = observer_notify._slack_blocks("[observer] pulse failure", "- a\n- b")
    assert blocks[0]["type"] == "header"
    assert blocks[0]["text"]["type"] == "plain_text"  # header cannot be mrkdwn
    assert blocks[1]["type"] == "section"
    assert blocks[1]["text"]["type"] == "mrkdwn"
    assert "- a" in blocks[1]["text"]["text"]


def test_header_capped_at_slack_limit():
    blocks = observer_notify._slack_blocks("x" * 400, "body")
    assert len(blocks[0]["text"]["text"]) <= 150


def test_long_body_is_truncated_under_section_limit():
    blocks = observer_notify._slack_blocks("t", "y" * 5000)
    assert len(blocks[1]["text"]["text"]) <= 3000
    assert blocks[1]["text"]["text"].endswith("(truncated — see the run)")


def test_empty_body_still_renders():
    blocks = observer_notify._slack_blocks("t", "   ")
    assert blocks[1]["text"]["text"].strip()  # never an empty section
