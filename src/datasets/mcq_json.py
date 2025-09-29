from typing import Iterator, Dict, Any, List
import json

# Expected JSONL format (one per line):
# {
#   "id": "sample-001",
#   "question": "....",
#   "options": ["optA", "optB", "optC", "optD"],
#   "answer_idx": 2
# }

def read_mcq_jsonl(path: str) -> Iterator[Dict[str, Any]]:
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line: continue
            ex = json.loads(line)
            # Basic validation
            assert isinstance(ex.get("options"), list) and len(ex["options"]) >= 2
            assert isinstance(ex.get("answer_idx"), int)
            yield ex
