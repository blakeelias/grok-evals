# grok-bench — Reproducible Grok Benchmark Harness

Reusable evaluation harness for **xAI Grok** models across two common task families:
- **MCQ-style** benchmarks (e.g., MMLU/GPQA/Winogrande-like; requires a JSONL adapter)
- **GSM8K**-style math reasoning

Includes:
- **Baseline** evaluation
- **Robustness** checks for MCQ: **option shuffling** and **answer-letter remapping**
- **Answer-format enforcement** for GSM8K (e.g., `Final Answer: <number>`)
- **Self-consistency** for GSM8K (n-sample majority vote)
- **One-command reproducibility** via `run.sh`

> ⚠️ Datasets are **not** included. Provide your own files under `data/` (see adapters) or wire in download scripts where licensing permits.

## Quickstart

```bash
git clone git@github.com:blakeelias/grok-evals.git
cd grok-evals
cp env.example .env                   # Add your XAI_API_KEY
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Example: MCQ baseline on a JSONL file
# Each line: {"id": "...", "question": "...", "options": ["...","...","...","..."], "answer_idx": 2}
./run.sh mcq-baseline data/mmlu_sample.jsonl results/mcq_baseline.jsonl

# MCQ robust (K=5 shuffles + letter remap)
./run.sh mcq-robust data/mmlu_sample.jsonl results/mcq_robust.jsonl --num-shuffles 5

# GSM8K baseline on a JSONL file
# Each line: {"id":"...", "question":"...", "answer":"<gold number>", "solution":"optional text"}
./run.sh gsm8k-baseline data/gsm8k_sample.jsonl results/gsm8k_baseline.jsonl

# GSM8K with strict answer format (require "Final Answer: <int>")
./run.sh gsm8k-format data/gsm8k_sample.jsonl results/gsm8k_format.jsonl

# GSM8K with self-consistency (n samples)
./run.sh gsm8k-selfconsistency data/gsm8k_sample.jsonl results/gsm8k_selfcon.jsonl --samples 5
```

Configure the client via environment variables (or `.env`):
- `XAI_API_KEY` (required)
- `XAI_BASE_URL` (default `https://api.x.ai`)
- `XAI_MODEL` (default `grok-4`)
- `XAI_TEMPERATURE` (default `0.2`)
- `XAI_TOP_P` (default `1.0`)
- `XAI_SEED` (default `7`)

## Repo Layout

```
grok-bench/
  README.md
  env.example
  requirements.txt
  run.sh
  LICENSE
  configs/
    config.example.json
  prompts/
    system.txt
    cot_template.txt
  data/
    .gitkeep
  results/
    .gitkeep
  src/
    api.py
    augment.py
    metrics.py
    analyze.py
    improved_benchmark.py
    datasets/
      __init__.py
      mcq_json.py
      gsm8k.py
    eval_mcq.py
    eval_gsm8k.py
```

## Philosophy

This harness emphasizes:
- **Clarity & Reproducibility:** fixed seeds, explicit configs, single-command runs.
- **Robustness over single-shot accuracy:** report mean/variance under simple perturbations.
- **Actionable failure analyses:** small clusters & crisp exemplars that teach.

## Notes

- The client is **OpenAI-compatible** and points at `https://api.x.ai` by default.
- Paraphrase augmentation is left as a stub (opt-in): you can generate paraphrases with Grok if desired, but be transparent if the evaluation prompt also uses the model under test.
- Use at **temperature ~0.2** (or 0.0) and **fixed seed** for evaluability; vary deliberately if studying sampling effects.
