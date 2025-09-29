import argparse, os, json, random
from typing import List, Dict, Any
from tqdm import tqdm

from .api import GrokClient
from .datasets.mcq_json import read_mcq_jsonl
from .augment import shuffle_options
from .metrics import accuracy, wilson_ci

MCQ_PROMPT_TEMPLATE = """
You will be given a question and multiple answer options.
Choose the single best option and reply ONLY with the option letter.

Question:
{question}

Options:
{options_block}

Reply with just the letter (A, B, C, ...).
"""

def make_options_block(options: List[str]) -> str:
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    return "\n".join([f"{letters[i]}. {opt}" for i, opt in enumerate(options)])

def extract_letter(text: str) -> str:
    text = (text or "").strip().upper()
    for ch in ["A","B","C","D","E","F","G","H"]:
        if ch in text:
            return ch
    return ""

def letter_to_index(letter: str) -> int:
    mapping = {c:i for i,c in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ")}
    return mapping.get(letter, -1)

def eval_mcq_once(client: GrokClient, ex: Dict[str, Any]) -> Dict[str, Any]:
    prompt = MCQ_PROMPT_TEMPLATE.format(
        question=ex["question"],
        options_block=make_options_block(ex["options"])
    )
    out = client.complete(prompt)
    letter = extract_letter(out)
    pred_idx = letter_to_index(letter)
    is_correct = (pred_idx == ex["answer_idx"])
    return {
        "id": ex.get("id"),
        "chosen_letter": letter,
        "chosen_position": pred_idx,
        "gold_idx": ex["answer_idx"],
        "is_correct": bool(is_correct),
        "raw_completion": out,
    }

def baseline(input_path: str, output_path: str, seed: int = 7):
    client = GrokClient()
    golds: List[int] = []
    preds: List[int] = []
    with open(output_path, "w", encoding="utf-8") as w:
        for ex in tqdm(read_mcq_jsonl(input_path)):
            r = eval_mcq_once(client, ex)
            golds.append(ex["answer_idx"])
            preds.append(r["chosen_position"])
            w.write(json.dumps(r) + "\n")
    acc = accuracy(preds, golds)
    lo, hi = wilson_ci(acc, len(golds))
    print(f"Baseline accuracy: {acc:.4f} (95% CI {lo:.4f}-{hi:.4f}, n={len(golds)})")

def robust(input_path: str, output_path: str, num_shuffles: int = 5, seed: int = 7):
    client = GrokClient()
    rng = random.Random(seed)
    rows: List[Dict[str, Any]] = []
    golds_all: List[int] = []
    preds_all: List[int] = []
    with open(output_path, "w", encoding="utf-8") as w:
        for ex in tqdm(read_mcq_jsonl(input_path)):
            ex_results = []
            for k in range(num_shuffles):
                ex_shuf = shuffle_options(ex, seed=rng.randint(0, 10**9))
                r = eval_mcq_once(client, ex_shuf)
                r["shuffle_id"] = k
                ex_results.append(r)
                rows.append(r)
                golds_all.append(ex_shuf["answer_idx"])
                preds_all.append(r["chosen_position"])
            # write per-shuffle rows
        for r in rows:
            w.write(json.dumps(r) + "\n")
    acc = accuracy(preds_all, golds_all)
    lo, hi = wilson_ci(acc, len(golds_all))
    print(f"RobustMC mean accuracy over {num_shuffles} shuffles: {acc:.4f} (95% CI {lo:.4f}-{hi:.4f}, n={len(golds_all)})")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["baseline","robust"])
    ap.add_argument("input_path")
    ap.add_argument("output_path")
    ap.add_argument("--num-shuffles", type=int, default=5)
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()
    if args.mode == "baseline":
        baseline(args.input_path, args.output_path, seed=args.seed)
    else:
        robust(args.input_path, args.output_path, num_shuffles=args.num_shuffles, seed=args.seed)
