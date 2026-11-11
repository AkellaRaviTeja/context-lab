"""Terminal output for lessons, with an optional screenshot of the whole run.

Run any lesson with `--shot` and the terminal output is saved as an SVG
under docs/screenshots/, which is how the screenshots in the READMEs are made.
"""

from __future__ import annotations

import re
import sys

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table

from lantern.config import ROOT, load_config

SHOT = "--shot" in sys.argv
console = Console(record=SHOT, width=110 if SHOT else None)

__all__ = [
    "Table",
    "chapter",
    "console",
    "draft",
    "evidence",
    "finding",
    "note",
    "reply",
    "save_shot",
    "step",
    "tool_call",
]


def _prose(text: str) -> str:
    """Join hard-wrapped lines into paragraphs so panels wrap to the terminal width."""
    paras = re.split(r"\n\s*\n", text.strip())
    return "\n\n".join(" ".join(line.strip() for line in p.splitlines()) for p in paras)


def chapter(number: str, title: str, scene: str) -> None:
    """Open a lesson: the chapter title and the opening scene of the story."""
    console.print(Rule(f"[bold]Chapter {number}: {title}[/bold]", style="yellow"))
    console.print(
        Panel(
            _prose(scene),
            title="Case File 06: What LANTERN Remembers",
            border_style="yellow",
            padding=(1, 2),
        )
    )


def step(title: str) -> None:
    console.print()
    console.print(Rule(f"[bold cyan]{title}[/bold cyan]", style="cyan", align="left"))


def evidence(label: str, text: str) -> None:
    console.print(Panel(text.strip(), title=f"[dim]evidence[/dim] {label}", border_style="dim"))


def reply(label: str, text: str, *, meta: str = "", style: str = "green") -> None:
    console.print(
        Panel(Markdown(text.strip() or "(empty)"), title=label, subtitle=meta, border_style=style)
    )


def note(text: str) -> None:
    console.print(f"[magenta]>[/magenta] {text}")


def tool_call(name: str, arguments: dict, result: str = "", limit: int | None = None) -> None:
    """Show one tool call and, if given, what it returned (cut to `limit` characters, with ...).

    Only the display is cut. Whatever the lesson sends back to the model is unchanged.
    """
    if limit is not None and len(result) > limit:
        result = result[:limit].rstrip() + " ..."
    args = ", ".join(f"{k}={v!r}" for k, v in arguments.items())
    body = f"[bold]{name}[/bold]({args})" + (f"\n[dim]returned[/dim] {result}" if result else "")
    console.print(Panel(body, title="[dim]tool call[/dim]", border_style="blue"))


def draft(number: str) -> None:
    """Stop a lesson that is not written yet, with a non-zero exit so `make lessons` notices."""
    console.print()
    console.print(
        Panel(
            f"Chapter {number} is a draft. The scene is written; the lesson is not.",
            border_style="red",
        )
    )
    raise SystemExit(3)


def finding(text: str) -> None:
    """Close a lesson: what the evidence now shows."""
    console.print()
    console.print(
        Panel(
            _prose(text),
            title="[bold]What the evidence now shows[/bold]",
            border_style="red",
            padding=(1, 2),
        )
    )


def save_shot(name: str) -> None:
    """Save the recorded terminal output as an SVG screenshot (only with --shot)."""
    if not SHOT:
        return
    out = ROOT / load_config()["screenshots_dir"] / f"{name}.svg"
    out.parent.mkdir(parents=True, exist_ok=True)
    console.save_svg(str(out), title=f"make lesson N={name[:2]}")
    # Fira Code draws "<|" and "|>" as arrows, which mangles chat-template text. Turn it off.
    svg = out.read_text(encoding="utf-8")
    out.write_text(
        svg.replace("<style>", "<style>\ntext { font-variant-ligatures: none; }", 1),
        encoding="utf-8",
    )
    console.print(f"[dim]screenshot saved to {out.relative_to(ROOT)}[/dim]")
