---
name: research-experiment
description: "在独立本地代码仓库执行有预算的实验，保留真实指标、失败、代码版本和配对分析，不远程调度。"
---

# Local experiments and analysis

All executable helpers and sample assets are inside this skill. Use Python 3.11+, Git, Linux/macOS/WSL, and the experiment's existing local environment. No cloud scheduler, dependency installation, or external hook is implied.

Copy `assets/plan.example.json` to a real plan under `research/experiments/`. Fill the question, falsifiable hypothesis, full code HEAD, dataset/version/split, baseline, metric direction/unit, seeds, comparison group, argv, and budget. The implementation lives in the independently registered code repository; plans/receipts live in the workspace.

```bash
python3 .agents/skills/research-experiment/scripts/run.py --plan research/experiments/my-plan.plan.json
python3 .agents/skills/research-experiment/scripts/analyze.py --baseline research/experiments/E-baseline.json --candidate research/experiments/E-candidate.json --output research/findings/comparison.json
```

The runner uses an argv array, not shell concatenation. `{seed}` and `{run_dir}` are substituted; `RW_SEED` and `RW_RUN_DIR` are available. Write fresh finite numeric metrics to `$RW_RUN_DIR/metrics.json`; never reuse a stale code-directory output. Booleans/NaN are not valid measurements. One workspace runs one plan at a time.

Success requires all planned seeds and no source change during execution. Preserve failures, timeouts, and tainted code states. Each run records code HEAD/diff fingerprint, seeds, termination, environment summary, and metric hashes. Raw outputs stay in `.runtime/`; receipts remain in `research/experiments/`. A receipt does not replace the code dependency lock, data version, and raw artifacts required for reproduction.

Dirty code is rejected by default; smoke/pilot may explicitly use `--allow-dirty` with recorded limitations, but confirmatory runs require a clean commit. Never reset/clean user changes to satisfy a gate. Pass only declared `plan.env_keys`, resolved as process > skill `.env` > project `.env`. Secrets never belong in argv. The runner is not an OS sandbox for untrusted code.

Native `experiment_implementer` workers edit only assigned files; `verifier` runs scoped approved checks without changing code/assertions to force success. Parent owns the experiment question and integration. Workers do not start Codex or additional workers.

Compare only successful non-smoke runs with matching protocol/data/metrics/comparison group/seeds. Interpret candidate-minus-baseline using the metric direction. The helper's paired bootstrap interval describes seed variation; fewer than three seeds yield no interval. It is not automatic significance or population uncertainty. `assets/toy_experiment.py` is only a synthetic smoke fixture, never a source of manuscript results.

## Communication

User-facing output: concise, natural Chinese; give the result, decisive evidence, and material limitation. On first use, append a Chinese gloss to a specialized English term, e.g. `ablation（消融实验）`. Keep complete sentences, negation, units, exact identifiers, and uncertainty. Do not abbreviate words artificially, narrate every tool call, or repeat a long report in chat. Give brief updates for long tasks. Code, literal API fields, quotations, and English manuscripts keep their required language; do not inject Chinese glosses into them. Shorter output must not mean shallower research.
