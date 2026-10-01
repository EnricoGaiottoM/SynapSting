"""Figura compacta para os resumos: (A) curvas do Modo A, (B) vulnerabilidade relativa."""
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8})
F = pd.read_csv("results/feeding.csv"); F["level"] = F.level.astype(float)
C = pd.read_csv("results/modeA_vs_B.csv")
fig, ax = plt.subplots(1, 2, figsize=(7.2, 2.5), gridspec_kw={"width_ratios": [1.1, 1]})
cols = {0.0: "#1b1b1b", 0.1: "#2a6f97", 0.2: "#61a5c2", 0.3: "#c9c9c9"}
for a, c in cols.items():
    m = F[(F["mode"] == "A") & (F.level == a)].groupby("stim_hz").MN9_hz.agg(["mean", "std"])
    ax[0].errorbar(m.index, m["mean"], m["std"], color=c, marker="o", ms=3, lw=1.4, capsize=2,
                   label="controle" if a == 0 else f"{int(a*100)}% de bloqueio")
ax[0].set(xlabel="Estímulo de açúcar (Hz nos neurônios gustativos)", ylabel="Neurônio motor MN9 (Hz)")
ax[0].set_title("A. Bloqueio colinérgico desloca a curva", loc="left", fontsize=8.5, fontweight="bold")
ax[0].legend(frameon=False, fontsize=7); ax[0].spines[["top", "right"]].set_visible(False)
sel = [("Alimentação 100 Hz", "Alimentação\n(açúcar moderado)"), ("Alimentação 200 Hz", "Alimentação\n(açúcar forte)"),
       ("Limpeza 200 Hz", "Limpeza\ndas antenas")]
conds = [("Modo A α=0,1", "Bloqueio 10%", "#2a6f97"), ("Modo A α=0,2", "Bloqueio 20%", "#61a5c2"), ("Modo B ρ=1", "Agonista tônico", "#d17a22")]
x = np.arange(len(sel)); w = 0.26
for i, (k, lab, col) in enumerate(conds):
    vals = []
    for circ, _ in sel:
        ctrl = C[(C.circuito == circ) & (C.condicao == "controle")].media_hz.values[0]
        v = C[(C.circuito == circ) & (C.condicao == k)].media_hz.values
        vals.append(100 * v[0] / ctrl if len(v) else np.nan)
    ax[1].bar(x + (i - 1) * w, vals, w, color=col, label=lab)
ax[1].axhline(100, color="k", lw=0.7, ls="--"); ax[1].set_xticks(x, [s[1] for s in sel])
ax[1].set_ylabel("% da resposta do controle"); ax[1].set_ylim(0, 128); ax[1].set_yticks([0, 25, 50, 75, 100])
ax[1].set_title("B. Cada mecanismo deixa uma assinatura", loc="left", fontsize=8.5, fontweight="bold")
ax[1].legend(frameon=False, fontsize=6.8, loc="upper center", ncol=3, columnspacing=0.8, handlelength=1.2); ax[1].spines[["top", "right"]].set_visible(False)
plt.tight_layout(); plt.savefig("figures/fig_resumo.png", dpi=300); print("ok")
