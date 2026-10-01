"""Perturbações do "veneno digital" e rodador de curvas estímulo -> resposta.

Modo A (bloqueio / dessensibilização):
    todo peso cujo neurônio PRÉ-sináptico é colinérgico vira peso x (1 - alfa).

Modo B (agonista tônico):
    cada neurônio recebe despolarização constante
        b_i = w_syn x (nº de sinapses colinérgicas que i recebe) x rho x tau
    ou seja: o efeito médio de cada sinapse colinérgica disparando a "rho" Hz
    o tempo todo. rho é a intensidade do agonista, em Hz-equivalentes.
    (Dedução: no modelo, um trem de spikes a taxa r por um peso w gera g médio
    = w x r x tau, e no estado estacionário v - v_rest = g.)

Controles:
    - shuffle_connectome: embaralha os alvos pós-sinápticos de todas as arestas.
      Preserva exatamente o grau de saída e de entrada de cada neurônio e os
      pesos de saída de cada neurônio (troca de extremidades, "configuration
      model"). Pode criar alguns pares duplicados e autoconexões (documentado).
    - shuffle_ach_labels: mantém a fiação, mas sorteia QUAIS neurônios
      excitatórios contam como colinérgicos (mesmo número). Pergunta: o efeito
      depende de onde estão as sinapses colinérgicas ou só de quantas são?
"""
from __future__ import annotations

import hashlib
import time
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd

from .connectome import Connectome
from .simulator import LIFParams, simulate


# ------------------------------------------------------------------ perturbações
def perturbation(con: Connectome, mode: str, level: float, params: LIFParams | None = None,
                 ach_mask: np.ndarray | None = None):
    """Retorna (weight_scale, bias_mv) para o modo e intensidade pedidos."""
    p = params or LIFParams()
    ach = con.is_ach() if ach_mask is None else ach_mask
    if mode == "control" or level == 0:
        return None, None
    if mode == "A":
        pre = con.pre_of_edges()
        scale = np.where(ach[pre], 1.0 - level, 1.0).astype(np.float32)
        return scale, None
    if mode == "B":
        pre = con.pre_of_edges()
        m = ach[pre]
        n_in = np.bincount(con.indices[m], weights=np.abs(con.weights[m]), minlength=con.N)
        bias = p.w_syn * n_in * level * (p.tau / 1000.0)
        return None, bias
    if mode == "AB":  # agonista parcial: bloqueio alfa + tônico rho (level = (alfa, rho))
        a, r = level
        s, _ = perturbation(con, "A", a, p, ach)
        _, b = perturbation(con, "B", r, p, ach)
        return s, b
    raise ValueError(mode)


def shuffle_connectome(con: Connectome, seed: int = 0) -> Connectome:
    rng = np.random.default_rng(seed)
    new_idx = con.indices.copy()
    rng.shuffle(new_idx)
    return replace(con, indices=new_idx)


def shuffle_ach_labels(con: Connectome, seed: int = 0) -> np.ndarray:
    """Máscara de 'colinérgicos' sorteada entre neurônios excitatórios."""
    rng = np.random.default_rng(seed)
    exc_nt = {"acetylcholine", "dopamine", "serotonin", "octopamine", "excitatory_unknown"}
    exc = np.flatnonzero(np.isin(con.nt, list(exc_nt)))
    n_ach = int(con.is_ach().sum())
    pick = rng.choice(exc, size=n_ach, replace=False)
    mask = np.zeros(con.N, dtype=bool)
    mask[pick] = True
    return mask


# ------------------------------------------------------------------ rodador
def _seed(*parts) -> int:
    h = hashlib.sha256("|".join(map(str, parts)).encode()).hexdigest()
    return int(h[:8], 16)


def run_curve(con: Connectome, name: str, stim_idx, readouts: dict, stim_rates,
              mode: str, level, n_trials: int = 8, params: LIFParams | None = None,
              ach_mask=None, extra: dict | None = None, out_csv: str | Path | None = None,
              verbose: bool = True) -> pd.DataFrame:
    """Roda uma curva (vários níveis de estímulo) e devolve uma linha por tentativa.

    readouts: {"MN9": [idx,...], ...} -> taxa média (Hz) de cada grupo por tentativa
    """
    p = params or LIFParams()
    scale, bias = perturbation(con, mode, level, p, ach_mask)
    n_spont = int((bias > (p.v_th - p.v0)).sum()) if bias is not None else 0
    rows = []
    for r in stim_rates:
        t0 = time.time()
        seed = _seed(name, mode, level, r, (extra or {}).get("rep", 0))
        counts = simulate(con, stim_idx, r, n_trials=n_trials, params=p,
                          weight_scale=scale, bias_mv=bias, seed=seed)
        tsec = p.t_run / 1000.0
        stim_set = set(np.atleast_1d(stim_idx).tolist())
        non_stim = np.array([i for i in range(0)])  # placeholder p/ clareza
        for k in range(n_trials):
            row = dict(experiment=name, mode=mode, level=str(level), stim_hz=r, trial=k,
                       n_spontaneous=n_spont, seed=seed)
            for lab, idx in readouts.items():
                row[f"{lab}_hz"] = counts[k, np.atleast_1d(idx)].mean() / tsec
            active = counts[k] / tsec > 5.0
            active[list(stim_set)] = False
            row["n_recruited_5hz"] = int(active.sum())
            row["total_spikes"] = int(counts[k].sum())
            if extra:
                row.update(extra)
            rows.append(row)
        if verbose:
            first = list(readouts)[0]
            m = np.mean([rw[f"{first}_hz"] for rw in rows[-n_trials:]])
            print(f"  {name} modo={mode} nível={level} estímulo={r:>5} Hz -> {first}={m:6.1f} Hz "
                  f"({time.time() - t0:4.1f}s)", flush=True)
    df = pd.DataFrame(rows)
    if out_csv is not None:
        out_csv = Path(out_csv)
        df.to_csv(out_csv, mode="a", header=not out_csv.exists(), index=False)
    return df
