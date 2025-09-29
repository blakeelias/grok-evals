import random
import copy
from typing import List, Dict, Any

LETTER_MAP = ['A','B','C','D','E','F','G','H']

def shuffle_options(example: Dict[str, Any], seed: int) -> Dict[str, Any]:
    rng = random.Random(seed)
    options = example['options']
    idx = example['answer_idx']
    pairs = list(enumerate(options))
    rng.shuffle(pairs)
    new_options = [opt for _, opt in pairs]
    # find where the correct one moved
    new_idx = [i for i,(old_i,_) in enumerate(pairs) if old_i == idx][0]
    out = copy.deepcopy(example)
    out['options'] = new_options
    out['answer_idx'] = new_idx
    return out

def remap_answer_letters(example: Dict[str, Any], offset: int = 1) -> Dict[str, Any]:
    """Shifts A/B/C/D label mapping by an offset, preserving correctness when
    evaluated by *content*, not label identity. This is mainly for analysis/visualization
    if your prompting uses letter reference only; recommended is to prompt by content."""
    out = copy.deepcopy(example)
    n = len(out['options'])
    out['letter_labels'] = [LETTER_MAP[(i+offset) % len(LETTER_MAP)] for i in range(n)]
    return out
