"""Roda uma etapa da rodada preliminar (útil para retomar em partes).
Ex.: PYTHONPATH=. python scripts/run_stage.py feeding A 0,0.1,0.2 --trials 4
"""
import argparse
from pathlib import Path
from synapsting.connectome import load_connectome
from synapsting.experiments import run_curve, shuffle_connectome
from synapsting import neurons as nr
from synapsting.simulator import LIFParams
ap = argparse.ArgumentParser()
ap.add_argument("stage"); ap.add_argument("mode"); ap.add_argument("levels")
ap.add_argument("--trials", type=int, default=4); ap.add_argument("--rep", type=int, default=0)
ap.add_argument("--trun", type=float, default=1000.0); ap.add_argument("--stims", default="")
a = ap.parse_args()
con = load_connectome("data", "783")
S = {k: con.idx(v) for k, v in nr.load_sets().items()}
feed = {"MN9": con.idx([nr.MN9]), "MN9pair": con.idx(nr.MN9_PAIR)}
groom = {"aDN1": con.idx([nr.ADN1]), "aBN1": con.idx([nr.ABN1])}
cfg = {"feeding": (S["sugar"], feed, [0, 25, 50, 75, 100, 150, 200]),
       "water": (S["water"], feed, [0, 100, 200]),
       "grooming": (S["jon_ce"], groom, [0, 50, 100, 150, 200]),
       "shuffle": (S["sugar"], feed, [100, 200])}
stim, ro, rates = cfg[a.stage]
if a.stims: rates = [float(x) for x in a.stims.split(",")]
P = LIFParams(t_run=a.trun)
if a.stage == "shuffle":
    con = shuffle_connectome(con, seed=a.rep)
for lv in [float(x) for x in a.levels.split(",")]:
    run_curve(con, a.stage, stim, ro, rates, a.mode, lv, a.trials, params=P, extra={"rep": a.rep, "t_run_ms": a.trun},
              out_csv=Path("results") / f"{a.stage}.csv")
