"""Every lesson folder must have a README with the required sections and a run.py.

A finished lesson also has a practice/ folder: practice.yaml (chapter check, exercise hints,
challenges), exercise.py (the stub), solution.py and test_exercise.py.

A README containing `<!-- status: draft -->` is a draft: it must still have every section in
order and a scene under 200 words, but it is excused the diagram and screenshot checks. Drafts
are counted and reported. With `--release`, any draft is a failure.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DRAFT = "<!-- status: draft -->"
REQUIRED = [
    "## The scene",
    "## The concept",
    "## How it works",
    "## The nuances",
    "## Run it",
    "## What you should see",
    "## Try this",
    "## Master it",
    "## What the evidence now shows",
]
# Drafts are excused "Master it" and the practice folder until their lesson is written.
DRAFT_EXCUSED = {"## Master it"}
PRACTICE = ("practice.yaml", "exercise.py", "solution.py", "test_exercise.py")
SCENE_LIMIT = 200


def scene_words(text: str) -> int:
    start = text.index("## The scene") + len("## The scene")
    end = text.index("## The concept", start)
    return len(text[start:end].split())


def main() -> int:
    release = "--release" in sys.argv
    lessons = sorted(p for p in (ROOT / "lessons").glob("[0-9][0-9]-*") if p.is_dir())
    problems: list[str] = []
    drafts: list[str] = []
    for lesson in lessons:
        readme = lesson / "README.md"
        if not (lesson / "run.py").exists():
            problems.append(f"{lesson.name}: missing run.py")
        if not readme.exists():
            problems.append(f"{lesson.name}: missing README.md")
            continue
        text = readme.read_text(encoding="utf-8")
        is_draft = DRAFT in text
        if is_draft:
            drafts.append(lesson.name)
        positions = []
        if not is_draft:
            for f in PRACTICE:
                if not (lesson / "practice" / f).exists():
                    problems.append(f"{lesson.name}: missing practice/{f}")
        for heading in REQUIRED:
            if is_draft and heading in DRAFT_EXCUSED and heading not in text:
                continue
            if heading not in text:
                problems.append(f"{lesson.name}: missing section '{heading}'")
            else:
                positions.append(text.index(heading))
        if positions != sorted(positions):
            problems.append(f"{lesson.name}: sections out of order")
        if "## The scene" in text and "## The concept" in text:
            words = scene_words(text)
            if words > SCENE_LIMIT:
                problems.append(f"{lesson.name}: scene is {words} words (limit {SCENE_LIMIT})")
        has_diagram = "```mermaid" in text or re.search(r"!\[[^\]]*\]\([^)]*diagrams/", text)
        if not is_draft and not has_diagram:
            problems.append(f"{lesson.name}: no diagram (mermaid block or docs/diagrams image)")
        for link in re.findall(r"\]\(([^)#]+)\)", text):
            if not link.startswith("http") and not (lesson / link).resolve().exists():
                if not (is_draft and "screenshots/" in link):
                    problems.append(f"{lesson.name}: broken link {link}")
    if release:
        problems += [f"{name}: still a draft" for name in drafts]
    print("\n".join(problems))
    print(
        f"structure: checked {len(lessons)} lessons, {len(drafts)} drafts, {len(problems)} problems"
    )
    return 1 if problems or not lessons else 0


if __name__ == "__main__":
    sys.exit(main())
