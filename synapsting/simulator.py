"""Simulador LIF do cérebro inteiro, orientado a eventos, em NumPy puro.

Reproduz as equações do modelo de Shiu et al. (2024) (arquivo model.py do
repositório original, que usa Brian2):

    dv/dt = (v_rest - v + g) / t_mbr     (congelado durante o período refratário)
    dg/dt = -g / tau
    spike quando v > v_th  ->  v = v_rst, g = 0
    cada spike pré-sináptico soma w = (nº de sinapses) x w_syn ao g do pós, com atraso de 1,8 ms
    neurônios estimulados recebem entrada de Poisson (cada evento soma w_syn x f_poi ao v)

Por que não usar o Brian2 direto? Porque, em cada passo, só uns poucos
milhares dos ~139 mil neurônios estão fora do repouso. Este código só
atualiza esse "conjunto ativo", e roda várias tentativas (trials) ao mesmo
tempo. Num notebook comum fica várias vezes mais rápido que o Brian2 em modo
NumPy, e a equivalência é conferida em scripts/01_validate.py.

Duas extensões usadas pelo projeto:
  - weight_scale: fator multiplicativo por aresta (Modo A, bloqueio colinérgico)
  - bias_mv: despolarização constante por neurônio (Modo B, agonista tônico).
    Com viés b, o repouso efetivo vira v_rest + b. Neurônios com repouso
    efetivo acima do limiar disparam sozinhos (atividade espontânea).
"""
from __future__ import annotations

from dataclasses import dataclass, asdict

import numpy as np

from .connectome import Connectome


@dataclass
class LIFParams:
    dt: float = 0.1        # ms
    t_run: float = 1000.0  # ms
    v0: float = -52.0      # mV, repouso
    v_rst: float = -52.0   # mV, reset
    v_th: float = -45.0    # mV, limiar
    t_mbr: float = 20.0    # ms, constante de membrana
    tau: float = 5.0       # ms, constante sináptica
    t_rfc: float = 2.2     # ms, refratário
    t_dly: float = 1.8     # ms, atraso sináptico
    w_syn: float = 0.275   # mV por sinapse (parâmetro livre do modelo original)
    f_poi: float = 250.0   # fator da entrada de Poisson

    def scaled(self, factor: float, names=("t_mbr", "tau", "t_rfc", "t_dly", "w_syn")):
        d = asdict(self)
        for n in names:
            d[n] *= factor
        return LIFParams(**d)


