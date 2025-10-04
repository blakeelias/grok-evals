#!/usr/bin/env bash
set -euo pipefail

if [ ! -d ".venv" ]; then
  python -m venv .venv
fi
source .venv/bin/activate

pip -q install -r requirements.txt

cmd="${1:-}"
if [ -z "$cmd" ]; then
  echo "Usage: ./run.sh <mcq-baseline|mcq-robust|gsm8k-baseline|gsm8k-format|gsm8k-selfconsistency> <input.jsonl> <output.jsonl> [args...]"
  exit 1
fi

shift || true

case "$cmd" in
  mcq-baseline)
    python -m src.run_eval mcq baseline "$@"
    ;;
  mcq-robust)
    # TODO: Implement robust mode with new architecture
    echo "mcq-robust not yet implemented in new architecture"
    exit 1
    ;;
  gsm8k-baseline)
    python -m src.run_eval gsm8k baseline "$@"
    ;;
  gsm8k-format)
    # With structured outputs, format is always strict
    python -m src.run_eval gsm8k baseline "$@"
    ;;
  gsm8k-selfconsistency)
    # TODO: Implement self-consistency with new architecture
    echo "gsm8k-selfconsistency not yet implemented in new architecture"
    exit 1
    ;;
  *)
    echo "Unknown command: $cmd"
    exit 1
    ;;
esac
