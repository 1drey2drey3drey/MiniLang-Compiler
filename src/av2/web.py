"""Servidor HTTP embutido (stdlib) para a Interface Web Interativa da AV2.

Execução:
    python -m src.av2.web
    python -m src.av2.web --port 8080 --no-browser
"""

from __future__ import annotations

import argparse
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from typing import Any, Tuple
import webbrowser

from .all_lba import construir_all
from .ap import construir_ap
from .cases import CASOS_ALL, CASOS_AP, CASOS_ERRO_LEXICO, CASOS_INTEGRACAO
from .glc import construir_glc
from .minilang_source import MINILANG_PRESETS, compilar_minilang, sintetizar_minilang_para_caso
from .pipeline import validar_entrada
from .spec import (
    ALL_FINAL_STATES,
    ALL_INITIAL_STATE,
    ALL_INPUT_ALPHABET,
    ALL_STATE_DESCRIPTIONS,
    ALL_STATES,
    ALL_TAPE_ALPHABET,
    ALL_TRANSITIONS,
    AP_FINAL_STATES,
    AP_INITIAL_STATE,
    AP_INPUT_ALPHABET,
    AP_STACK_ALPHABET,
    AP_STATE_DESCRIPTIONS,
    AP_STATES,
    AP_TRANSITIONS,
    GLC_NON_TERMINALS,
    GLC_PRODUCTIONS,
    GLC_START_SYMBOL,
    GLC_TERMINALS,
    LEFT_MARKER,
    RIGHT_MARKER,
    STACK_INITIAL,
)

STATIC_DIR = Path(__file__).resolve().parent / "static"

CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
}


def build_spec_payload() -> dict[str, Any]:
    """Serializa especificações formais da GLC, AP, ALL e catálogo oficial de casos."""
    return {
        "project": {
            "name": "MiniLang-Compiler (AV2)",
            "subtitle": "Validador em Duas Etapas: MiniParser (GLC + AP) → MiniSemantic (LSC + ALL)",
            "team": ["Andrey Lourival Andrade Garcia", "Igor Cecim Vilhena"],
            "class": "CC6NA",
        },
        "glc": {
            "non_terminals": list(GLC_NON_TERMINALS),
            "terminals": list(GLC_TERMINALS),
            "start_symbol": GLC_START_SYMBOL,
            "productions": [
                {"id": p.id, "lhs": p.lhs, "rhs": p.rhs_str, "text": str(p)}
                for p in GLC_PRODUCTIONS
            ],
        },
        "ap": {
            "states": list(AP_STATES),
            "state_count": len(AP_STATES),
            "descriptions": AP_STATE_DESCRIPTIONS,
            "input_alphabet": list(AP_INPUT_ALPHABET),
            "stack_alphabet": list(AP_STACK_ALPHABET),
            "initial_state": AP_INITIAL_STATE,
            "initial_stack_symbol": STACK_INITIAL,
            "final_states": list(AP_FINAL_STATES),
            "acceptance": "Estado final (q8) com consumo integral da entrada",
            "transitions": [
                {
                    "from": t.from_state,
                    "read": t.read or "ε",
                    "pop": t.pop,
                    "to": t.to_state,
                    "push": t.push or "ε",
                    "label": t.label(),
                }
                for t in AP_TRANSITIONS
            ],
        },
        "all": {
            "states": list(ALL_STATES),
            "state_count": len(ALL_STATES),
            "descriptions": ALL_STATE_DESCRIPTIONS,
            "input_alphabet": list(ALL_INPUT_ALPHABET),
            "tape_alphabet": list(ALL_TAPE_ALPHABET),
            "left_marker": LEFT_MARKER,
            "right_marker": RIGHT_MARKER,
            "initial_state": ALL_INITIAL_STATE,
            "final_states": list(ALL_FINAL_STATES),
            "transitions": [
                {
                    "from": t.from_state,
                    "read": t.read,
                    "to": t.to_state,
                    "write": t.write,
                    "move": t.move,
                    "label": t.label(),
                }
                for t in ALL_TRANSITIONS
            ],
        },
        "cases": {
            "ap": [c.to_dict() for c in CASOS_AP],
            "all": [c.to_dict() for c in CASOS_ALL],
            "integration": [c.to_dict() for c in CASOS_INTEGRACAO],
            "lexical": [c.to_dict() for c in CASOS_ERRO_LEXICO],
        },
        "minilang_presets": list(MINILANG_PRESETS),
    }


