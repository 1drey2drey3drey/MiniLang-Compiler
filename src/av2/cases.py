"""Catálogo oficial de casos de teste obrigatórios da lauda (AV2).

Requisitos atendidos com folga:
- AP isolado: 10 aceitas (>= 18 chars) + 10 rejeitadas (>= 18 chars) + 2 casos-limite.
- ALL isolado: 10 aceitas (>= 18 chars) + 10 rejeitadas (>= 18 chars) + 3 casos-limite.
- Integração: 3 cenários obrigatórios (AP✓/ALL✓, AP✗/ALL pulado, AP✓/ALL✗), todos >= 18 chars.
- Erro léxico: símbolos fora de Σ_AP e Σ_ALL com validação da mensagem exibida.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Tuple

ModuloCaso = Literal["AP", "ALL", "INTEGRACAO", "ERRO_LEXICO"]
CategoriaCaso = Literal["aceita", "rejeitada", "caso_limite", "integracao", "erro_lexico"]


@dataclass(frozen=True, slots=True)
class TestCaseRecord:
    """Registro documentado de um caso de teste da lauda."""

    id: str
    modulo: ModuloCaso
    entrada: str
    esperado: bool
    categoria: CategoriaCaso
    regra_verificada: str
    etapa_parada_esperada: str | None = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "modulo": self.modulo,
            "entrada": self.entrada,
            "comprimento": len(self.entrada),
            "esperado": self.esperado,
            "categoria": self.categoria,
            "regra_verificada": self.regra_verificada,
            "etapa_parada_esperada": self.etapa_parada_esperada,
        }


# =============================================================================
# AP ISOLADO — 10 aceitas (>= 18) + 10 rejeitadas (>= 18) + 2 casos-limite
# =============================================================================

CASOS_AP: Tuple[TestCaseRecord, ...] = (
    # --- Aceitas (>= 18 caracteres) ---
    TestCaseRecord(
        "AP-A01", "AP", "p{(()){}}#isisi:isisi;", True, "aceita",
        "Aninhamento misto de blocos e expressões com assinatura e chamada válidas (22 chars).",
    ),
    TestCaseRecord(
        "AP-A02", "AP", "p{((()))}#isisis:sisi;", True, "aceita",
        "Parênteses profundamente aninhados; AP aceita mesmo com aridades diferentes (22 chars).",
    ),
    TestCaseRecord(
        "AP-A03", "AP", "p{{({})}}#iiisss:ssii;", True, "aceita",
        "Escopos aninhados em 3 níveis com expressão interna e tipos variados (22 chars).",
    ),
    TestCaseRecord(
        "AP-A04", "AP", "p{()()()}#sisisi:isii;", True, "aceita",
        "Três expressões sequenciais no escopo principal (22 chars).",
    ),
    TestCaseRecord(
        "AP-A05", "AP", "p{{}(){}}#iissii:siss;", True, "aceita",
        "Combinação sequencial de sub-blocos vazios e expressão vazia (22 chars).",
    ),
    TestCaseRecord(
        "AP-A06", "AP", "p{({()})}#ssssss:iiii;", True, "aceita",
        "Alternância estrita entre parênteses e chaves em 4 níveis de pilha (22 chars).",
    ),
    TestCaseRecord(
        "AP-A07", "AP", "p{(()){}}#isisiisis:isisiisis;", True, "aceita",
        "Cadeia completa reaproveitada na integração (cenário aceito por ambos, 30 chars).",
    ),
    TestCaseRecord(
        "AP-A08", "AP", "p{(()){}}#isisiisis:isisiissi;", True, "aceita",
        "Sintaxe correta com ordem de tipos trocada — AP aceita (cenário 3 de integração, 30 chars).",
    ),
    TestCaseRecord(
        "AP-A09", "AP", "p{{{()}}}#is:isisiisis;", True, "aceita",
        "Escopo triplo com assinatura curta e chamada longa (23 chars).",
    ),
    TestCaseRecord(
        "AP-A10", "AP", "p{({})()}#iiiiiiii:ss;", True, "aceita",
        "Escopo com bloco contendo expressão seguida de expressão irmã (22 chars).",
    ),
    # --- Rejeitadas (>= 18 caracteres, estritamente no alfabeto Σ_AP) ---
    TestCaseRecord(
        "AP-R01", "AP", "p{(()){}#isisiisis:isisiisis;", False, "rejeitada",
        "Chave '{' do escopo principal não fechada antes de '#' (cenário 2 de integração, 29 chars).",
    ),
    TestCaseRecord(
        "AP-R02", "AP", "p{({)})}#isisis:isisis;", False, "rejeitada",
        "Cruzamento inválido de delimitadores: ')' tentando fechar '{' no topo da pilha (23 chars).",
    ),
    TestCaseRecord(
        "AP-R03", "AP", "{(()){}}#isisis:isisis;", False, "rejeitada",
        "Ausência do cabeçalho obrigatório 'p' no início do programa (23 chars).",
    ),
    TestCaseRecord(
        "AP-R04", "AP", "p{(()){}}}#isisi:isisi;", False, "rejeitada",
        "Chave '}' excedente após o fechamento do escopo principal (23 chars).",
    ),
    TestCaseRecord(
        "AP-R05", "AP", "p{(()){}}isisi:isisis;", False, "rejeitada",
        "Ausência do separador '#' entre escopos e seção de assinatura/chamada (22 chars).",
    ),
    TestCaseRecord(
        "AP-R06", "AP", "p{(()){}}#:isisisisisi;", False, "rejeitada",
        "Bloco de assinatura vazio antes de ':' (violação de T -> iR | sR, 23 chars).",
    ),
    TestCaseRecord(
        "AP-R07", "AP", "p{(()){}}#isisisisisi:;", False, "rejeitada",
        "Bloco de chamada vazio após ':' (violação de T -> iR | sR, 23 chars).",
    ),
    TestCaseRecord(
        "AP-R08", "AP", "p{(()){}}#isisis:isisis", False, "rejeitada",
        "Ausência do terminador ';' ao final da cadeia (estado final q8 não atingido, 23 chars).",
    ),
    TestCaseRecord(
        "AP-R09", "AP", "p{(()){}}#isisi:isisi;;", False, "rejeitada",
        "Símbolo excedente ';' após o estado final q8 (entrada não pode ter sobras, 23 chars).",
    ),
    TestCaseRecord(
        "AP-R10", "AP", "p{(()){}}#is:is:isisis;", False, "rejeitada",
        "Separador ':' duplicado na seção de assinatura/chamada (23 chars).",
    ),
    # --- Casos-limite do AP ---
    TestCaseRecord(
        "AP-L01", "AP", "", False, "caso_limite",
        "Caso-limite: cadeia vazia (rejeitada sem consumir entrada, permanece em q0).",
    ),
    TestCaseRecord(
        "AP-L02", "AP", "p{}#i:i;", True, "caso_limite",
        "Caso-limite: menor cadeia aceita pela GLC e pelo AP (8 caracteres).",
    ),
)

# =============================================================================
# ALL ISOLADO — 10 aceitas (>= 18) + 10 rejeitadas (>= 18) + 3 casos-limite
# =============================================================================

CASOS_ALL: Tuple[TestCaseRecord, ...] = (
    # --- Aceitas (>= 18 caracteres, formato w:w com |w| >= 9) ---
    TestCaseRecord(
        "ALL-A01", "ALL", "isisiisis:isisiisis", True, "aceita",
        "Cópia exata de 9 parâmetros mistos (reaproveitada na integração, 19 chars).",
    ),
    TestCaseRecord(
        "ALL-A02", "ALL", "iiiiiiiii:iiiiiiiii", True, "aceita",
        "Nove parâmetros homogêneos do tipo 'i' (int) idênticos (19 chars).",
    ),
    TestCaseRecord(
        "ALL-A03", "ALL", "sssssssss:sssssssss", True, "aceita",
        "Nove parâmetros homogêneos do tipo 's' (string) idênticos (19 chars).",
    ),
    TestCaseRecord(
        "ALL-A04", "ALL", "iiiiisssss:iiiiisssss", True, "aceita",
        "Dois blocos contíguos (5 'i' seguidos de 5 's') espelhados diretamente (21 chars).",
    ),
    TestCaseRecord(
        "ALL-A05", "ALL", "sssssiiiii:sssssiiiii", True, "aceita",
        "Dois blocos contíguos (5 's' seguidos de 5 'i') idênticos (21 chars).",
    ),
    TestCaseRecord(
        "ALL-A06", "ALL", "isisisisis:isisisisis", True, "aceita",
        "Alternância estrita de 10 parâmetros 'is' repetida integralmente (21 chars).",
    ),
    TestCaseRecord(
        "ALL-A07", "ALL", "siiisssiii:siiisssiii", True, "aceita",
        "Padrão assimétrico de 10 tipos casado posição a posição (21 chars).",
    ),
    TestCaseRecord(
        "ALL-A08", "ALL", "iisssiiis:iisssiiis", True, "aceita",
        "Assinatura assimétrica de 9 parâmetros casada exatamente (19 chars).",
    ),
    TestCaseRecord(
        "ALL-A09", "ALL", "sssiisssi:sssiisssi", True, "aceita",
        "Sequência de 9 parâmetros começando por 's' e terminando em 'i' (19 chars).",
    ),
    TestCaseRecord(
        "ALL-A10", "ALL", "isssiiisss:isssiiisss", True, "aceita",
        "Sequência simétrica de 10 parâmetros validada em fita limitada (21 chars).",
    ),
    # --- Rejeitadas (>= 18 caracteres, estritamente no alfabeto Σ_ALL) ---
    TestCaseRecord(
        "ALL-R01", "ALL", "isisiisis:isisiissi", False, "rejeitada",
        "Erro de ordem posicional nos 2 últimos tipos ('is' vs 'si'); mesmas quantidades (19 chars).",
    ),
    TestCaseRecord(
        "ALL-R02", "ALL", "isisiisis:isisiisisi", False, "rejeitada",
        "Erro de aridade: chamada possui 1 argumento excedente após casar assinatura (20 chars).",
    ),
    TestCaseRecord(
        "ALL-R03", "ALL", "isisiisisi:isisiisis", False, "rejeitada",
        "Erro de aridade: chamada possui 1 argumento a menos do que a assinatura (20 chars).",
    ),
    TestCaseRecord(
        "ALL-R04", "ALL", "iiiiiiiii:iiiiiiiis", False, "rejeitada",
        "Erro de tipo na última posição ('i' esperado, 's' encontrado, 19 chars).",
    ),
    TestCaseRecord(
        "ALL-R05", "ALL", "sssssssss:issssssss", False, "rejeitada",
        "Erro de tipo logo na 1ª posição ('s' esperado, 'i' encontrado, 19 chars).",
    ),
    TestCaseRecord(
        "ALL-R06", "ALL", "iiiiisssss:sssssiiiii", False, "rejeitada",
        "Erro de ordem: exatamente 5 'i' e 5 's' de cada lado, porém invertidos (21 chars).",
    ),
    TestCaseRecord(
        "ALL-R07", "ALL", "isisiisisisisiisis", False, "rejeitada",
        "Ausência do separador ':' na fita (cabeçote atinge '>' em q2/q3, 18 chars).",
    ),
    TestCaseRecord(
        "ALL-R08", "ALL", "isisi:isisi:isisii", False, "rejeitada",
        "Presença de dois separadores ':' na fita (rejeitado na varredura final q9, 18 chars).",
    ),
    TestCaseRecord(
        "ALL-R09", "ALL", ":isisiisisisisiisi", False, "rejeitada",
        "Assinatura vazia antes do separador ':' (rejeitado imediatamente em q1, 18 chars).",
    ),
    TestCaseRecord(
        "ALL-R10", "ALL", "isisiisisisisiisi:", False, "rejeitada",
        "Chamada vazia após o separador ':' (rejeitado ao encontrar '>' em q4/q5, 18 chars).",
    ),
    # --- Casos-limite do ALL ---
    TestCaseRecord(
        "ALL-L01", "ALL", "", False, "caso_limite",
        "Caso-limite: cadeia vazia (fita '<>', rejeitada imediatamente em q1 sem cruzar bordas).",
    ),
    TestCaseRecord(
        "ALL-L02", "ALL", ":", False, "caso_limite",
        "Caso-limite: apenas o separador ':' sem tipos em nenhum lado (fita '<:>').",
    ),
    TestCaseRecord(
        "ALL-L03", "ALL", "i:i", True, "caso_limite",
        "Caso-limite: menor cadeia aceita pelo ALL (3 células graváveis + 2 marcadores fixos).",
    ),
)

# =============================================================================
# INTEGRAÇÃO — 3 cenários obrigatórios do fluxo completo (AP -> ALL)
# =============================================================================

CASOS_INTEGRACAO: Tuple[TestCaseRecord, ...] = (
    TestCaseRecord(
        "INT-01", "INTEGRACAO", "p{(()){}}#isisiisis:isisiisis;", True, "integracao",
        "Cenário 1: AP aceita a estrutura sintática e ALL aceita a assinatura/chamada idêntica.",
        etapa_parada_esperada="CONCLUIDO",
    ),
    TestCaseRecord(
        "INT-02", "INTEGRACAO", "p{(()){}#isisiisis:isisiisis;", False, "integracao",
        "Cenário 2: AP rejeita por '{' não fechado; ALL não é executado.",
        etapa_parada_esperada="AP",
    ),
    TestCaseRecord(
        "INT-03", "INTEGRACAO", "p{(()){}}#isisiisis:isisiissi;", False, "integracao",
        "Cenário 3: AP aceita a sintaxe, mas ALL rejeita pela troca posicional dos tipos finais.",
        etapa_parada_esperada="ALL",
    ),
)

# =============================================================================
# ERRO LÉXICO — símbolos fora do alfabeto de entrada
# =============================================================================

CASOS_ERRO_LEXICO: Tuple[TestCaseRecord, ...] = (
    TestCaseRecord(
        "LEX-01", "ERRO_LEXICO", "p{(()){}}#isisi@isisi;", False, "erro_lexico",
        "Símbolo '@' fora de Σ_AP detectado antes da execução dos autômatos.",
        etapa_parada_esperada="LEXICO",
    ),
    TestCaseRecord(
        "LEX-02", "ERRO_LEXICO", "isisiisis$isisiisis", False, "erro_lexico",
        "Símbolo '$' fora de Σ_ALL detectado no validador isolado do ALL.",
        etapa_parada_esperada="LEXICO",
    ),
)


def todos_os_casos() -> Tuple[TestCaseRecord, ...]:
    """Retorna todos os casos oficiais ordenados por seção."""
    return CASOS_AP + CASOS_ALL + CASOS_INTEGRACAO + CASOS_ERRO_LEXICO
