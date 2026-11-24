"""Fonte de verdade única das especificações formais da AV2 (GLC, AP e ALL).

Todos os simuladores Python, os arquivos JFLAP (.jff), os diagramas Mermaid e a
suíte de testes consomem diretamente as definições imutáveis deste módulo,
garantindo consistência total entre documentação formal, código e JFLAP 7.1.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Tuple

EPSILON = ""
LEFT_MARKER = "<"
RIGHT_MARKER = ">"
STACK_INITIAL = "Z"


@dataclass(frozen=True, slots=True)
class Production:
    """Produção formal A -> alpha de uma Gramática Livre de Contexto."""

    id: str
    lhs: str
    rhs: Tuple[str, ...]

    @property
    def rhs_str(self) -> str:
        return "".join(self.rhs) if self.rhs else "ε"

    def __str__(self) -> str:
        return f"{self.lhs} → {self.rhs_str}"


@dataclass(frozen=True, slots=True)
class APTransitionSpec:
    """Transição formal δ_AP(from_state, read, pop) = (to_state, push)."""

    from_state: str
    read: str  # "" representa ε
    pop: str
    to_state: str
    push: str  # "" representa ε (desempilhar sem empilhar nada)

    def label(self) -> str:
        r = self.read if self.read != EPSILON else "ε"
        p = self.push if self.push != EPSILON else "ε"
        return f"δ({self.from_state}, {r}, {self.pop}) = ({self.to_state}, {p})"


@dataclass(frozen=True, slots=True)
class ALLTransitionSpec:
    """Transição formal δ_ALL(from_state, read) = (to_state, write, move)."""

    from_state: str
    read: str
    to_state: str
    write: str
    move: Literal["L", "R"]

    def label(self) -> str:
        return f"δ({self.from_state}, {self.read}) = ({self.to_state}, {self.write}, {self.move})"


# =============================================================================
# ETAPA 1 — GRAMÁTICA LIVRE DE CONTEXTO (GLC — LL(1) não-ambígua)
# =============================================================================

GLC_NON_TERMINALS: Tuple[str, ...] = ("S", "B", "T", "R")
GLC_TERMINALS: Tuple[str, ...] = ("p", "{", "}", "(", ")", "#", "i", "s", ":", ";")
GLC_START_SYMBOL = "S"

GLC_PRODUCTIONS: Tuple[Production, ...] = (
    Production("P1", "S", ("p", "{", "B", "}", "#", "T", ":", "T", ";")),
    Production("P2", "B", ("{", "B", "}", "B")),
    Production("P3", "B", ("(", "B", ")", "B")),
    Production("P4", "B", ()),
    Production("P5", "T", ("i", "R")),
    Production("P6", "T", ("s", "R")),
    Production("P7", "R", ("i", "R")),
    Production("P8", "R", ("s", "R")),
    Production("P9", "R", ()),
)

# =============================================================================
# ETAPA 1 — AUTÔMATO DE PILHA DETERMINÍSTICO (DPDA — 9 estados)
# =============================================================================

AP_STATES: Tuple[str, ...] = (
    "q0",  # Estado inicial: aguarda cabeçalho 'p' (program)
    "q1",  # Leu 'p': aguarda abertura '{' do escopo principal
    "q2",  # Corpo do programa: valida balanceamento de '{...}' e '(...)' na pilha
    "q3",  # Escopo principal fechado (pilha em Z): aguarda separador '#'
    "q4",  # Leu '#': exige 1º tipo da assinatura ('i' ou 's')
    "q5",  # Lê tipos adicionais da assinatura ou separador ':'
    "q6",  # Leu ':': exige 1º tipo da chamada ('i' ou 's')
    "q7",  # Lê tipos adicionais da chamada ou terminador ';'
    "q8",  # Estado final de aceitação (entrada totalmente consumida, pilha = Z)
)

AP_STATE_DESCRIPTIONS = {
    "q0": "Aguarda cabeçalho do programa ('p')",
    "q1": "Aguarda abertura do escopo principal ('{')",
    "q2": "Valida blocos '{...}' e expressões '(...)' aninhados via pilha",
    "q3": "Escopo principal fechado (topo Z); aguarda separador '#'",
    "q4": "Aguarda o 1º tipo da assinatura de função ('i' ou 's')",
    "q5": "Lê demais tipos da assinatura ('i'/'s') ou separador ':'",
    "q6": "Aguarda o 1º tipo dos argumentos na chamada ('i' ou 's')",
    "q7": "Lê demais tipos da chamada ('i'/'s') ou terminador ';'",
    "q8": "Estado final — sintaxe válida (entrada integralmente consumida)",
}

AP_INPUT_ALPHABET: Tuple[str, ...] = GLC_TERMINALS
AP_STACK_ALPHABET: Tuple[str, ...] = (STACK_INITIAL, "{", "(")
AP_INITIAL_STATE = "q0"
AP_FINAL_STATES: Tuple[str, ...] = ("q8",)

AP_TRANSITIONS: Tuple[APTransitionSpec, ...] = (
    # Cabeçalho e abertura do escopo principal
    APTransitionSpec("q0", "p", "Z", "q1", "Z"),
    APTransitionSpec("q1", "{", "Z", "q2", "{Z"),
    # Balanceamento Dyck D2 no corpo do programa (empilha/desempilha '{' e '(')
    APTransitionSpec("q2", "{", "{", "q2", "{{"),
    APTransitionSpec("q2", "{", "(", "q2", "{("),
    APTransitionSpec("q2", "(", "{", "q2", "({"),
    APTransitionSpec("q2", "(", "(", "q2", "(("),
    APTransitionSpec("q2", "}", "{", "q2", EPSILON),
    APTransitionSpec("q2", ")", "(", "q2", EPSILON),
    # Transição ε determinística ao encerrar o escopo principal (topo volta a Z)
    APTransitionSpec("q2", EPSILON, "Z", "q3", "Z"),
    # Separador '#' e bloco de assinatura não vazio {i, s}+
    APTransitionSpec("q3", "#", "Z", "q4", "Z"),
    APTransitionSpec("q4", "i", "Z", "q5", "Z"),
    APTransitionSpec("q4", "s", "Z", "q5", "Z"),
    APTransitionSpec("q5", "i", "Z", "q5", "Z"),
    APTransitionSpec("q5", "s", "Z", "q5", "Z"),
    # Separador ':' e bloco de chamada não vazio {i, s}+
    APTransitionSpec("q5", ":", "Z", "q6", "Z"),
    APTransitionSpec("q6", "i", "Z", "q7", "Z"),
    APTransitionSpec("q6", "s", "Z", "q7", "Z"),
    APTransitionSpec("q7", "i", "Z", "q7", "Z"),
    APTransitionSpec("q7", "s", "Z", "q7", "Z"),
    # Terminador ';' -> estado final q8
    APTransitionSpec("q7", ";", "Z", "q8", "Z"),
)

# =============================================================================
# ETAPA 2 — AUTÔMATO LINEARMENTE LIMITADO DETERMINÍSTICO (D-LBA — 11 estados)
# =============================================================================

ALL_STATES: Tuple[str, ...] = (
    "q0",   # Estado inicial: lê marcador esquerdo '<' e avança para célula 1
    "q1",   # Exige assinatura não vazia: marca 1º símbolo ('i'→'I' ou 's'→'S')
    "q2",   # Transporta 'i' até o separador ':'
    "q3",   # Transporta 's' até o separador ':'
    "q4",   # No lado direito, pula 'I'/'S' e casa exatamente 'i' → 'I'
    "q5",   # No lado direito, pula 'I'/'S' e casa exatamente 's' → 'S'
    "q6",   # Retorna à esquerda pelo lado direito até ':'
    "q7",   # Retorna à esquerda pelo lado esquerdo até a fronteira marcada ('I'/'S')
    "q8",   # Seleciona próximo símbolo da assinatura ou inicia checagem final em ':'
    "q9",   # Varredura final à direita: confirma que só há 'I'/'S' até '>'
    "q10",  # Estado final de aceitação (sem cruzar '>')
)

ALL_STATE_DESCRIPTIONS = {
    "q0": "Lê marcador de borda esquerdo '<' e entra na 1ª célula gravável",
    "q1": "Exige 1º tipo na assinatura ('i'→'I' ou 's'→'S')",
    "q2": "Carrega tipo 'i' pela assinatura até alcançar ':'",
    "q3": "Carrega tipo 's' pela assinatura até alcançar ':'",
    "q4": "Busca o próximo tipo livre na chamada e exige 'i' ('i'→'I')",
    "q5": "Busca o próximo tipo livre na chamada e exige 's' ('s'→'S')",
    "q6": "Retorna à esquerda pela chamada já marcada até ':'",
    "q7": "Retorna à esquerda pela assinatura até a fronteira já marcada ('I'/'S')",
    "q8": "Lê próximo tipo da assinatura ou, em ':', inicia varredura final",
    "q9": "Varredura final na chamada: confirma ausência de sobras até '>'",
    "q10": "Estado final — aridade e ordem posicional de tipos 100% compatíveis",
}

ALL_INPUT_ALPHABET: Tuple[str, ...] = ("i", "s", ":")
ALL_TAPE_ALPHABET: Tuple[str, ...] = (LEFT_MARKER, RIGHT_MARKER, "i", "s", ":", "I", "S")
ALL_INITIAL_STATE = "q0"
ALL_FINAL_STATES: Tuple[str, ...] = ("q10",)

ALL_TRANSITIONS: Tuple[ALLTransitionSpec, ...] = (
    # q0: valida marcador esquerdo '<' e entra na célula 1
    ALLTransitionSpec("q0", LEFT_MARKER, "q1", LEFT_MARKER, "R"),
    # q1: exige ao menos um tipo na assinatura (rejeita entrada vazia ou ':...')
    ALLTransitionSpec("q1", "i", "q2", "I", "R"),
    ALLTransitionSpec("q1", "s", "q3", "S", "R"),
    # q2: carrega 'i' até ':'
    ALLTransitionSpec("q2", "i", "q2", "i", "R"),
    ALLTransitionSpec("q2", "s", "q2", "s", "R"),
    ALLTransitionSpec("q2", ":", "q4", ":", "R"),
    # q3: carrega 's' até ':'
    ALLTransitionSpec("q3", "i", "q3", "i", "R"),
    ALLTransitionSpec("q3", "s", "q3", "s", "R"),
    ALLTransitionSpec("q3", ":", "q5", ":", "R"),
    # q4: casa 'i' no lado direito
    ALLTransitionSpec("q4", "I", "q4", "I", "R"),
    ALLTransitionSpec("q4", "S", "q4", "S", "R"),
    ALLTransitionSpec("q4", "i", "q6", "I", "L"),
    # q5: casa 's' no lado direito
    ALLTransitionSpec("q5", "I", "q5", "I", "R"),
    ALLTransitionSpec("q5", "S", "q5", "S", "R"),
    ALLTransitionSpec("q5", "s", "q6", "S", "L"),
    # q6: retorna ao ':'
    ALLTransitionSpec("q6", "I", "q6", "I", "L"),
    ALLTransitionSpec("q6", "S", "q6", "S", "L"),
    ALLTransitionSpec("q6", ":", "q7", ":", "L"),
    # q7: retorna até a fronteira já marcada ('I' ou 'S')
    ALLTransitionSpec("q7", "i", "q7", "i", "L"),
    ALLTransitionSpec("q7", "s", "q7", "s", "L"),
    ALLTransitionSpec("q7", "I", "q8", "I", "R"),
    ALLTransitionSpec("q7", "S", "q8", "S", "R"),
    # q8: seleciona próximo tipo da assinatura ou inicia verificação final
    ALLTransitionSpec("q8", "i", "q2", "I", "R"),
    ALLTransitionSpec("q8", "s", "q3", "S", "R"),
    ALLTransitionSpec("q8", ":", "q9", ":", "R"),
    # q9: confirma ausência de símbolos não casados até o marcador direito '>'
    ALLTransitionSpec("q9", "I", "q9", "I", "R"),
    ALLTransitionSpec("q9", "S", "q9", "S", "R"),
    ALLTransitionSpec("q9", RIGHT_MARKER, "q10", RIGHT_MARKER, "L"),
)
