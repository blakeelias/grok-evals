# Evaluation Architecture

## Overview

This codebase implements a flexible, async evaluation harness for LLM benchmarks with the following key features:

- **Structured outputs via Pydantic schemas** - No more fragile regex parsing
- **Async parallel execution** - Fast evaluation with configurable concurrency
- **Flexible evaluation types** - Binary, categorical, or custom evaluation per benchmark
- **LLM-based judges** - Support for async judge model calls
- **Type-safe generics** - Full type safety for responses and evaluations

## Core Components

### 1. Benchmark Abstract Class (`src/benchmark.py`)

```python
class Benchmark(ABC, Generic[TResponse, TEvaluation]):
    def load_dataset(path) -> Iterator[Dict]
    def format_prompt(example) -> str
    def response_schema() -> Type[TResponse]  # Pydantic model
    async def evaluate(response, example) -> TEvaluation
    def name -> str
```

**Generic Parameters:**
- `TResponse`: Pydantic model defining structured output format
- `TEvaluation`: Type of evaluation result (bool, Enum, dataclass, etc.)

### 2. EvaluationRunner (`src/runner.py`)

Handles async parallel execution:
- Rate limiting via semaphore
- Progress tracking with tqdm
- Result collection and JSONL persistence
- Error handling per item

### 3. AsyncGrokClient (`src/api.py`)

Async API client with:
- `complete_structured()` - Structured outputs using `beta.chat.completions.parse`
- Automatic prompt caching (enabled by Grok API)
- Configurable temperature, seed, top_p for reproducibility

### 4. Concrete Benchmarks (`src/benchmarks/`)

**MCQBenchmark:**
- Response: `{answer: str}` (single letter)
- Evaluation: `bool` (correct/incorrect)

**GSM8KBenchmark:**
- Response: `{reasoning: str, final_answer: int}`
- Evaluation: `bool` (answer matches gold)

## Usage

### Run via shell script:
```bash
./run.sh mcq-baseline data/mmlu_sample.jsonl results/mcq_out.jsonl
./run.sh gsm8k-baseline data/gsm8k_sample.jsonl results/gsm8k_out.jsonl
```

### Run directly:
```bash
python -m src.run_eval mcq baseline input.jsonl output.jsonl
python -m src.run_eval gsm8k baseline input.jsonl output.jsonl
```

## Adding New Benchmarks

1. Define response schema:
```python
class MyResponse(BaseModel):
    answer: str
    confidence: float
```

2. Define evaluation type (bool, Enum, dataclass):
```python
class MyScore(Enum):
    PERFECT = 3
    PARTIAL = 2
    WRONG = 1
```

3. Implement Benchmark:
```python
class MyBenchmark(Benchmark[MyResponse, MyScore]):
    def load_dataset(self, path):
        # Load from JSONL

    def format_prompt(self, example):
        # Format prompt

    def response_schema(self):
        return MyResponse

    async def evaluate(self, response, example):
        # Return MyScore enum
```

4. Register in `src/benchmarks/__init__.py` and `src/run_eval.py`

## Key Design Decisions

1. **Double-generic Benchmark** - Each benchmark defines both response format AND evaluation type
2. **Async evaluate()** - Enables LLM judge calls without blocking
3. **Structured outputs** - Eliminates parsing failures, improves reliability
4. **JSONL everywhere** - Transparent, debuggable, easy to analyze

## Future Extensions

- Augmentation strategies (shuffling, paraphrasing)
- Self-consistency / majority voting
- Multi-turn evaluations
- Batch API support (if available)
- Prompt caching optimization
