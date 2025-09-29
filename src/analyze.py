import json, os
from typing import List, Dict, Any
from collections import defaultdict

def load_jsonl(path: str) -> List[Dict[str, Any]]:
    arr = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line: continue
            arr.append(json.loads(line))
    return arr

def summarize_mcq(results_path: str) -> Dict[str, Any]:
    data = load_jsonl(results_path)
    n = len(data)
    pos_acc = defaultdict(lambda: [0,0])  # position -> [correct, total]
    for r in data:
        pos = r.get("chosen_position")
        if pos is not None:
            pos_acc[pos][1] += 1
            if r.get("is_correct"):
                pos_acc[pos][0] += 1
    per_pos = {int(k): (v[0]/v[1] if v[1] else 0.0) for k,v in pos_acc.items()}
    return {
        "n": n,
        "overall_acc": sum(int(r.get("is_correct", False)) for r in data)/n if n else 0.0,
        "per_position_acc": per_pos,
    }
