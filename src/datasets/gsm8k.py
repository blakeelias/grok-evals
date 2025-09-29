from typing import Iterator, Dict, Any
import json, re

# Expected JSONL format per line:
# {"id":"...","question":"...","answer":"<gold number>","solution":"optional text"}

FINAL_RE = re.compile(r"Final Answer:\s*([+-]?[0-9]+)", re.IGNORECASE)

def read_gsm8k_jsonl(path: str) -> Iterator[Dict[str, Any]]:
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line: continue
            ex = json.loads(line)
            yield ex

def parse_final_answer(text: str):
    if text is None: return None
    m = FINAL_RE.search(text)
    if not m: return None
    try:
        return int(m.group(1))
    except Exception:
        return None
