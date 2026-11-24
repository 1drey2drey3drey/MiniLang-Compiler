"""Interface de linha de comando (CLI) da AV2 — MiniLang-Compiler.

Exemplos:
    python -m src.av2.cli "p{(()){}}#isisiisis:isisiisis;"
    python -m src.av2.cli --mode ap "p{(()){}}#isisi:isisi;"
    python -m src.av2.cli --mode all "isisiisis:isisiisis"
    python -m src.av2.cli --suite
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

from .all_lba import ALLResult, construir_all
from .ap import APResult, construir_ap
from .cases import CASOS_ALL, CASOS_AP, CASOS_ERRO_LEXICO, CASOS_INTEGRACAO
from .glc import DerivationStep, construir_glc
from .pipeline import PipelineResult, validar_entrada


def _print_ap_trace(res: APResult, max_rows: int | None = None) -> None:
    print(f"\n[ETAPA 1 — AP (DPDA, 9 estados)] Decisão: {'ACEITA' if res.accepted else 'REJEITA'}")
    print(f"Motivo: {res.reason}")
    if not res.trace:
        return
    print(f"\n{'Passo':>5} | {'Estado':<6} | {'Pos':>3} | {'Pilha (topo←)':<14} | {'Restante':<32} | Transição")
    print("-" * 105)
    rows = res.trace if max_rows is None else res.trace[:max_rows]
    for step in rows:
        rem = step.remaining_input if step.remaining_input else "ε"
        tr = step.transition or "(configuração inicial)"
        print(f"{step.step:>5} | {step.state:<6} | {step.position:>3} | {step.stack:<14} | {rem:<32} | {tr}")


def _print_derivation(steps: Iterable[DerivationStep]) -> None:
    print("\n[DERIVAÇÃO MAIS À ESQUERDA — GLC]")
    for s in steps:
        regra = f"  [{s.rule_applied}]" if s.rule_applied else ""
        seta = "  " if s.step == 0 else "⇒ "
        print(f"  {s.step:>2}. {seta}{s.sentential_form}{regra}")


def _print_all_trace(res: ALLResult, max_rows: int | None = None) -> None:
    print(f"\n[ETAPA 2 — ALL (D-LBA, 11 estados)] Decisão: {'ACEITA' if res.accepted else 'REJEITA'}")
    print(
        f"Fita limitada: {res.writable_cells} células graváveis + 2 bordas fixas ('<' e '>') "
        f"| Total de passos: {len(res.trace) - 1 if res.trace else 0}"
    )
    print(f"Motivo: {res.reason}")
    if not res.trace:
        return
    print(f"\n{'Passo':>5} | {'Estado':<6} | {'Cab':>3} | {'Lido':<4} | {'Fita (cabeçote entre [ ])':<34} | Transição")
    print("-" * 108)
    rows = res.trace if max_rows is None else res.trace[:max_rows]
    for step in rows:
        fita_marcada = (
            step.tape[: step.head] + f"[{step.tape[step.head]}]" + step.tape[step.head + 1 :]
        )
        tr = step.transition or "(configuração inicial)"
        print(
            f"{step.step:>5} | {step.state:<6} | {step.head:>3} | {step.symbol_read:<4} | "
            f"{fita_marcada:<34} | {tr}"
        )


def _print_pipeline(res: PipelineResult, show_derivation: bool, max_rows: int | None) -> None:
    print("=" * 108)
    print(f"ENTRADA ({len(res.input_str)} chars): {res.input_str!r}")
    print(f"DECISÃO GLOBAL : {'ACEITA' if res.overall_accepted else 'REJEITADA'} (parada: {res.stage_stopped})")
    print(f"RESUMO         : {res.summary}")
    print("=" * 108)
    if res.lexical_error:
        print(f"\n[ERRO LÉXICO] {res.lexical_error}")
        return
    if res.ap_result:
        _print_ap_trace(res.ap_result, max_rows=max_rows)
    if show_derivation and res.derivation:
        _print_derivation(res.derivation)
    if res.all_result:
        print(f"\nFatia semântica enviada ao ALL (entre '#' e ';'): {res.semantic_slice!r}")
        _print_all_trace(res.all_result, max_rows=max_rows)
    else:
        print("\n[ETAPA 2 — ALL] Não executada (entrada rejeitada na Etapa 1).")


def run_suite() -> int:
    """Executa toda a bateria obrigatória da lauda e imprime a tabela consolidada."""
    ap = construir_ap()
    all_lba = construir_all()
    falhas = 0

    def header(titulo: str) -> None:
        print(f"\n=== {titulo} ===")
        print(f"{'ID':<8} | {'Tam':>3} | {'Esp':<7} | {'Obt':<7} | {'OK':<4} | {'Entrada':<32} | Regra verificada")
        print("-" * 120)

    header("AP ISOLADO (10 aceitas + 10 rejeitadas + 2 casos-limite)")
    for c in CASOS_AP:
        res = ap.simular(c.entrada)
        ok = res.accepted == c.esperado
        if not ok:
            falhas += 1
        print(
            f"{c.id:<8} | {len(c.entrada):>3} | {'ACEITA' if c.esperado else 'REJEITA':<7} | "
            f"{'ACEITA' if res.accepted else 'REJEITA':<7} | {'OK' if ok else 'ERRO':<4} | "
            f"{c.entrada:<32} | {c.regra_verificada}"
        )

    header("ALL ISOLADO (10 aceitas + 10 rejeitadas + 3 casos-limite)")
    for c in CASOS_ALL:
        res = all_lba.simular(c.entrada)
        ok = res.accepted == c.esperado
        if not ok:
            falhas += 1
        print(
            f"{c.id:<8} | {len(c.entrada):>3} | {'ACEITA' if c.esperado else 'REJEITA':<7} | "
            f"{'ACEITA' if res.accepted else 'REJEITA':<7} | {'OK' if ok else 'ERRO':<4} | "
            f"{c.entrada:<32} | {c.regra_verificada}"
        )

    header("INTEGRAÇÃO (3 CENÁRIOS OBRIGATÓRIOS)")
    for c in CASOS_INTEGRACAO:
        res = validar_entrada(c.entrada)
        ok = (res.overall_accepted == c.esperado) and (res.stage_stopped == c.etapa_parada_esperada)
        if not ok:
            falhas += 1
        print(
            f"{c.id:<8} | {len(c.entrada):>3} | {'ACEITA' if c.esperado else 'REJEITA':<7} | "
            f"{'ACEITA' if res.overall_accepted else 'REJEITA':<7} | {'OK' if ok else 'ERRO':<4} | "
            f"{c.entrada:<32} | [{res.stage_stopped}] {c.regra_verificada}"
        )

    print("\n=== TESTES DE ERRO LÉXICO (SÍMBOLO FORA DO ALFABETO) ===")
    for c in CASOS_ERRO_LEXICO:
        if c.id == "LEX-01":
            res = validar_entrada(c.entrada)
            ok = (not res.overall_accepted) and (res.stage_stopped == "LEXICO") and bool(res.lexical_error)
            msg = res.lexical_error or ""
        else:
            res_all = all_lba.simular(c.entrada)
            ok = (not res_all.accepted) and bool(res_all.lexical_error)
            msg = res_all.lexical_error or ""
        if not ok:
            falhas += 1
        print(f"  {c.id} ({'OK' if ok else 'ERRO'}) | Entrada: {c.entrada!r}")
        print(f"      Mensagem registrada: {msg}")

    total = len(CASOS_AP) + len(CASOS_ALL) + len(CASOS_INTEGRACAO) + len(CASOS_ERRO_LEXICO)
    print(f"\nResumo final: {total - falhas}/{total} casos aprovados, {falhas} divergências.")
    return 0 if falhas == 0 else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="MiniLang-Compiler (AV2) — Validador em duas etapas (GLC/AP + LSC/ALL)"
    )
    parser.add_argument("cadeia", nargs="?", help="Cadeia formal de entrada")
    parser.add_argument(
        "--mode",
        choices=("pipeline", "ap", "all"),
        default="pipeline",
        help="Modo de execução: pipeline completo (padrão), ap isolado ou all isolado",
    )
    parser.add_argument("--file", help="Lê cadeias de um arquivo texto (uma por linha, ignora '# ' comentários)")
    parser.add_argument("--suite", action="store_true", help="Executa toda a bateria de testes obrigatórios da lauda")
    parser.add_argument("--no-derivation", action="store_true", help="Oculta a derivação passo a passo da GLC")
    parser.add_argument("--max-trace", type=int, default=None, help="Limita linhas impressas no trace")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.suite:
        return run_suite()

    entradas: list[str] = []
    if args.file:
        linhas = Path(args.file).read_text(encoding="utf-8").splitlines()
        entradas = [ln.strip() for ln in linhas if ln.strip() and not ln.strip().startswith("//")]
    elif args.cadeia is not None:
        entradas = [args.cadeia]
    else:
        entradas = [input("Digite a cadeia formal da AV2: ").strip()]

    exit_code = 0
    for cadeia in entradas:
        if args.mode == "pipeline":
            res = validar_entrada(cadeia)
            _print_pipeline(res, show_derivation=not args.no_derivation, max_rows=args.max_trace)
            if not res.overall_accepted:
                exit_code = 1
        elif args.mode == "ap":
            ap = construir_ap()
            res_ap = ap.simular(cadeia)
            _print_ap_trace(res_ap, max_rows=args.max_trace)
            if res_ap.accepted and not args.no_derivation:
                _print_derivation(construir_glc().derivar_esquerda(cadeia))
            if not res_ap.accepted:
                exit_code = 1
        else:
            all_lba = construir_all()
            res_all = all_lba.simular(cadeia)
            _print_all_trace(res_all, max_rows=args.max_trace)
            if not res_all.accepted:
                exit_code = 1
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
