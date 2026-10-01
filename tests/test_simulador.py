"""Testes do simulador. Rodam sem os dados do conectoma: python -m pytest"""
import numpy as np
from synapsting.simulator import simulate, LIFParams
from synapsting.experiments import perturbation, shuffle_connectome
from synapsting.analysis import hill, fit_hill
from conftest import make_con


def referencia_escalar(t_pre_spikes, w, p=LIFParams(), n_steps=450):
    """Implementação independente, passo a passo, da semântica do Brian2 (1 neurônio).
    Conferida contra o Brian2: entradas a cada 0,7 ms com w=40 mV dão spikes em 14,0; 18,9; 23,8 ms..."""
    dt = p.dt; Pm = np.exp(-dt / p.t_mbr); Pg = np.exp(-dt / p.tau); Q = p.tau / (p.tau - p.t_mbr) * (Pg - Pm)
    D = int(round(p.t_dly / dt)); rfc = int(round(p.t_rfc / dt))
    arr = [s + D for s in t_pre_spikes]
    v, g, ref, out = p.v0, 0.0, 0, []
    for t in range(n_steps):
        if ref <= t:
            v = p.v0 + (v - p.v0) * Pm + g * Q; g *= Pg
        spk = v > p.v_th and ref <= t
        if ref <= t:
            g += w * arr.count(t)
        if spk:
            v, g, ref = p.v_rst, 0.0, t + rfc; out.append(t)
    return out


def test_brian_semantica_numero_conhecido():
    p = LIFParams()
    pre = [int(round(t / p.dt)) for t in np.arange(10, 40, 0.7)]
    spikes = [round(t * p.dt, 1) for t in referencia_escalar(pre, 40.0)]
    assert spikes[:6] == [14.0, 18.9, 23.8, 28.7, 33.6, 38.5]


def test_simulador_igual_a_referencia():
    """Neurônio 0 dispara sozinho (viés acima do limiar); 0 -> 1 com peso forte.
    Os spikes do neurônio 1 no simulador vetorizado devem ser idênticos aos da referência."""
    p = LIFParams(t_run=60.0)
    con = make_con([(0, 1, 100)], ["acetylcholine", "acetylcholine"])
    w_mv = 100 * p.w_syn
    bias = np.array([12.0, 0.0])
    # spikes do neurônio 0 (determinísticos) pela própria referência de um neurônio com viés
    Pm = np.exp(-p.dt / p.t_mbr); v, ref, s0 = p.v0 + 12.0, 0, []
    rest0 = p.v0 + 12.0
    for t in range(int(p.t_run / p.dt)):
        if ref <= t:
            v = rest0 + (v - rest0) * Pm
        if v > p.v_th and ref <= t:
            v, ref = p.v_rst, t + int(round(p.t_rfc / p.dt)); s0.append(t)
    esperado = referencia_escalar(s0, w_mv, p, n_steps=int(p.t_run / p.dt))
    counts = simulate(con, [], 0.0, n_trials=1, params=p, bias_mv=bias, seed=0)
    assert counts[0, 0] == len(s0)
    assert counts[0, 1] == len(esperado)


def test_mesma_semente_mesmo_resultado(rede_aleatoria):
    a = simulate(rede_aleatoria, np.arange(10), 150, n_trials=2, params=LIFParams(t_run=100), seed=7)
    b = simulate(rede_aleatoria, np.arange(10), 150, n_trials=2, params=LIFParams(t_run=100), seed=7)
    assert np.array_equal(a, b)


def test_modo_A_zero_e_controle(rede_aleatoria):
    assert perturbation(rede_aleatoria, "A", 0.0) == (None, None)


def test_modo_A_so_mexe_em_acetilcolina(rede_aleatoria):
    s, b = perturbation(rede_aleatoria, "A", 0.3)
    pre = rede_aleatoria.pre_of_edges(); ach = rede_aleatoria.is_ach()[pre]
    assert b is None and np.allclose(s[ach], 0.7) and np.allclose(s[~ach], 1.0)


def test_modo_B_formula(rede_aleatoria):
    p = LIFParams(); rho = 1.5
    _, b = perturbation(rede_aleatoria, "B", rho, p)
    esperado = p.w_syn * rede_aleatoria.ach_synapses_in() * rho * p.tau / 1000
    assert np.allclose(b, esperado)


def test_bloqueio_reduz_atividade(rede_aleatoria):
    p = LIFParams(t_run=200)
    c0 = simulate(rede_aleatoria, np.arange(10), 200, n_trials=3, params=p, seed=1)
    s, _ = perturbation(rede_aleatoria, "A", 0.5)
    c1 = simulate(rede_aleatoria, np.arange(10), 200, n_trials=3, params=p, weight_scale=s, seed=1)
    assert c1[:, 10:].sum() <= c0[:, 10:].sum()


def test_embaralhar_preserva_graus(rede_aleatoria):
    sh = shuffle_connectome(rede_aleatoria, seed=3)
    N = rede_aleatoria.N
    assert np.array_equal(np.diff(sh.indptr), np.diff(rede_aleatoria.indptr))            # grau de saída
    assert np.array_equal(np.bincount(sh.indices, minlength=N), np.bincount(rede_aleatoria.indices, minlength=N))
    assert not np.array_equal(sh.indices, rede_aleatoria.indices)


def test_ajuste_de_hill_recupera_parametros():
    s = np.array([0, 25, 50, 75, 100, 150, 200.0])
    f = fit_hill(s, hill(s, 90, 80, 4))
    assert abs(f["s50"] - 80) < 1 and abs(f["rmax"] - 90) < 1
