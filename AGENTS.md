# Repository Guidelines

## Project Structure & Module Organization
- `src/` holds the harness: `eval_mcq.py`/`eval_gsm8k.py` drive runs, `datasets/` adapts JSONL inputs, `api.py` manages the Grok client, and `metrics.py` reports accuracy.
- `run.sh` bootstraps `.venv`, installs dependencies, and dispatches to the requested mode.
- `prompts/` stores the system and chain-of-thought templates; update when prompt wording changes.
- `configs/` hosts sample configs; `data/` and `results/` house local inputs and outputs (tracked via `.gitkeep`).
- Review `CLAUDE.md` for architectural background before reworking execution flows.

## Build, Test, and Development Commands
- `python -m venv .venv && source .venv/bin/activate` creates `.venv`; rerun after Python upgrades.
- `pip install -r requirements.txt` (also run by `run.sh`) keeps client tooling pinned.
- `./run.sh mcq-baseline data/mmlu_sample.jsonl results/mcq_baseline.jsonl` executes the canonical MCQ pass; switch to `mcq-robust` or `gsm8k-selfconsistency` for other modes.
- For debugging, call modules directly: `python -m src.eval_gsm8k baseline <in> <out>`.

## Coding Style & Naming Conventions
- Python files use 4-space indentation, type hints for public functions, and `snake_case` for modules, files, and helpers.
- Keep functions pure when practical and return structured dicts like the existing evaluators.
- Prefer f-strings for user-visible output and log succinct summaries (accuracy, CI).
- Document non-obvious prompt or shuffling logic with short comments rather than verbose blocks.

## Testing Guidelines
- There is no standalone test suite; validate changes by running the relevant `./run.sh` mode against a representative JSONL sample in `data/`.
- Capture before/after metrics under `results/` and verify output rows include required fields (`chosen_letter`, `raw_completion`, etc.).
- When adding adapters or modes, include a minimal synthetic fixture in `data/` so reviewers can reproduce results quickly.

## Commit & Pull Request Guidelines
- Follow the existing history: start messages with an imperative verb and keep them under ~72 characters (e.g., `Add MCQ shuffle guard`).
- Each PR should summarize scope, list datasets or commands used for validation, and attach key metrics or diffs from `results/`.
- Link tracking issues when applicable and flag any API key or configuration changes reviewers must apply.

## Environment & API Configuration
- Duplicate `env.example` to `.env` and populate `XAI_API_KEY`; optional overrides include `XAI_MODEL`, `XAI_TEMPERATURE`, and the base URL.
- Never commit secrets or dataset dumps; scrub outputs before sharing and reference paths like `results/*.jsonl` in documentation.
- After rotating keys, update `.env` and re-source the virtualenv so the client picks up the new environment.
