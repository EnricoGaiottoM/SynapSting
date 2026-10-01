"""Verificação rápida da instalação: python -m synapsting.check"""
import os, platform, sys, time
from pathlib import Path


def main():
    print(f"Python {sys.version.split()[0]} | {platform.system()} | {os.cpu_count()} núcleos")
    try:
        import numpy, scipy, pandas, pyarrow  # noqa: F401
    except ImportError as e:
        sys.exit(f"Falta pacote: {e.name}. Rode: pip install -e .")
    try:
        import psutil
        print(f"RAM: {psutil.virtual_memory().total / 1e9:.1f} GB")
    except ImportError:
        pass
    data = Path("data")
    need = ["Connectivity_783.parquet", "Completeness_783.csv", "flywire_annotations_783.tsv"]
    miss = [f for f in need if not (data / f).exists()]
    if miss:
        sys.exit(f"Faltam dados: {miss}. Rode: python scripts/baixar_dados.py")
    from synapsting.connectome import load_connectome
    from synapsting.simulator import simulate, LIFParams
    from synapsting import neurons as nr
    t0 = time.time(); con = load_connectome("data", "783")
    print(f"Conectoma: {con.N} neurônios, {con.n_edges} pares ({time.time() - t0:.1f}s)")
    sugar = con.idx(nr.load_sets()["sugar"]); mn9 = con.idx([nr.MN9])[0]
    t0 = time.time()
    c = simulate(con, sugar, 200, n_trials=2, params=LIFParams(t_run=300), seed=1)
    dt = time.time() - t0
    rate = c[:, mn9].mean() / 0.3
    print(f"Teste: açúcar a 200 Hz por 0,3 s -> MN9 = {rate:.0f} Hz ({dt:.1f}s para 2 tentativas)")
    print("OK: instalação funcionando." if rate > 30 else "ATENÇÃO: MN9 baixo demais; algo está errado.")
    est = dt / 0.3 / 2 * 30 * 7 * 11 / 60
    print(f"Estimativa da grade completa de alimentação (11 condições x 7 estímulos x 30 tentativas): "
          f"~{est:.0f} min em 1 núcleo (Modo B leva mais).")


if __name__ == "__main__":
    main()
