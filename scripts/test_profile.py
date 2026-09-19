#!/usr/bin/env python3
"""Smoke tests for the generated profile repository."""
from __future__ import annotations

import json
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]

config = json.loads((ROOT / "profile.config.json").read_text(encoding="utf-8"))
assert config["profile"]["username"] == "Ekagra444"
assert len(config["experience"]) >= 3
assert len(config["projects"]) >= 3
assert "TypeScript" in config["skills"]["languages"]
assert any("900+" in item for item in config["achievements"])

for path in (ROOT / "assets/hero/hero-dark.svg", ROOT / "assets/hero/hero-light.svg"):
    root = ET.parse(path).getroot()
    assert root.tag.endswith("svg")
    content = path.read_text(encoding="utf-8")
    assert "<animate " in content
    assert "data:image" not in content

readme = (ROOT / "README.md").read_text(encoding="utf-8")
for expected in ("~/about", "~/experience", "~/projects", "~/stack", "~/problem-solving"):
    assert expected in readme

print("smoke tests passed")
