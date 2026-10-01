"""Gera tabelas e figuras dos resultados preliminares a partir de results/*.csv."""
import json, numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from synapsting.analysis import bootstrap_hill, hill
F = pd.read_csv("results/feeding.csv"); F["level"] = F.level.astype(float)
out = {}
# --- Fig 1: curvas do Modo A
A = F[F["mode"] == "A"]; lv = sorted(A.level.unique())
fig, ax = plt.subplots(1, 2, figsize=(10, 4))
cm = plt.cm.viridis(np.linspace(0, .9, len(lv))); fits = []
for c, a in zip(cm, lv):
    d = A[A.level == a]; m = d.groupby("stim_hz").MN9_hz.agg(["mean", "std"])
    ax[0].errorbar(m.index, m["mean"], m["std"], color=c, marker="o", ms=4, capsize=2, label=f"α = {a:.2f}")
    f = bootstrap_hill(d, n_boot=300); f["alpha"] = a; fits.append(f)
    if f["ok"]:
        s = np.linspace(0, 200, 200); ax[0].plot(s, hill(s, f["rmax"], f["s50"], f["n"]), color=c, lw=1, alpha=.6)
ax[0].set(xlabel="Estímulo nos GRNs de açúcar (Hz)", ylabel="Taxa do MN9 (Hz)", title="Modo A: bloqueio colinérgico")
ax[0].legend(fontsize=7)
T = pd.DataFrame(fits)[["alpha", "s50", "s50_lo", "s50_hi", "rmax", "n", "frac_finite"]]
fin = T[np.isfinite(T.s50)]
ax[1].errorbar(fin.alpha, fin.s50, [fin.s50 - fin.s50_lo, fin.s50_hi - fin.s50], marker="o", capsize=3, color="k")
for _, r in T[~np.isfinite(T.s50)].iterrows():
    ax[1].annotate("sem resposta\n(S50 > 200 Hz)", (r.alpha, 200), ha="center", fontsize=7)
ax[1].set(xlabel="α (fração de bloqueio das sinapses de ACh)", ylabel="S50 (Hz), IC 95% bootstrap", title="Limiar do PER no modelo", ylim=(0, 240))
plt.tight_layout(); plt.savefig("figures/fig1_modoA_curvas.png", dpi=160); plt.close()
T.round(2).to_csv("results/fits_modeA.csv", index=False); out["fits_modeA"] = T.round(2).to_dict("records")
# --- Fig 2: A vs B (alimentação, água, limpeza) em estímulo fixo
W = pd.read_csv("results/water.csv"); G = pd.read_csv("results/grooming.csv")
for d in (W, G): d["level"] = d.level.astype(float)
def get(d, mode, lvl, s, col): x = d[(d["mode"] == mode) & (d.level == lvl) & (d.stim_hz == s)][col]; return x.mean(), x.std(), len(x)
rows = []
for lab, d, s, col in [("Alimentação 100 Hz", F, 100, "MN9_hz"), ("Alimentação 200 Hz", F, 200, "MN9_hz"),
                       ("Água 200 Hz", W, 200, "MN9_hz"), ("Limpeza 200 Hz", G, 200, "aDN1_hz")]:
    for cond, (mode, lvl) in {"controle": ("A", 0.0), "Modo A α=0,1": ("A", .1), "Modo A α=0,15": ("A", .15),
                              "Modo A α=0,2": ("A", .2), "Modo B ρ=0,5": ("B", .5), "Modo B ρ=1": ("B", 1.0)}.items():
        m, sd, n = get(d, mode, lvl, s, col)
        if n: rows.append(dict(circuito=lab, condicao=cond, media_hz=round(m, 1), dp=round(sd, 1), n=n))
C = pd.DataFrame(rows); C.to_csv("results/modeA_vs_B.csv", index=False); out["modeA_vs_B"] = rows
piv = C.pivot(index="circuito", columns="condicao", values="media_hz")
ctrl = piv["controle"]; rel = (piv.div(ctrl, axis=0) * 100).round(0)
fig, ax = plt.subplots(figsize=(9, 4)); rel.drop(columns="controle").plot.bar(ax=ax, rot=0, width=.8)
ax.axhline(100, color="k", lw=.8, ls="--"); ax.set(ylabel="% da resposta do controle", title="Vulnerabilidade relativa por circuito e mecanismo")
ax.legend(fontsize=7, ncol=3); plt.tight_layout(); plt.savefig("figures/fig2_vulnerabilidade.png", dpi=160); plt.close()
out["relative_pct"] = rel.to_dict()
# --- Fig 3: gargalos
B = pd.read_csv("results/bottleneck.csv"); B = B[B.flywire_id != "baseline"].sort_values("drop_pct")
fig, ax = plt.subplots(figsize=(7, 4.5))
ax.barh([f"{t} ({str(i)[-6:]})" for t, i in zip(B.cell_type, B.flywire_id)], B.drop_pct, color="#b5651d")
ax.set(xlabel="Queda do MN9 ao silenciar o neurônio (%)", title="Triagem de gargalos colinérgicos (açúcar 100 Hz)")
plt.tight_layout(); plt.savefig("figures/fig3_gargalos.png", dpi=160); plt.close()
# --- controle embaralhado
S = pd.read_csv("results/shuffle.csv"); out["shuffle"] = S.groupby("stim_hz")[["MN9_hz", "n_recruited_5hz"]].mean().round(1).to_dict()
out["real_recruit"] = F[(F["mode"] == "A") & (F.level == 0)].groupby("stim_hz").n_recruited_5hz.mean().round(1).to_dict()
json.dump(out, open("results/summary.json", "w"), indent=1, ensure_ascii=False, default=float)
print(T.round(1).to_string(index=False)); print(rel.to_string()); print(out["shuffle"], out["real_recruit"])
