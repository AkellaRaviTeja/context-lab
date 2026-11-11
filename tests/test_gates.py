import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(script, *args):
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts" / script), *args], capture_output=True, text=True
    )


def test_prose_gate_passes_and_counts():
    r = run("lint_prose.py")
    assert r.returncode == 0, r.stdout
    assert "checked" in r.stdout and "checked 0 files" not in r.stdout


def test_prose_gate_catches_em_dash():
    bad = ROOT / "lessons" / "_tmp_bad.md"
    bad.write_text("a " + chr(0x2014) + " b\n", encoding="utf-8")
    try:
        r = run("lint_prose.py")
        assert r.returncode == 1 and "em dash" in r.stdout
    finally:
        bad.unlink()


def test_structure_gate_counts_lessons_and_drafts():
    r = run("check_lessons.py")
    assert r.returncode == 0, r.stdout
    assert "checked 0 lessons" not in r.stdout
    assert "drafts" in r.stdout


def test_release_gate_fails_while_drafts_remain():
    r = run("check_lessons.py")
    if " 0 drafts" in r.stdout:
        return
    r = run("check_lessons.py", "--release")
    assert r.returncode == 1 and "still a draft" in r.stdout


def test_structure_gate_rejects_long_scene():
    lesson = ROOT / "lessons" / "99-tmp-long-scene"
    lesson.mkdir()
    try:
        (lesson / "run.py").write_text("", encoding="utf-8")
        sections = [
            "## The concept",
            "## How it works",
            "## The nuances",
            "## Run it",
            "## What you should see",
            "## Try this",
            "## What the evidence now shows",
        ]
        text = "<!-- status: draft -->\n## The scene\n" + "word " * 201 + "\n" + "\n".join(sections)
        (lesson / "README.md").write_text(text, encoding="utf-8")
        r = run("check_lessons.py")
        assert r.returncode == 1 and "99-tmp-long-scene: scene is 201 words" in r.stdout
    finally:
        for f in lesson.iterdir():
            f.unlink()
        lesson.rmdir()
