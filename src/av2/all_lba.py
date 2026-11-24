"""Simulador formal do Autômato Linearmente Limitado Determinístico (D-LBA — 11 estados)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, FrozenSet, List, Tuple

from .spec import (
    ALL_FINAL_STATES,
    ALL_INITIAL_STATE,
    ALL_INPUT_ALPHABET,
    ALL_STATES,
    ALL_TAPE_ALPHABET,
    ALL_TRANSITIONS,
    ALLTransitionSpec,
    LEFT_MARKER,
    RIGHT_MARKER,
)


@dataclass(frozen=True, slots=True)
class ALLTraceStep:
    """Configuração instantânea do ALL em um passo da simulação."""

    step: int
    state: str
    head: int
    tape: str
    symbol_read: str
    transition: str | None

    def to_dict(self) -> dict:
        return {
            "step": self.step,
            "state": self.state,
            "head": self.head,
            "tape": self.tape,
            "symbol_read": self.symbol_read,
            "transition": self.transition,
        }


@dataclass(frozen=True, slots=True)
class ALLResult:
    """Resultado completo da execução do Autômato Linearmente Limitado."""

    accepted: bool
    input_str: str
    final_state: str
    final_head: int
    final_tape: str
    writable_cells: int
    reason: str
    trace: Tuple[ALLTraceStep, ...]
    lexical_error: str | None = None

    def to_dict(self) -> dict:
        return {
            "accepted": self.accepted,
            "input_str": self.input_str,
            "final_state": self.final_state,
            "final_head": self.final_head,
            "final_tape": self.final_tape,
            "writable_cells": self.writable_cells,
            "total_cells": self.writable_cells + 2,
            "reason": self.reason,
            "lexical_error": self.lexical_error,
            "steps": len(self.trace) - 1 if self.trace else 0,
            "trace": [t.to_dict() for t in self.trace],
        }


class AutomatoLinearmenteLimitado:
    """Simulador de Autômato Linearmente Limitado Determinístico (D-LBA).

    Para uma entrada de n símbolos, aloca exatamente n células graváveis e dois
    marcadores de borda fixos ('<' na posição 0 e '>' na posição n+1). A memória
    de trabalho cabe integralmente nessa fita e o cabeçote jamais sobrescreve ou
    ultrapassa os marcadores de borda.
    """

    def __init__(
        self,
        states: Tuple[str, ...] = ALL_STATES,
        input_alphabet: Tuple[str, ...] = ALL_INPUT_ALPHABET,
        tape_alphabet: Tuple[str, ...] = ALL_TAPE_ALPHABET,
        transitions: Tuple[ALLTransitionSpec, ...] = ALL_TRANSITIONS,
        initial_state: str = ALL_INITIAL_STATE,
        final_states: Tuple[str, ...] = ALL_FINAL_STATES,
        left_marker: str = LEFT_MARKER,
        right_marker: str = RIGHT_MARKER,
    ) -> None:
        self.states: Tuple[str, ...] = states
        self.state_set: FrozenSet[str] = frozenset(states)
        self.input_alphabet: Tuple[str, ...] = input_alphabet
        self.input_alphabet_set: FrozenSet[str] = frozenset(input_alphabet)
        self.tape_alphabet: Tuple[str, ...] = tape_alphabet
        self.tape_alphabet_set: FrozenSet[str] = frozenset(tape_alphabet)
        self.initial_state = initial_state
        self.final_states: FrozenSet[str] = frozenset(final_states)
        self.left_marker = left_marker
        self.right_marker = right_marker
        self.transitions_list: Tuple[ALLTransitionSpec, ...] = transitions
        self._delta: Dict[Tuple[str, str], ALLTransitionSpec] = {}
        self._validar_estrutura()

    def _validar_estrutura(self) -> None:
        if self.initial_state not in self.state_set:
            raise ValueError(f"Estado inicial inválido: {self.initial_state}")
        if not self.final_states.issubset(self.state_set):
            raise ValueError("Estados finais contêm estado fora de Q.")
        if not self.input_alphabet_set.issubset(self.tape_alphabet_set):
            raise ValueError("Σ_ALL deve ser subconjunto de Γ_ALL.")
        if self.left_marker not in self.tape_alphabet_set or self.right_marker not in self.tape_alphabet_set:
            raise ValueError("Marcadores de borda devem pertencer a Γ_ALL.")

        for tr in self.transitions_list:
            if tr.from_state not in self.state_set or tr.to_state not in self.state_set:
                raise ValueError(f"Estado inválido na transição {tr}")
            if tr.read not in self.tape_alphabet_set or tr.write not in self.tape_alphabet_set:
                raise ValueError(f"Símbolo fora de Γ_ALL na transição {tr}")
            if tr.move not in ("L", "R"):
                raise ValueError(f"Movimento inválido: {tr.move!r}")

            # Invariantes estruturais de fita limitada (bordas fixas e invioláveis)
            if tr.read == self.left_marker:
                if tr.write != self.left_marker or tr.move != "R":
                    raise ValueError(
                        f"Violação da borda esquerda em {tr}: '<' é fixo e só permite movimento 'R'."
                    )
            if tr.read == self.right_marker:
                if tr.write != self.right_marker or tr.move != "L":
                    raise ValueError(
                        f"Violação da borda direita em {tr}: '>' é fixo e só permite movimento 'L'."
                    )
            if tr.read not in (self.left_marker, self.right_marker) and tr.write in (
                self.left_marker,
                self.right_marker,
            ):
                raise ValueError(f"Célula interna não pode receber marcador de borda: {tr}")

            key = (tr.from_state, tr.read)
            if key in self._delta:
                raise ValueError(f"Não determinismo detectado em {key}")
            self._delta[key] = tr

    def validar_alfabeto(self, cadeia: str) -> str | None:
        """Retorna mensagem de erro léxico se houver símbolo fora de Σ_ALL."""
        for idx, ch in enumerate(cadeia):
            if ch not in self.input_alphabet_set:
                alfabeto_fmt = ", ".join(self.input_alphabet)
                return (
                    f"Erro léxico (ALL): símbolo inválido {ch!r} na posição {idx}. "
                    f"Alfabeto aceito Σ_ALL = {{{alfabeto_fmt}}}."
                )
        return None

    def simular(self, cadeia: str) -> ALLResult:
        """Executa o D-LBA passo a passo sobre fita limitada < + cadeia + >."""
        n = len(cadeia)
        erro_lex = self.validar_alfabeto(cadeia)
        if erro_lex is not None:
            return ALLResult(
                accepted=False,
                input_str=cadeia,
                final_state=self.initial_state,
                final_head=0,
                final_tape=f"{self.left_marker}{cadeia}{self.right_marker}",
                writable_cells=n,
                reason=erro_lex,
                trace=(),
                lexical_error=erro_lex,
            )

        # Fita de tamanho estrito n + 2: célula 0 = '<', células 1..n = entrada, célula n+1 = '>'
        tape: List[str] = [self.left_marker, *list(cadeia), self.right_marker]
        expected_len = n + 2
        head = 0
        state = self.initial_state

        trace: List[ALLTraceStep] = [
            ALLTraceStep(
                step=0,
                state=state,
                head=head,
                tape="".join(tape),
                symbol_read=tape[head],
                transition=None,
            )
        ]

        # Cota superior teórica: O(n^2), estritamente <= (n + 2)^2 + 10
        max_steps = (n + 2) ** 2 + 10
        step_count = 0

        while step_count < max_steps:
            sym = tape[head]
            tr = self._delta.get((state, sym))
            if tr is None:
                break

            tape[head] = tr.write
            next_head = head - 1 if tr.move == "L" else head + 1

            # Asserções em tempo de execução garantindo respeito absoluto aos limites da fita
            if not (0 <= next_head < expected_len):
                raise RuntimeError(
                    f"Violação de limite da fita: cabeçote tentou acessar posição {next_head}."
                )
            if len(tape) != expected_len or tape[0] != self.left_marker or tape[-1] != self.right_marker:
                raise RuntimeError("Violação de integridade dos marcadores de borda da fita.")

            head = next_head
            state = tr.to_state
            step_count += 1

            trace.append(
                ALLTraceStep(
                    step=step_count,
                    state=state,
                    head=head,
                    tape="".join(tape),
                    symbol_read=tape[head],
                    transition=tr.label(),
                )
            )

            if state in self.final_states:
                break

        accepted = state in self.final_states
        final_tape_str = "".join(tape)

        if accepted:
            reason = (
                f"Aceito pelo ALL: estado final {state} atingido em {step_count} passos "
                f"(fita limitada de {n} células graváveis + 2 bordas fixas)."
            )
        else:
            motivo_especifico = self._diagnosticar_rejeicao(state, tape[head])
            reason = (
                f"Rejeitado pelo ALL em {state} (cabeçote={head}, lendo {tape[head]!r}): "
                f"{motivo_especifico}"
            )

        return ALLResult(
            accepted=accepted,
            input_str=cadeia,
            final_state=state,
            final_head=head,
            final_tape=final_tape_str,
            writable_cells=n,
            reason=reason,
            trace=tuple(trace),
        )

    @staticmethod
    def _diagnosticar_rejeicao(state: str, sym: str) -> str:
        """Gera descrição legível do motivo da parada sem transição (apenas diagnóstico)."""
        if state == "q1":
            return "lado esquerdo (assinatura) vazio ou ausente antes de ':'."
        if state in ("q2", "q3") and sym == RIGHT_MARKER:
            return "separador ':' ausente na fita (cabeçote atingiu '>' sem encontrar ':')."
        if state == "q4":
            if sym == "s":
                return "incompatibilidade de tipo/ordem: assinatura esperava 'i' (int), chamada trouxe 's' (string)."
            if sym == RIGHT_MARKER:
                return "erro de aridade: chamada tem menos argumentos do que a assinatura (atingiu '>')."
            if sym == ":":
                return "separador ':' duplicado na chamada."
        if state == "q5":
            if sym == "i":
                return "incompatibilidade de tipo/ordem: assinatura esperava 's' (string), chamada trouxe 'i' (int)."
            if sym == RIGHT_MARKER:
                return "erro de aridade: chamada tem menos argumentos do que a assinatura (atingiu '>')."
            if sym == ":":
                return "separador ':' duplicado na chamada."
        if state == "q9":
            if sym in ("i", "s"):
                tipo = "int" if sym == "i" else "string"
                return f"erro de aridade: sobrou argumento excedente {sym!r} ({tipo}) na chamada após casar toda a assinatura."
            if sym == ":":
                return "separador ':' duplicado na fita (encontrado na varredura final)."
        return "nenhuma transição definida para a configuração atual."

    def aceita(self, cadeia: str) -> bool:
        return self.simular(cadeia).accepted


def construir_all() -> AutomatoLinearmenteLimitado:
    """Retorna a instância oficial do D-LBA de 11 estados da Etapa 2."""
    return AutomatoLinearmenteLimitado()
