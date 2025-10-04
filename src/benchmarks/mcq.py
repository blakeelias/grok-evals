"""Multiple Choice Question benchmark implementation."""

from typing import Dict, Any, Iterator, Type
from pydantic import BaseModel, Field

from ..benchmark import Benchmark
from ..datasets.mcq_json import read_mcq_jsonl


class MCQResponse(BaseModel):
    """Structured response for multiple choice questions."""
    answer: str = Field(description="Single letter answer choice (A, B, C, D, etc.)")


class MCQBenchmark(Benchmark[MCQResponse, bool]):
    """
    Multiple choice question benchmark with structured outputs.

    Evaluation is binary: correct (True) if the chosen letter matches
    the gold answer index, incorrect (False) otherwise.
    """

    def __init__(self, prompt_template: str | None = None):
        """
        Initialize MCQ benchmark.

        Args:
            prompt_template: Optional custom prompt template with {question} and {options_block} placeholders
        """
        self.prompt_template = prompt_template or self._default_prompt()

    def _default_prompt(self) -> str:
        return """You will be given a question and multiple answer options.
Choose the single best option and reply with the letter.

Question:
{question}

Options:
{options_block}

Reply with just the letter (A, B, C, ...)."""

    def load_dataset(self, path: str) -> Iterator[Dict[str, Any]]:
        """Load MCQ dataset from JSONL file."""
        return read_mcq_jsonl(path)

    def format_prompt(self, example: Dict[str, Any]) -> str:
        """Format MCQ prompt with question and options."""
        options_block = self._make_options_block(example["options"])
        return self.prompt_template.format(
            question=example["question"],
            options_block=options_block
        )

    def _make_options_block(self, options: list[str]) -> str:
        """Convert option list to lettered format."""
        letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        return "\n".join([f"{letters[i]}. {opt}" for i, opt in enumerate(options)])

    def response_schema(self) -> Type[MCQResponse]:
        """Return MCQ response schema."""
        return MCQResponse

    async def evaluate(self, response: MCQResponse, example: Dict[str, Any]) -> bool:
        """
        Evaluate MCQ response.

        Returns:
            True if chosen letter matches gold answer index, False otherwise
        """
        # Convert letter to index
        letter_to_idx = {c: i for i, c in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ")}
        pred_idx = letter_to_idx.get(response.answer.upper(), -1)

        # Compare to gold answer
        return pred_idx == example["answer_idx"]

    @property
    def name(self) -> str:
        return "mcq"
