"""Conjuntos de neurônios usados no projeto (IDs FlyWire).

Os IDs vêm do notebook figures.ipynb de Shiu et al. (versão 630). Cerca de
83% dos IDs não mudaram na versão pública 783; usamos os que existem nela.
Identidades na v783 (anotações FlyWire):
  MN9  = tipo CB0701 (par: 720575940660219265 e 720575940618238523)
  aDN1 = 720575940616185531 (anotado como DNg62 na v783)
  aBN1 = 720575940630907434 (anotado como SAD093 na v783)
"""
import json
from pathlib import Path

MN9 = 720575940660219265          # o MN9 usado por Shiu
MN9_PAIR = [720575940660219265, 720575940618238523]
ADN1 = 720575940616185531
ABN1 = 720575940630907434


def load_sets(path="data/neuron_ids_630.json"):
    d = json.loads(Path(path).read_text())
    s = d["sets_630"]
    return {
        "sugar": s["neu_sugar"],     # GRNs de açúcar do labelo (direita)
        "water": s["neu_water"],     # GRNs de água
        "bitter": s["neu_bitter"],
        "jon_ce": s["neu_JON_CE"],   # neurônios do órgão de Johnston (limpeza)
    }
