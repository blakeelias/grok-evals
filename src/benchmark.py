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

# Generic type variable for the evaluation result
# Can be bool for binary, Enum for categorical, or any custom type
TEvaluation = TypeVar('TEvaluation')


class Benchmark(ABC, Generic[TResponse, TEvaluation]):
    """
    Abstract interface for an evaluation benchmark with structured outputs.

    A Benchmark encapsulates all dataset-specific logic for a particular evaluation task.
    It knows how to load examples, format prompts, define response schemas, and evaluate
    correctness. Different benchmarks (MCQ, GSM8K, etc.) have different dataset formats,
    but all implement this common interface.

    The generic type parameters are:
    - TResponse: Pydantic model defining the structure of model responses
    - TEvaluation: Type of evaluation result (bool, Enum, custom dataclass, etc.)

    The general evaluation flow is:
    1. load_dataset() yields raw examples in their native format
    2. format_prompt() converts each example into a model prompt
    3. response_schema() provides the Pydantic schema for structured outputs
    4. Model generates a structured response (handled by EvaluationRunner)
    5. evaluate() checks response quality (may involve async LLM judge calls)
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
    async def evaluate(self, response: TResponse, example: Dict[str, Any]) -> TEvaluation:
        """
        Evaluate the quality of the structured response against the gold answer.

        This is an async method to support evaluation strategies that require LLM judge
        calls (e.g., rubric-based grading, semantic equivalence checking). Simple
        benchmarks can use synchronous logic and just wrap the return value in an
        async function.

        The return type TEvaluation is benchmark-specific and can be:
        - bool: Simple binary correct/incorrect (MCQ, exact match)
        - Enum: Categorical scores (e.g., CorrectnessLevel.FULL, PARTIAL, NONE)
        - Dataclass: Structured evaluation with multiple dimensions
        - Custom type: Any type that captures the evaluation semantics

        Args:
            response: Structured response from the model (instance of response_schema())
            example: The original dataset example containing the gold answer

        Returns:
            Evaluation result of type TEvaluation

        Examples:
            Binary evaluation (MCQ):
                return response.answer == correct_letter  # Returns bool

            Categorical evaluation (Math reasoning):
                class MathScore(Enum):
                    CORRECT_ANSWER_AND_REASONING = 3
                    CORRECT_ANSWER_WRONG_REASONING = 2
                    WRONG_ANSWER_VALID_APPROACH = 1
                    COMPLETELY_WRONG = 0
                return MathScore.CORRECT_ANSWER_AND_REASONING

            Structured evaluation (Code generation):
                @dataclass
                class CodeEvaluation:
                    passes_tests: bool
                    follows_style: bool
                    has_comments: bool
                    reasoning_steps_correct: List[bool]
                return CodeEvaluation(True, True, False, [True, True, False])

            LLM-based judge (Essay grading):
                # Make async LLM call to judge model
                judge_response = await self.judge_client.complete(
                    prompt=f"Grade this essay: {response.text}",
                    schema=EssayGrade
                )
                return judge_response.grade  # Returns Enum from judge
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
