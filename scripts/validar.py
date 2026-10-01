"""Validação do simulador contra o modelo original de Shiu et al. (Brian2).
Compara a atividade de todos os neurônios ao estimular os 21 GRNs de açúcar a 200 Hz
(v630) com o arquivo results/example/sugarR.parquet do repositório original.
Resultado obtido (26/09/2026): r = 0,999 entre neurônios; atividade total 1,001x; MN9 94,7 vs 93,3 Hz.
Uso: python scripts/validar.py
"""
import sys, json, numpy as np, pandas as pd
from synapsting.connectome import load_connectome
from synapsting.simulator import simulate
con = load_connectome("data", "630")
from pathlib import Path
import synapsting
ids = json.load(open(Path(synapsting.__file__).with_name("neuron_ids.json")))
sugar = con.idx(ids["sets_630"]["neu_sugar"]); mn9 = con.id2idx[ids["singles_630"]["mn9_left"]]
ref = pd.read_parquet(sys.argv[1] if len(sys.argv) > 1 else "data/shiu_sugarR_200Hz.parquet").groupby("flywire_id").size() / 30
refv = np.zeros(con.N)
for f, r in ref.items(): refv[con.id2idx[f]] = r
m = simulate(con, sugar, 200, n_trials=6, seed=2).mean(0); act = (m > 0) | (refv > 0)
print(f"correlação entre neurônios ativos: r = {np.corrcoef(m[act], refv[act])[0, 1]:.4f}")
print(f"atividade total (nosso / Brian2): {m.sum() / refv.sum():.3f}")
print(f"MN9: nosso {m[mn9]:.1f} Hz | Brian2 {refv[mn9]:.1f} Hz")
