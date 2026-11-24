"""Compilador de código-fonte MiniLang -> cadeia formal da AV2 (ponte real com o MiniLexer da AV1)
e sintetizador de programas MiniLang representativos para cada um dos 50 casos de teste oficiais.

Usa o analisador léxico real da AV1 (`src/lexer.py`, baseado em AFNε de Thompson)
para tokenizar programas escritos em MiniLang e projetar mecanicamente os tokens
para o alfabeto formal Σ_AP — sem realizar balanceamento sintático nem comparação
semântica fora dos autômatos. Toda decisão de aceitação/rejeição ocorre
estritamente em δ_AP (9 estados) e δ_ALL (11 estados).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from src.lexer import LexicalError, tokenize
from src.tokens import Token, TokenType

from .cases import TestCaseRecord
from .pipeline import PipelineResult, validar_entrada

MINILANG_PRESETS: Tuple[dict[str, str], ...] = (
    {
        "id": "ok",
        "label": "✓ Programa Válido",
        "badge": "ok",
        "description": "Escopos balanceados + chamada compatível com os 9 parâmetros declarados.",
        "code": (
            'program matricula {\n'
            '    if ((nota >= 7)) {\n'
            '        aprovado = 1;\n'
            '    }\n'
            '\n'
            '    fn matricular(int id, string nome, int cpf, string curso, int sem, int ano, string turno, int sala, string campus);\n'
            '    matricular(10, "ana", 20, "cc", 30, 40, "noite", 50, "argo");\n'
            '}'
        ),
    },
    {
        "id": "syntax_err",
        "label": "✗ Erro de Escopo (AP)",
        "badge": "err",
        "description": "Chave '}' do bloco program esquecida — AP rejeita na Etapa 1 e o ALL não executa.",
        "code": (
            'program folha_pagamento {\n'
            '    while ((horas > 0)) {\n'
            '        saldo = 100;\n'
            '    }\n'
            '\n'
            '    fn lancar_lote(int cod, string setor, int mes, string cargo, int hrs, int base, string banco, int dia, string status);\n'
            '    lancar_lote(1, "ti", 11, "dev", 40, 5000, "bb", 25, "ok");\n'
            '// faltou fechar \'}\' do program'
        ),
    },
    {
        "id": "semantic_err",
        "label": "⚠ Erro de Tipos (ALL)",
        "badge": "warn",
        "description": 'Sintaxe perfeita, mas os 2 últimos argumentos estão invertidos ("rj", 90 vs int, string).',
        "code": (
            'program envio_pedido {\n'
            '    if ((estoque > 0)) {\n'
            '        despacho = 1;\n'
            '    }\n'
            '\n'
            '    fn emitir_nota(int ped, string cli, int qtd, string prod, int cep, int peso, string transp, int prazo, string uf);\n'
            '    emitir_nota(99, "bia", 3, "ssd", 66000, 2, "sedex", "rj", 90);\n'
            '}'
        ),
    },
    {
        "id": "lexical_err",
        "label": "⊘ Erro Léxico (AV1)",
        "badge": "lex",
        "description": "Caractere '@' inválido capturado pelo MiniLexer (AFNε) com linha e coluna.",
        "code": (
            'program autenticacao {\n'
            '    if ((tentativas < 3)) {\n'
            '        chave = 10 @ 5;\n'
            '    }\n'
            '\n'
            '    fn validar_token(int uid, string hash);\n'
            '    validar_token(1, "abc");\n'
            '}'
        ),
    },
)


@dataclass(frozen=True, slots=True)
class ProjectionStep:
    """Mapeamento transparente de um token MiniLang para um símbolo formal de Σ_AP."""

    source_lexeme: str
    token_type: str
    formal_symbol: str
    line: int
    column: int
    length: int
    role: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_lexeme": self.source_lexeme,
            "token_type": self.token_type,
            "formal_symbol": self.formal_symbol,
            "line": self.line,
            "column": self.column,
            "length": self.length,
            "role": self.role,
        }


def _make_step(tok: Token, formal_symbol: str, role: str, token_type_override: str | None = None) -> ProjectionStep:
    return ProjectionStep(
        source_lexeme=tok.lexeme,
        token_type=token_type_override or tok.type.value,
        formal_symbol=formal_symbol,
        line=tok.line,
        column=tok.column,
        length=max(1, len(tok.lexeme)),
        role=role,
    )


def _collect_typed_variables(tokens: List[Token]) -> Dict[str, str]:
    """Mapeia declarações simples `int x` / `string s` no escopo para projeção de argumentos."""
    env: Dict[str, str] = {}
    for idx in range(len(tokens) - 1):
        t = tokens[idx]
        nxt = tokens[idx + 1]
        if nxt.type is TokenType.IDENTIFIER:
            if t.type is TokenType.TYPE_INT:
                env[nxt.lexeme] = "i"
            elif t.type is TokenType.TYPE_STRING:
                env[nxt.lexeme] = "s"
    return env


def extrair_cadeia_formal_de_minilang(
    source: str,
) -> Tuple[str, Tuple[ProjectionStep, ...], int, str | None, dict[str, Any] | None]:
    """Tokeniza código MiniLang com o MiniLexer real (AV1) e projeta para Σ_AP.

    Retorna: (cadeia_formal, lista_projecoes, total_tokens, erro_front_ou_None, error_span_ou_None)
    """
    try:
        tokens = tokenize(source)
    except LexicalError as exc:
        span = {
            "line": exc.line,
            "column": exc.column,
            "length": max(1, len(exc.lexeme)) if getattr(exc, "lexeme", None) else 1,
            "severity": "err",
            "message": str(exc),
        }
        return "", (), 0, str(exc), span

    var_types = _collect_typed_variables(tokens)
    structural: List[ProjectionStep] = []
    fn_tok: Token | None = None
    fn_name: str | None = None
    sig_steps: List[ProjectionStep] = []
    calls_list: List[Tuple[Token, List[ProjectionStep], Token | None]] = []
    has_sig = False
    trailing_semi_tokens: List[Token] = []

    i = 0
    n = len(tokens)
    while i < n:
        tok = tokens[i]

        # Declaração de função: fn <nome>(int a, string b, ...);
        if tok.type is TokenType.IDENTIFIER and tok.lexeme == "fn" and i + 2 < n:
            if tokens[i + 1].type is TokenType.IDENTIFIER and tokens[i + 2].type is TokenType.LPAREN:
                has_sig = True
                fn_tok = tok
                fn_name = tokens[i + 1].lexeme
                j = i + 3
                closed = False
                while j < n:
                    cur = tokens[j]
                    if cur.type is TokenType.RPAREN:
                        closed = True
                        break
                    if cur.type in (TokenType.SEMICOLON, TokenType.RBRACE):
                        structural.append(_make_step(tokens[i + 2], "(", "Parêntese não fechado em fn"))
                        break
                    if cur.type is TokenType.COMMA:
                        j += 1
                        continue
                    if cur.type is TokenType.TYPE_INT:
                        sig_steps.append(_make_step(cur, "i", "Parâmetro int"))
                        if j + 1 < n and tokens[j + 1].type is TokenType.IDENTIFIER:
                            j += 1
                    elif cur.type is TokenType.TYPE_STRING:
                        sig_steps.append(_make_step(cur, "s", "Parâmetro string"))
                        if j + 1 < n and tokens[j + 1].type is TokenType.IDENTIFIER:
                            j += 1
                    else:
                        msg = (
                            f"Erro léxico/projeção (linha {cur.line}, coluna {cur.column}): "
                            f"tipo {cur.lexeme!r} ({cur.type.value}) fora do subconjunto AV2 {{int, string}}."
                        )
                        span = {
                            "line": cur.line,
                            "column": cur.column,
                            "length": max(1, len(cur.lexeme)),
                            "severity": "err",
                            "message": msg,
                        }
                        return "", (), len(tokens), msg, span
                    j += 1
                i = (j + 1) if closed else j
                if i < n and tokens[i].type is TokenType.SEMICOLON:
                    i += 1
                continue

        # Chamada da função declarada: <nome>(arg1, arg2, ...);
        if (
            fn_name is not None
            and tok.type is TokenType.IDENTIFIER
            and tok.lexeme == fn_name
            and i + 1 < n
            and tokens[i + 1].type is TokenType.LPAREN
        ):
            cur_call: List[ProjectionStep] = []
            j = i + 2
            closed = False
            rparen_tok: Token | None = None
            while j < n:
                cur = tokens[j]
                if cur.type is TokenType.RPAREN:
                    closed = True
                    rparen_tok = cur
                    break
                if cur.type in (TokenType.SEMICOLON, TokenType.RBRACE):
                    structural.append(_make_step(tokens[i + 1], "(", "Parêntese não fechado na chamada"))
                    break
                if cur.type is TokenType.COMMA:
                    j += 1
                    continue
                if cur.type in (TokenType.TYPE_INT, TokenType.INTEGER):
                    cur_call.append(_make_step(cur, "i", "Argumento int"))
                elif cur.type in (TokenType.TYPE_STRING, TokenType.STRING):
                    cur_call.append(_make_step(cur, "s", "Argumento string"))
                elif cur.type is TokenType.IDENTIFIER and cur.lexeme in var_types:
                    sym = var_types[cur.lexeme]
                    cur_call.append(_make_step(cur, sym, f"Variável tipada ({sym})", f"VAR({sym})"))
                else:
                    msg = (
                        f"Erro léxico/projeção (linha {cur.line}, coluna {cur.column}): "
                        f"argumento {cur.lexeme!r} ({cur.type.value}) não mapeia para {{int, string}}."
                    )
                    span = {
                        "line": cur.line,
                        "column": cur.column,
                        "length": max(1, len(cur.lexeme)),
                        "severity": "err",
                        "message": msg,
                    }
                    return "", (), len(tokens), msg, span
                j += 1
            calls_list.append((tok, cur_call, rparen_tok))
            i = (j + 1) if closed else j
            trailing_semi_tokens = []
            while i < n and tokens[i].type is TokenType.SEMICOLON:
                trailing_semi_tokens.append(tokens[i])
                i += 1
            continue

        # Estrutura sintática (program, blocos {} e expressões ())
        if tok.type is TokenType.PROGRAM:
            structural.append(_make_step(tok, "p", "Cabeçalho"))
        elif tok.type is TokenType.LBRACE:
            structural.append(_make_step(tok, "{", "Abre escopo"))
        elif tok.type is TokenType.RBRACE:
            structural.append(_make_step(tok, "}", "Fecha escopo"))
        elif tok.type is TokenType.LPAREN:
            structural.append(_make_step(tok, "(", "Abre expressão"))
        elif tok.type is TokenType.RPAREN:
            structural.append(_make_step(tok, ")", "Fecha expressão"))

        i += 1

    all_projections: List[ProjectionStep] = list(structural)
    formal_parts: List[str] = [p.formal_symbol for p in structural]

    if has_sig or calls_list:
        if fn_tok is not None:
            all_projections.append(_make_step(fn_tok, "#", "Separador sintaxe/semântica", "SECTION"))
        else:
            all_projections.append(ProjectionStep("fn", "SECTION", "#", 1, 1, 1, "Separador sintaxe/semântica"))
        formal_parts.append("#")
        all_projections.extend(sig_steps)
        formal_parts.extend(p.formal_symbol for p in sig_steps)

        for call_tok, call_steps, _rparen in calls_list:
            all_projections.append(_make_step(call_tok, ":", "Separador assinatura/chamada", "CALL"))
            formal_parts.append(":")
            all_projections.extend(call_steps)
            formal_parts.extend(p.formal_symbol for p in call_steps)

        for semi_tok in trailing_semi_tokens:
            all_projections.append(_make_step(semi_tok, ";", "Terminador"))
            formal_parts.append(";")

    return "".join(formal_parts), tuple(all_projections), len(tokens), None, None


def _resolver_error_span(
    source: str,
    projections: Tuple[ProjectionStep, ...],
    pipe: PipelineResult,
) -> dict[str, Any] | None:
    """Mapeia o ponto de parada exato do AP ou do ALL de volta para (linha, coluna, tam) no código."""
    if pipe.overall_accepted:
        return None

    def _from_proj(step: ProjectionStep, severity: str, message: str) -> dict[str, Any]:
        return {
            "line": step.line,
            "column": step.column,
            "length": step.length,
            "severity": severity,
            "message": message,
        }

    # Etapa 1: rejeição no AP
    if pipe.stage_stopped == "AP" and pipe.ap_result is not None:
        pos = pipe.ap_result.final_position
        msg = pipe.ap_result.reason
        # Caso clássico de '{' sem fechar ao chegar em '#': destaca o '{' ainda aberto na pilha!
        if (
            pipe.ap_result.final_state == "q2"
            and pos < len(projections)
            and projections[pos].formal_symbol == "#"
        ):
            # Encontra o primeiro '{' não pareado antes de pos
            open_stack: List[ProjectionStep] = []
            for p in projections[:pos]:
                if p.formal_symbol in ("{", "("):
                    open_stack.append(p)
                elif p.formal_symbol == "}" and open_stack and open_stack[-1].formal_symbol == "{":
                    open_stack.pop()
                elif p.formal_symbol == ")" and open_stack and open_stack[-1].formal_symbol == "(":
                    open_stack.pop()
            if open_stack:
                return _from_proj(open_stack[-1], "err", msg)
        if pos < len(projections):
            return _from_proj(projections[pos], "err", msg)
        if projections:
            return _from_proj(projections[-1], "err", msg)
        # Entrada vazia
        return {"line": 1, "column": 1, "length": max(1, len(source.splitlines()[0]) if source.splitlines() else 1), "severity": "err", "message": msg}

    # Etapa 2: rejeição no ALL (mapeia final_head na fita '< w:u >' para o argumento exato!)
    if pipe.stage_stopped == "ALL" and pipe.all_result is not None:
        msg = pipe.all_result.reason
        hash_idx = next((idx for idx, p in enumerate(projections) if p.formal_symbol == "#"), None)
        if hash_idx is not None:
            # Na fita '< w:u >', célula 0 é '<', células 1..n correspondem a hash_idx+1 .. hash_idx+n
            offset = pipe.all_result.final_head - 1
            target_idx = hash_idx + 1 + offset
            if 0 <= target_idx < len(projections):
                step = projections[target_idx]
                # Se bateu no '>' (aridade menor), target_idx cai no ';': aponta para o último arg ou chamada
                if step.formal_symbol == ";" and target_idx > 0:
                    return _from_proj(projections[target_idx - 1], "warn", msg)
                return _from_proj(step, "warn", msg)
        if projections:
            return _from_proj(projections[-1], "warn", msg)

    return None


def compilar_minilang(source: str) -> dict[str, Any]:
    """Executa compilação completa: MiniLexer (AV1) -> projeção -> AP -> ALL + error_span IDE."""
    formal_str, projections, token_count, lex_err, lex_span = extrair_cadeia_formal_de_minilang(source)

    if lex_err is not None:
        return {
            "source": source,
            "lexical_ok": False,
            "lexical_error": lex_err,
            "error_span": lex_span,
            "token_count": token_count,
            "formal_string": "",
            "projections": [],
            "pipeline": {
                "input_str": "",
                "length": 0,
                "overall_accepted": False,
                "stage_stopped": "LEXICO",
                "summary": lex_err,
                "lexical_error": lex_err,
                "ap_result": None,
                "derivation": None,
                "semantic_slice": None,
                "all_result": None,
                "minilang_preview": source,
            },
        }

    pipe: PipelineResult = validar_entrada(formal_str)
    error_span = _resolver_error_span(source, projections, pipe)
    return {
        "source": source,
        "lexical_ok": True,
        "lexical_error": None,
        "error_span": error_span,
        "token_count": token_count,
        "formal_string": formal_str,
        "projections": [p.to_dict() for p in projections],
        "pipeline": pipe.to_dict(),
    }


# =============================================================================
# SINTETIZADOR DE CÓDIGO MINILANG PARA TODOS OS 50 CASOS OFICIAIS
# =============================================================================

_SAMPLE_STRINGS = ('"ana"', '"bia"', '"leo"', '"eva"', '"rui"', '"sol"', '"lua"', '"mar"', '"rio"', '"luz"')


def _fmt_params(sig: str) -> str:
    parts = []
    for idx, ch in enumerate(sig):
        tipo = "int" if ch == "i" else "string"
        parts.append(f"{tipo} p{idx + 1}")
    return ", ".join(parts)


def _fmt_args(call: str) -> str:
    parts = []
    for idx, ch in enumerate(call):
        if ch == "i":
            parts.append(str((idx + 1) * 10))
        else:
            parts.append(_SAMPLE_STRINGS[idx % len(_SAMPLE_STRINGS)])
    return ", ".join(parts)


def _render_delimiters(seq: str) -> str:
    """Converte uma sequência de '{', '}', '(', ')' em trecho MiniLang equivalente."""
    if not seq:
        return "    ativo = 1;"
    out: List[str] = []
    for ch in seq:
        if ch == "(":
            out.append("(")
        elif ch == ")":
            if out and out[-1] == "(":
                out.append("x > 0)")
            else:
                out.append(")")
        elif ch == "{":
            out.append("{ ")
        elif ch == "}":
            if out and out[-1] == "{ ":
                out.append("ok = 1; } ")
            else:
                out.append("} ")
    body = "".join(out).strip()
    return f"    if {body}" if body.startswith("(") else f"    {body}"


def sintetizar_minilang_para_caso(caso: TestCaseRecord) -> str:
    """Gera código-fonte MiniLang legível que representa fielmente cada caso oficial."""
    cid = caso.id
    ent = caso.entrada

    if ent == "":
        return f"// {cid} — {caso.regra_verificada}\n"

    if cid == "LEX-01":
        return (
            f"// {cid} — {caso.regra_verificada}\n"
            "program teste_lex {\n"
            "    if ((x > 0)) { ok = 1; }\n"
            "    total = 10 @ 5;\n"
            "    fn validar(int p1, string p2, int p3, string p4, int p5);\n"
            '    validar(10, "ana", 30, "bia", 50);\n'
            "}"
        )
    if cid == "LEX-02":
        return (
            f"// {cid} — {caso.regra_verificada}\n"
            "program teste_lex_all {\n"
            "    valor = 10 $ 2;\n"
            "    fn validar(int p1, string p2);\n"
            '    validar(10, "ana");\n'
            "}"
        )

    if caso.modulo == "ALL":
        if ":" not in ent:
            return (
                f"// {cid} — {caso.regra_verificada}\n"
                "program teste_all {\n"
                f"    fn validar({_fmt_params(ent)});\n"
                "    // chamada omitida (sem separador ':')\n"
                "}"
            )
        partes = ent.split(":")
        sig = partes[0]
        calls = partes[1:]
        linhas = [
            f"// {cid} — {caso.regra_verificada}",
            "program teste_all {",
            f"    fn validar({_fmt_params(sig)});",
        ]
        for c_args in calls:
            linhas.append(f"    validar({_fmt_args(c_args)});")
        linhas.append("}")
        return "\n".join(linhas)

    has_p = ent.startswith("p")
    rest = ent[1:] if has_p else ent

    if "#" not in rest:
        delim = "".join(ch for ch in rest if ch in "{}()")
        inner = delim[1:-1] if delim.startswith("{") and delim.endswith("}") else delim
        return (
            f"// {cid} — {caso.regra_verificada}\n"
            f"{'program sem_fn ' if has_p else ''}{{\n"
            f"{_render_delimiters(inner)}\n"
            "    // faltou declarar 'fn' antes dos argumentos\n"
            "}"
        )

    struct_raw, sem_raw = rest.split("#", 1)
    semis = 0
    while sem_raw.endswith(";"):
        semis += 1
        sem_raw = sem_raw[:-1]

    partes_sem = sem_raw.split(":")
    sig = partes_sem[0]
    calls = partes_sem[1:]

    header = "program teste_av2 " if has_p else "// faltou 'program'\n"
    open_brace = "{" if struct_raw.startswith("{") else ""
    body_seq = struct_raw[1:] if open_brace else struct_raw

    close_braces = 0
    if body_seq.endswith("}") and cid not in ("AP-R01", "INT-02"):
        if body_seq.endswith("}}}") and cid == "AP-R04":
            close_braces = 2
            body_seq = body_seq[:-2]
        else:
            close_braces = 1
            body_seq = body_seq[:-1]

    linhas = [
        f"// {cid} — {caso.regra_verificada}",
        f"{header}{open_brace}".rstrip(),
        _render_delimiters(body_seq),
        f"    fn validar({_fmt_params(sig)});",
    ]

    for idx, c_args in enumerate(calls):
        fim = (";" * semis) if idx == len(calls) - 1 else ";"
        linhas.append(f"    validar({_fmt_args(c_args)}){fim}")

    if close_braces == 0:
        linhas.append("// faltou fechar '}' do escopo principal")
    else:
        linhas.append("}" * close_braces)

    return "\n".join(linhas)
