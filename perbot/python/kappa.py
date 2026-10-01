"""Concordância PER-bot x avaliador humano cego (kappa de Cohen + IC por bootstrap).
Uso: python kappa.py robo.csv humano.csv   (colunas: trial, fly, per)
Meta pré-registrada: kappa >= 0,8 em >= 200 eventos; senão, pontuação manual cega é a medida principal.
"""
import sys, numpy as np, pandas as pd

def cohen_kappa(a, b):
    a, b = np.asarray(a), np.asarray(b); po = (a == b).mean()
    pe = sum((a == c).mean() * (b == c).mean() for c in np.union1d(a, b))
    return (po - pe) / (1 - pe) if pe < 1 else 1.0

if __name__ == "__main__":
    r, h = pd.read_csv(sys.argv[1]), pd.read_csv(sys.argv[2])
    m = r.merge(h, on=["trial", "fly"], suffixes=("_robo", "_humano"))
    k = cohen_kappa(m.per_robo, m.per_humano); rng = np.random.default_rng(0)
    bs = [cohen_kappa(*m.sample(len(m), replace=True, random_state=int(rng.integers(1e9)))[["per_robo", "per_humano"]].T.values) for _ in range(2000)]
    print(f"n={len(m)} eventos | concordância={(m.per_robo == m.per_humano).mean():.3f} | kappa={k:.3f} "
          f"(IC95% {np.percentile(bs, 2.5):.3f}–{np.percentile(bs, 97.5):.3f})")
    print(pd.crosstab(m.per_humano, m.per_robo, rownames=["humano"], colnames=["robô"]))
