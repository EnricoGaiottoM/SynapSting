"""Cegamento: gera códigos de frascos e ordem de teste sorteada.
A CHAVE (chave_SECRETA.csv) fica com outra pessoa (orientador) até o fim da análise.
Uso: python randomize_blind.py --groups veiculo,baixa,media,alta --flies 30 --seed <número sorteado no dia>
"""
import argparse, secrets, numpy as np, pandas as pd
ap = argparse.ArgumentParser(); ap.add_argument("--groups", default="veiculo,baixa,media,alta")
ap.add_argument("--flies", type=int, default=30); ap.add_argument("--per-session", type=int, default=8)
ap.add_argument("--seed", type=int, default=None); a = ap.parse_args()
seed = a.seed if a.seed is not None else secrets.randbelow(10**9); rng = np.random.default_rng(seed)
groups = a.groups.split(","); codes = rng.choice(np.arange(100, 1000), size=len(groups), replace=False)
key = pd.DataFrame({"codigo_frasco": [f"F{c}" for c in codes], "grupo": groups})
key.assign(seed=seed).to_csv("chave_SECRETA.csv", index=False)
flies = [(f"F{c}", i + 1) for c in codes for i in range(a.flies)]
order = [flies[i] for i in rng.permutation(len(flies))]
sheet = pd.DataFrame(order, columns=["codigo_frasco", "mosca_no_frasco"])
sheet.insert(0, "sessao", np.arange(len(sheet)) // a.per_session + 1)
sheet.insert(1, "id_mosca", [f"M{i+1:03d}" for i in range(len(sheet))])
sheet.to_csv("planilha_cega.csv", index=False)
print(f"{len(sheet)} moscas em {sheet.sessao.max()} sessões. Entregue chave_SECRETA.csv ao orientador e apague sua cópia.")
