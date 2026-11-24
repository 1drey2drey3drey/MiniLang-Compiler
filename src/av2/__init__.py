"""Núcleo formal da AV2 — MiniLang-Compiler (MiniParser GLC/AP + MiniSemantic LSC/ALL)."""

from .all_lba import ALLResult, ALLTraceStep, AutomatoLinearmenteLimitado, construir_all
from .ap import APResult, APTraceStep, AutomatoPilha, construir_ap
from .cases import (
    CASOS_ALL,
    CASOS_AP,
    CASOS_ERRO_LEXICO,
    CASOS_INTEGRACAO,
    TestCaseRecord,
    todos_os_casos,
)
from .glc import DerivationStep, GLC, construir_glc
from .pipeline import PipelineResult, formatar_equivalente_minilang, validar_entrada

__all__ = [
    "ALLResult",
    "ALLTraceStep",
    "APResult",
    "APTraceStep",
    "AutomatoLinearmenteLimitado",
    "AutomatoPilha",
    "CASOS_ALL",
    "CASOS_AP",
    "CASOS_ERRO_LEXICO",
    "CASOS_INTEGRACAO",
    "DerivationStep",
    "GLC",
    "PipelineResult",
    "TestCaseRecord",
    "construir_all",
    "construir_ap",
    "construir_glc",
    "formatar_equivalente_minilang",
    "todos_os_casos",
    "validar_entrada",
]
