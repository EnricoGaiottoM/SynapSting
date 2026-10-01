"""Triagem de gargalos: bloqueia a saída de UM neurônio colinérgico por vez
(os mais ativos durante o estímulo de açúcar) e mede a queda do MN9.
Uso: PYTHONPATH=. python scripts/screen_bottlenecks.py --top 15 --trials 3
"""
import argparse, numpy as np, pandas as pd
from synapsting.connectome import load_connectome
from synapsting.simulator import simulate
from synapsting import neurons as nr
ap = argparse.ArgumentParser(); ap.add_argument("--top", type=int, default=40)
ap.add_argument("--trials", type=int, default=4); ap.add_argument("--rate", type=float, default=100)
a = ap.parse_args()
con = load_connectome("data", "783")
ann = pd.read_csv("data/flywire_annotations_783.tsv", sep="\t", usecols=["root_id", "cell_type", "super_class"], low_memory=False).set_index("root_id")
sugar = con.idx(nr.load_sets()["sugar"]); mn9 = con.idx([nr.MN9])[0]
base = simulate(con, sugar, a.rate, n_trials=6, seed=11)
rate = base.mean(0); sset = set(sugar.tolist())
cand = [i for i in np.argsort(-rate) if con.nt[i] == "acetylcholine" and i not in sset and i != mn9][:a.top]
rows = [dict(flywire_id="baseline", cell_type="", base_rate_hz=np.nan, MN9_hz=base[:, mn9].mean(), drop_pct=0.0)]
for j, i in enumerate(cand):
    c = simulate(con, sugar, a.rate, n_trials=a.trials, silence=[i], seed=100 + j)
    m = c[:, mn9].mean()
    fid = int(con.ids[i]); ct = ann.cell_type.get(fid, "")
    rows.append(dict(flywire_id=fid, cell_type=ct if isinstance(ct, str) else "", base_rate_hz=round(rate[i], 1),
                     MN9_hz=m, drop_pct=round(100 * (1 - m / base[:, mn9].mean()), 1)))
    pd.DataFrame(rows).to_csv("results/bottleneck.csv", index=False)
print(pd.DataFrame(rows).sort_values("drop_pct", ascending=False).to_string(index=False))
