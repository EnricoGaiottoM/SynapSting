"""Baixa os dados do conectoma em versões FIXAS e confere a integridade (SHA-256).

Uso:
  python scripts/setup_data.py            # baixa o que falta (v783 + anotações)
  python scripts/setup_data.py --all      # inclui a v630 e o arquivo de validação
  python scripts/setup_data.py --verify   # só confere os arquivos já baixados

Por que versões fixas: o resultado científico só é reproduzível se todos usarem
exatamente os mesmos arquivos. Os links apontam para commits específicos.
"""
import argparse, hashlib, sys, time, urllib.request
from pathlib import Path

SHIU = "https://raw.githubusercontent.com/philshiu/Drosophila_brain_model/91bdd1e7dcf193f3e7ca5a8933497fcef63b7960/"
ANN = "https://raw.githubusercontent.com/flyconnectome/flywire_annotations/8587524c1748ce5ef2080822a2fc890fc03bf597/"
FILES = {  # destino: (url, sha256, tamanho em bytes, obrigatório?)
    "Connectivity_783.parquet": (SHIU + "Connectivity_783.parquet",
        "efeb23fb99098e9c390f6869969b2a121a2ee92c833cfc45ecb2c1d8e1af0347", 100804642, True),
    "Completeness_783.csv": (SHIU + "Completeness_783.csv",
        "bbb847a4cc2caaa7a16349722d220c087317b946d148d4d592d94d250617a311", 3327347, True),
    "flywire_annotations_783.tsv": (ANN + "supplemental_files/Supplemental_file1_neuron_annotations.tsv",
        "9a4f8b2f843196074431ebd7cd883536afa1be86c8a4ce90970441e8be81d1be", 31718505, True),
    "Connectivity_630.parquet": (SHIU + "2023_03_23_connectivity_630_final.parquet",
        "94db8c650533bc36ffa3223f2e62325d5648b8d6bd31c3a4e1c804628c7557b3", 86630944, False),
    "Completeness_630.csv": (SHIU + "2023_03_23_completeness_630_final.csv",
        "e6b71e17671a9bdb05f55e4bc6774640a1418cb7a05125e0fc994ad40f9bfdfb", 3057611, False),
    "shiu_sugarR_200Hz.parquet": (SHIU + "results/example/sugarR.parquet",
        "83921d50089d966785e402d6c0e3be5ab3eba5beb680410a09c557b0f22dcc28", 948526, False),
}


def sha256(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while b := f.read(chunk):
            h.update(b)
    return h.hexdigest()


def download(url, dest, size, tries=3):
    tmp = dest.with_suffix(dest.suffix + ".part")
    for k in range(1, tries + 1):
        try:
            with urllib.request.urlopen(url, timeout=60) as r, open(tmp, "wb") as f:
                got, t0 = 0, time.time()
                while b := r.read(1 << 20):
                    f.write(b); got += len(b)
                    print(f"\r  {dest.name}: {got / 1e6:6.1f} / {size / 1e6:.1f} MB "
                          f"({got / 1e6 / max(time.time() - t0, 1e-3):.1f} MB/s)", end="", flush=True)
            print(); tmp.replace(dest); return
        except Exception as e:
            print(f"\n  tentativa {k} falhou: {e}")
            time.sleep(3 * k)
    sys.exit(f"ERRO: não consegui baixar {url}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true"); ap.add_argument("--verify", action="store_true")
    ap.add_argument("--dir", default="data")
    a = ap.parse_args(); d = Path(a.dir); d.mkdir(exist_ok=True); ok = True
    for name, (url, digest, size, required) in FILES.items():
        if not (required or a.all):
            continue
        dest = d / name
        if not dest.exists():
            if a.verify:
                print(f"[FALTA] {name}"); ok = False; continue
            download(url, dest, size)
        good = sha256(dest) == digest
        print(f"[{'OK' if good else 'ERRO'}] {name}")
        ok &= good
    print("Tudo certo." if ok else "Há problemas: apague o arquivo com ERRO e rode de novo.")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
