from pathlib import Path
import json

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
INSTRUMENTS_DIR = REPO_ROOT / "notes" / "static" / "instruments"
TEMPLATES_DIR = REPO_ROOT / "notes" / "templates" / "notes" / "instruments"


def _load_unique_ui_templates() -> list[str]:
    templates: set[str] = set()
    for json_path in sorted(INSTRUMENTS_DIR.glob("*.json")):
        with json_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        ui_template = str(data.get("ui_template", "")).strip()
        if ui_template:
            templates.add(ui_template)
    return sorted(templates)


@pytest.mark.parametrize("template_name", _load_unique_ui_templates())
def test_ui_template_files_exist(template_name: str):
    """
    Scan instrument JSON files to collect unique ui_template names and
    assert that each referenced template exists in the instruments templates directory.
    """
    template_path = TEMPLATES_DIR / template_name
    assert template_path.exists(), (
        f"Missing instrument template: {template_name} (expected at {template_path})"
    )
