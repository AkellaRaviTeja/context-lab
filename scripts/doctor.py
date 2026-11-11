"""Check that LANTERN is ready: Ollama, the models and the configuration."""

from __future__ import annotations

import sys

import httpx

from lantern.config import load_config

PROVIDERS = {"ollama", "openrouter", "anthropic", "openai", "gemini"}


def main() -> int:
    cfg = load_config()
    checks: list[tuple[str, bool, str]] = []
    host = cfg["ollama"]["host"]
    try:
        version = httpx.get(f"{host}/api/version", timeout=5).json()["version"]
        checks.append(("Ollama reachable", True, f"{host} (version {version})"))
        pulled = {m["name"] for m in httpx.get(f"{host}/api/tags", timeout=5).json()["models"]}
    except httpx.HTTPError as e:
        checks.append(("Ollama reachable", False, f"{host}: {e}. Run `make up`."))
        pulled = set()
    for alias, name in cfg["models"].items():
        checks.append(
            (
                f"model {alias}",
                name in pulled,
                name if name in pulled else f"{name} missing. Run `make models`.",
            )
        )
    checks.append(("provider", cfg["provider"] in PROVIDERS, cfg["provider"]))
    local = cfg["provider"] == "ollama" and not cfg["synthetic"]["cloud"]
    checks.append(
        (
            "evidence stays local",
            local,
            "provider ollama, synthetic.cloud off"
            if local
            else "a cloud route is on. Evidence chapters must run on Ollama.",
        )
    )
    for label, ok, info in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {label:<20} {info}")
    failed = sum(not ok for _, ok, _ in checks)
    print(f"doctor: {len(checks)} checks, {failed} failed")
    return 1 if failed or not checks else 0


if __name__ == "__main__":
    sys.exit(main())
