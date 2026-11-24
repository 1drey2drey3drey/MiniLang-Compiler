"""Testes formais do Autômato de Pilha Determinístico (AP — 9 estados) e ap.jff."""

from __future__ import annotations

import pytest

from src.av2.ap import AutomatoPilha, construir_ap
from src.av2.cases import CASOS_AP
from src.av2.jflap_io import DIAGRAMS_DIR, parse_ap_jff
from src.av2.spec import AP_FINAL_STATES, AP_INITIAL_STATE, AP_STATES, AP_TRANSITIONS


def test_requisitos_estruturais_ap():
    ap = construir_ap()
    assert len(ap.states) >= 8, "Lauda exige no mínimo 8 estados no AP."
    assert len(ap.states) == 9
    assert ap.initial_state == AP_INITIAL_STATE
    assert ap.final_states == frozenset(AP_FINAL_STATES)


def test_requisitos_quantitativos_casos_ap():
    aceitas = [c for c in CASOS_AP if c.categoria == "aceita"]
    rejeitadas = [c for c in CASOS_AP if c.categoria == "rejeitada"]
    limites = [c for c in CASOS_AP if c.categoria == "caso_limite"]
    entradas = [c.entrada for c in CASOS_AP]

    assert len(aceitas) >= 8
    assert len(rejeitadas) >= 8
    assert len(limites) >= 1
    assert len(entradas) == len(set(entradas)), "Todas as cadeias de teste do AP devem ser distintas."

    ap = construir_ap()
    for c in CASOS_AP:
        assert ap.validar_alfabeto(c.entrada) is None, f"{c.id} contém símbolo fora de Σ_AP"
    for c in aceitas + rejeitadas:
        assert len(c.entrada) >= 18, f"{c.id} tem menos de 18 caracteres: {len(c.entrada)}"


@pytest.mark.parametrize("caso", CASOS_AP, ids=lambda c: c.id)
def test_casos_oficiais_ap(caso):
    ap = construir_ap()
    res = ap.simular(caso.entrada)
    assert res.accepted == caso.esperado, (caso.id, res.reason)
    assert res.lexical_error is None
    assert len(res.trace) >= 1
    assert res.trace[0].state == AP_INITIAL_STATE
    assert res.trace[0].position == 0
    assert res.trace[0].stack == "Z"
    if caso.esperado:
        assert res.final_position == len(caso.entrada)
        assert res.final_state in AP_FINAL_STATES
        assert res.final_stack == "Z"


def test_equivalencia_estrutural_e_funcional_ap_jff():
    jff_path = DIAGRAMS_DIR / "ap.jff"
    assert jff_path.is_file()
    states, initial, finals, transitions = parse_ap_jff(jff_path)
    assert states == AP_STATES
    assert initial == AP_INITIAL_STATE
    assert finals == AP_FINAL_STATES
    assert transitions == AP_TRANSITIONS

    ap_from_jff = AutomatoPilha(
        states=states,
        transitions=transitions,
        initial_state=initial,
        final_states=finals,
    )
    for c in CASOS_AP:
        assert ap_from_jff.aceita(c.entrada) == c.esperado
