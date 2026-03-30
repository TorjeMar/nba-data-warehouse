import pytest

from src.etl.transform import build_record


def test_build_record_valid():
    row = {
        "gameId": "123",
        "teamId": "1",
        "teamCity": "City",
        "teamName": "Team",
        "teamTricode": "ABC",
        "teamSlug": "team",
        "personId": "42",
        "firstName": "John",
        "familyName": "Doe",
        "points": "10",
    }

    record = build_record(row)

    assert record.source_game_id == "123"
    assert record.source_team_id == 1
    assert record.source_person_id == 42
    assert record.points == 10


def test_build_record_missing_required_field():
    row = {"bad": "data"}

    with pytest.raises(KeyError):
        build_record(row)
