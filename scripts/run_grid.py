"""Roda a grade de simulações definida num arquivo de configuração, em paralelo e
com retomada automática.

Uso:
  python scripts/run_grid.py configs/grid_teste.json              # teste rápido (~2 min)
  python scripts/run_grid.py configs/grid_final.json --jobs 4     # grade do pré-registro

Cada "tarefa" é uma combinação (experimento, modo, nível, estímulo, repetição) com N
tentativas. Os resultados vão para results/<saida>/<experimento>.csv. Se o programa for
interrompido, rode de novo: as tarefas já salvas são puladas.

Memória: cada processo carrega o conectoma (~1,5 GB). Use --jobs <= RAM(GB) / 2.
"""
import argparse, json, os, sys, time
from multiprocessing import get_context
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from synapsting.connectome import load_connectome          # noqa: E402
from synapsting.experiments import perturbation, shuffle_connectome, _seed  # noqa: E402
from synapsting.simulator import simulate, LIFParams        # noqa: E402
from synapsting import neurons as nr                        # noqa: E402

READOUTS = {"MN9": [nr.MN9], "MN9pair": nr.MN9_PAIR, "aDN1": [nr.ADN1], "aBN1": [nr.ABN1]}
_G = {}


def _init(version):
    _G["con"] = load_connectome("data", version)
    _G["sets"] = {k: _G["con"].idx(v) for k, v in nr.load_sets().items()}
    _G["cache"] = {}


def _get(shuffle_seed, mode, level, p):
    key = (shuffle_seed, mode, level)
    if key not in _G["cache"]:
        con = _G["con"] if shuffle_seed is None else shuffle_connectome(_G["con"], seed=shuffle_seed)
        _G["cache"] = {k: v for k, v in _G["cache"].items() if k[0] == shuffle_seed}  # limita memória
        _G["cache"][key] = (con, *perturbation(con, mode, level, p))
    return _G["cache"][key]


def _run(task):
    t0 = time.time()
    p = LIFParams(t_run=task["t_run_ms"])
    con, scale, bias = _get(task["shuffle_seed"], task["mode"], task["level"], p)
    stim = _G["sets"][task["stim"]]
    seed = _seed(task["experiment"], task["mode"], task["level"], task["stim_hz"], task["rep"])
    counts = simulate(con, stim, task["stim_hz"], n_trials=task["trials"], params=p,
                      weight_scale=scale, bias_mv=bias, seed=seed)
    tsec = p.t_run / 1000.0
    ro = {k: con.idx(READOUTS[k]) for k in task["readouts"]}
    rows = []
    stim_mask = np.zeros(con.N, bool); stim_mask[stim] = True
    for k in range(task["trials"]):
        r = {kk: task[kk] for kk in ("experiment", "mode", "level", "stim_hz", "rep", "shuffle_seed", "t_run_ms")}
        r.update(trial=k, seed=seed, n_spontaneous=int((bias > (p.v_th - p.v0)).sum()) if bias is not None else 0)
        for lab, idx in ro.items():
            r[f"{lab}_hz"] = counts[k, idx].mean() / tsec
        rate = counts[k] / tsec
        r["n_recruited_5hz"] = int(((rate > 5) & ~stim_mask).sum())
        r["total_spikes"] = int(counts[k].sum())
        rows.append(r)
    return task, rows, time.time() - t0


def build_tasks(cfg):
    tasks = []
    for ex in cfg["experiments"]:
        seeds = ex.get("shuffle_seeds", [None])
        for rep, sseed in enumerate(seeds):
            for mode, level in ex["conditions"]:
                for s in ex["rates"]:
                    t_run = ex.get("t_run_ms_B", cfg["t_run_ms"]) if mode == "B" else cfg["t_run_ms"]
                    tasks.append(dict(experiment=ex["name"], stim=ex["stim"], readouts=ex["readouts"],
                                      mode=mode, level=float(level), stim_hz=float(s), rep=rep,
                                      shuffle_seed=sseed, trials=(ex.get("trials_B", cfg.get("trials_B", cfg["trials"])) if mode == "B"
                                              else ex.get("trials", cfg["trials"])), t_run_ms=float(t_run)))
    return tasks


def done_keys(out):
    keys = set()
    for f in out.glob("*.csv"):
        d = pd.read_csv(f)
        for r in d[["experiment", "mode", "level", "stim_hz", "rep"]].drop_duplicates().itertuples(index=False):
            keys.add((r.experiment, r.mode, float(r.level), float(r.stim_hz), int(r.rep)))
    return keys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("config"); ap.add_argument("--jobs", type=int, default=1)
    a = ap.parse_args()
    cfg = json.loads(Path(a.config).read_text())
    out = Path("results") / cfg["output"]; out.mkdir(parents=True, exist_ok=True)
    (out / "config_usada.json").write_text(json.dumps(cfg, indent=1, ensure_ascii=False))
    tasks = build_tasks(cfg); done = done_keys(out)
    todo = [t for t in tasks if (t["experiment"], t["mode"], t["level"], t["stim_hz"], t["rep"]) not in done]
    # tarefas lentas (Modo B, estímulo alto) primeiro: melhora o balanceamento entre processos
    todo.sort(key=lambda t: (t["mode"] != "B", -t["stim_hz"]))
    print(f"{len(tasks)} tarefas no total, {len(tasks) - len(todo)} já feitas, {len(todo)} a fazer, "
          f"{a.jobs} processo(s). Saída: {out}", flush=True)
    if not todo:
        return
    t0 = time.time()
    ctx = get_context("spawn")
    with ctx.Pool(a.jobs, initializer=_init, initargs=(cfg["version"],)) as pool:
        for i, (task, rows, dt) in enumerate(pool.imap_unordered(_run, todo), 1):
            f = out / f"{task['experiment']}.csv"
            pd.DataFrame(rows).to_csv(f, mode="a", header=not f.exists(), index=False)
            el = time.time() - t0; eta = el / i * (len(todo) - i)
            first = f"{task['readouts'][0]}_hz"
            m = np.mean([r[first] for r in rows])
            print(f"[{i}/{len(todo)}] {task['experiment']} {task['mode']}={task['level']:g} "
                  f"estímulo={task['stim_hz']:g}Hz rep={task['rep']} -> {task['readouts'][0]}={m:.1f}Hz "
                  f"({dt:.0f}s) | faltam ~{eta / 60:.0f} min", flush=True)
    print(f"Concluído em {(time.time() - t0) / 60:.1f} min.")


if __name__ == "__main__":
    main()
