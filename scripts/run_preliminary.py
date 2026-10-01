"""Rodada preliminar: grades de alimentação, água, controle embaralhado,
limpeza das antenas e triagem de gargalos. Gera CSVs em results/.
Uso: PYTHONPATH=. python scripts/run_preliminary.py [--trials 5]
"""
import argparse, time
from pathlib import Path
import numpy as np, pandas as pd
from synapsting.connectome import load_connectome
from synapsting.experiments import run_curve, shuffle_connectome, perturbation
from synapsting.simulator import simulate, LIFParams
from synapsting import neurons as nr

ap = argparse.ArgumentParser(); ap.add_argument("--trials", type=int, default=5)
ap.add_argument("--stages", default="feeding,water,shuffle,grooming,bottleneck")
a = ap.parse_args(); K = a.trials; stages = a.stages.split(",")
R = Path("results"); R.mkdir(exist_ok=True)
con = load_connectome("data", "783")
S = {k: con.idx(v) for k, v in nr.load_sets().items()}
feed_ro = {"MN9": con.idx([nr.MN9]), "MN9pair": con.idx(nr.MN9_PAIR)}
groom_ro = {"aDN1": con.idx([nr.ADN1]), "aBN1": con.idx([nr.ABN1])}
STIM = [0, 25, 50, 75, 100, 150, 200]
t0 = time.time()

if "feeding" in stages:
    print("== Grade de alimentação", flush=True)
    for mode, levels in [("A", [0, .1, .2, .3, .4, .5]), ("B", [.5, 1, 1.5, 2])]:
        for lv in levels:
            run_curve(con, "feeding", S["sugar"], feed_ro, STIM, mode, lv, K,
                      out_csv=R / "feeding_grid.csv")
if "water" in stages:
    print("== Resposta à água (assinatura do mecanismo)", flush=True)
    for mode, lv in [("A", 0), ("A", .3), ("B", 1), ("B", 2)]:
        run_curve(con, "water", S["water"], feed_ro, [0, 100, 200], mode, lv, K,
                  out_csv=R / "water.csv")
if "shuffle" in stages:
    print("== Conectoma embaralhado (graus preservados)", flush=True)
    for rep in range(2):
        sh = shuffle_connectome(con, seed=rep)
        for lv in [0, .3]:
            run_curve(sh, "feeding_shuffled", S["sugar"], feed_ro, [100, 200], "A", lv, K,
                      extra={"rep": rep}, out_csv=R / "shuffle.csv")
        del sh
if "grooming" in stages:
    print("== Grade de limpeza das antenas", flush=True)
    for mode, levels in [("A", [0, .2, .4]), ("B", [1, 2])]:
        for lv in levels:
            run_curve(con, "grooming", S["jon_ce"], groom_ro, [0, 50, 100, 150, 200], mode, lv, K,
                      out_csv=R / "grooming_grid.csv")
if "bottleneck" in stages:
    print("== Triagem de gargalos (bloqueio total de 1 neurônio colinérgico por vez)", flush=True)
    base = simulate(con, S["sugar"], 100, n_trials=8, seed=11)
    rate = base.mean(0)
    mn9 = feed_ro["MN9"][0]
    cand = [i for i in np.argsort(-rate) if con.nt[i] == "acetylcholine"
            and i not in set(S["sugar"].tolist()) and i != mn9 and rate[i] > 5][:40]
    rows = [dict(neuron_id=0, idx=-1, nt="none", base_rate=np.nan,
                 MN9_hz=base[:, mn9].mean(), MN9_sd=base[:, mn9].std())]
    for j, i in enumerate(cand):
        c = simulate(con, S["sugar"], 100, n_trials=4, silence=[i], seed=100 + j)
        rows.append(dict(neuron_id=int(con.ids[i]), idx=int(i), nt=con.nt[i], base_rate=rate[i],
                         MN9_hz=c[:, mn9].mean(), MN9_sd=c[:, mn9].std()))
        print(f"  gargalo {j+1}/{len(cand)} id={con.ids[i]} MN9={c[:, mn9].mean():.1f}", flush=True)
        pd.DataFrame(rows).to_csv(R / "bottleneck.csv", index=False)
print(f"FIM em {time.time()-t0:.0f}s", flush=True)
