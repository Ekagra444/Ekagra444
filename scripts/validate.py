#!/usr/bin/env python3
"""Repository validation for generated GitHub profile assets."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
errors: list[str] = []

config = json.loads((ROOT / "profile.config.json").read_text(encoding="utf-8"))
if config["profile"]["username"] != ROOT.name:
    # The repo can be named differently while developing locally, but this is a
    # warning worth surfacing before publish.
    print(f"warning: local directory is {ROOT.name!r}; GitHub profile repo must be named {config['profile']['username']!r}")

for path in [ROOT / "README.md", ROOT / "assets/hero/hero-dark.svg", ROOT / "assets/hero/hero-light.svg", ROOT / "assets/hero/manifest.json"]:
    if not path.exists():
        errors.append(f"missing generated asset: {path}")

readme = (ROOT / "README.md").read_text(encoding="utf-8")
for required in ["hero-dark.svg", "hero-light.svg", "~/about", "~/experience", "~/projects", "~/stack", "~/problem-solving"]:
    if required not in readme:
        errors.append(f"README missing expected marker/content: {required}")

# Catch accidental public source-portrait files. The exception allows generated
# metadata/artifacts under assets/.
for p in ROOT.rglob("*"):
    if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg"}:
        errors.append(f"source portrait must not be committed: {p.relative_to(ROOT)}")

for svg in [ROOT / "assets/hero/hero-dark.svg", ROOT / "assets/hero/hero-light.svg"]:
    text = svg.read_text(encoding="utf-8")
    if not text.lstrip().startswith("<?xml"):
        errors.append(f"invalid SVG header: {svg.name}")
    for token in ["<animate ", "roll-mask", "aria-labelledby"]:
        if token not in text:
            errors.append(f"SVG {svg.name} missing expected token: {token}")

if errors:
    print("VALIDATION FAILED")
    for err in errors:
        print(f"- {err}")
    raise SystemExit(1)

print("validation passed")
