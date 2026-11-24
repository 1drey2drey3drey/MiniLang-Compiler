"""Gerador e leitor estrutural de arquivos JFLAP 7.1 (.jff) e diagramas Mermaid da AV2.

Todos os artefatos são gerados diretamente de `src/av2/spec.py` (fonte única de verdade).
Uso:
    python -m src.av2.jflap_io
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple
import xml.etree.ElementTree as ET

from .spec import (
    ALL_FINAL_STATES,
    ALL_INITIAL_STATE,
    ALL_STATE_DESCRIPTIONS,
    ALL_STATES,
    ALL_TRANSITIONS,
    ALLTransitionSpec,
    AP_FINAL_STATES,
    AP_INITIAL_STATE,
    AP_STATE_DESCRIPTIONS,
    AP_STATES,
    AP_TRANSITIONS,
    APTransitionSpec,
    EPSILON,
    GLC_PRODUCTIONS,
)

ROOT = Path(__file__).resolve().parents[2]
DIAGRAMS_DIR = ROOT / "docs" / "diagramas" / "AV2"

# Coordenadas limpas para visualização direta no JFLAP 7.1
AP_COORDS: Dict[str, Tuple[float, float]] = {
    "q0": (80.0, 220.0),
    "q1": (200.0, 220.0),
    "q2": (340.0, 220.0),
    "q3": (500.0, 220.0),
    "q4": (630.0, 220.0),
    "q5": (770.0, 220.0),
    "q6": (910.0, 220.0),
    "q7": (1050.0, 220.0),
    "q8": (1190.0, 220.0),
}

ALL_COORDS: Dict[str, Tuple[float, float]] = {
    "q0": (70.0, 260.0),
    "q1": (190.0, 260.0),
    "q2": (360.0, 140.0),
    "q3": (360.0, 380.0),
    "q4": (560.0, 140.0),
    "q5": (560.0, 380.0),
    "q6": (740.0, 260.0),
    "q7": (560.0, 260.0),
    "q8": (360.0, 260.0),
    "q9": (360.0, 500.0),
    "q10": (560.0, 500.0),
}


def _indent_xml(elem: ET.Element, level: int = 0) -> None:
    indent = "\n" + level * "\t"
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = indent + "\t"
        for child in elem:
            _indent_xml(child, level + 1)
        if not elem[-1].tail or not elem[-1].tail.strip():
            elem[-1].tail = indent
    if level and (not elem.tail or not elem.tail.strip()):
        elem.tail = indent


def _serialize_xml(root: ET.Element) -> str:
    _indent_xml(root)
    xml_body = ET.tostring(root, encoding="unicode")
    return '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n' + xml_body + "\n"


def build_glc_jff() -> str:
    """Gera XML JFLAP 7.1 para a GLC (tipo grammar)."""
    structure = ET.Element("structure")
    ET.SubElement(structure, "type").text = "grammar"
    for prod in GLC_PRODUCTIONS:
        p_el = ET.SubElement(structure, "production")
        ET.SubElement(p_el, "left").text = prod.lhs
        right = ET.SubElement(p_el, "right")
        if prod.rhs:
            right.text = "".join(prod.rhs)
    return _serialize_xml(structure)


def build_ap_jff() -> str:
    """Gera XML JFLAP 7.1 para o AP determinístico de 9 estados (tipo pda)."""
    structure = ET.Element("structure")
    ET.SubElement(structure, "type").text = "pda"
    automaton = ET.SubElement(structure, "automaton")

    id_map = {name: str(idx) for idx, name in enumerate(AP_STATES)}
    for name in AP_STATES:
        x, y = AP_COORDS[name]
        st = ET.SubElement(automaton, "state", {"id": id_map[name], "name": name})
        ET.SubElement(st, "x").text = f"{x:.1f}"
        ET.SubElement(st, "y").text = f"{y:.1f}"
        ET.SubElement(st, "label").text = AP_STATE_DESCRIPTIONS[name]
        if name == AP_INITIAL_STATE:
            ET.SubElement(st, "initial")
        if name in AP_FINAL_STATES:
            ET.SubElement(st, "final")

    for tr in AP_TRANSITIONS:
        t_el = ET.SubElement(automaton, "transition")
        ET.SubElement(t_el, "from").text = id_map[tr.from_state]
        ET.SubElement(t_el, "to").text = id_map[tr.to_state]
        r_el = ET.SubElement(t_el, "read")
        if tr.read != EPSILON:
            r_el.text = tr.read
        ET.SubElement(t_el, "pop").text = tr.pop
        p_el = ET.SubElement(t_el, "push")
        if tr.push != EPSILON:
            p_el.text = tr.push

    return _serialize_xml(structure)


def build_all_jff() -> str:
    """Gera XML JFLAP 7.1 para o ALL determinístico de 11 estados (tipo turing)."""
    structure = ET.Element("structure")
    ET.SubElement(structure, "type").text = "turing"
    automaton = ET.SubElement(structure, "automaton")

    id_map = {name: str(idx) for idx, name in enumerate(ALL_STATES)}
    for name in ALL_STATES:
        x, y = ALL_COORDS[name]
        st = ET.SubElement(automaton, "state", {"id": id_map[name], "name": name})
        ET.SubElement(st, "x").text = f"{x:.1f}"
        ET.SubElement(st, "y").text = f"{y:.1f}"
        ET.SubElement(st, "label").text = ALL_STATE_DESCRIPTIONS[name]
        if name == ALL_INITIAL_STATE:
            ET.SubElement(st, "initial")
        if name in ALL_FINAL_STATES:
            ET.SubElement(st, "final")

    for tr in ALL_TRANSITIONS:
        t_el = ET.SubElement(automaton, "transition")
        ET.SubElement(t_el, "from").text = id_map[tr.from_state]
        ET.SubElement(t_el, "to").text = id_map[tr.to_state]
        ET.SubElement(t_el, "read").text = tr.read
        ET.SubElement(t_el, "write").text = tr.write
        ET.SubElement(t_el, "move").text = tr.move

    return _serialize_xml(structure)


def parse_ap_jff(path: Path) -> Tuple[Tuple[str, ...], str, Tuple[str, ...], Tuple[APTransitionSpec, ...]]:
    """Lê um arquivo ap.jff e devolve (estados, inicial, finais, transições)."""
    root = ET.parse(path).getroot()
    assert root.findtext("type") == "pda"
    aut = root.find("automaton")
    assert aut is not None
    id_to_name: Dict[str, str] = {}
    states: List[str] = []
    initial = ""
    finals: List[str] = []
    for st in aut.findall("state"):
        sid = st.attrib["id"]
        sname = st.attrib["name"]
        id_to_name[sid] = sname
        states.append(sname)
        if st.find("initial") is not None:
            initial = sname
        if st.find("final") is not None:
            finals.append(sname)
    transitions: List[APTransitionSpec] = []
    for t in aut.findall("transition"):
        transitions.append(
            APTransitionSpec(
                from_state=id_to_name[t.findtext("from") or ""],
                read=t.findtext("read") or EPSILON,
                pop=t.findtext("pop") or EPSILON,
                to_state=id_to_name[t.findtext("to") or ""],
                push=t.findtext("push") or EPSILON,
            )
        )
    return tuple(states), initial, tuple(finals), tuple(transitions)


def parse_all_jff(path: Path) -> Tuple[Tuple[str, ...], str, Tuple[str, ...], Tuple[ALLTransitionSpec, ...]]:
    """Lê um arquivo all.jff e devolve (estados, inicial, finais, transições)."""
    root = ET.parse(path).getroot()
    assert root.findtext("type") == "turing"
    aut = root.find("automaton")
    assert aut is not None
    id_to_name: Dict[str, str] = {}
    states: List[str] = []
    initial = ""
    finals: List[str] = []
    for st in aut.findall("state"):
        sid = st.attrib["id"]
        sname = st.attrib["name"]
        id_to_name[sid] = sname
        states.append(sname)
        if st.find("initial") is not None:
            initial = sname
        if st.find("final") is not None:
            finals.append(sname)
    transitions: List[ALLTransitionSpec] = []
    for t in aut.findall("transition"):
        move = t.findtext("move") or ""
        assert move in ("L", "R")
        transitions.append(
            ALLTransitionSpec(
                from_state=id_to_name[t.findtext("from") or ""],
                read=t.findtext("read") or "",
                to_state=id_to_name[t.findtext("to") or ""],
                write=t.findtext("write") or "",
                move=move,  # type: ignore[arg-type]
            )
        )
    return tuple(states), initial, tuple(finals), tuple(transitions)


def build_ap_mermaid_md() -> str:
    linhas = [
        "# Autômato de Pilha Determinístico (AP — MiniParser, 9 estados)",
        "",
        "```mermaid",
        "stateDiagram-v2",
        "    direction LR",
        "    [*] --> q0",
        '    q0 --> q1: "p, Z / Z"',
        '    q1 --> q2: "{, Z / {Z"',
        '    q2 --> q2: "{, { / {{ | {, ( / {( | (, { / ({ | (, ( / (( | }, { / ε | ), ( / ε"',
        '    q2 --> q3: "ε, Z / Z"',
        '    q3 --> q4: "#, Z / Z"',
        '    q4 --> q5: "i, Z / Z | s, Z / Z"',
        '    q5 --> q5: "i, Z / Z | s, Z / Z"',
        '    q5 --> q6: ":, Z / Z"',
        '    q6 --> q7: "i, Z / Z | s, Z / Z"',
        '    q7 --> q7: "i, Z / Z | s, Z / Z"',
        '    q7 --> q8: ";, Z / Z"',
        "    q8 --> [*]",
        "```",
        "",
        "## Tabela completa de transições (δ_AP)",
        "",
        "| Origem | Leitura | Desempilha | Destino | Empilha |",
        "| :--- | :---: | :---: | :--- | :---: |",
    ]
    for tr in AP_TRANSITIONS:
        r = tr.read if tr.read else "ε"
        p = tr.push if tr.push else "ε"
        linhas.append(f"| `{tr.from_state}` | `{r}` | `{tr.pop}` | `{tr.to_state}` | `{p}` |")
    return "\n".join(linhas) + "\n"


def build_all_mermaid_md() -> str:
    linhas = [
        "# Autômato Linearmente Limitado Determinístico (ALL — MiniSemantic, 11 estados)",
        "",
        "```mermaid",
        "stateDiagram-v2",
        "    direction LR",
        "    [*] --> q0",
        '    q0 --> q1: "< -> <, R"',
        '    q1 --> q2: "i -> I, R"',
        '    q1 --> q3: "s -> S, R"',
        '    q2 --> q2: "i/s -> mesmo, R"',
        '    q2 --> q4: ": -> :, R"',
        '    q3 --> q3: "i/s -> mesmo, R"',
        '    q3 --> q5: ": -> :, R"',
        '    q4 --> q4: "I/S -> mesmo, R"',
        '    q4 --> q6: "i -> I, L"',
        '    q5 --> q5: "I/S -> mesmo, R"',
        '    q5 --> q6: "s -> S, L"',
        '    q6 --> q6: "I/S -> mesmo, L"',
        '    q6 --> q7: ": -> :, L"',
        '    q7 --> q7: "i/s -> mesmo, L"',
        '    q7 --> q8: "I/S -> mesmo, R"',
        '    q8 --> q2: "i -> I, R"',
        '    q8 --> q3: "s -> S, R"',
        '    q8 --> q9: ": -> :, R"',
        '    q9 --> q9: "I/S -> mesmo, R"',
        '    q9 --> q10: "> -> >, L"',
        "    q10 --> [*]",
        "```",
        "",
        "## Tabela completa de transições (δ_ALL)",
        "",
        "| Origem | Lê | Destino | Escreve | Movimento |",
        "| :--- | :---: | :--- | :---: | :---: |",
    ]
    for tr in ALL_TRANSITIONS:
        linhas.append(f"| `{tr.from_state}` | `{tr.read}` | `{tr.to_state}` | `{tr.write}` | `{tr.move}` |")
    return "\n".join(linhas) + "\n"


def build_architecture_mermaid_md() -> str:
    return (
        "# Arquitetura do Pipeline em Duas Etapas — MiniLang-Compiler (AV2)\n\n"
        "```mermaid\n"
        "flowchart LR\n"
        '    A["Entrada formal (Σ_AP)"] --> B{"Validação de Alfabeto"}\n'
        '    B -- "Símbolo inválido" --> E1["Rejeição Léxica"]\n'
        '    B -- "Válido" --> C["Etapa 1: AP (DPDA, 9 estados)\\nGLC LL(1) + Pilha"]\n'
        '    C -- "Rejeita" --> E2["Rejeitado no AP\\n(ALL não executa)"]\n'
        '    C -- "Aceita" --> D["Extração da fatia w:u\\nentre # e ;"]\n'
        '    D --> F["Etapa 2: ALL (D-LBA, 11 estados)\\nFita limitada < w:u >"]\n'
        '    F -- "Rejeita" --> E3["Aceito no AP\\nRejeitado no ALL"]\n'
        '    F -- "Aceita" --> OK["Aceito Integralmente"]\n'
        "```\n"
    )


def generate_all_artifacts(output_dir: Path = DIAGRAMS_DIR) -> None:
    """Escreve todos os arquivos .jff e .md em docs/diagramas/AV2/."""
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "glc.jff").write_text(build_glc_jff(), encoding="utf-8")
    (output_dir / "ap.jff").write_text(build_ap_jff(), encoding="utf-8")
    (output_dir / "all.jff").write_text(build_all_jff(), encoding="utf-8")
    (output_dir / "ap.md").write_text(build_ap_mermaid_md(), encoding="utf-8")
    (output_dir / "all.md").write_text(build_all_mermaid_md(), encoding="utf-8")
    (output_dir / "arquitetura.md").write_text(build_architecture_mermaid_md(), encoding="utf-8")


if __name__ == "__main__":
    generate_all_artifacts()
    print(f"Artefatos JFLAP e Mermaid gerados em: {DIAGRAMS_DIR}")
