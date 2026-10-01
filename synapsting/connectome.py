"""Carrega o conectoma FlyWire no formato usado por Shiu et al. (2024).

O arquivo de conectividade tem uma linha por par (pré, pós) com:
  - Connectivity: número de sinapses entre os dois neurônios
  - Excitatory: +1 (ACh, DA, 5-HT, OA) ou -1 (GABA, Glu)
  - Excitatory x Connectivity: peso com sinal, em "número de sinapses"

Aqui guardamos tudo em formato CSR (uma linha por neurônio pré-sináptico),
que é o formato mais rápido para "entregar" os spikes de um neurônio a
todos os seus alvos. Também separamos quais neurônios são colinérgicos
(alvo do imidacloprido) usando as anotações do FlyWire (top_nt).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd


@dataclass
class Connectome:
    ids: np.ndarray            # FlyWire root_id de cada índice (int64)
    indptr: np.ndarray         # CSR: início das saídas de cada neurônio pré
    indices: np.ndarray        # CSR: índice do neurônio pós (int32)
    weights: np.ndarray        # CSR: peso com sinal em nº de sinapses (float32)
    nt: np.ndarray             # neurotransmissor previsto (str) de cada neurônio
    version: str = "783"
    id2idx: dict = field(default_factory=dict)

    @property
    def N(self) -> int:
        return len(self.ids)

    @property
    def n_edges(self) -> int:
        return len(self.indices)

    def idx(self, flywire_ids) -> np.ndarray:
        """Converte IDs do FlyWire em índices; ignora IDs ausentes com aviso."""
        out, missing = [], []
        for f in flywire_ids:
            i = self.id2idx.get(int(f))
            (missing if i is None else out).append(f if i is None else i)
        if missing:
            print(f"[aviso] {len(missing)} ID(s) não existem na versão {self.version}: {missing[:3]}...")
        return np.asarray(out, dtype=np.int64)

    # ----- quantidades usadas pelos modos de perturbação -----
    def is_ach(self) -> np.ndarray:
        """True para neurônios cujo neurotransmissor previsto é acetilcolina."""
        return self.nt == "acetylcholine"

    def pre_of_edges(self) -> np.ndarray:
        """Índice do neurônio pré-sináptico de cada aresta (expande o CSR)."""
        return np.repeat(np.arange(self.N, dtype=np.int32), np.diff(self.indptr))

    def ach_synapses_in(self) -> np.ndarray:
        """Número de sinapses colinérgicas que cada neurônio RECEBE."""
        pre = self.pre_of_edges()
        mask = self.is_ach()[pre]
        return np.bincount(self.indices[mask], weights=np.abs(self.weights[mask]),
                           minlength=self.N)


def load_connectome(data_dir: str | Path = "data", version: str = "783",
                    annotations: str | Path | None = None) -> Connectome:
    data_dir = Path(data_dir)
    comp = pd.read_csv(data_dir / f"Completeness_{version}.csv", index_col=0)
    ids = comp.index.values.astype(np.int64)
    N = len(ids)

    con = pd.read_parquet(
        data_dir / f"Connectivity_{version}.parquet",
        columns=["Presynaptic_Index", "Postsynaptic_Index", "Excitatory x Connectivity"],
    )
    pre = con["Presynaptic_Index"].to_numpy(np.int32)
    post = con["Postsynaptic_Index"].to_numpy(np.int32)
    w = con["Excitatory x Connectivity"].to_numpy(np.float32)
    del con

    order = np.argsort(pre, kind="stable")
    pre, post, w = pre[order], post[order], w[order]
    indptr = np.zeros(N + 1, dtype=np.int64)
    np.cumsum(np.bincount(pre, minlength=N), out=indptr[1:])

    # neurotransmissor: anotações FlyWire (v783). Sem anotação -> infere pelo sinal.
    nt = np.full(N, "unknown", dtype=object)
    ann_path = Path(annotations) if annotations else data_dir / "flywire_annotations_783.tsv"
    if ann_path.exists():
        ann = pd.read_csv(ann_path, sep="\t", usecols=["root_id", "top_nt"], low_memory=False)
        m = dict(zip(ann.root_id.astype(np.int64), ann.top_nt.fillna("unknown")))
        nt = np.array([m.get(int(i), "unknown") for i in ids], dtype=object)
    sign = np.zeros(N, dtype=np.float32)
    np.maximum.at(sign, pre, np.sign(w))  # +1 se alguma saída é excitatória
    unk = nt == "unknown"
    nt[unk & (sign > 0)] = "excitatory_unknown"
    nt[unk & (sign <= 0)] = "inhibitory_unknown"

    c = Connectome(ids=ids, indptr=indptr, indices=post, weights=w, nt=nt.astype(str),
                   version=version)
    c.id2idx = {int(f): i for i, f in enumerate(ids)}
    return c
