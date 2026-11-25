"""Gera a seção LaTeX 05_testes_e_resultados.tex (compatível com artigo twocolumn)
diretamente a partir da execução real do motor formal src/av2.

Uso:
    python docs/relatorio_av2/build_report.py
"""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.av2.all_lba import construir_all
from src.av2.ap import construir_ap
from src.av2.cases import CASOS_ALL, CASOS_AP, CASOS_ERRO_LEXICO, CASOS_INTEGRACAO
from src.av2.glc import construir_glc
from src.av2.pipeline import validar_entrada

OUT_DIR = Path(__file__).resolve().parent


def _tex_escape(s: str) -> str:
    rep = {
        "\\": r"\textbackslash{}",
        "{": r"\{",
        "}": r"\}",
        "#": r"\#",
        "$": r"\$",
        "%": r"\%",
        "&": r"\&",
        "_": r"\_",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
        "δ": r"$\delta$",
        "ε": r"$\varepsilon$",
        "→": r"$\to$",
        "Σ": r"$\Sigma$",
        "—": "---",
    }
    return "".join(rep.get(c, c) for c in s)


def _tex_code(s: str) -> str:
    if not s:
        return r"\texttt{\textquotedbl\textquotedbl}"
    return r"\texttt{" + _tex_escape(s) + "}"


def collect_results() -> dict:
    ap = construir_ap()
    all_lba = construir_all()
    glc = construir_glc()

    ap_rows = []
    for c in CASOS_AP:
        res = ap.simular(c.entrada)
        ap_rows.append((c, res.accepted, len(res.trace) - 1, res.reason))

    all_rows = []
    for c in CASOS_ALL:
        res = all_lba.simular(c.entrada)
        all_rows.append((c, res.accepted, len(res.trace) - 1, res.reason))

    int_rows = []
    for c in CASOS_INTEGRACAO:
        res = validar_entrada(c.entrada)
        int_rows.append((c, res))

    lex_rows = []
    for c in CASOS_ERRO_LEXICO:
        if c.id == "LEX-01":
            res = validar_entrada(c.entrada)
            lex_rows.append((c, res.lexical_error or res.summary))
        else:
            res_all = all_lba.simular(c.entrada)
            lex_rows.append((c, res_all.lexical_error or res_all.reason))

    deriv = glc.derivar_esquerda("p{(()){}}#isisiisis:isisiisis;")
    ap_trace_demo = ap.simular("p{(()){}}#isisiisis:isisiisis;").trace
    all_trace_min = all_lba.simular("i:i").trace
    all_trace_int1 = all_lba.simular("isisiisis:isisiisis").trace
    return {
        "ap": ap_rows,
        "all": all_rows,
        "int": int_rows,
        "lex": lex_rows,
        "deriv": deriv,
        "ap_trace_demo": ap_trace_demo,
        "all_trace_min": all_trace_min,
        "all_trace_int1": all_trace_int1,
    }


