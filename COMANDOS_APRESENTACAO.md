# Comandos e Roteiro para Apresentação — MiniLang-Compiler (AV2)

Execute todos os comandos a partir da **raiz do repositório** (`MiniLang-Compiler`).

## 0. Preparação (antes de entrar em sala)

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 1. Subir a Interface Web Interativa (demonstração principal — projetor)

```powershell
.\.venv\Scripts\python.exe -m src.av2.web
```

Na interface (`http://127.0.0.1:8000/`):
1. **`./run` (Frontpage — Editor `programa.min` + `raw` sincronizados):** mostrar os 4 cenários na barra única `$ cenários:`:
   - **`--valid (INT-01)` (`p{(()){}}#isisiisis:isisiisis;` — 30 chars):** `program matricula` aceito nas 3 etapas (abrir gaveta `token_projection.log` para mostrar projeção mecânica via `MiniLexer`).
   - **`--err-scope (INT-02)` (`p{(()){}#isisiisis:isisiisis;` — 29 chars):** `program folha_pagamento` com sublinhado vermelho no `{` aberto; AP rejeita em `q2` e **ALL não executa**.
   - **`--err-types (INT-03)` (`p{(()){}}#isisiisis:isisiissi;` — 30 chars):** `program envio_pedido` com sublinhado âmbar em `"rj"`; AP aceita a sintaxe, **ALL rejeita em `q4`**.
   - **`--err-lex (LEX-01)`:** `program autenticacao` com sublinhado vermelho em `@` bloqueado antes dos autômatos.
   - Alternar para **`raw`** para mostrar o visualizador colorido por símbolo (e receber qualquer cadeia ditada pelo professor na arguição!).
2. **`./ap`, `./all` e `./glc`:** usar **`⛶ fullscreen`** nos grafos SVG (estado ativo em verde / rejeição em vermelho / aresta em ciano) com controles `◀ ▶/⏸ ▶` + torre da pilha, fita limitada `<` `>` e derivação passo a passo.
3. **`./suite`:** mostrar os **50/50 casos aprovados** (com `code →` para abrir qualquer teste rejeitado como código `MiniLang` e `sim →` para simular).

## 2. Demonstração rápida via CLI (opcional / backup)

```powershell
# Cenário 1 (AP aceita + derivação GLC + ALL aceita)
.\.venv\Scripts\python.exe -m src.av2.cli "p{(()){}}#isisiisis:isisiisis;" --max-trace 20

# Cenário 2 (AP rejeita, ALL não executa)
.\.venv\Scripts\python.exe -m src.av2.cli "p{(()){}#isisiisis:isisiisis;"

# Cenário 3 (AP aceita, ALL rejeita)
.\.venv\Scripts\python.exe -m src.av2.cli "p{(()){}}#isisiisis:isisiissi;" --max-trace 25

# Erro léxico (símbolo fora do alfabeto)
.\.venv\Scripts\python.exe -m src.av2.cli "p{(()){}}#isisi@isisi;"

# Tabela completa dos 50 casos oficiais da lauda
.\.venv\Scripts\python.exe -m src.av2.cli --suite
```

## 3. Rodar a suíte completa de testes (`pytest`)

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

Resultado esperado: **`227 passed`** (135 da AV1 + 92 da AV2).

## 4. Validação real nos arquivos `.jff` usando o `JFLAP7.1.jar`

```powershell
.\.venv\Scripts\python.exe .\tests\validate_av2_jflap_runtime.py "C:\Users\Andrey\Downloads\JFLAP7.1.jar"
```

Resultado esperado:
```text
GLC (glc.jff): carregada pelo JFLAP 7.1 com 9 producoes
AP (ap.jff): 9 estados, 0 estados nao-deterministicos, 34 casos, 0 divergencias
ALL (all.jff): 11 estados, 384 casos, 0 divergencias
JFLAP AV2: 418 casos, 0 divergencias
```

## 5. Abrir os diagramas no JFLAP 7.1 (visual)

- `docs/diagramas/AV2/glc.jff`
- `docs/diagramas/AV2/ap.jff`
- `docs/diagramas/AV2/all.jff`
