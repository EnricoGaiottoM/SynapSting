"""Ajuste de curvas estímulo -> resposta e incerteza por bootstrap.

Modelo de Hill: r(s) = Rmax * s^n / (s^n + S50^n)
  S50  = estímulo que dá metade da resposta máxima (o "limiar")
  n    = inclinação;  Rmax = resposta máxima
Bootstrap: reamostra tentativas dentro de cada nível de estímulo [Efron & Tibshirani].
"""
import numpy as np
from scipy.optimize import curve_fit


def hill(s, rmax, s50, n):
    s = np.asarray(s, float)
    return rmax * s**n / (s**n + s50**n + 1e-12)


def fit_hill(stim, resp, s50_max=2000.0):
    stim, resp = np.asarray(stim, float), np.asarray(resp, float)
    if np.nanmax(resp) < 2.0:          # sem resposta: limiar indefinido (acima da faixa testada)
        return dict(rmax=np.nan, s50=np.inf, n=np.nan, ok=False)
    p0 = [max(resp.max(), 1), np.median(stim[stim > 0]), 3]
    try:
        p, _ = curve_fit(hill, stim, resp, p0=p0, bounds=([0, 1, 0.5], [400, s50_max, 20]), maxfev=20000)
        return dict(rmax=p[0], s50=p[1], n=p[2], ok=True)
    except Exception:
        return dict(rmax=np.nan, s50=np.nan, n=np.nan, ok=False)


def bootstrap_hill(df, stim_col="stim_hz", resp_col="MN9_hz", n_boot=500, seed=0):
    rng = np.random.default_rng(seed)
    groups = {s: g[resp_col].to_numpy() for s, g in df.groupby(stim_col)}
    stims = np.array(sorted(groups))
    base = fit_hill(stims, [groups[s].mean() for s in stims])
    s50s = []
    for _ in range(n_boot):
        m = [rng.choice(groups[s], size=len(groups[s])).mean() for s in stims]
        s50s.append(fit_hill(stims, m)["s50"])
    s50s = np.array(s50s, float)
    fin = s50s[np.isfinite(s50s)]
    lo, hi = (np.percentile(fin, [2.5, 97.5]) if len(fin) > 20 else (np.nan, np.nan))
    base.update(s50_lo=lo, s50_hi=hi, frac_finite=len(fin) / n_boot)
    return base
