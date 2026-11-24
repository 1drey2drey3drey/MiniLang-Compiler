"""Pipeline integrado em duas etapas (AP -> extração semântica -> ALL) e ponte MiniLang."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Tuple

from .all_lba import ALLResult, construir_all
from .ap import APResult, construir_ap
from .glc import DerivationStep, construir_glc

StageStopped = Literal["LEXICO", "AP", "ALL", "CONCLUIDO"]


@dataclass(frozen=True, slots=True)
class PipelineResult:
    """Resultado completo da validação integrada em duas etapas."""

    input_str: str
    overall_accepted: bool
    stage_stopped: StageStopped
    summary: str
    lexical_error: str | None
    ap_result: APResult | None
    derivation: Tuple[DerivationStep, ...] | None
    semantic_slice: str | None
    all_result: ALLResult | None
    minilang_preview: str

    def to_dict(self) -> dict:
        return {
            "input_str": self.input_str,
            "length": len(self.input_str),
            "overall_accepted": self.overall_accepted,
            "stage_stopped": self.stage_stopped,
            "summary": self.summary,
            "lexical_error": self.lexical_error,
            "ap_result": self.ap_result.to_dict() if self.ap_result else None,
            "derivation": [d.to_dict() for d in self.derivation] if self.derivation else None,
            "semantic_slice": self.semantic_slice,
            "all_result": self.all_result.to_dict() if self.all_result else None,
            "minilang_preview": self.minilang_preview,
        }


def extrair_trecho_semantico(cadeia_aceita_ap: str) -> str:
    """Extrai a subcadeia semântica w:u delimitada entre '#' e ';' após aceitação do AP."""
    hash_pos = cadeia_aceita_ap.index("#")
    semi_pos = cadeia_aceita_ap.index(";", hash_pos + 1)
    return cadeia_aceita_ap[hash_pos + 1 : semi_pos]


def formatar_equivalente_minilang(cadeia: str) -> str:
    """Gera uma leitura didática aproximada da cadeia formal em código MiniLang."""
    if not cadeia:
        return "// cadeia vazia"

    if "#" not in cadeia:
        return f"// trecho sem separador '#': {cadeia}"

    estrutura, resto = cadeia.split("#", 1)
    assinatura_chamada = resto[:-1] if resto.endswith(";") else resto

    tipo_nome = {"i": "int", "s": "string"}
    valor_ex = {"i": "10", "s": '"ok"'}

    if ":" in assinatura_chamada:
        sig_raw, call_raw = assinatura_chamada.split(":", 1)
        params = ", ".join(
            f"{tipo_nome.get(c, '?')} p{idx + 1}" for idx, c in enumerate(sig_raw)
        )
        args = ", ".join(valor_ex.get(c, "?") for c in call_raw)
        decl_str = f"fn validar({params})"
        call_str = f"validar({args});"
    else:
        decl_str = f"// assinatura/chamada incompleta: {assinatura_chamada}"
        call_str = ""

    linhas = [f"// Estrutura sintática: {estrutura}"]
    if estrutura.startswith("p{"):
        linhas.append("program mini_av2 {")
        linhas.append(f"    {decl_str} {{ /* escopos: {estrutura[1:]} */ }}")
        if call_str:
            linhas.append(f"    {call_str}")
        linhas.append("}")
    else:
        linhas.append(f"// Cabeçalho fora do padrão 'p{{...}}': {estrutura}")
        linhas.append(decl_str)
        if call_str:
            linhas.append(call_str)

    return "\n".join(linhas)


def validar_entrada(cadeia: str) -> PipelineResult:
    """Executa o fluxo oficial em duas etapas: AP (GLC) -> ALL (LSC)."""
    ap = construir_ap()
    erro_lex = ap.validar_alfabeto(cadeia)
    preview = formatar_equivalente_minilang(cadeia)

    if erro_lex is not None:
        return PipelineResult(
            input_str=cadeia,
            overall_accepted=False,
            stage_stopped="LEXICO",
            summary=f"Entrada rejeitada na verificação léxica: {erro_lex}",
            lexical_error=erro_lex,
            ap_result=None,
            derivation=None,
            semantic_slice=None,
            all_result=None,
            minilang_preview=preview,
        )

    ap_result = ap.simular(cadeia)
    if not ap_result.accepted:
        return PipelineResult(
            input_str=cadeia,
            overall_accepted=False,
            stage_stopped="AP",
            summary="Rejeitado na Etapa 1 (AP). A Etapa 2 (ALL) não foi executada.",
            lexical_error=None,
            ap_result=ap_result,
            derivation=None,
            semantic_slice=None,
            all_result=None,
            minilang_preview=preview,
        )

    # Etapa 1 aceita -> gera derivação da GLC e extrai fatia w:u para a Etapa 2 (ALL)
    glc = construir_glc()
    derivation = glc.derivar_esquerda(cadeia)
    semantic_slice = extrair_trecho_semantico(cadeia)

    all_lba = construir_all()
    all_result = all_lba.simular(semantic_slice)

    if not all_result.accepted:
        return PipelineResult(
            input_str=cadeia,
            overall_accepted=False,
            stage_stopped="ALL",
            summary=(
                f"Aceito na Etapa 1 (AP); fatia '{semantic_slice}' rejeitada na Etapa 2 "
                f"(ALL) — {all_result.reason}"
            ),
            lexical_error=None,
            ap_result=ap_result,
            derivation=derivation,
            semantic_slice=semantic_slice,
            all_result=all_result,
            minilang_preview=preview,
        )

    return PipelineResult(
        input_str=cadeia,
        overall_accepted=True,
        stage_stopped="CONCLUIDO",
        summary=(
            f"Entrada aceita integralmente (AP aceitou a sintaxe em "
            f"{len(ap_result.trace) - 1} passos e ALL validou '{semantic_slice}' em "
            f"{len(all_result.trace) - 1} passos)."
        ),
        lexical_error=None,
        ap_result=ap_result,
        derivation=derivation,
        semantic_slice=semantic_slice,
        all_result=all_result,
        minilang_preview=preview,
    )
