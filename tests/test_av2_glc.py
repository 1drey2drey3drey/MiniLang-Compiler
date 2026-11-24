"""Testes formais da GLC (Etapa 1) e validação passo a passo das derivações."""

from __future__ import annotations

import pytest

from src.av2.ap import construir_ap
from src.av2.cases import CASOS_AP
from src.av2.glc import construir_glc
from src.av2.spec import GLC_NON_TERMINALS, GLC_PRODUCTIONS, GLC_START_SYMBOL, GLC_TERMINALS


def test_estrutura_glc():
    glc = construir_glc()
    assert glc.start_symbol == GLC_START_SYMBOL == "S"
    assert set(glc.non_terminals) == set(GLC_NON_TERMINALS)
    assert set(glc.terminals) == set(GLC_TERMINALS)
    assert len(glc.productions) == len(GLC_PRODUCTIONS) == 9


@pytest.mark.parametrize("caso", [c for c in CASOS_AP if c.esperado], ids=lambda c: c.id)
def test_derivacao_esquerda_som_e_completa(caso):
    """Confirma que cada passo da derivação substitui exatamente o não-terminal mais à esquerda."""
    glc = construir_glc()
    prod_by_id = {p.id: p for p in glc.productions}
    nt_set = set(glc.non_terminals)

    steps = glc.derivar_esquerda(caso.entrada)
    assert steps[0].sentential_form == glc.start_symbol
    assert steps[-1].sentential_form == caso.entrada

    for prev, curr in zip(steps, steps[1:]):
        assert curr.rule_id in prod_by_id
        prod = prod_by_id[curr.rule_id]
        # Encontra o primeiro não-terminal na forma sentencial anterior
        idx = next(i for i, ch in enumerate(prev.sentential_form) if ch in nt_set)
        assert prev.sentential_form[idx] == prod.lhs
        esperada = (
            prev.sentential_form[:idx]
            + "".join(prod.rhs)
            + prev.sentential_form[idx + 1 :]
        )
        assert curr.sentential_form == esperada


@pytest.mark.parametrize("caso", CASOS_AP, ids=lambda c: c.id)
def test_equivalencia_glc_e_ap_nos_casos_oficiais(caso):
    glc = construir_glc()
    ap = construir_ap()
    assert glc.aceita(caso.entrada) == caso.esperado
    assert ap.aceita(caso.entrada) == glc.aceita(caso.entrada)
