"""Simulador formal do Autômato de Pilha Determinístico (DPDA — 9 estados)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, FrozenSet, List, Tuple

from .spec import (
    AP_FINAL_STATES,
    AP_INITIAL_STATE,
    AP_INPUT_ALPHABET,
    AP_STACK_ALPHABET,
    AP_STATES,
    AP_TRANSITIONS,
    APTransitionSpec,
    EPSILON,
    STACK_INITIAL,
)


@dataclass(frozen=True, slots=True)
class APTraceStep:
    """Configuração instantânea do AP em um passo da simulação."""

    step: int
    state: str
    position: int
    remaining_input: str
    stack: str  # Topo à esquerda (convenção padrão e JFLAP)
    transition: str | None

    def to_dict(self) -> dict:
        return {
            "step": self.step,
            "state": self.state,
            "position": self.position,
            "remaining_input": self.remaining_input,
            "stack": self.stack,
            "transition": self.transition,
        }


@dataclass(frozen=True, slots=True)
class APResult:
    """Resultado completo da execução do Autômato de Pilha."""

    accepted: bool
    input_str: str
    final_state: str
    final_position: int
    final_stack: str
    reason: str
    trace: Tuple[APTraceStep, ...]
    lexical_error: str | None = None

    def to_dict(self) -> dict:
        return {
            "accepted": self.accepted,
            "input_str": self.input_str,
            "final_state": self.final_state,
            "final_position": self.final_position,
            "final_stack": self.final_stack,
            "reason": self.reason,
            "lexical_error": self.lexical_error,
            "steps": len(self.trace) - 1 if self.trace else 0,
            "trace": [t.to_dict() for t in self.trace],
        }


class AutomatoPilha:
    """Simulador de Autômato de Pilha Determinístico (aceitação por estado final).

    A decisão resulta exclusivamente da consulta à função de transição δ_AP e das
    operações reais de empilhar e desempilhar sobre a pilha, exigindo consumo
    integral da cadeia de entrada.
    """

    def __init__(
        self,
        states: Tuple[str, ...] = AP_STATES,
        input_alphabet: Tuple[str, ...] = AP_INPUT_ALPHABET,
        stack_alphabet: Tuple[str, ...] = AP_STACK_ALPHABET,
        transitions: Tuple[APTransitionSpec, ...] = AP_TRANSITIONS,
        initial_state: str = AP_INITIAL_STATE,
        initial_stack_symbol: str = STACK_INITIAL,
        final_states: Tuple[str, ...] = AP_FINAL_STATES,
    ) -> None:
        self.states: Tuple[str, ...] = states
        self.state_set: FrozenSet[str] = frozenset(states)
        self.input_alphabet: Tuple[str, ...] = input_alphabet
        self.input_alphabet_set: FrozenSet[str] = frozenset(input_alphabet)
        self.stack_alphabet: Tuple[str, ...] = stack_alphabet
        self.stack_alphabet_set: FrozenSet[str] = frozenset(stack_alphabet)
        self.initial_state = initial_state
        self.initial_stack_symbol = initial_stack_symbol
        self.final_states: FrozenSet[str] = frozenset(final_states)
        self.transitions_list: Tuple[APTransitionSpec, ...] = transitions
        self._delta: Dict[Tuple[str, str, str], APTransitionSpec] = {}
        self._validar_estrutura()

    def _validar_estrutura(self) -> None:
        if self.initial_state not in self.state_set:
            raise ValueError(f"Estado inicial inválido: {self.initial_state}")
        if not self.final_states.issubset(self.state_set):
            raise ValueError("Estados finais contêm estado fora de Q.")
        if self.initial_stack_symbol not in self.stack_alphabet_set:
            raise ValueError("Símbolo inicial da pilha fora de Γ.")

        # Verifica validade de cada transição e determinismo do DPDA
        eps_keys: set[Tuple[str, str]] = set()
        sym_keys: set[Tuple[str, str]] = set()

        for tr in self.transitions_list:
            if tr.from_state not in self.state_set or tr.to_state not in self.state_set:
                raise ValueError(f"Estado inválido na transição {tr}")
            if tr.read != EPSILON and tr.read not in self.input_alphabet_set:
                raise ValueError(f"Símbolo de leitura fora de Σ_AP: {tr.read!r}")
            if tr.pop not in self.stack_alphabet_set:
                raise ValueError(f"Símbolo de desempilhamento fora de Γ_AP: {tr.pop!r}")
            for sym in tr.push:
                if sym not in self.stack_alphabet_set:
                    raise ValueError(f"Símbolo de empilhamento fora de Γ_AP: {sym!r}")

            key = (tr.from_state, tr.read, tr.pop)
            if key in self._delta:
                raise ValueError(f"Não determinismo detectado em {key}")
            self._delta[key] = tr

            if tr.read == EPSILON:
                eps_keys.add((tr.from_state, tr.pop))
            else:
                sym_keys.add((tr.from_state, tr.pop))

        conflito = eps_keys & sym_keys
        if conflito:
            raise ValueError(
                f"Conflito entre transição ε e transição de símbolo em {sorted(conflito)}"
            )

    def validar_alfabeto(self, cadeia: str) -> str | None:
        """Retorna mensagem de erro léxico se houver símbolo fora de Σ_AP."""
        for idx, ch in enumerate(cadeia):
            if ch not in self.input_alphabet_set:
                alfabeto_fmt = ", ".join(self.input_alphabet)
                return (
                    f"Erro léxico (AP): símbolo inválido {ch!r} na posição {idx}. "
                    f"Alfabeto aceito Σ_AP = {{{alfabeto_fmt}}}."
                )
        return None

    def simular(self, cadeia: str) -> APResult:
        """Executa o DPDA passo a passo e retorna resultado + rastreamento completo."""
        erro_lex = self.validar_alfabeto(cadeia)
        if erro_lex is not None:
            return APResult(
                accepted=False,
                input_str=cadeia,
                final_state=self.initial_state,
                final_position=0,
                final_stack=self.initial_stack_symbol,
                reason=erro_lex,
                trace=(),
                lexical_error=erro_lex,
            )

        state = self.initial_state
        pos = 0
        # Pilha real: índice -1 é o topo; exibida com topo à esquerda (ex.: "({Z")
        stack: List[str] = [self.initial_stack_symbol]

        def format_stack() -> str:
            return "".join(reversed(stack)) if stack else "ε"

        trace: List[APTraceStep] = [
            APTraceStep(
                step=0,
                state=state,
                position=pos,
                remaining_input=cadeia[pos:],
                stack=format_stack(),
                transition=None,
            )
        ]

        step_count = 0
        max_steps = len(cadeia) + 5  # Cota teórica garantida: <= n + 1

        while step_count < max_steps:
            if not stack:
                break

            top = stack[-1]
            tr: APTransitionSpec | None = None

            # Em um DPDA bem formado, não há conflito entre leitura de símbolo e ε
            if pos < len(cadeia):
                tr = self._delta.get((state, cadeia[pos], top))
            if tr is None:
                tr = self._delta.get((state, EPSILON, top))

            if tr is None:
                break

            # Aplica transição formal: consome entrada (se não for ε), desempilha e empilha
            if tr.read != EPSILON:
                pos += 1
            stack.pop()
            # Convenção padrão/JFLAP: caractere mais à esquerda de push fica no topo
            for sym in reversed(tr.push):
                stack.append(sym)
            state = tr.to_state

            step_count += 1
            trace.append(
                APTraceStep(
                    step=step_count,
                    state=state,
                    position=pos,
                    remaining_input=cadeia[pos:],
                    stack=format_stack(),
                    transition=tr.label(),
                )
            )

        consumed_all = pos == len(cadeia)
        in_final = state in self.final_states
        accepted = consumed_all and in_final

        if accepted:
            reason = (
                f"Aceito pelo AP: estado final {state} atingido com consumo integral "
                f"dos {len(cadeia)} símbolos e pilha final '{format_stack()}'."
            )
        elif not consumed_all:
            simbolo_parada = cadeia[pos]
            top_sym = stack[-1] if stack else "ε"
            detalhe = self._diagnosticar_rejeicao(state, simbolo_parada, top_sym, consumed_all=False)
            reason = (
                f"Rejeitado pelo AP em {state} (pos={pos}, leu {simbolo_parada!r}, "
                f"topo={top_sym!r}): {detalhe}"
            )
        else:
            top_sym = stack[-1] if stack else "ε"
            detalhe = self._diagnosticar_rejeicao(state, None, top_sym, consumed_all=True)
            reason = (
                f"Rejeitado pelo AP em {state} (fim da entrada na pos={pos}, "
                f"pilha='{format_stack()}'): {detalhe}"
            )

        return APResult(
            accepted=accepted,
            input_str=cadeia,
            final_state=state,
            final_position=pos,
            final_stack=format_stack(),
            reason=reason,
            trace=tuple(trace),
        )

    @staticmethod
    def _diagnosticar_rejeicao(
        state: str, sym: str | None, top: str, consumed_all: bool
    ) -> str:
        """Explica em linguagem clara por que a transição do AP falhou (apenas diagnóstico)."""
        if consumed_all:
            if state == "q0":
                return "entrada vazia — faltou o cabeçalho 'p' (program) e o corpo do programa."
            if state == "q1":
                return "entrada terminou após 'p' — faltou abrir '{' do escopo principal."
            if state == "q2":
                return f"fim da entrada com delimitador '{top}' ainda aberto na pilha."
            if state == "q3":
                return "faltou o separador '#', a assinatura e a chamada após fechar o escopo."
            if state == "q4":
                return "faltou declarar ao menos um tipo ('i'/'s') na assinatura após '#'."
            if state == "q5":
                return "faltou o separador ':' e os argumentos da chamada."
            if state == "q6":
                return "faltou ao menos um argumento ('i'/'s') na chamada após ':'."
            if state == "q7":
                return "faltou o terminador ';' ao final da chamada para atingir o estado final q8."
            return "entrada consumida sem atingir o estado final q8."

        if state == "q0":
            return f"esperava o cabeçalho 'p' (program) no início, mas encontrou {sym!r}."
        if state == "q1":
            return f"após 'p', esperava '{{' para abrir o escopo principal, mas encontrou {sym!r}."
        if state == "q2":
            if sym == "#":
                return f"escopo/expressão '{top}' ainda aberto na pilha ao alcançar '#' (faltou fechar)."
            if sym in (")", "}"):
                return f"cruzamento inválido de delimitadores: {sym!r} tentando fechar '{top}' no topo da pilha."
            return f"símbolo inesperado {sym!r} dentro do bloco de escopos (topo '{top}')."
        if state == "q3":
            if sym == "}":
                return "chave '}' excedente após o fechamento do escopo principal (esperava '#')."
            return f"após fechar o escopo principal, esperava '#', mas encontrou {sym!r}."
        if state == "q4":
            if sym == ":":
                return "bloco de assinatura vazio antes de ':' (exige ao menos um tipo 'i' ou 's')."
            return f"esperava o 1º tipo da assinatura ('i' ou 's') após '#', mas encontrou {sym!r}."
        if state == "q5":
            return f"esperava tipo ('i'/'s') da assinatura ou separador ':', mas encontrou {sym!r}."
        if state == "q6":
            if sym == ";":
                return "bloco de chamada vazio após ':' (exige ao menos um argumento 'i' ou 's')."
            return f"esperava o 1º tipo da chamada ('i' ou 's') após ':', mas encontrou {sym!r}."
        if state == "q7":
            if sym == ":":
                return "separador ':' duplicado na seção de assinatura/chamada."
            return f"esperava tipo ('i'/'s') da chamada ou terminador ';', mas encontrou {sym!r}."
        if state == "q8":
            return f"símbolo excedente {sym!r} após o terminador ';' — a entrada deve encerrar em q8."
        return "nenhuma transição definida para a configuração atual."

    def aceita(self, cadeia: str) -> bool:
        return self.simular(cadeia).accepted


def construir_ap() -> AutomatoPilha:
    """Retorna a instância oficial do DPDA de 9 estados da Etapa 1."""
    return AutomatoPilha()
