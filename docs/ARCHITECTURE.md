# Evaluation Architecture

## Overview

This codebase implements a flexible, async evaluation harness for LLM benchmarks using xAI's native SDK. Key features:

- **xAI Native SDK** - Built on `xai_sdk.AsyncClient` with automatic prompt caching
- **Structured outputs via Pydantic** - No fragile regex parsing
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

### 3. GrokClient (`src/api.py`)

Async API client using xAI's official SDK:
- `complete_structured()` - Structured outputs using `chat.sample(output_model=...)`
- Native xAI `AsyncClient` with automatic prompt caching
- Configurable temperature, top_p, max_tokens for reproducibility

**Implementation:**
```python
from xai_sdk import AsyncClient
from xai_sdk.chat import user, system

client = GrokClient()  # Wraps xAI AsyncClient

# Structured outputs using xAI's native API
response = await client.complete_structured(
    prompt="What is 2+2?",
    response_model=MathResponse  # Pydantic model
)
```

**Benefits:**
- Native async/await throughout
- Automatic prompt caching (built into xAI API)
- Better performance and reliability
- Simpler API than OpenAI's beta endpoints

### 4. Concrete Benchmarks (`src/benchmarks/`)

**MCQBenchmark:**
- Response: `{answer: str}` (single letter)
- Evaluation: `bool` (correct/incorrect)

**GSM8KBenchmark:**
- Response: `{reasoning: str, final_answer: int}`
- Evaluation: `bool` (answer matches gold)

## Architecture Diagram

```
┌─────────────────────────────────────────┐
│  Benchmark[TResponse, TEvaluation]      │
│  - Defines dataset format               │
│  - Defines response schema (Pydantic)   │
│  - Defines evaluation type (bool/Enum)  │
│  - Async evaluate() for LLM judges      │
└─────────────────────────────────────────┘
                  ▼
┌─────────────────────────────────────────┐
│  EvaluationRunner                        │
│  - Parallel async execution             │
│  - Rate limiting (configurable)         │
│  - Progress tracking                    │
│  - Result persistence (JSONL)           │
└─────────────────────────────────────────┘
                  ▼
┌─────────────────────────────────────────┐
│  GrokClient (xAI AsyncClient wrapper)   │
│  - complete_structured() for Pydantic   │
│  - Automatic prompt caching             │
│  - Native async support                 │
└─────────────────────────────────────────┘
```

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

### 1. Define response schema:
```python
from pydantic import BaseModel, Field

class MyResponse(BaseModel):
    answer: str
    confidence: float = Field(ge=0.0, le=1.0)
```

### 2. Define evaluation type (bool, Enum, dataclass):
```python
from enum import Enum

class MyScore(Enum):
    PERFECT = 3
    PARTIAL = 2
    WRONG = 1
```

### 3. Implement Benchmark:
```python
from src.benchmark import Benchmark

class MyBenchmark(Benchmark[MyResponse, MyScore]):
    def load_dataset(self, path):
        # Load from JSONL
        with open(path) as f:
            for line in f:
                yield json.loads(line)

    def format_prompt(self, example):
        return f"Question: {example['question']}\nAnswer:"

    def response_schema(self):
        return MyResponse

    async def evaluate(self, response, example):
        # Could call LLM judge here!
        if response.answer == example['gold_answer']:
            return MyScore.PERFECT
        elif response.confidence > 0.5:
            return MyScore.PARTIAL
        else:
            return MyScore.WRONG

    @property
    def name(self):
        return "my_benchmark"
```

### 4. Register in `src/benchmarks/__init__.py` and `src/run_eval.py`

## Key Design Decisions

1. **Double-generic Benchmark** - Each benchmark defines both response format AND evaluation type
2. **Async evaluate()** - Enables LLM judge calls without blocking
3. **Structured outputs** - Eliminates parsing failures, improves reliability
4. **JSONL everywhere** - Transparent, debuggable, easy to analyze
5. **xAI Native SDK** - Better performance, automatic caching, simpler API

## Migration from OpenAI SDK

### Old Code (OpenAI SDK):
```python
from openai import AsyncOpenAI

client = AsyncOpenAI(base_url="https://api.x.ai")
response = await client.beta.chat.completions.parse(
    model="grok-4",
    messages=[{"role": "user", "content": prompt}],
    response_format=MySchema
)
result = response.choices[0].message.parsed
```

### New Code (xAI SDK):
```python
from src.api import GrokClient

client = GrokClient()
result = await client.complete_structured(
    prompt=prompt,
    response_model=MySchema
)
```

### Requirements Changes:

**Before:**
```
openai>=1.40.0
```

**After:**
```
xai-sdk>=0.1.0
pydantic>=2.0.0
```

## Advanced Features

### LLM-based Judge Example:
```python
class EssayBenchmark(Benchmark[EssayResponse, EssayGrade]):
    def __init__(self, judge_client: GrokClient):
        self.judge_client = judge_client

    async def evaluate(self, response, example):
        # Call LLM judge asynchronously
        grade = await self.judge_client.complete_structured(
            prompt=f"Grade this essay: {response.text}\nRubric: {example['rubric']}",
            response_model=EssayGrade
        )
        return grade
```

### Structured Evaluation Result:
```python
from dataclasses import dataclass

@dataclass
class CodeEvaluation:
    passes_tests: bool
    follows_style: bool
    reasoning_steps_correct: List[bool]

class CodeBenchmark(Benchmark[CodeResponse, CodeEvaluation]):
    async def evaluate(self, response, example):
        return CodeEvaluation(
            passes_tests=self._run_tests(response.code),
            follows_style=self._check_style(response.code),
            reasoning_steps_correct=[True, True, False]
        )
```

## Implementation Status

- ✅ xAI SDK integration
- ✅ Single unified async client
- ✅ Structured outputs with Pydantic
- ✅ Async parallel execution with rate limiting
- ✅ Automatic prompt caching
- ✅ Binary evaluation (bool)
- ✅ Generic evaluation types (bool, Enum, custom)
- 🔲 Augmentation strategies (shuffling, paraphrasing)
- 🔲 Self-consistency / majority voting
- 🔲 LLM-based judge examples
- 🔲 Multi-turn evaluations
