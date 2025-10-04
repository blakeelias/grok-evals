"""
Async evaluation runner for executing benchmarks with parallel inference.

This module provides the EvaluationRunner class that handles:
- Parallel async LLM API calls
- Result collection and persistence
- Progress tracking
- Rate limiting and error handling
"""

import asyncio
import json
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional, TypeVar, Generic
from tqdm.asyncio import tqdm
from pydantic import BaseModel

from .benchmark import Benchmark

# Type variables matching the Benchmark generics
TResponse = TypeVar('TResponse', bound=BaseModel)
TEvaluation = TypeVar('TEvaluation')


@dataclass
class EvaluationItem(Generic[TResponse, TEvaluation]):
    """
    Represents a single evaluation instance with all associated data.

    This stores the complete evaluation pipeline for one item:
    - Input: example data, formatted prompt
    - Model output: parsed structured response (Pydantic model)
    - Evaluation: evaluation result
    - Metadata: IDs for tracking and grouping
    """
    item_id: str                              # Unique ID for this specific item
    group_id: Optional[str]                   # ID linking related items (e.g., shuffled variants)
    example: Dict[str, Any]                   # Original dataset example
    prompt: str                               # Formatted prompt sent to model
    parsed_response: Optional[TResponse]      # Structured response (Pydantic model)
    evaluation: Optional[TEvaluation]         # Evaluation result (type defined by benchmark)
    metadata: Dict[str, Any]                  # Extra info (shuffle_id, temperature, etc.)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSONL serialization."""
        result = {
            "item_id": self.item_id,
            "group_id": self.group_id,
            "example": self.example,
            "prompt": self.prompt,
            "metadata": self.metadata,
        }

        # Handle Pydantic model serialization
        if self.parsed_response is not None:
            result["parsed_response"] = self.parsed_response.model_dump()
        else:
            result["parsed_response"] = None

        # Handle various evaluation types
        if self.evaluation is not None:
            if hasattr(self.evaluation, '__dict__'):
                # Dataclass or object
                result["evaluation"] = asdict(self.evaluation) if hasattr(self.evaluation, '__dataclass_fields__') else str(self.evaluation)
            else:
                # Primitive or Enum
                result["evaluation"] = self.evaluation.value if hasattr(self.evaluation, 'value') else self.evaluation
        else:
            result["evaluation"] = None

        return result


class EvaluationResults(Generic[TResponse, TEvaluation]):
    """
    Collection of evaluation results with grouping and analysis support.
    """

    def __init__(self):
        self.items: List[EvaluationItem[TResponse, TEvaluation]] = []

    def add_item(self, item: EvaluationItem[TResponse, TEvaluation]):
        """Add a single evaluation result."""
        self.items.append(item)

    def get_by_group(self, group_id: str) -> List[EvaluationItem[TResponse, TEvaluation]]:
        """Get all items in a group (e.g., all shuffled variants of same question)."""
        return [item for item in self.items if item.group_id == group_id]

    def to_jsonl(self, path: str):
        """Save results as JSONL file."""
        with open(path, 'w', encoding='utf-8') as f:
            for item in self.items:
                f.write(json.dumps(item.to_dict()) + '\n')

    def __len__(self) -> int:
        return len(self.items)


class EvaluationRunner:
    """
    Handles async parallel evaluation execution.

    This runner manages the complete evaluation pipeline:
    1. Load dataset examples
    2. Format prompts for each example
    3. Make parallel async API calls to get model responses
    4. Parse responses using benchmark's schema
    5. Evaluate responses (potentially with async LLM judge)
    6. Collect and persist results
    """

    def __init__(self, client, max_parallel: int = 10):
        """
        Initialize the evaluation runner.

        Args:
            client: Async LLM client (must have complete_structured method)
            max_parallel: Maximum number of concurrent API calls
        """
        self.client = client
        self.max_parallel = max_parallel
        self.semaphore = asyncio.Semaphore(max_parallel)

    async def run_benchmark(
        self,
        benchmark: Benchmark[TResponse, TEvaluation],
        dataset_path: str,
        output_path: Optional[str] = None,
        **kwargs
    ) -> EvaluationResults[TResponse, TEvaluation]:
        """
        Run evaluation on a benchmark with async parallel execution.

        Args:
            benchmark: The benchmark to evaluate
            dataset_path: Path to dataset file
            output_path: Optional path to save results JSONL
            **kwargs: Additional options (for future expansion)

        Returns:
            EvaluationResults containing all evaluation items
        """
        # Load dataset
        examples = list(benchmark.load_dataset(dataset_path))

        # Prepare evaluation items
        eval_items = self._prepare_eval_items(benchmark, examples)

        # Run parallel inference and evaluation
        results = EvaluationResults[TResponse, TEvaluation]()

        # Process with progress bar
        tasks = [self._process_item(benchmark, item) for item in eval_items]

        for coro in tqdm.as_completed(tasks, total=len(tasks), desc=f"Evaluating {benchmark.name}"):
            completed_item = await coro
            results.add_item(completed_item)

        # Save results if output path provided
        if output_path:
            results.to_jsonl(output_path)

        return results

    def _prepare_eval_items(
        self,
        benchmark: Benchmark[TResponse, TEvaluation],
        examples: List[Dict[str, Any]]
    ) -> List[EvaluationItem[TResponse, TEvaluation]]:
        """
        Create evaluation items from dataset examples.

        Currently creates one item per example. In the future, this could
        handle augmentation strategies (shuffling, etc.).
        """
        items = []
        for i, example in enumerate(examples):
            item = EvaluationItem(
                item_id=example.get('id', f'item_{i}'),
                group_id=example.get('id', f'item_{i}'),  # Same as item_id for now
                example=example,
                prompt=benchmark.format_prompt(example),
                parsed_response=None,
                evaluation=None,
                metadata={}
            )
            items.append(item)
        return items

    async def _process_item(
        self,
        benchmark: Benchmark[TResponse, TEvaluation],
        item: EvaluationItem[TResponse, TEvaluation]
    ) -> EvaluationItem[TResponse, TEvaluation]:
        """
        Process a single evaluation item: inference + evaluation.

        Uses semaphore for rate limiting concurrent API calls.
        """
        async with self.semaphore:
            try:
                # Get model response with structured output
                parsed_response = await self.client.complete_structured(
                    prompt=item.prompt,
                    response_model=benchmark.response_schema()
                )

                item.parsed_response = parsed_response

                # Evaluate (may involve async LLM judge call)
                evaluation = await benchmark.evaluate(parsed_response, item.example)
                item.evaluation = evaluation

            except Exception as e:
                # Handle errors gracefully
                item.metadata['error'] = str(e)
                item.evaluation = None

            return item
