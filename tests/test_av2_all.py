"""Testes formais do Autômato Linearmente Limitado Determinístico (ALL — 11 estados) e all.jff."""

from __future__ import annotations

import itertools

import pytest

from src.av2.all_lba import AutomatoLinearmenteLimitado, construir_all
from src.av2.cases import CASOS_ALL
from src.av2.jflap_io import DIAGRAMS_DIR, parse_all_jff
from src.av2.spec import (
    ALL_FINAL_STATES,
    ALL_INITIAL_STATE,
    ALL_STATES,
    ALL_TRANSITIONS,
    LEFT_MARKER,
    RIGHT_MARKER,
)


def _oraculo_l2(cadeia: str) -> bool:
    """Especificação matemática de referência de L2 = { w:w | w ∈ {i, s}+ }."""
    if cadeia.count(":") != 1:
        return False
    esq, dir_ = cadeia.split(":")
    return len(esq) >= 1 and esq == dir_ and set(esq).issubset({"i", "s"})


def test_requisitos_estruturais_all():
    all_lba = construir_all()
    assert len(all_lba.states) >= 8, "Lauda exige no mínimo 8 estados no ALL."
    assert len(all_lba.states) == 11
    assert all_lba.initial_state == ALL_INITIAL_STATE
    assert all_lba.final_states == frozenset(ALL_FINAL_STATES)


def test_requisitos_quantitativos_casos_all():
    aceitas = [c for c in CASOS_ALL if c.categoria == "aceita"]
    rejeitadas = [c for c in CASOS_ALL if c.categoria == "rejeitada"]
    limites = [c for c in CASOS_ALL if c.categoria == "caso_limite"]
    entradas = [c.entrada for c in CASOS_ALL]

    assert len(aceitas) >= 8
    assert len(rejeitadas) >= 8
    assert len(limites) >= 1
    assert len(entradas) == len(set(entradas)), "Todas as cadeias de teste do ALL devem ser distintas."

    all_lba = construir_all()
    for c in CASOS_ALL:
        assert all_lba.validar_alfabeto(c.entrada) is None, f"{c.id} contém símbolo fora de Σ_ALL"
    for c in aceitas + rejeitadas:
        assert len(c.entrada) >= 18, f"{c.id} tem menos de 18 caracteres: {len(c.entrada)}"


@pytest.mark.parametrize("caso", CASOS_ALL, ids=lambda c: c.id)
def test_casos_oficiais_all_e_invariantes_fita_limitada(caso):
    all_lba = construir_all()
    res = all_lba.simular(caso.entrada)
    assert res.accepted == caso.esperado, (caso.id, res.reason)
    assert res.accepted == _oraculo_l2(caso.entrada)
    assert res.writable_cells == len(caso.entrada)

    # Verifica invariante de fita limitada em TODOS os passos do trace
    tamanho_esperado = len(caso.entrada) + 2
    assert len(res.trace) >= 1
    for passo in res.trace:
        assert len(passo.tape) == tamanho_esperado
        assert passo.tape[0] == LEFT_MARKER
        assert passo.tape[-1] == RIGHT_MARKER
        assert 0 <= passo.head < tamanho_esperado
        assert passo.symbol_read == passo.tape[passo.head]


def test_enumeracao_exaustiva_ate_comprimento_7():
    """Valida exaustivamente todas as cadeias em {i, s, :}^k para k = 0..7 (3.280 cadeias)."""
    all_lba = construir_all()
    for k in range(8):
        for tup in itertools.product("is:", repeat=k):
            cadeia = "".join(tup)
            assert all_lba.aceita(cadeia) == _oraculo_l2(cadeia), cadeia


def test_equivalencia_estrutural_e_funcional_all_jff():
    jff_path = DIAGRAMS_DIR / "all.jff"
    assert jff_path.is_file()
    states, initial, finals, transitions = parse_all_jff(jff_path)
    assert states == ALL_STATES
    assert initial == ALL_INITIAL_STATE
    assert finals == ALL_FINAL_STATES
    assert transitions == ALL_TRANSITIONS

    all_from_jff = AutomatoLinearmenteLimitado(
        states=states,
        transitions=transitions,
        initial_state=initial,
        final_states=finals,
    )
    for c in CASOS_ALL:
        assert all_from_jff.aceita(c.entrada) == c.esperado
