from pathlib import Path
import json

import pytest


INSTRUMENTS_DIR = Path(__file__).resolve().parents[1] / "notes" / "static" / "instruments"


@pytest.mark.parametrize("json_path", sorted(INSTRUMENTS_DIR.glob("*.json")))
def test_instrument_json_schema(json_path: Path):
    # Load JSON
    with json_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # Required top-level keys
    required_top_keys = {
        "name": str,
        "ui_template": str,
        "clefs": list,
        "common_keys": list,
        "skill_levels": dict,
        "fingerings": dict,
    }

    for key, expected_type in required_top_keys.items():
        assert key in data, f"Missing required key '{key}' in {json_path.name}"
        assert isinstance(data[key], expected_type), (
            f"Key '{key}' in {json_path.name} must be of type {expected_type.__name__}"
        )

    # name must be non-empty
    assert data["name"].strip(), f"'name' must be non-empty in {json_path.name}"

    # ui_template must be a non-empty filename-like string
    assert data["ui_template"].strip(), f"'ui_template' must be non-empty in {json_path.name}"
    assert "." in data["ui_template"], f"'ui_template' should include an extension in {json_path.name}"

    # clefs: list of non-empty strings
    assert data["clefs"], f"'clefs' must not be empty in {json_path.name}"
    assert all(isinstance(c, str) and c.strip() for c in data["clefs"]), (
        f"All 'clefs' entries must be non-empty strings in {json_path.name}"
    )

    # common_keys: list of non-empty strings
    assert data["common_keys"], f"'common_keys' must not be empty in {json_path.name}"
    assert all(isinstance(k, str) and k.strip() for k in data["common_keys"]), (
        f"All 'common_keys' entries must be non-empty strings in {json_path.name}"
    )

    # skill_levels: must include Beginner, Intermediate, Advanced
    skill_levels = data["skill_levels"]
    for level in ("Beginner", "Intermediate", "Advanced"):
        assert level in skill_levels, f"Missing skill level '{level}' in {json_path.name}"
        assert isinstance(skill_levels[level], dict), (
            f"Skill level '{level}' must be an object in {json_path.name}"
        )
        level_obj = skill_levels[level]
        # Each level must either have 'notes' (string) or both 'lowest_note' and 'highest_note' (strings)
        has_notes = "notes" in level_obj
        has_range = "lowest_note" in level_obj and "highest_note" in level_obj
        assert has_notes or has_range, (
            f"Level '{level}' in {json_path.name} must define 'notes' or both 'lowest_note' and 'highest_note'"
        )
        if has_notes:
            assert isinstance(level_obj["notes"], str) and level_obj["notes"].strip(), (
                f"'notes' in level '{level}' must be a non-empty string in {json_path.name}"
            )
        if has_range:
            assert isinstance(level_obj["lowest_note"], str) and level_obj["lowest_note"].strip(), (
                f"'lowest_note' in level '{level}' must be a non-empty string in {json_path.name}"
            )
            assert isinstance(level_obj["highest_note"], str) and level_obj["highest_note"].strip(), (
                f"'highest_note' in level '{level}' must be a non-empty string in {json_path.name}"
            )

    # fingerings: dict mapping note identifiers to list[str]
    fingerings = data["fingerings"]
    for note_id, options in fingerings.items():
        assert isinstance(note_id, str) and note_id.strip(), (
            f"Fingering key must be a non-empty string in {json_path.name}"
        )
        assert isinstance(options, list), (
            f"Fingering value for '{note_id}' must be a list in {json_path.name}"
        )
        assert all(isinstance(opt, str) for opt in options), (
            f"All fingering options for '{note_id}' must be strings in {json_path.name}"
        )
