"""Ajusta as curvas, calcula a vulnerabilidade relativa e gera as figuras de uma rodada.

Uso:
  python scripts/analisar.py                       # resultados/preliminar
  python scripts/analisar.py resultados/final      # depois da grade final

Lê (os que existirem): alimentacao.csv, agua.csv, limpeza.csv, embaralhado.csv, gargalos.csv
Gera: ajustes_modoA.csv, modoA_vs_B.csv e figuras/fig1_curvas_modoA.png, fig2_vulnerabilidade.png, fig3_gargalos.png
"""
import os, sys
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from synapsting.analysis import bootstrap_hill, hill

D = sys.argv[1] if len(sys.argv) > 1 else "resultados/preliminar"
FIG = os.path.join(D, "figuras"); os.makedirs(FIG, exist_ok=True)


def ler(nome):
    f = os.path.join(D, f"{nome}.csv")
    if not os.path.exists(f):
        return None
    d = pd.read_csv(f)
    if "level" in d:
        d["level"] = d.level.astype(float)
    return d


F, W, G, S, B = (ler(n) for n in ["alimentacao", "agua", "limpeza", "embaralhado", "gargalos"])

# Figura 1: curvas do Modo A e limiar S50 com IC por bootstrap
A = F[F["mode"] == "A"]; niveis = sorted(A.level.unique()); ajustes = []
fig, ax = plt.subplots(1, 2, figsize=(10, 4))
for c, a in zip(plt.cm.viridis(np.linspace(0, .9, len(niveis))), niveis):
    d = A[A.level == a]; m = d.groupby("stim_hz").MN9_hz.agg(["mean", "std"])
    ax[0].errorbar(m.index, m["mean"], m["std"], color=c, marker="o", ms=4, capsize=2, label=f"α = {a:.2f}")
    f = bootstrap_hill(d, n_boot=300); f["alpha"] = a; ajustes.append(f)
    if f["ok"]:
        s = np.linspace(0, 200, 200); ax[0].plot(s, hill(s, f["rmax"], f["s50"], f["n"]), color=c, lw=1, alpha=.6)
ax[0].set(xlabel="Estímulo nos GRNs de açúcar (Hz)", ylabel="Taxa do MN9 (Hz)", title="Modo A: bloqueio colinérgico")
ax[0].legend(fontsize=7)
T = pd.DataFrame(ajustes)[["alpha", "s50", "s50_lo", "s50_hi", "rmax", "n", "frac_finite"]]
ok = T[np.isfinite(T.s50)]
ax[1].errorbar(ok.alpha, ok.s50, [ok.s50 - ok.s50_lo, ok.s50_hi - ok.s50], marker="o", capsize=3, color="k")
ax[1].set(xlabel="α (fração de bloqueio das sinapses de ACh)", ylabel="S50 (Hz), IC 95%", title="Limiar do reflexo no modelo", ylim=(0, 240))
plt.tight_layout(); plt.savefig(f"{FIG}/fig1_curvas_modoA.png", dpi=160); plt.close()
T.round(2).to_csv(f"{D}/ajustes_modoA.csv", index=False)

# Figura 2: resposta em % do controle, por circuito e mecanismo
conds = {"controle": ("A", 0.0), "Modo A α=0,1": ("A", .1), "Modo A α=0,15": ("A", .15), "Modo A α=0,2": ("A", .2),
         "Modo B ρ=0,5": ("B", .5), "Modo B ρ=1": ("B", 1.0)}
linhas = []
for lab, d, s, col in [("Alimentação 100 Hz", F, 100, "MN9_hz"), ("Alimentação 200 Hz", F, 200, "MN9_hz"),
                       ("Água 200 Hz", W, 200, "MN9_hz"), ("Limpeza 200 Hz", G, 200, "aDN1_hz")]:
    if d is None:
        continue
    for cond, (mode, lvl) in conds.items():
        x = d[(d["mode"] == mode) & (d.level == lvl) & (d.stim_hz == s)][col]
        if len(x):
            linhas.append(dict(circuito=lab, condicao=cond, media_hz=round(x.mean(), 1), dp=round(x.std(), 1), n=len(x)))
C = pd.DataFrame(linhas); C.to_csv(f"{D}/modoA_vs_B.csv", index=False)
piv = C.pivot(index="circuito", columns="condicao", values="media_hz")
rel = (piv.div(piv["controle"], axis=0) * 100).round(0)
fig, ax = plt.subplots(figsize=(9, 4)); rel.drop(columns="controle").plot.bar(ax=ax, rot=0, width=.8)
ax.axhline(100, color="k", lw=.8, ls="--"); ax.set(ylabel="% da resposta do controle", title="Vulnerabilidade por circuito e mecanismo")
ax.legend(fontsize=7, ncol=3); plt.tight_layout(); plt.savefig(f"{FIG}/fig2_vulnerabilidade.png", dpi=160); plt.close()

# Figura 3: triagem de gargalos
if B is not None:
    B = B[B.flywire_id.astype(str) != "baseline"].sort_values("drop_pct")
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.barh([f"{t} ({str(i)[-6:]})" for t, i in zip(B.cell_type.fillna(""), B.flywire_id)], B.drop_pct, color="#b5651d")
    ax.set(xlabel="Queda do MN9 ao silenciar o neurônio (%)", title="Triagem de gargalos colinérgicos")
    plt.tight_layout(); plt.savefig(f"{FIG}/fig3_gargalos.png", dpi=160); plt.close()

print(T.round(1).to_string(index=False)); print(); print(rel.to_string())
if S is not None:
    print("\nEmbaralhado:", S.groupby("stim_hz")[["MN9_hz", "n_recruited_5hz"]].mean().round(1).to_dict())
