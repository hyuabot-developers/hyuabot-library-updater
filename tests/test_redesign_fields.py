import json
from datetime import datetime, timezone
from pathlib import Path

from scripts.realtime import reading_room_item


FIXTURE = Path(__file__).parent / "fixtures" / "reading_room_unavailable.json"


def test_unavailable_room_fixture_keeps_existing_reservable_flag_and_reason():
    room = json.loads(FIXTURE.read_text())
    item = reading_room_item(room, 1, datetime(2026, 10, 4, tzinfo=timezone.utc))

    assert item["is_reservable"] is False
    assert item["unable_message"] == "점검 중"
