"""Valida ap.jff e all.jff diretamente no simulador oficial do JFLAP 7.1.

Uso:
    python tests/validate_av2_jflap_runtime.py "C:\\caminho\\para\\JFLAP7.1.jar"
"""

from __future__ import annotations

import base64
import itertools
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.av2.all_lba import construir_all
from src.av2.ap import construir_ap
from src.av2.cases import CASOS_ALL, CASOS_AP, CASOS_INTEGRACAO
from src.av2.spec import LEFT_MARKER, RIGHT_MARKER


def montar_casos_ap() -> dict[str, bool]:
    ap = construir_ap()
    casos: dict[str, bool] = {}
    for c in CASOS_AP + CASOS_INTEGRACAO:
        casos[c.entrada] = ap.aceita(c.entrada)

    # Extras estruturais para stress-test no JFLAP
    extras = [
        "p",
        "p{",
        "p{}",
        "p{}#",
        "p{}#i:",
        "p{}#:i;",
        "p{}#s:s;",
        "p{()}#is:si;",
        "p{({})}#iis:sii;",
        "p{({)}#i:i;",
        "p{{}()}#ii:ss;",
        "p{}{}#i:i;",
    ]
    for s in extras:
        casos[s] = ap.aceita(s)
    return casos


def montar_casos_all() -> dict[str, bool]:
    all_lba = construir_all()
    casos: dict[str, bool] = {}
    # No JFLAP (turing), a entrada já carrega os marcadores fixos '<' e '>' na fita
    for c in CASOS_ALL:
        casos[f"{LEFT_MARKER}{c.entrada}{RIGHT_MARKER}"] = c.esperado

    # Enumeração completa até tamanho 5 (3^0 + ... + 3^5 = 364 cadeias) no motor real do JFLAP
    for k in range(6):
        for tup in itertools.product("is:", repeat=k):
            s = "".join(tup)
            casos[f"{LEFT_MARKER}{s}{RIGHT_MARKER}"] = all_lba.aceita(s)
    return casos


def main() -> int:
    if len(sys.argv) != 2 or not Path(sys.argv[1]).is_file():
        raise SystemExit("Uso: python tests/validate_av2_jflap_runtime.py caminho/JFLAP7.1.jar")

    jar_path = Path(sys.argv[1]).resolve()
    with tempfile.TemporaryDirectory(prefix="minilang-av2-jflap-") as temp_dir:
        temp = Path(temp_dir)

        ap_lines = [
            f"{int(esp)}\t{base64.b64encode(s.encode('utf-8')).decode('ascii')}\n"
            for s, esp in montar_casos_ap().items()
        ]
        (temp / "ap.tsv").write_text("".join(ap_lines), encoding="utf-8")

        all_lines = [
            f"{int(esp)}\t{base64.b64encode(s.encode('utf-8')).decode('ascii')}\n"
            for s, esp in montar_casos_all().items()
        ]
        (temp / "all.tsv").write_text("".join(all_lines), encoding="utf-8")

        proc = subprocess.run(
            [
                "java",
                "-Djava.awt.headless=true",
                "-cp",
                str(jar_path),
                str(ROOT / "tests" / "JflapAv2RuntimeCheck.java"),
                str(ROOT),
                str(temp),
            ],
            cwd=ROOT,
        )
        return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