def simulate(con: Connectome, stim, rate_hz: float, n_trials: int = 10,
             params: LIFParams | None = None, weight_scale=None, bias_mv=None,
             silence=None, stim2=None, rate2_hz: float = 0.0, seed: int = 0,
             prune_every: int = 20, return_active_size: bool = False):
    """Roda n_trials tentativas independentes em paralelo.

    stim, stim2 : índices (não IDs FlyWire) dos neurônios com entrada de Poisson
    rate_hz     : taxa de Poisson do grupo stim
    weight_scale: array (n_edges,) multiplicando cada peso, ou None
    bias_mv     : array (N,) de despolarização constante em mV, ou None
    silence     : índices de neurônios cujas saídas são zeradas
    Retorna counts: array (n_trials, N) com o número de spikes de cada neurônio.
    """
    p = params or LIFParams()
    rng = np.random.default_rng(seed)
    N, K = con.N, n_trials
    NK = N * K
    n_steps = int(round(p.t_run / p.dt))
    D = max(1, int(round(p.t_dly / p.dt)))
    rfc_steps = int(round(p.t_rfc / p.dt))

    Pm = np.exp(-p.dt / p.t_mbr)
    Pg = np.exp(-p.dt / p.tau)
    Q = p.tau / (p.tau - p.t_mbr) * (Pg - Pm)  # integração exata do sistema linear

    # pesos efetivos em mV
    w_eff = con.weights * np.float32(p.w_syn)
    if weight_scale is not None:
        w_eff = w_eff * weight_scale.astype(np.float32)
    if silence is not None and len(silence):
        w_eff = w_eff.copy()
        for i in np.atleast_1d(silence):
            w_eff[con.indptr[i]:con.indptr[i + 1]] = 0.0
    indptr, indices = con.indptr, con.indices

    rest = np.full(N, p.v0, dtype=np.float64)
    if bias_mv is not None:
        rest = rest + bias_mv
    rest_flat = np.tile(rest, K)

    v = rest_flat.copy()
    g = np.zeros(NK)
    ref_until = np.zeros(NK, dtype=np.int64)
    counts = np.zeros(NK, dtype=np.int32)

    stim = np.asarray(stim if stim is not None else [], dtype=np.int64)
    stim2 = np.asarray(stim2 if stim2 is not None else [], dtype=np.int64)
    offs = (np.arange(K, dtype=np.int64) * N)
    stim_flat = (stim[None, :] + offs[:, None]).ravel()
    stim2_flat = (stim2[None, :] + offs[:, None]).ravel()
    rfc_unit = np.full(NK, rfc_steps, dtype=np.int64)
    rfc_unit[stim_flat] = 0
    rfc_unit[stim2_flat] = 0
    p1 = rate_hz * p.dt / 1000.0
    p2 = rate2_hz * p.dt / 1000.0
    kick = p.w_syn * p.f_poi

    spont = np.flatnonzero(rest_flat > p.v_th)
    always = np.unique(np.concatenate([stim_flat, stim2_flat, spont]))
    is_act = np.zeros(NK, dtype=bool)
    is_act[always] = True
    act = always.copy()
    is_always = np.zeros(NK, dtype=bool)
    is_always[always] = True

    buf = [np.empty(0, dtype=np.int64) for _ in range(D)]
    act_sizes = []

    for t in range(n_steps):
        a = act
        # 1) integração exata (neurônios fora do refratário)
        free = a[ref_until[a] <= t]
        if free.size:
            va, ga, ra = v[free], g[free], rest_flat[free]
            v[free] = ra + (va - ra) * Pm + ga * Q
            g[free] = ga * Pg
        # 2) limiar
        spk = a[(v[a] > p.v_th) & (ref_until[a] <= t)]
        # 3) entrega dos spikes emitidos D passos atrás
        pend = buf[t % D]
        if pend.size:
            src = pend % N
            trial_off = pend - src
            starts = indptr[src]
            lens = indptr[src + 1] - starts
            tot = int(lens.sum())
            if tot:
                excl = np.cumsum(lens) - lens
                pos = np.repeat(starts - excl, lens) + np.arange(tot)
                tgt = indices[pos].astype(np.int64) + np.repeat(trial_off, lens)
                wv = w_eff[pos]
                # Semântica do Brian2 (conferida em scripts/01_validate.py):
                # entrada que chega durante o refratário do alvo é descartada.
                ok = ref_until[tgt] <= t
                tgt, wv = tgt[ok], wv[ok]
                np.add.at(g, tgt, wv)
                new = tgt[~is_act[tgt]]
                if new.size:
                    new = np.unique(new)
                    is_act[new] = True
                    act = np.concatenate([act, new])
        # 4) entrada de Poisson
        if p1 > 0 and stim_flat.size:
            hit = stim_flat[rng.random(stim_flat.size) < p1]
            v[hit] += kick
        if p2 > 0 and stim2_flat.size:
            hit = stim2_flat[rng.random(stim2_flat.size) < p2]
            v[hit] += kick
        # 5) reset e registro
        if spk.size:
            v[spk] = p.v_rst
            g[spk] = 0.0
            ref_until[spk] = t + rfc_unit[spk]
            counts[spk] += 1
        buf[t % D] = spk
        # 6) poda do conjunto ativo (neurônios que voltaram ao repouso)
        if t % prune_every == 0 and act.size > always.size:
            quiet = (np.abs(v[act] - rest_flat[act]) < 1e-4) & (np.abs(g[act]) < 1e-4) \
                    & (ref_until[act] <= t) & ~is_always[act]
            if quiet.any():
                q = act[quiet]
                v[q] = rest_flat[q]
                g[q] = 0.0
                is_act[q] = False
                act = act[~quiet]
        if return_active_size and t % 100 == 0:
            act_sizes.append(act.size / K)

    counts = counts.reshape(K, N)
    if return_active_size:
        return counts, np.array(act_sizes)
    return counts


def rates(counts: np.ndarray, idx, params: LIFParams | None = None) -> np.ndarray:
    """Taxa (Hz) por tentativa dos neurônios idx; média se idx tiver vários."""
    p = params or LIFParams()
    r = counts[:, np.atleast_1d(idx)] / (p.t_run / 1000.0)
    return r.mean(axis=1)
