"""Gramática Livre de Contexto (GLC) da Etapa 1 e gerador de derivação mais à esquerda."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

from .spec import (
    GLC_NON_TERMINALS,
    GLC_PRODUCTIONS,
    GLC_START_SYMBOL,
    GLC_TERMINALS,
    Production,
)


@dataclass(frozen=True, slots=True)
class DerivationStep:
    """Um passo da derivação mais à esquerda S ⇒* w."""

    step: int
    sentential_form: str
    rule_id: str | None
    rule_applied: str | None

    def to_dict(self) -> dict:
        return {
            "step": self.step,
            "sentential_form": self.sentential_form,
            "rule_id": self.rule_id,
            "rule_applied": self.rule_applied,
        }


class GLC:
    """Representação formal da GLC LL(1) do MiniParser com derivação determinística."""

    def __init__(
        self,
        non_terminals: Tuple[str, ...] = GLC_NON_TERMINALS,
        terminals: Tuple[str, ...] = GLC_TERMINALS,
        productions: Tuple[Production, ...] = GLC_PRODUCTIONS,
        start_symbol: str = GLC_START_SYMBOL,
    ) -> None:
        self.non_terminals = non_terminals
        self.terminals = terminals
        self.productions = productions
        self.start_symbol = start_symbol
        self._by_id: Dict[str, Production] = {p.id: p for p in productions}
        self._ll1_table: Dict[Tuple[str, str], Production] = self._build_ll1_table()

    def _build_ll1_table(self) -> Dict[Tuple[str, str], Production]:
        """Tabela preditiva LL(1) derivada diretamente das produções P1..P9."""
        p = self._by_id
        return {
            ("S", "p"): p["P1"],
            ("B", "{"): p["P2"],
            ("B", "("): p["P3"],
            ("B", "}"): p["P4"],
            ("B", ")"): p["P4"],
            ("T", "i"): p["P5"],
            ("T", "s"): p["P6"],
            ("R", "i"): p["P7"],
            ("R", "s"): p["P8"],
            ("R", ":"): p["P9"],
            ("R", ";"): p["P9"],
        }

    def derivar_esquerda(self, cadeia: str) -> Tuple[DerivationStep, ...]:
        """Gera a derivação mais à esquerda exata para uma cadeia em L(G).

        Lança ValueError se a cadeia não puder ser derivada pela GLC.
        """
        non_terminal_set = set(self.non_terminals)
        sentential: List[str] = [self.start_symbol]
        steps: List[DerivationStep] = [
            DerivationStep(
                step=0,
                sentential_form=self.start_symbol,
                rule_id=None,
                rule_applied="Símbolo inicial",
            )
        ]

        pos = 0
        step_num = 0
        # Mantemos índice do primeiro símbolo ainda não casado com a entrada
        while True:
            # Encontra o não-terminal mais à esquerda
            nt_index = next(
                (idx for idx, sym in enumerate(sentential) if sym in non_terminal_set),
                None,
            )
            if nt_index is None:
                break

            # Confere que o prefixo de terminais antes do não-terminal bate com a entrada
            while pos < nt_index:
                if pos >= len(cadeia) or sentential[pos] != cadeia[pos]:
                    raise ValueError(
                        f"Divergência de terminal na posição {pos}: "
                        f"esperado {sentential[pos]!r}"
                    )
                pos += 1

            nt = sentential[nt_index]
            lookahead = cadeia[pos] if pos < len(cadeia) else ""
            prod = self._ll1_table.get((nt, lookahead))
            if prod is None:
                raise ValueError(
                    f"Cadeia fora de L(G): nenhuma produção aplicável para "
                    f"({nt}, {lookahead!r}) na posição {pos}."
                )

            sentential[nt_index : nt_index + 1] = list(prod.rhs)
            step_num += 1
            steps.append(
                DerivationStep(
                    step=step_num,
                    sentential_form="".join(sentential),
                    rule_id=prod.id,
                    rule_applied=f"{prod.id}: {prod}",
                )
            )

        final_form = "".join(sentential)
        if final_form != cadeia:
            raise ValueError(
                f"Forma sentencial final {final_form!r} difere da entrada {cadeia!r}."
            )
        return tuple(steps)

    def aceita(self, cadeia: str) -> bool:
        """Indica se a cadeia pertence a L(G)."""
        try:
            self.derivar_esquerda(cadeia)
            return True
        except ValueError:
            return False


def construir_glc() -> GLC:
    """Retorna a instância oficial da GLC da Etapa 1."""
    return GLC()
