"""Synthetic smoke fixture, NOT evidence about a real research problem."""
import argparse
import json
import os
from pathlib import Path
import random

p = argparse.ArgumentParser()
p.add_argument("--method", choices=["mean", "linear"], default="linear")
p.add_argument("--seed", type=int, default=int(os.environ.get("RW_SEED", "0")))
a = p.parse_args()
rng = random.Random(a.seed)
points = [(x, 2*x+1+rng.gauss(0, 0.1)) for x in [rng.uniform(-1, 1) for _ in range(100)]]
train, test = points[:60], points[60:]
xm = sum(x for x, _ in train)/len(train)
ym = sum(y for _, y in train)/len(train)
slope = sum((x-xm)*(y-ym) for x, y in train)/sum((x-xm)**2 for x, _ in train) if a.method == "linear" else 0.0
intercept = ym-slope*xm
mse = sum((y-(slope*x+intercept))**2 for x, y in test)/len(test)
out = Path(os.environ["RW_RUN_DIR"])
out.mkdir(parents=True, exist_ok=True)
(out / "metrics.json").write_text(json.dumps({"mse": mse, "test_samples": len(test)}, allow_nan=False)+"\n", encoding="utf-8")
print("Synthetic smoke fixture complete; no real-project conclusion is implied.")
