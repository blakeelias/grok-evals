"""
Unified evaluation script using the new Benchmark + Runner architecture.

This replaces the old eval_mcq.py and eval_gsm8k.py scripts with a single
interface that works with any Benchmark implementation.
"""

import argparse
import asyncio
from typing import Any

from .api import AsyncGrokClient
from .runner import EvaluationRunner
from .benchmarks import MCQBenchmark, GSM8KBenchmark
from .metrics import accuracy, wilson_ci


def compute_binary_accuracy(results: Any) -> tuple[float, float, float, int]:
    """
    Compute accuracy for binary evaluation results.

    Args:
        results: EvaluationResults with bool evaluations

    Returns:
        Tuple of (accuracy, ci_low, ci_high, n)
    """
    # Extract evaluation results
    evaluations = [item.evaluation for item in results.items if item.evaluation is not None]

    if not evaluations:
        return 0.0, 0.0, 0.0, 0

    # Compute accuracy
    correct = sum(1 for e in evaluations if e)
    n = len(evaluations)
    acc = correct / n if n > 0 else 0.0

    # Compute confidence interval
    lo, hi = wilson_ci(acc, n)

    return acc, lo, hi, n


async def run_mcq_baseline(input_path: str, output_path: str):
    """Run MCQ baseline evaluation."""
    client = AsyncGrokClient()
    benchmark = MCQBenchmark()
    runner = EvaluationRunner(client, max_parallel=10)

    print(f"Running MCQ baseline evaluation on {input_path}...")
    results = await runner.run_benchmark(benchmark, input_path, output_path)

    # Compute and print accuracy
    acc, lo, hi, n = compute_binary_accuracy(results)
    print(f"MCQ Baseline Accuracy: {acc:.4f} (95% CI {lo:.4f}-{hi:.4f}, n={n})")


async def run_gsm8k_baseline(input_path: str, output_path: str):
    """Run GSM8K baseline evaluation."""
    client = AsyncGrokClient()
    benchmark = GSM8KBenchmark()
    runner = EvaluationRunner(client, max_parallel=10)

    print(f"Running GSM8K baseline evaluation on {input_path}...")
    results = await runner.run_benchmark(benchmark, input_path, output_path)

    # Compute and print accuracy
    acc, lo, hi, n = compute_binary_accuracy(results)
    print(f"GSM8K Baseline Accuracy: {acc:.4f} (95% CI {lo:.4f}-{hi:.4f}, n={n})")


def main():
    parser = argparse.ArgumentParser(description="Run benchmark evaluations")
    parser.add_argument("benchmark", choices=["mcq", "gsm8k"],
                        help="Benchmark to run")
    parser.add_argument("mode", choices=["baseline"],
                        help="Evaluation mode (more modes coming)")
    parser.add_argument("input_path", help="Path to input JSONL dataset")
    parser.add_argument("output_path", help="Path to output JSONL results")
    parser.add_argument("--max-parallel", type=int, default=10,
                        help="Maximum parallel API calls")

    args = parser.parse_args()

    # Route to appropriate evaluation function
    if args.benchmark == "mcq" and args.mode == "baseline":
        asyncio.run(run_mcq_baseline(args.input_path, args.output_path))
    elif args.benchmark == "gsm8k" and args.mode == "baseline":
        asyncio.run(run_gsm8k_baseline(args.input_path, args.output_path))
    else:
        print(f"Unsupported combination: {args.benchmark} + {args.mode}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