def run_all_tests_payload() -> dict[str, Any]:
    """Executa todos os casos oficiais da lauda e devolve tabela pronta para a UI."""
    ap = construir_ap()
    all_lba = construir_all()
    rows: list[dict[str, Any]] = []

    for c in CASOS_AP:
        res = ap.simular(c.entrada)
        rows.append(
            {
                **c.to_dict(),
                "minilang_code": sintetizar_minilang_para_caso(c),
                "obtido": res.accepted,
                "passou": res.accepted == c.esperado,
                "detalhe": res.reason,
                "passos": len(res.trace) - 1 if res.trace else 0,
            }
        )

    for c in CASOS_ALL:
        res = all_lba.simular(c.entrada)
        rows.append(
            {
                **c.to_dict(),
                "minilang_code": sintetizar_minilang_para_caso(c),
                "obtido": res.accepted,
                "passou": res.accepted == c.esperado,
                "detalhe": res.reason,
                "passos": len(res.trace) - 1 if res.trace else 0,
            }
        )

    for c in CASOS_INTEGRACAO:
        res = validar_entrada(c.entrada)
        passou = (res.overall_accepted == c.esperado) and (
            res.stage_stopped == c.etapa_parada_esperada
        )
        rows.append(
            {
                **c.to_dict(),
                "minilang_code": sintetizar_minilang_para_caso(c),
                "obtido": res.overall_accepted,
                "passou": passou,
                "etapa_parada": res.stage_stopped,
                "detalhe": res.summary,
                "passos": (
                    (len(res.ap_result.trace) - 1 if res.ap_result else 0)
                    + (len(res.all_result.trace) - 1 if res.all_result else 0)
                ),
            }
        )

    for c in CASOS_ERRO_LEXICO:
        if c.id == "LEX-01":
            res = validar_entrada(c.entrada)
            passou = (not res.overall_accepted) and (res.stage_stopped == "LEXICO") and bool(res.lexical_error)
            detalhe = res.lexical_error or res.summary
        else:
            res_all = all_lba.simular(c.entrada)
            passou = (not res_all.accepted) and bool(res_all.lexical_error)
            detalhe = res_all.lexical_error or res_all.reason
        rows.append(
            {
                **c.to_dict(),
                "minilang_code": sintetizar_minilang_para_caso(c),
                "obtido": False,
                "passou": passou,
                "etapa_parada": "LEXICO",
                "detalhe": detalhe,
                "passos": 0,
            }
        )

    passed = sum(1 for r in rows if r["passou"])
    return {
        "total": len(rows),
        "passed": passed,
        "failed": len(rows) - passed,
        "rows": rows,
    }


def dispatch_api(method: str, path: str, body: dict[str, Any] | None = None) -> Tuple[int, dict[str, Any]]:
    """Roteador puro de API (facilmente testável sem precisar abrir socket)."""
    if method == "GET" and path == "/api/spec":
        return HTTPStatus.OK, build_spec_payload()

    if method == "GET" and path == "/api/tests/run":
        return HTTPStatus.OK, run_all_tests_payload()

    if method == "POST":
        payload = body or {}
        cadeia = payload.get("input", "")
        if not isinstance(cadeia, str):
            return HTTPStatus.BAD_REQUEST, {"error": "O campo 'input' deve ser string."}

        if path == "/api/compile/minilang":
            source = payload.get("source", "")
            if not isinstance(source, str):
                return HTTPStatus.BAD_REQUEST, {"error": "O campo 'source' deve ser string."}
            return HTTPStatus.OK, compilar_minilang(source)

        if path == "/api/validate/pipeline":
            return HTTPStatus.OK, validar_entrada(cadeia).to_dict()

        if path == "/api/validate/ap":
            ap_res = construir_ap().simular(cadeia)
            deriv = None
            if ap_res.accepted:
                deriv = [d.to_dict() for d in construir_glc().derivar_esquerda(cadeia)]
            return HTTPStatus.OK, {"ap_result": ap_res.to_dict(), "derivation": deriv}

        if path == "/api/validate/all":
            all_res = construir_all().simular(cadeia)
            return HTTPStatus.OK, {"all_result": all_res.to_dict()}

    return HTTPStatus.NOT_FOUND, {"error": f"Rota não encontrada: {method} {path}"}


class AV2RequestHandler(BaseHTTPRequestHandler):
    """Handler HTTP servindo assets estáticos e endpoints JSON da AV2."""

    def log_message(self, format: str, *args: object) -> None:
        return  # Mantém o terminal limpo durante a apresentação

    def _send_bytes(self, status: int, content_type: str, data: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self._send_bytes(status, CONTENT_TYPES[".json"], data)

    def do_GET(self) -> None:  # noqa: N802
        clean_path = self.path.split("?", 1)[0]
        if clean_path.startswith("/api/"):
            status, payload = dispatch_api("GET", clean_path)
            self._send_json(status, payload)
            return

        rel = "index.html" if clean_path in ("", "/") else clean_path.lstrip("/")
        target = (STATIC_DIR / rel).resolve()
        if not target.is_relative_to(STATIC_DIR) or not target.is_file():
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "Arquivo não encontrado."})
            return

        ctype = CONTENT_TYPES.get(target.suffix.lower(), "application/octet-stream")
        self._send_bytes(HTTPStatus.OK, ctype, target.read_bytes())

    def do_POST(self) -> None:  # noqa: N802
        clean_path = self.path.split("?", 1)[0]
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length > 0 else b"{}"
        try:
            body = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "JSON inválido."})
            return

        status, payload = dispatch_api("POST", clean_path, body)
        self._send_json(status, payload)


def create_server(host: str = "127.0.0.1", port: int = 8000) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), AV2RequestHandler)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Interface Web Interativa — MiniLang-Compiler (AV2)")
    parser.add_argument("--host", default="127.0.0.1", help="Endereço de escuta (padrão: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Porta HTTP (padrão: 8000)")
    parser.add_argument("--no-browser", action="store_true", help="Não abre o navegador automaticamente")
    args = parser.parse_args(argv)

    server = create_server(args.host, args.port)
    url = f"http://{args.host}:{args.port}/"
    print(f"MiniLang-Compiler (AV2) — Interface Web Interativa rodando em {url}")
    print("Pressione Ctrl+C para encerrar.")
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor encerrado.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
