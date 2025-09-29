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
    python -m src.eval_mcq baseline "$@"
    ;;
  mcq-robust)
    python -m src.eval_mcq robust "$@"
    ;;
  gsm8k-baseline)
    python -m src.eval_gsm8k baseline "$@"
    ;;
  gsm8k-format)
    python -m src.eval_gsm8k format_strict "$@"
    ;;
  gsm8k-selfconsistency)
    python -m src.eval_gsm8k self_consistency "$@"
    ;;
  *)
    echo "Unknown command: $cmd"
    exit 1
    ;;
esac
