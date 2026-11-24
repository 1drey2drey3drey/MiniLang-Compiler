"""Testes de integração (3 cenários), erro léxico, CLI e endpoints da API Web da AV2."""

from __future__ import annotations

import pytest

from src.av2.all_lba import construir_all
from src.av2.cases import CASOS_ERRO_LEXICO, CASOS_INTEGRACAO
from src.av2.cli import main as cli_main
from src.av2.pipeline import validar_entrada
from src.av2.web import dispatch_api


@pytest.mark.parametrize("caso", CASOS_INTEGRACAO, ids=lambda c: c.id)
def test_cenarios_integracao_obrigatorios(caso):
    assert len(caso.entrada) >= 18
    res = validar_entrada(caso.entrada)
    assert res.overall_accepted == caso.esperado
    assert res.stage_stopped == caso.etapa_parada_esperada
    assert res.lexical_error is None
    assert res.ap_result is not None

    if caso.etapa_parada_esperada == "AP":
        assert res.ap_result.accepted is False
        assert res.all_result is None, "ALL não pode ser executado quando o AP rejeita."
        assert res.derivation is None
    elif caso.etapa_parada_esperada == "ALL":
        assert res.ap_result.accepted is True
        assert res.derivation is not None
        assert res.all_result is not None and res.all_result.accepted is False
    elif caso.etapa_parada_esperada == "CONCLUIDO":
        assert res.ap_result.accepted is True
        assert res.derivation is not None
        assert res.all_result is not None and res.all_result.accepted is True


def test_erros_lexicos_fora_do_alfabeto():
    c_pipe, c_all = CASOS_ERRO_LEXICO
    res_pipe = validar_entrada(c_pipe.entrada)
    assert res_pipe.overall_accepted is False
    assert res_pipe.stage_stopped == "LEXICO"
    assert res_pipe.lexical_error is not None
    assert "'@'" in res_pipe.lexical_error
    assert res_pipe.ap_result is None and res_pipe.all_result is None

    res_all = construir_all().simular(c_all.entrada)
    assert res_all.accepted is False
    assert res_all.lexical_error is not None
    assert "'$'" in res_all.lexical_error


def test_cli_suite_e_modos(capsys):
    assert cli_main(["--suite"]) == 0
    out = capsys.readouterr().out
    assert "50/50 casos aprovados, 0 divergências" in out

    assert cli_main(["p{(()){}}#isisiisis:isisiisis;"]) == 0
    assert cli_main(["p{(()){}#isisiisis:isisiisis;"]) == 1
    assert cli_main(["--mode", "all", "isisiisis:isisiisis"]) == 0


def test_api_web_endpoints():
    status, spec = dispatch_api("GET", "/api/spec")
    assert status == 200
    assert spec["ap"]["state_count"] == 9
    assert spec["all"]["state_count"] == 11

    status, suite = dispatch_api("GET", "/api/tests/run")
    assert status == 200
    assert suite["failed"] == 0
    assert suite["total"] == 50

    status, pipe = dispatch_api("POST", "/api/validate/pipeline", {"input": "p{(()){}}#isisiisis:isisiisis;"})
    assert status == 200
    assert pipe["overall_accepted"] is True
    assert pipe["all_result"]["writable_cells"] == 19

    status, ap_iso = dispatch_api("POST", "/api/validate/ap", {"input": "p{}#i:i;"})
    assert status == 200
    assert ap_iso["ap_result"]["accepted"] is True
    assert len(ap_iso["derivation"]) > 0

    status, all_iso = dispatch_api("POST", "/api/validate/all", {"input": "isisiisis:isisiissi"})
    assert status == 200
    assert all_iso["all_result"]["accepted"] is False

    # Testa compilação direta de código-fonte MiniLang (MiniLexer AV1 -> AP -> ALL)
    presets = {p["id"]: p["code"] for p in spec["minilang_presets"]}
    st, r_ok = dispatch_api("POST", "/api/compile/minilang", {"source": presets["ok"]})
    assert st == 200 and r_ok["lexical_ok"] is True
    assert r_ok["formal_string"] == "p{(()){}}#isisiisis:isisiisis;"
    assert r_ok["pipeline"]["overall_accepted"] is True

    st, r_syn = dispatch_api("POST", "/api/compile/minilang", {"source": presets["syntax_err"]})
    assert st == 200 and r_syn["pipeline"]["stage_stopped"] == "AP"
    assert r_syn["pipeline"]["all_result"] is None

    st, r_sem = dispatch_api("POST", "/api/compile/minilang", {"source": presets["semantic_err"]})
    assert st == 200 and r_sem["pipeline"]["stage_stopped"] == "ALL"

    st, r_lex = dispatch_api("POST", "/api/compile/minilang", {"source": presets["lexical_err"]})
    assert st == 200 and r_lex["lexical_ok"] is False
    assert r_lex["pipeline"]["stage_stopped"] == "LEXICO"

    # Casos adversários da auditoria de erros/avisos no front-end MiniLang
    st, r_float = dispatch_api("POST", "/api/compile/minilang", {"source": "program x { fn f(int a); f(3.14); }"})
    assert st == 200 and r_float["lexical_ok"] is False and "3.14" in r_float["lexical_error"]

    st, r_var = dispatch_api("POST", "/api/compile/minilang", {"source": "program x { int y = 1; fn f(int a); f(y); }"})
    assert st == 200 and r_var["pipeline"]["overall_accepted"] is True

    st, r_semi = dispatch_api("POST", "/api/compile/minilang", {"source": "program x { fn f(int a); f(10);; }"})
    assert st == 200 and r_semi["pipeline"]["stage_stopped"] == "AP"

    st, r_unclosed = dispatch_api("POST", "/api/compile/minilang", {"source": "program x { fn f(int a; f(10); }"})
    assert st == 200 and r_unclosed["pipeline"]["stage_stopped"] == "AP"

    # Confirma que todos os 50 casos da lauda possuem código MiniLang sintetizado coerente
    for row in suite["rows"]:
        code = row["minilang_code"]
        assert isinstance(code, str) and len(code.strip()) > 0
        st_c, comp = dispatch_api("POST", "/api/compile/minilang", {"source": code})
        assert st_c == 200
        if row["modulo"] == "ERRO_LEXICO":
            assert comp["lexical_ok"] is False
        elif row["modulo"] == "AP":
            ap_r = comp["pipeline"]["ap_result"]
            assert ap_r is not None and ap_r["accepted"] == row["esperado"]
        elif row["modulo"] == "ALL":
            if row["esperado"]:
                assert comp["pipeline"]["overall_accepted"] is True
                assert comp["pipeline"]["semantic_slice"] == row["entrada"]
            else:
                assert comp["pipeline"]["overall_accepted"] is False
        elif row["modulo"] == "INTEGRACAO":
            assert comp["pipeline"]["overall_accepted"] == row["esperado"]
            assert comp["pipeline"]["stage_stopped"] == row["etapa_parada_esperada"]
