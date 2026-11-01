"""Sends test-set applicants to the running API like a loan app would.  --downturn simulates a recession."""
import argparse
import time
import httpx
import numpy as np
import pandas as pd
from src.config import PROCESSED, FEATURES
from src.drift import stress

parser = argparse.ArgumentParser()
parser.add_argument("--n", type=int, default=500)
parser.add_argument("--downturn", action="store_true")
parser.add_argument("--url", default="http://127.0.0.1:8000")
args = parser.parse_args()

df = pd.read_csv(PROCESSED / "test.csv").sample(args.n, random_state=1)
if args.downturn:
    df = stress(df)
fields = [c for c in FEATURES if c != "loan_percent_income"]            # the API computes this itself
payloads = df[fields].astype(object).where(df[fields].notna(), None).to_dict("records")   # NaN -> null

times, decisions = [], []
with httpx.Client(base_url=args.url, timeout=10) as client:
    for p in payloads:
        t = time.perf_counter()
        r = client.post("/predict", json=p)
        times.append((time.perf_counter() - t) * 1000)
        r.raise_for_status()
        decisions.append(r.json()["decision"])
print(f"sent {len(times)} requests | round-trip ms p50 {np.percentile(times, 50):.1f}  p95 {np.percentile(times, 95):.1f}")
print(pd.Series(decisions).value_counts(normalize=True).round(3).to_dict())
