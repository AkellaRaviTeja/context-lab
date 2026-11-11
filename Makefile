# Context Lab (Case File 06). Run `make help` for the list.
SHELL := /bin/bash
.DEFAULT_GOAL := help
MODELS := qwen3:8b qwen3:4b
OLLAMA_HOST ?= http://localhost:11434
# Use the Docker container when it is running, otherwise a native `ollama` binary.
# Recursive `=` so the check runs when a recipe uses it, after `up` has started the container.
OLLAMA = $(shell docker ps --format '{{.Names}}' 2>/dev/null | grep -qx context-ollama && echo "docker exec context-ollama ollama" || echo ollama)

# Every target here has its script or tool in this repository. Targets for the case builder and
# the memory libraries are added with the chapters that bring those scripts.
.PHONY: help setup install up up-gpu down models doctor lesson lessons shots \
        check release-check lint test prose structure smoke clean \
        quiz exercise exercise-reset hint solution challenge progress \
        notebooks notebooks-check notebook

help: ## Show this help
	@grep -hE '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

setup: install models doctor ## Install, pull models, check (start Ollama first, natively or with `make up`)
	@echo "Ready. Start with: make lesson N=01"

install: ## Install the Python dependencies with uv
	uv sync

up: ## Start Ollama in Docker (CPU)
	docker compose up -d

up-gpu: ## Start Ollama in Docker with an NVIDIA GPU
	docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d

down: ## Stop the Ollama container (models are kept in a volume)
	docker compose down

models: ## Pull the LANTERN models
	@for m in $(MODELS); do echo "pulling $$m"; $(OLLAMA) pull $$m || exit 1; done

doctor: ## Check Ollama, models and config
	uv run python scripts/doctor.py

lesson: ## Run one lesson: make lesson N=09, on OpenRouter: PROVIDER=openrouter
	@test -n "$(N)" || (echo "usage: make lesson N=01 [PROVIDER=openrouter]" && exit 2)
	@$(if $(PROVIDER),LANTERN_PROVIDER=$(PROVIDER)) uv run python lessons/$(N)-*/run.py $(ARGS)

lessons: ## Run every lesson in order (stops at the first draft)
	@for d in lessons/[0-9][0-9]-*/; do n=$$(basename $$d | cut -c1-2); $(MAKE) -s lesson N=$$n || exit 1; done

shots: ## Re-run every lesson and save terminal screenshots to docs/screenshots
	@for d in lessons/[0-9][0-9]-*/; do n=$$(basename $$d | cut -c1-2); $(MAKE) -s lesson N=$$n ARGS=--shot || exit 1; done
	uv run python scripts/svg_to_png.py

check: lint test prose structure ## Every offline gate: lint, tests, prose, structure (drafts allowed)

release-check: check notebooks-check ## Every gate, notebooks current, and no lesson may still be a draft
	uv run python scripts/check_lessons.py --release

lint: ## Ruff
	uv run ruff check src scripts lessons tests

test: ## Unit tests (no model needed)
	uv run pytest -q

prose: ## No em or en dashes in any text file
	uv run python scripts/lint_prose.py

structure: ## Every lesson has the required sections, in order, and a run.py
	uv run python scripts/check_lessons.py

smoke: ## Live tests against Ollama
	uv run pytest -q -m live

# ---- practice: every chapter's practice/ folder (see scripts/learn.py) ----
quiz: ## The chapter check, with why after each answer: make quiz N=05
	@uv run python scripts/learn.py quiz $(N)

exercise: ## Grade your practice/exercise.py, offline: make exercise N=05
	@uv run python scripts/learn.py exercise $(N)

exercise-reset: ## Put a chapter's exercise.py back to the starting stub: make exercise-reset N=05
	git checkout -- lessons/$(N)-*/practice/exercise.py

hint: ## The next hint for a chapter's exercise: make hint N=05
	@uv run python scripts/learn.py hint $(N)

solution: ## The reference solution, once you have tried: make solution N=05
	@uv run python scripts/learn.py solution $(N) $(ARGS)

challenge: ## Break-it challenges, checked against your latest run: make challenge N=05 [ID=...]
	@ID=$(ID) uv run python scripts/learn.py challenge $(N)

progress: ## Every chapter: predictions, check, exercise, challenges
	@uv run python scripts/learn.py progress

notebooks: ## Build lessons/NN-*/lesson.ipynb from each finished chapter's README, run.py and practice
	uv run python scripts/build_notebooks.py

notebooks-check: ## Fail if a committed notebook is out of date
	uv run python scripts/build_notebooks.py --check

notebook: ## Open a chapter's notebook in JupyterLab: make notebook N=05
	@test -n "$(N)" || (echo "usage: make notebook N=05" && exit 2)
	uv run --extra notebooks jupyter lab lessons/$(N)-*/lesson.ipynb

clean: ## Remove caches and the scratch area
	rm -rf .pytest_cache .ruff_cache .scratch
