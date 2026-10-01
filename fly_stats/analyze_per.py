"""Análise pré-registrada dos dados de PER.

Entrada (formato longo): id_mosca, grupo, sacarose_mM, resposta (0/1)
1) Curva dose-resposta por grupo: logística em log10(sacarose); EC50 = concentração
   com 50% de PER; IC 95% por bootstrap reamostrando MOSCAS (não tentativas).
2) Modelo com efeito da mosca: GEE binomial agrupado por mosca (robusto; em R, o
   equivalente é glmer(resposta ~ log10(sac) * grupo + (1|id_mosca), binomial) [lme4]).
3) Compara com o registro de previsões (razão EC50 tratado / EC50 veículo).
Uso: python analyze_per.py dados.csv   |   python analyze_per.py --demo  (dados SINTÉTICOS de teste)
"""
import sys, numpy as np, pandas as pd, statsmodels.api as sm, statsmodels.formula.api as smf

def ec50(d):
    X = sm.add_constant(np.log10(d.sacarose_mM)); y = d.resposta
    try:
        b = sm.GLM(y, X, family=sm.families.Binomial()).fit().params.values
        return 10 ** (-b[0] / b[1]) if b[1] > 0 else np.nan
    except Exception:
        return np.nan

def boot_ec50(d, n=1000, seed=0):
    rng = np.random.default_rng(seed); flies = d.id_mosca.unique(); g = dict(tuple(d.groupby("id_mosca"))); out = []
    for _ in range(n):
        out.append(ec50(pd.concat([g[f] for f in rng.choice(flies, len(flies))])))
    out = np.array(out); out = out[np.isfinite(out)]
    return np.percentile(out, [2.5, 97.5]) if len(out) else (np.nan, np.nan)

def demo(seed=1):
    rng = np.random.default_rng(seed); rows = []
    for grp, shift in [("veiculo", 1.0), ("baixa", 1.3), ("media", 1.8), ("alta", 2.6)]:
        for f in range(30):
            ec = 50 * shift * np.exp(rng.normal(0, .3))
            for c in [1, 3, 10, 30, 100, 300, 1000]:
                p = 1 / (1 + (ec / c) ** 1.5); rows.append((f"{grp}_{f}", grp, c, int(rng.random() < p)))
    return pd.DataFrame(rows, columns=["id_mosca", "grupo", "sacarose_mM", "resposta"])

if __name__ == "__main__":
    d = demo() if "--demo" in sys.argv else pd.read_csv(sys.argv[1])
    if "--demo" in sys.argv: print("ATENÇÃO: dados SINTÉTICOS, só para testar o código.\n")
    d["logc"] = np.log10(d.sacarose_mM); res = []
    for grp, g in d.groupby("grupo"):
        e = ec50(g); lo, hi = boot_ec50(g, n=300); res.append(dict(grupo=grp, n_moscas=g.id_mosca.nunique(), EC50_mM=e, IC_lo=lo, IC_hi=hi))
    R = pd.DataFrame(res); ref = R.loc[R.grupo == "veiculo", "EC50_mM"].values[0]; R["razao_vs_veiculo"] = R.EC50_mM / ref
    print(R.round(2).to_string(index=False))
    gee = smf.gee("resposta ~ logc * C(grupo, Treatment('veiculo'))", "id_mosca", d,
                  family=sm.families.Binomial(), cov_struct=sm.cov_struct.Exchangeable()).fit()
    print("\nGEE (efeito da mosca como agrupamento):"); print(gee.summary().tables[1])
