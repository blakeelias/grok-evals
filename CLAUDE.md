# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a reproducible evaluation harness for xAI Grok models, focusing on two main task families:
- **MCQ-style benchmarks** (multiple choice questions with JSONL format)
- **GSM8K-style math reasoning** (mathematical word problems)

The system emphasizes reproducibility, robustness testing, and clear failure analysis over single-shot accuracy.

## Common Development Commands

### Setup and Environment
```bash
# Setup virtual environment and dependencies
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Configure API access (required)
cp env.example .env
# Edit .env to add your XAI_API_KEY
```

### Running Evaluations
Use the `run.sh` script for all evaluations:

```bash
# MCQ baseline evaluation
./run.sh mcq-baseline data/input.jsonl results/output.jsonl

# MCQ robustness testing (with option shuffling)
./run.sh mcq-robust data/input.jsonl results/output.jsonl --num-shuffles 5

# GSM8K baseline evaluation
./run.sh gsm8k-baseline data/input.jsonl results/output.jsonl

# GSM8K with strict answer format enforcement
./run.sh gsm8k-format data/input.jsonl results/output.jsonl

# GSM8K with self-consistency (majority voting)
./run.sh gsm8k-selfconsistency data/input.jsonl results/output.jsonl --samples 5
```

### Direct Python Module Execution
```bash
# MCQ evaluations
python -m src.eval_mcq baseline input.jsonl output.jsonl
python -m src.eval_mcq robust input.jsonl output.jsonl --num-shuffles 5

# GSM8K evaluations
python -m src.eval_gsm8k baseline input.jsonl output.jsonl
python -m src.eval_gsm8k format_strict input.jsonl output.jsonl
python -m src.eval_gsm8k self_consistency input.jsonl output.jsonl --samples 5
```

## Architecture and Code Structure

### Core Components

- **`src/api.py`**: OpenAI-compatible API client wrapper for Grok models
- **`src/eval_mcq.py`**: MCQ evaluation pipeline with baseline and robustness testing
- **`src/eval_gsm8k.py`**: GSM8K evaluation pipeline with answer parsing and self-consistency
- **`src/metrics.py`**: Statistical utilities (accuracy, Wilson confidence intervals, majority voting)
- **`src/augment.py`**: Data augmentation for robustness testing (option shuffling, letter remapping)

### Dataset Adapters

- **`src/datasets/mcq_json.py`**: JSONL loader for MCQ format (`{"question": "...", "options": [...], "answer_idx": 2}`)
- **`src/datasets/gsm8k.py`**: JSONL loader for GSM8K format with answer parsing (`{"question": "...", "answer": "42"}`)

### Key Design Patterns

1. **Abstract Benchmark Interface**: All benchmarks implement `Benchmark[TResponse, TEvaluation]` with structured outputs
2. **Client Abstraction**: `GrokClient` uses xAI's native AsyncClient for async parallel execution
3. **Structured Outputs**: Pydantic schemas eliminate parsing - models return typed objects
4. **Reproducibility**: Fixed seeds, explicit configuration, deterministic evaluation pipelines

### Configuration

- **Environment variables**: Set via `.env` file (XAI_API_KEY, XAI_MODEL, XAI_TEMPERATURE, etc.)
- **Prompt templates**: Located in `prompts/` directory
- **Default model**: `grok-4` with temperature 0.2 and fixed seed 7

### Data Formats

**MCQ JSONL format**:
```json
{"id": "sample-001", "question": "...", "options": ["A", "B", "C", "D"], "answer_idx": 2}
```

**GSM8K JSONL format**:
```json
{"id": "sample-001", "question": "...", "answer": "42", "solution": "..."}
```

## Development Guidelines

- Use fixed seeds for reproducibility (default: 7)
- Maintain temperature ~0.2 for consistent evaluation
- All dataset files should be placed in `data/` directory
- Output results go in `results/` directory
- The system expects JSONL format (one JSON object per line)
- Answer parsing is strict - GSM8K requires "Final Answer: <number>" format

## Testing and Validation

This codebase focuses on evaluation rather than unit testing. Validation occurs through:
- Format validation in dataset readers
- Statistical confidence intervals (Wilson CI) for results
- Robustness testing via option shuffling and multiple sampling
- Answer format enforcement and rejection counting