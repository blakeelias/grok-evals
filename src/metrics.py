from typing import List, Tuple
import math
from collections import Counter

def accuracy(preds: List[int], golds: List[int]) -> float:
    assert len(preds) == len(golds)
    if not preds: return 0.0
    correct = sum(int(p==g) for p,g in zip(preds, golds))
    return correct / len(preds)

def wilson_ci(p_hat: float, n: int, z: float = 1.96) -> Tuple[float,float]:
    if n == 0: return (0.0, 0.0)
    denom = 1 + z**2/n
    center = (p_hat + z**2/(2*n)) / denom
    margin = z*math.sqrt((p_hat*(1-p_hat) + z**2/(4*n))/n) / denom
    return (max(0.0, center - margin), min(1.0, center + margin))

def majority_vote(vals: List[str]) -> str:
    c = Counter(vals)
    top = c.most_common(1)
    return top[0][0] if top else ""
