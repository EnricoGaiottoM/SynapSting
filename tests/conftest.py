import numpy as np, pytest
from synapsting.connectome import Connectome


def make_con(edges, nt, N=None):
    """edges: lista (pre, pos, peso em nº de sinapses com sinal)."""
    edges = sorted(edges)
    N = N or len(nt)
    pre = np.array([e[0] for e in edges], np.int32); post = np.array([e[1] for e in edges], np.int32)
    w = np.array([e[2] for e in edges], np.float32)
    indptr = np.zeros(N + 1, np.int64); np.cumsum(np.bincount(pre, minlength=N), out=indptr[1:])
    c = Connectome(ids=np.arange(N, dtype=np.int64) + 10**6, indptr=indptr, indices=post, weights=w,
                   nt=np.array(nt, dtype=str), version="teste")
    c.id2idx = {int(f): i for i, f in enumerate(c.ids)}
    return c


@pytest.fixture
def rede_aleatoria():
    rng = np.random.default_rng(0); N = 300; edges = set()
    for i in range(N):
        for j in rng.choice(N, 15, replace=False):
            if j != i:
                edges.add((i, int(j)))
    nt = rng.choice(["acetylcholine", "gaba", "glutamate", "dopamine"], N, p=[.6, .2, .15, .05])
    sign = {"acetylcholine": 1, "dopamine": 1, "gaba": -1, "glutamate": -1}
    e = [(i, j, sign[nt[i]] * int(rng.integers(1, 20))) for i, j in edges]
    nt[:10] = "acetylcholine"
    e = [(i, j, abs(w) if i < 10 else w) for i, j, w in e]
    return make_con(e, list(nt))
