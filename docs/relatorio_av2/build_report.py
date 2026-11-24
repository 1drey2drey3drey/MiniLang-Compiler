"""Gera a seção LaTeX 05_testes_e_resultados.tex e o relatório HTML imprimível (PDF)
diretamente a partir da execução real do motor formal src/av2.

Uso:
    python docs/relatorio_av2/build_report.py
"""

from __future__ import annotations

import html
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.av2.all_lba import construir_all
from src.av2.ap import construir_ap
from src.av2.cases import CASOS_ALL, CASOS_AP, CASOS_ERRO_LEXICO, CASOS_INTEGRACAO
from src.av2.glc import construir_glc
from src.av2.pipeline import validar_entrada
from src.av2.spec import ALL_TRANSITIONS, AP_TRANSITIONS, GLC_PRODUCTIONS

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

    deriv = glc.derivar_esquerda("p{(()){}}#isisi:isisi;")
    return {
        "ap": ap_rows,
        "all": all_rows,
        "int": int_rows,
        "lex": lex_rows,
        "deriv": deriv,
    }


def write_latex_section5(data: dict) -> None:
    lines: list[str] = [
        r"\chapter{Testes Obrigatórios e Análise dos Resultados}",
        "",
        r"Todos os testes exigidos pela atividade~\cite{atividade} foram executados automaticamente via \texttt{pytest} (227 testes aprovados: 135 da AV1 + 92 da AV2), via CLI (\texttt{python -m src.av2.cli --suite}) e validados em runtime diretamente no simulador oficial do \texttt{JFLAP7.1.jar} (\textbf{418 casos, 0 divergências}). Além das tabelas abaixo, o ALL foi validado exaustivamente contra a especificação matemática $L_2$ em todas as \textbf{3.280 cadeias} de comprimento $0 \dots 7$ sobre $\{\texttt{i}, \texttt{s}, \texttt{:}\}$.",
        "",
        r"\section{Testes Isolados do AP (10 aceitas + 10 rejeitadas + 2 casos-limite)}",
        r"{\scriptsize",
        r"\begin{longtable}{@{}llccp{6.4cm}@{}}",
        r"\toprule",
        r"ID & Entrada & Esp. & Obt. & Regra verificada \\",
        r"\midrule",
        r"\endhead",
    ]
    for c, obt, _steps, _reason in data["ap"]:
        esp_s = "Aceita" if c.esperado else "Rejeita"
        obt_s = "Aceita" if obt else "Rejeita"
        lines.append(
            f"{_tex_escape(c.id)} & {_tex_code(c.entrada)} & {esp_s} & {obt_s} & {_tex_escape(c.regra_verificada)} \\\\"
        )
    lines += [
        r"\bottomrule",
        r"\end{longtable}}",
        "",
        r"\section{Testes Isolados do ALL (10 aceitas + 10 rejeitadas + 3 casos-limite)}",
        r"{\scriptsize",
        r"\begin{longtable}{@{}llccp{6.6cm}@{}}",
        r"\toprule",
        r"ID & Entrada & Esp. & Obt. & Regra verificada \\",
        r"\midrule",
        r"\endhead",
    ]
    for c, obt, _steps, _reason in data["all"]:
        esp_s = "Aceita" if c.esperado else "Rejeita"
        obt_s = "Aceita" if obt else "Rejeita"
        lines.append(
            f"{_tex_escape(c.id)} & {_tex_code(c.entrada)} & {esp_s} & {obt_s} & {_tex_escape(c.regra_verificada)} \\\\"
        )
    lines += [
        r"\bottomrule",
        r"\end{longtable}}",
        "",
        r"\section{Testes de Integração (Fluxo Completo AP $\to$ ALL)}",
        r"{\scriptsize",
        r"\begin{longtable}{@{}llccp{5.4cm}@{}}",
        r"\toprule",
        r"ID & Entrada & Esp. & Obt. (Parada) & Regra verificada \\",
        r"\midrule",
        r"\endhead",
    ]
    for c, res in data["int"]:
        esp_s = "Aceita" if c.esperado else "Rejeita"
        obt_s = f"{'Aceita' if res.overall_accepted else 'Rejeita'} ({res.stage_stopped})"
        lines.append(
            f"{_tex_escape(c.id)} & {_tex_code(c.entrada)} & {esp_s} & {_tex_escape(obt_s)} & {_tex_escape(c.regra_verificada)} \\\\"
        )
    lines += [
        r"\bottomrule",
        r"\end{longtable}}",
        "",
        r"\section{Testes com Símbolo Fora do Alfabeto (Erro Léxico)}",
        r"\begin{itemize}",
    ]
    for c, msg in data["lex"]:
        lines.append(
            f"    \\item \\textbf{{{_tex_escape(c.id)}}} --- Entrada: {_tex_code(c.entrada)}. Mensagem exibida: \\texttt{{{_tex_escape(msg)}}}"
        )
    lines += [
        r"\end{itemize}",
        "",
        r"\section{Validação Cruzada no JFLAP 7.1}",
        r"O script \texttt{tests/validate\_av2\_jflap\_runtime.py} executa \texttt{glc.jff}, \texttt{ap.jff} e \texttt{all.jff} diretamente sobre o \texttt{JFLAP7.1.jar}, confirmando:",
        r"\begin{itemize}",
        r"    \item \texttt{glc.jff}: 9 produções carregadas sem erro pelo \texttt{XMLCodec};",
        r"    \item \texttt{ap.jff}: 9 estados, \textbf{0 estados não-determinísticos} (via \texttt{PDANondeterminismDetector}), 34 casos, \textbf{0 divergências};",
        r"    \item \texttt{all.jff}: 11 estados, 384 casos (oficiais + enumeração completa até tamanho 5), com asserção de limites de fita no \texttt{TMSimulator}, \textbf{0 divergências}.",
        r"\end{itemize}",
    ]

    (OUT_DIR / "secoes" / "05_testes_e_resultados.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_html_report(data: dict) -> None:
    def esc(s: str) -> str:
        return html.escape(s)

    def render_table(rows: list[tuple]) -> str:
        out = []
        for c, obt, steps, _reason in rows:
            cls = "ok" if obt == c.esperado else "err"
            ent = esc(c.entrada) if c.entrada else '"" (vazia)'
            out.append(
                f"<tr><td><code>{esc(c.id)}</code></td><td><code>{ent}</code></td>"
                f"<td>{len(c.entrada)}</td><td>{'Aceita' if c.esperado else 'Rejeita'}</td>"
                f"<td class='{cls}'>{'Aceita' if obt else 'Rejeita'}</td>"
                f"<td>{steps}</td><td>{esc(c.regra_verificada)}</td></tr>"
            )
        return "\n".join(out)

    int_html = []
    for c, res in data["int"]:
        ap_s = "Aceita" if (res.ap_result and res.ap_result.accepted) else "Rejeita"
        all_s = (
            "Não executado"
            if res.all_result is None
            else ("Aceita" if res.all_result.accepted else "Rejeita")
        )
        int_html.append(
            f"<tr><td><code>{esc(c.id)}</code></td><td><code>{esc(c.entrada)}</code></td>"
            f"<td>{len(c.entrada)}</td><td>{ap_s}</td><td>{all_s}</td>"
            f"<td><strong>{'Aceita' if res.overall_accepted else 'Rejeita'}</strong> ({esc(res.stage_stopped)})</td>"
            f"<td>{esc(c.regra_verificada)}</td></tr>"
        )

    lex_html = "\n".join(
        f"<li><strong>{esc(c.id)}</strong> — Entrada: <code>{esc(c.entrada)}</code><br>"
        f"Mensagem exibida: <code>{esc(msg)}</code></li>"
        for c, msg in data["lex"]
    )

    deriv_html = "\n".join(
        f"<tr><td>{d.step}</td><td><code>{esc(d.sentential_form)}</code></td>"
        f"<td><code>{esc(d.rule_applied or '')}</code></td></tr>"
        for d in data["deriv"]
    )

    ap_tr_html = "\n".join(
        f"<tr><td><code>{t.from_state}</code></td><td><code>{esc(t.read or 'ε')}</code></td>"
        f"<td><code>{esc(t.pop)}</code></td><td><code>{t.to_state}</code></td>"
        f"<td><code>{esc(t.push or 'ε')}</code></td></tr>"
        for t in AP_TRANSITIONS
    )

    all_tr_html = "\n".join(
        f"<tr><td><code>{t.from_state}</code></td><td><code>{esc(t.read)}</code></td>"
        f"<td><code>{t.to_state}</code></td><td><code>{esc(t.write)}</code></td>"
        f"<td><code>{t.move}</code></td></tr>"
        for t in ALL_TRANSITIONS
    )

    prod_html = "\n".join(
        f"<li><code>{p.id}: {esc(str(p))}</code></li>" for p in GLC_PRODUCTIONS
    )

    doc = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <title>Relatório Técnico — MiniLang-Compiler (AV2 de LFA)</title>
  <style>
    @page {{ size: A4; margin: 22mm 18mm 20mm 25mm; }}
    body {{ font-family: Georgia, "Times New Roman", serif; color: #111827; line-height: 1.55; max-width: 900px; margin: 0 auto; padding: 24px; }}
    .no-print {{ background: #eff6ff; border: 1px solid #93c5fd; padding: 12px 16px; border-radius: 8px; margin-bottom: 24px; display: flex; justify-content: space-between; align-items: center; font-family: system-ui, sans-serif; font-size: 14px; }}
    .no-print button {{ background: #2563eb; color: #fff; border: none; padding: 8px 14px; border-radius: 6px; cursor: pointer; font-weight: 600; }}
    .cover {{ text-align: center; padding: 64px 20px 48px; border-bottom: 2px solid #1e3a8a; page-break-after: always; }}
    .cover h1 {{ font-size: 28px; color: #1e3a8a; margin: 28px 0 8px; }}
    .cover h2 {{ font-size: 18px; font-weight: normal; color: #374151; }}
    h1, h2, h3 {{ font-family: system-ui, -apple-system, sans-serif; color: #1e3a8a; }}
    h2 {{ border-bottom: 1px solid #cbd5e1; padding-bottom: 4px; margin-top: 28px; page-break-after: avoid; }}
    code {{ font-family: "Cascadia Code", Consolas, monospace; font-size: 0.9em; background: #f1f5f9; padding: 1px 4px; border-radius: 3px; }}
    table {{ width: 100%; border-collapse: collapse; margin: 12px 0 18px; font-size: 12.5px; }}
    th, td {{ border: 1px solid #cbd5e1; padding: 5px 7px; text-align: left; vertical-align: top; }}
    th {{ background: #f1f5f9; font-family: system-ui, sans-serif; }}
    .ok {{ color: #15803d; font-weight: 700; }}
    .err {{ color: #b91c1c; font-weight: 700; }}
    .proof {{ background: #f8fafc; border-left: 4px solid #2563eb; padding: 10px 14px; margin: 12px 0; }}
    @media print {{ .no-print {{ display: none; }} body {{ padding: 0; max-width: none; }} }}
  </style>
</head>
<body>
  <div class="no-print">
    <span>Versão pronta para exportação direta em PDF (ou compile <code>docs/relatorio_av2/main.tex</code> no Overleaf).</span>
    <button type="button" onclick="window.print()">Salvar / Imprimir PDF</button>
  </div>

  <section class="cover">
    <p><strong>CENTRO UNIVERSITÁRIO DO ESTADO DO PARÁ — CESUPA</strong><br>Curso de Ciência da Computação — Turma CC6NA</p>
    <h1>MiniLang-Compiler (AV2)</h1>
    <h2>Reconhecimento de Linguagens em Duas Etapas com Autômato de Pilha (GLC) e Autômato Linearmente Limitado (LSC)</h2>
    <p style="margin-top:48px;"><strong>Integrantes:</strong><br>Andrey Lourival Andrade Garcia<br>Igor Cecim Vilhena</p>
    <p style="margin-top:24px;"><strong>Disciplina:</strong> Linguagens Formais e Autômatos<br><strong>Docente:</strong> Prof. Daniel Leal Souza</p>
    <p style="margin-top:64px;">Belém — PA • 25 de novembro de 2026</p>
  </section>

  <h2>1. Problema, Originalidade e Fundamentação na Hierarquia de Chomsky</h2>
  <p>O <strong>MiniLang-Compiler (AV2)</strong> evolui o analisador léxico <code>MiniLang-MiniLexer</code> (AV1, Tipo 3 / Regular) para um validador em duas etapas sobre a linguagem educacional <code>MiniLang</code>:</p>
  <ol>
    <li><strong>Etapa 1 — MiniParser (Tipo 2 / LLC não-regular):</strong> Autômato de Pilha Determinístico (<strong>9 estados</strong>) que reconhece a GLC <code>G</code> para programas com cabeçalho <code>p</code>, escopos <code>&#123;...&#125;</code> e expressões <code>(...)</code> balanceados, seguidos de <code>#assinatura:chamada;</code> sobre tipos <code>i</code> (<code>int</code>) e <code>s</code> (<code>string</code>).</li>
    <li><strong>Etapa 2 — MiniSemantic (Tipo 1 / LSC não-LLC):</strong> Autômato Linearmente Limitado Determinístico (<strong>11 estados</strong>) executado somente se o AP aceitar, validando sobre fita estritamente limitada <code>&lt;w:u&gt;</code> a igualdade posicional de aridade e tipos <code>L₂ = &#123; w:w | w ∈ &#123;i, s&#125;⁺ &#125;</code>.</li>
  </ol>

  <div class="proof">
    <strong>Prova de Não-Regularidade de L₁ (Lema do Bombeamento Regular — Sipser, 2013; Hopcroft et al., 2007):</strong>
    Suponha L₁ regular com constante <em>p ≥ 3</em> e considere <code>z = p&#123;(ᵖ)ᵖ&#125;#i:i; ∈ L₁</code>. Para qualquer decomposição <code>z = xyz</code> com <code>|xy| ≤ p</code> e <code>|y| ≥ 1</code>, <code>y</code> está no prefixo <code>p&#123;(ᵖ⁻²</code>. Bombear <code>xy²z</code> duplica <code>p</code>, cria <code>&#123;</code> sem fechamento ou gera mais <code>(</code> do que <code>)</code>. Contradição ⇒ <strong>L₁ ∉ LR</strong>.
  </div>

  <div class="proof">
    <strong>Prova de Não-Livre de Contexto de L₂ (Lema do Bombeamento LLC — Sipser, 2013; Aho et al., 2006):</strong>
    Suponha L₂ livre de contexto com constante <em>p ≥ 1</em> e tome <code>z = iᵖsᵖ:iᵖsᵖ ∈ L₂</code>, <code>z = uvwxy</code>, <code>|vwx| ≤ p</code>, <code>|vx| ≥ 1</code>. Se <code>vwx</code> fica de um lado de <code>:</code>, <code>uv²wx²y</code> quebra o tamanho igual; se cruza <code>:</code>, só atinge <code>sᵖ</code> à esquerda e <code>iᵖ</code> à direita (remover <code>:</code> em <code>i=0</code> ou bombear <code>s</code> à esquerda / <code>i</code> à direita destrói <code>w = u</code>). Contradição ⇒ <strong>L₂ ∈ LSC \\ LLC</strong>.
  </div>

  <h2>2. Etapa 1 — GLC (G), Derivação e Autômato de Pilha (9 estados)</h2>
  <p><strong>GLC LL(1):</strong> <code>V = &#123;S, B, T, R&#125;</code>, <code>T = Σ_AP = &#123;p, &#123;, &#125;, (, ), #, i, s, :, ;&#125;</code>, inicial <code>S</code>:</p>
  <ul>{prod_html}</ul>

  <h3>2.1 Derivação Mais à Esquerda de <code>p&#123;(())&#123;&#125;&#125;#isisi:isisi;</code> (22 caracteres)</h3>
  <table>
    <thead><tr><th>Passo</th><th>Forma Sentencial</th><th>Produção Aplicada</th></tr></thead>
    <tbody>{deriv_html}</tbody>
  </table>

  <h3>2.2 Especificação do AP (DPDA — 9 estados) e Equivalência com a GLC</h3>
  <p><code>M_AP = (Q_AP, Σ_AP, Γ_AP, δ_AP, q0, Z, F_AP)</code>, com <code>Q_AP = &#123;q0..q8&#125;</code>, <code>Γ_AP = &#123;Z, &#123;, (&#125;</code> e aceitação por <strong>estado final</strong> (<code>F = &#123;q8&#125;</code>) com <strong>consumo integral da entrada</strong>. Em <code>q2</code>, a pilha acima de <code>Z</code> registra exatamente os delimitadores abertos de <code>B</code>; quando o escopo externo fecha, <code>(q2, ε, Z) → (q3, Z)</code> dispara deterministicamente e <code>q3..q8</code> reconhecem <code>#T:T;</code>, garantindo <code>L(M_AP) = L(G)</code>. Terminação garantida em no máximo <code>n + 1</code> passos (<code>O(n)</code>).</p>
  <table>
    <thead><tr><th>Origem</th><th>Lê</th><th>Desempilha</th><th>Destino</th><th>Empilha</th></tr></thead>
    <tbody>{ap_tr_html}</tbody>
  </table>

  <h2>3. Etapa 2 — LSC e Autômato Linearmente Limitado (11 estados)</h2>
  <p><code>M_ALL = (Q_ALL, Σ_ALL, Γ_ALL, &lt;, &gt;, δ_ALL, q0, F_ALL)</code>, com <code>Q_ALL = &#123;q0..q10&#125;</code>, <code>Σ_ALL = &#123;i, s, :&#125;</code>, <code>Γ_ALL = &#123;&lt;, &gt;, i, s, :, I, S&#125;</code> e <code>F_ALL = &#123;q10&#125;</code>. Para entrada de <code>n</code> símbolos, usa exatamente <code>n</code> células graváveis (<code>1..n</code>) + 2 marcadores fixos (<code>&lt;</code> na célula <code>0</code> e <code>&gt;</code> na célula <code>n+1</code>). Apenas <code>(q0, &lt;)</code> move <code>R</code> e apenas <code>(q9, &gt;)</code> move <code>L</code>; nenhuma borda é sobrescrita ou ultrapassada. Cada ciclo marca irreversivelmente 1 símbolo de cada lado (<code>i→I</code>, <code>s→S</code>), garantindo terminação determinística em <code>O(n²)</code>.</p>
  <table>
    <thead><tr><th>Origem</th><th>Lê</th><th>Destino</th><th>Escreve</th><th>Movimento</th></tr></thead>
    <tbody>{all_tr_html}</tbody>
  </table>

  <h2>4. Bateria de Testes Obrigatórios e Resultados (50 Casos Oficiais)</h2>
  <p>Todos os testes foram verificados no <code>pytest</code> (<strong>227 passed</strong>: 135 AV1 + 92 AV2, incluindo enumeração exaustiva de 3.280 cadeias no ALL) e no motor real do <code>JFLAP7.1.jar</code> (<strong>418 casos, 0 divergências</strong>; 0 estados não-determinísticos em <code>ap.jff</code>).</p>

  <h3>4.1 AP Isolado (10 aceitas ≥ 18 + 10 rejeitadas ≥ 18 + 2 casos-limite)</h3>
  <table>
    <thead><tr><th>ID</th><th>Entrada</th><th>Tam</th><th>Esperado</th><th>Obtido</th><th>Passos</th><th>Regra Verificada</th></tr></thead>
    <tbody>{render_table(data["ap"])}</tbody>
  </table>

  <h3>4.2 ALL Isolado (10 aceitas ≥ 18 + 10 rejeitadas ≥ 18 + 3 casos-limite)</h3>
  <table>
    <thead><tr><th>ID</th><th>Entrada</th><th>Tam</th><th>Esperado</th><th>Obtido</th><th>Passos</th><th>Regra Verificada</th></tr></thead>
    <tbody>{render_table(data["all"])}</tbody>
  </table>

  <h3>4.3 Integração (3 Cenários Obrigatórios)</h3>
  <table>
    <thead><tr><th>ID</th><th>Entrada</th><th>Tam</th><th>AP</th><th>ALL</th><th>Decisão Global</th><th>Regra Verificada</th></tr></thead>
    <tbody>{"".join(int_html)}</tbody>
  </table>

  <h3>4.4 Testes com Símbolo Fora do Alfabeto (Erro Léxico)</h3>
  <ul>{lex_html}</ul>

  <h2>5. Limitações Observadas, Contribuições e Declaração de IA</h2>
  <ul>
    <li><strong>Limitações observadas:</strong> (1) complexidade temporal <code>O(n²)</code> do ALL em fita única (ex.: 19 chars → 201 passos); (2) subconjunto de 2 tipos (<code>i</code>, <code>s</code>) para preservar clareza nos 11 estados; (3) validação de uma única assinatura/chamada por cadeia formal.</li>
    <li><strong>Contribuições:</strong> <em>Andrey Lourival Andrade Garcia</em> (especificação formal, motor Python, CLI, Interface Web Interativa, gerador/validador JFLAP 7.1 e testes); <em>Igor Cecim Vilhena</em> (pesquisa bibliográfica, provas pelo Lema do Bombeamento, revisão da derivação e dos 50 casos, relatório técnico, slides e análise de limitações).</li>
    <li><strong>Uso de IA:</strong> Google Antigravity / Gemini (AV2) e Claude / ChatGPT (AV1) usados como apoio de estruturação, código, interface e revisão textual. A equipe verificou todas as provas, transições, 227 testes <code>pytest</code> e 418 casos reais no <code>JFLAP7.1.jar</code> (0 divergências).</li>
  </ul>

  <h2>6. Referências</h2>
  <ol>
    <li>SIPSER, M. <em>Introduction to the Theory of Computation</em>. 3. ed. Cengage Learning, 2013.</li>
    <li>HOPCROFT, J. E.; MOTWANI, R.; ULLMAN, J. D. <em>Introduction to Automata Theory, Languages, and Computation</em>. 3. ed. Pearson, 2007.</li>
    <li>AHO, A. V. et al. <em>Compilers: Principles, Techniques, and Tools</em>. 2. ed. Pearson, 2006.</li>
    <li>RODGER, S. H.; FINLEY, T. W. <em>JFLAP: An Interactive Formal Languages and Automata Package</em>. Jones &amp; Bartlett, 2006.</li>
    <li>SOUZA, D. L. <em>Atividade Prática AV2: Linguagens Livres de Contexto e Sensíveis ao Contexto</em>. CESUPA, 2026.</li>
  </ol>
</body>
</html>
"""
    (OUT_DIR / "relatorio_av2.html").write_text(doc, encoding="utf-8")


def main() -> None:
    data = collect_results()
    write_latex_section5(data)
    write_html_report(data)
    print("Gerados com sucesso: secoes/05_testes_e_resultados.tex e relatorio_av2.html")


if __name__ == "__main__":
    main()
