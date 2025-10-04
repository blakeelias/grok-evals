"""
Abstract benchmark interface for evaluation tasks with structured outputs.

This module defines the core Benchmark abstraction that all evaluation tasks
must implement. Benchmarks handle dataset loading, prompt formatting, response
schema definition, and correctness evaluation.
"""

from abc import ABC, abstractmethod
from typing import Iterator, Dict, Any, Type, TypeVar, Generic
from pydantic import BaseModel

# Generic type variable for the response schema
TResponse = TypeVar('TResponse', bound=BaseModel)


class Benchmark(ABC, Generic[TResponse]):
    """
    Abstract interface for an evaluation benchmark with structured outputs.

    A Benchmark encapsulates all dataset-specific logic for a particular evaluation task.
    It knows how to load examples, format prompts, define response schemas, and evaluate
    correctness. Different benchmarks (MCQ, GSM8K, etc.) have different dataset formats,
    but all implement this common interface.

    The generic type parameter TResponse specifies the Pydantic model that defines
    the expected structure of model responses.

    The general evaluation flow is:
    1. load_dataset() yields raw examples in their native format
    2. format_prompt() converts each example into a model prompt
    3. response_schema() provides the Pydantic schema for structured outputs
    4. Model generates a structured response (handled by EvaluationRunner)
    5. evaluate() checks if the structured response matches the gold answer
    """

    @abstractmethod
    def load_dataset(self, path: str) -> Iterator[Dict[str, Any]]:
        """
        Load and yield dataset examples from a file.

        Each yielded dictionary represents one example in the dataset's native format.
        The structure is benchmark-specific, but typically includes:
        - 'id': unique identifier for the example
        - 'question' or 'input': the input text to be evaluated
        - Gold answer field(s): benchmark-specific (e.g., 'answer_idx', 'answer', etc.)
        - Optional metadata: source, difficulty, category, etc.

        Examples:
            MCQ format: {"id": "q1", "question": "...", "options": [...], "answer_idx": 2}
            GSM8K format: {"id": "p1", "question": "...", "answer": "42", "solution": "..."}

        Args:
            path: Path to the dataset file (typically JSONL format)

        Yields:
            Dictionary containing a single dataset example in its native format
        """
        pass

    @abstractmethod
    def format_prompt(self, example: Dict[str, Any]) -> str:
        """
        Convert a dataset example into a prompt string for the model.

        This method transforms the raw example dictionary (from load_dataset) into
        a formatted prompt that will be sent to the language model. It typically
        includes instructions, the question/input, and any formatting requirements.

        The model will respond using the structured output schema defined by
        response_schema(), so the prompt doesn't need to specify output format.

        Args:
            example: A dataset example dictionary (structure defined by this benchmark)

        Returns:
            Formatted prompt string ready to send to the model

        Example:
            For MCQ: "Question: What is 2+2?\nOptions:\nA. 3\nB. 4\n..."
            For GSM8K: "Solve this problem step by step: Janet has 5 apples..."
        """
        pass

    @abstractmethod
    def response_schema(self) -> Type[TResponse]:
        """
        Return the Pydantic model class defining the expected response structure.

        This schema is used for structured outputs from the language model API.
        The model will be constrained to return JSON matching this schema, eliminating
        the need for fragile text parsing.

        Returns:
            A Pydantic BaseModel subclass that defines the response format

        Example:
            For MCQ:
                class MCQResponse(BaseModel):
                    answer: str  # Single letter like "A", "B", "C", "D"

            For GSM8K:
                class GSM8KResponse(BaseModel):
                    reasoning: str
                    final_answer: int
        """
        pass

    @abstractmethod
    def evaluate(self, response: TResponse, example: Dict[str, Any]) -> bool:
        """
        Check if the structured response matches the gold answer.

        Compares the model's structured response against the ground truth from the
        dataset example. The comparison logic is benchmark-specific (e.g., exact
        match for MCQ, numerical equality for math problems).

        Args:
            response: Structured response from the model (instance of response_schema())
            example: The original dataset example containing the gold answer

        Returns:
            True if the response is correct, False otherwise

        Example:
            MCQ: response.answer="B", example["answer_idx"]=1 (B is index 1) -> True
            GSM8K: response.final_answer=42, int(example["answer"])=42 -> True
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Return a unique identifier for this benchmark.

        Used for logging, result organization, and file naming.
        Should be lowercase, no spaces (e.g., 'mcq', 'gsm8k', 'mmlu_chemistry').
        """
        pass
