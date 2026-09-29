from datetime import timedelta

import pytest

from bot.db import Database
from bot.utils import format_duration, parse_duration


@pytest.mark.parametrize(
    "text, expected",
    [
        ("30s", timedelta(seconds=30)),
        ("10m", timedelta(minutes=10)),
        ("10min", timedelta(minutes=10)),
        ("2h", timedelta(hours=2)),
        ("1j", timedelta(days=1)),
        ("1d", timedelta(days=1)),
        ("1h30m", timedelta(hours=1, minutes=30)),
        ("1h 30m", timedelta(hours=1, minutes=30)),
    ],
)
def test_parse_duration(text, expected):
    assert parse_duration(text) == expected


@pytest.mark.parametrize("text", ["", "abc", "10", "10x", "0m", "m10", "10m abc"])
def test_parse_duration_invalid(text):
    assert parse_duration(text) is None


def test_format_duration():
    assert format_duration(timedelta(hours=1, minutes=30)) == "1 h 30 min"
    assert format_duration(timedelta(days=2)) == "2 j"


def test_warnings_database(tmp_path):
    db = Database(tmp_path / "test.sqlite3")
    first = db.add_warning(1, 42, 7, "spam")
    db.add_warning(1, 42, 7, "insulte")
    db.add_warning(2, 42, 7, "autre serveur")
    assert db.count_warnings(1, 42) == 2
    assert [w.reason for w in db.list_warnings(1, 42)] == ["spam", "insulte"]
    assert db.delete_warning(1, first)
    assert not db.delete_warning(1, first)
    assert db.clear_warnings(1, 42) == 1
    assert db.count_warnings(2, 42) == 1
    db.close()
