#!/usr/bin/env python3
"""Generate README.md from profile.config.json.

Only README content is generated. Hand-authored implementation files are not
modified, which makes the repository safe to evolve without template drift.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "profile.config.json"
README = ROOT / "README.md"


def li(items: list[str]) -> str:
    return "\n".join(f"  - {x}" for x in items)


def project_block(p: dict) -> str:
    link = f" — [source]({p['repo']})" if p.get("repo") else ""
    tech = " · ".join(p["tech"])
    highlights = "\n".join(f"  - {x}" for x in p["highlights"])
    return f"""<details open>\n<summary><strong>{p['name']}</strong> — {p['label']}</summary>\n\n{p['summary']}{link}\n\n**Stack:** `{tech}`\n\n{highlights}\n\n</details>"""


def main() -> None:
    data = json.loads(CONFIG.read_text(encoding="utf-8"))
    p = data["profile"]
    contact = data["contact"]

    skills_rows = []
    labels = {
        "languages": "Languages",
        "backend": "Backend",
        "frontend": "Frontend",
        "data": "Data",
        "systems": "Systems",
        "tooling": "Tooling"
    }
    for key, label in labels.items():
        skills_rows.append(f"| {label} | {' · '.join(data['skills'][key])} |")

    experience = []
    for x in data["experience"]:
        bullets = "\n".join(f"  - {h}" for h in x["highlights"])
        experience.append(f"### {x['company']}\n**{x['role']}** · {x['period']} · {x['mode']}\n\n{bullets}")

    projects = "\n\n".join(project_block(x) for x in data["projects"])
    achievements = "\n".join(f"- {x}" for x in data["achievements"])

    readme = f"""<!-- AUTO-GENERATED SECTION: do not hand-edit between profile markers. -->\n<div align=\"center\">\n\n<picture>\n  <source media=\"(prefers-color-scheme: dark)\" srcset=\"./assets/hero/hero-dark.svg\">\n  <source media=\"(prefers-color-scheme: light)\" srcset=\"./assets/hero/hero-light.svg\">\n  <img alt=\"Ekagra Agrawal — animated terminal portrait\" src=\"./assets/hero/hero-light.svg\" width=\"980\">\n</picture>\n\n</div>\n\n---\n\n## `~/about`\n\nI am a **software engineer** with a systems-oriented focus on backend engineering, distributed systems, and reliability. I enjoy building services where correctness, failure handling, performance, and clean abstractions matter.\n\n{p['education']} · **CGPA {p['cgpa']}**\n\n## `~/experience`\n\n{chr(10).join(experience)}\n\n## `~/projects`\n\n{projects}\n\n## `~/stack`\n\n| Area | Technologies |\n|---|---|\n{chr(10).join(skills_rows)}\n\n## `~/problem-solving`\n\n{achievements}\n\n## `~/connect`\n\n[GitHub]({contact['github']}) · [Email](mailto:{contact['email']})\n\n```text\n$ echo \"build reliable systems, then make them easy to understand\"\nbuild reliable systems, then make them easy to understand\n```\n\n<!-- END AUTO-GENERATED SECTION -->\n"""

    README.write_text(readme, encoding="utf-8")
    print(f"wrote {README}")


if __name__ == "__main__":
    main()
