import argparse, json
from typing import List, Dict, Any
from tqdm import tqdm

from .api import GrokClient
from .datasets.gsm8k import read_gsm8k_jsonl, parse_final_answer
from .metrics import accuracy, wilson_ci, majority_vote

BASE_PROMPT = """
Solve the following math word problem. Think step by step, then provide the final numeric answer.

{question}

Respond in this exact format:
<your reasoning>
Final Answer: <integer>
"""

def infer_once(client: GrokClient, q: str) -> str:
    return client.complete(BASE_PROMPT.format(question=q))

def baseline(input_path: str, output_path: str):
    client = GrokClient()
    preds: List[int] = []
    golds: List[int] = []
    n_reject = 0
    with open(output_path, "w", encoding="utf-8") as w:
        for ex in tqdm(read_gsm8k_jsonl(input_path)):
            out = infer_once(client, ex["question"])
            y = parse_final_answer(out)
            if y is None:
                n_reject += 1
            gold = int(ex["answer"])
            res = {
                "id": ex.get("id"),
                "gold": gold,
                "pred": y,
                "is_correct": (y == gold),
                "raw_completion": out
            }
            preds.append(y if y is not None else 10**18)  # placeholder to preserve length
            golds.append(gold)
            w.write(json.dumps(res) + "\n")
    # compute accuracy ignoring rejects by treating them as wrong
    correct = sum(1 for p,g in zip(preds,golds) if p == g)
    n = len(golds)
    acc = correct/n if n else 0.0
    lo,hi = wilson_ci(acc, n)
    print(f"GSM8K baseline accuracy: {acc:.4f} (95% CI {lo:.4f}-{hi:.4f}, n={n}, rejects={n_reject})")

def format_strict(input_path: str, output_path: str):
    # Same as baseline but *rejects* any answer lacking strict schema (already enforced).
    baseline(input_path, output_path)

def self_consistency(input_path: str, output_path: str, samples: int = 5):
    client = GrokClient()
    correct = 0
    n = 0
    with open(output_path, "w", encoding="utf-8") as w:
        for ex in tqdm(read_gsm8k_jsonl(input_path)):
            answers = []
            for _ in range(samples):
                out = infer_once(client, ex["question"])
                y = parse_final_answer(out)
                if y is not None:
                    answers.append(str(y))
            voted = majority_vote(answers) if answers else None
            gold = str(int(ex["answer"]))
            is_ok = (voted == gold)
            n += 1
            if is_ok:
                correct += 1
            w.write(json.dumps({
                "id": ex.get("id"),
                "gold": gold,
                "votes": answers,
                "voted": voted,
                "is_correct": is_ok
            }) + "\n")
    acc = correct/n if n else 0.0
    lo, hi = wilson_ci(acc, n)
    print(f"GSM8K self-consistency (n={samples}) accuracy: {acc:.4f} (95% CI {lo:.4f}-{hi:.4f}, n={n})")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["baseline","format_strict","self_consistency"])
    ap.add_argument("input_path")
    ap.add_argument("output_path")
    ap.add_argument("--samples", type=int, default=5)
    args = ap.parse_args()
    if args.mode == "baseline":
        baseline(args.input_path, args.output_path)
    elif args.mode == "format_strict":
        format_strict(args.input_path, args.output_path)
    else:
        self_consistency(args.input_path, args.output_path, samples=args.samples)
