"""GSM8K math reasoning benchmark implementation."""

from typing import Dict, Any, Iterator, Type
from pydantic import BaseModel, Field

from ..benchmark import Benchmark
from ..datasets.gsm8k import read_gsm8k_jsonl


class GSM8KResponse(BaseModel):
    """Structured response for GSM8K math problems."""
    reasoning: str = Field(description="Step-by-step solution process")
    final_answer: int = Field(description="The numeric answer to the problem")


class GSM8KBenchmark(Benchmark[GSM8KResponse, bool]):
    """
    GSM8K math reasoning benchmark with structured outputs.

    Evaluation is binary: correct (True) if the final_answer matches
    the gold answer, incorrect (False) otherwise.
    """

    def __init__(self, prompt_template: str | None = None):
        """
        Initialize GSM8K benchmark.

        Args:
            prompt_template: Optional custom prompt template with {question} placeholder
        """
        self.prompt_template = prompt_template or self._default_prompt()

    def _default_prompt(self) -> str:
        return """Solve the following math word problem. Think step by step, then provide the final numeric answer.

{question}

Provide your reasoning and the final answer."""

    def load_dataset(self, path: str) -> Iterator[Dict[str, Any]]:
        """Load GSM8K dataset from JSONL file."""
        return read_gsm8k_jsonl(path)

    def format_prompt(self, example: Dict[str, Any]) -> str:
        """Format GSM8K prompt with question."""
        return self.prompt_template.format(question=example["question"])

    def response_schema(self) -> Type[GSM8KResponse]:
        """Return GSM8K response schema."""
        return GSM8KResponse

    async def evaluate(self, response: GSM8KResponse, example: Dict[str, Any]) -> bool:
        """
        Evaluate GSM8K response.

        Returns:
            True if final_answer matches gold answer, False otherwise
        """
        gold = int(example["answer"])
        return response.final_answer == gold

    @property
    def name(self) -> str:
        return "gsm8k"