def write_latex_section5(data: dict) -> None:
    lines: list[str] = [
        r"\section{Testes Obrigatórios e Análise dos Resultados}",
        "",
        r"Todos os 50 casos exigidos pela atividade~\cite{atividade} foram executados automaticamente via \texttt{pytest} (\textbf{92 testes automatizados da AV2 aprovados}; entregas históricas da AV1 arquivadas em \texttt{archive/av1/}), via CLI (\texttt{python -m src.av2.cli --suite}) e validados em runtime diretamente no simulador oficial do \texttt{JFLAP7.1.jar} (\textbf{418 casos, 0 divergências}). Além das Tabelas~\ref{tab:casos_ap}--\ref{tab:casos_int}, o ALL foi validado exaustivamente contra a especificação matemática $L_2$ em todas as \textbf{3.280 cadeias} de comprimento $0 \dots 7$ sobre $\{\texttt{i}, \texttt{s}, \texttt{:}\}$.",
        "",
        r"\begin{table*}[t]",
        r"\centering",
        r"\caption{Testes isolados do AP (10 aceitas + 10 rejeitadas + 2 casos-limite).}",
        r"\label{tab:casos_ap}",
        r"\scriptsize\setlength{\tabcolsep}{4pt}",
        r"\begin{tabularx}{\textwidth}{@{}llccX@{}}",
        r"\toprule",
        r"ID & Entrada & Esp. & Obt. & Regra verificada \\",
        r"\midrule",
    ]
    for c, obt, _steps, _reason in data["ap"]:
        esp_s = "Aceita" if c.esperado else "Rejeita"
        obt_s = "Aceita" if obt else "Rejeita"
        lines.append(
            f"{_tex_escape(c.id)} & {_tex_code(c.entrada)} & {esp_s} & {obt_s} & {_tex_escape(c.regra_verificada)} \\\\"
        )
    lines += [
        r"\bottomrule",
        r"\end{tabularx}",
        r"\end{table*}",
        "",
        r"\begin{table*}[t]",
        r"\centering",
        r"\caption{Testes isolados do ALL (10 aceitas + 10 rejeitadas + 3 casos-limite).}",
        r"\label{tab:casos_all}",
        r"\scriptsize\setlength{\tabcolsep}{4pt}",
        r"\begin{tabularx}{\textwidth}{@{}llccX@{}}",
        r"\toprule",
        r"ID & Entrada & Esp. & Obt. & Regra verificada \\",
        r"\midrule",
    ]
    for c, obt, _steps, _reason in data["all"]:
        esp_s = "Aceita" if c.esperado else "Rejeita"
        obt_s = "Aceita" if obt else "Rejeita"
        lines.append(
            f"{_tex_escape(c.id)} & {_tex_code(c.entrada)} & {esp_s} & {obt_s} & {_tex_escape(c.regra_verificada)} \\\\"
        )
    lines += [
        r"\bottomrule",
        r"\end{tabularx}",
        r"\end{table*}",
        "",
        r"\begin{table*}[t]",
        r"\centering",
        r"\caption{Testes de integração do pipeline completo (AP $\to$ ALL).}",
        r"\label{tab:casos_int}",
        r"\scriptsize\setlength{\tabcolsep}{4pt}",
        r"\begin{tabularx}{\textwidth}{@{}llccX@{}}",
        r"\toprule",
        r"ID & Entrada & Esp. & Obt. (Parada) & Regra verificada \\",
        r"\midrule",
    ]
    for c, res in data["int"]:
        esp_s = "Aceita" if c.esperado else "Rejeita"
        obt_s = f"{'Aceita' if res.overall_accepted else 'Rejeita'} ({res.stage_stopped})"
        lines.append(
            f"{_tex_escape(c.id)} & {_tex_code(c.entrada)} & {esp_s} & {_tex_escape(obt_s)} & {_tex_escape(c.regra_verificada)} \\\\"
        )
    lines += [
        r"\bottomrule",
        r"\end{tabularx}",
        r"\end{table*}",
        "",
        r"\subsection{Testes com Símbolo Fora do Alfabeto (Erro Léxico)}",
        r"\begin{itemize}",
    ]
    for c, msg in data["lex"]:
        lines.append(
            f"    \\item \\textbf{{{_tex_escape(c.id)}}} --- Entrada: {_tex_code(c.entrada)}. Saída: \\texttt{{{_tex_escape(msg)}}}"
        )
    lines += [
        r"\end{itemize}",
        "",
        r"\subsection{Validação Cruzada no JFLAP 7.1}",
        r"O script \texttt{tests/validate\_av2\_jflap\_runtime.py} executa \texttt{glc.jff}, \texttt{ap.jff} e \texttt{all.jff} diretamente sobre o \texttt{JFLAP7.1.jar}, confirmando:",
        r"\begin{itemize}",
        r"    \item \texttt{glc.jff}: 9 produções carregadas sem erro pelo \texttt{XMLCodec};",
        r"    \item \texttt{ap.jff}: 9 estados, \textbf{0 estados não-determinísticos} (via \texttt{PDANondeterminismDetector}), 34 casos, \textbf{0 divergências};",
        r"    \item \texttt{all.jff}: 11 estados, 384 casos (oficiais + enumeração completa até tamanho 5), com asserção de limites de fita no \texttt{TMSimulator}, \textbf{0 divergências}.",
        r"\end{itemize}",
        "",
        r"\subsection{Rastreamento Passo a Passo (Execuções Reais)}",
        r"As Tabelas~\ref{tab:trace_ap}, \ref{tab:trace_all_min} e \ref{tab:trace_all_int1} apresentam os rastreamentos reais produzidos pelos simuladores em Python sobre o cenário principal \texttt{INT-01} e o caso-limite \texttt{ALL-L03}, evidenciando as operações de pilha e os limites invioláveis \texttt{<} e \texttt{>} da fita.",
        "",
        r"\begin{table*}[t]",
        r"\centering",
        r"\caption{Rastreamento completo do AP sobre \texttt{INT-01} (\texttt{p\{(())\{\}\}\#isisiisis:isisiisis;}, 31 passos).}",
        r"\label{tab:trace_ap}",
        r"\scriptsize\setlength{\tabcolsep}{4pt}",
        r"\begin{tabularx}{\textwidth}{@{}rllllX@{}}",
        r"\toprule",
        r"Passo & Estado & Pos & Pilha & Restante & Transição \\",
        r"\midrule",
    ]
    for s in data["ap_trace_demo"]:
        rem = s.remaining_input if s.remaining_input else "ε"
        tr = s.transition or "(inicial)"
        lines.append(
            f"{s.step} & {_tex_code(s.state)} & {s.position} & {_tex_code(s.stack)} & {_tex_code(rem)} & {_tex_code(tr)} \\\\"
        )
    lines += [
        r"\bottomrule",
        r"\end{tabularx}",
        r"\end{table*}",
        "",
        r"\begin{table*}[t]",
        r"\centering",
        r"\caption{Rastreamento completo do ALL sobre o caso-limite \texttt{ALL-L03} (\texttt{i:i}, 9 passos).}",
        r"\label{tab:trace_all_min}",
        r"\scriptsize\setlength{\tabcolsep}{5pt}",
        r"\begin{tabularx}{\textwidth}{@{}rllllX@{}}",
        r"\toprule",
        r"Passo & Estado & Cabeçote & Lido & Fita (cabeçote em \texttt{[ ]}) & Transição \\",
        r"\midrule",
    ]
    for s in data["all_trace_min"]:
        fita = s.tape[: s.head] + f"[{s.tape[s.head]}]" + s.tape[s.head + 1 :]
        tr = s.transition or "(inicial)"
        lines.append(
            f"{s.step} & {_tex_code(s.state)} & {s.head} & {_tex_code(s.symbol_read)} & {_tex_code(fita)} & {_tex_code(tr)} \\\\"
        )
    lines += [
        r"\bottomrule",
        r"\end{tabularx}",
        r"\end{table*}",
        "",
        r"\begin{table*}[t]",
        r"\centering",
        r"\caption{Amostra do rastreamento do ALL sobre \texttt{INT-01} (fatia \texttt{isisiisis:isisiisis}, 21 células, 201 passos: 1º ciclo e varredura final).}",
        r"\label{tab:trace_all_int1}",
        r"\scriptsize\setlength{\tabcolsep}{4pt}",
        r"\begin{tabularx}{\textwidth}{@{}rllllX@{}}",
        r"\toprule",
        r"Passo & Estado & Cab. & Lido & Fita (cabeçote em \texttt{[ ]}) & Transição \\",
        r"\midrule",
    ]
    amostra = list(data["all_trace_int1"][:23]) + list(data["all_trace_int1"][189:])
    for idx_s, s in enumerate(amostra):
        if idx_s == 23:
            lines.append(r"\multicolumn{6}{c}{\textit{... ciclos intermediários de casamento (passos 23 a 188) ...}} \\")
        fita = s.tape[: s.head] + f"[{s.tape[s.head]}]" + s.tape[s.head + 1 :]
        tr = s.transition or "(inicial)"
        lines.append(
            f"{s.step} & {_tex_code(s.state)} & {s.head} & {_tex_code(s.symbol_read)} & {_tex_code(fita)} & {_tex_code(tr)} \\\\"
        )
    lines += [
        r"\bottomrule",
        r"\end{tabularx}",
        r"\end{table*}",
    ]

    (OUT_DIR / "secoes" / "05_testes_e_resultados.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    data = collect_results()
    write_latex_section5(data)
    print("Gerado com sucesso: secoes/05_testes_e_resultados.tex")


if __name__ == "__main__":
    main()
