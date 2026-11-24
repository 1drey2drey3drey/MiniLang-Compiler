# MiniLang-Compiler — Analisador Léxico (AV1), Sintático (GLC + AP) e Semântico (LSC + ALL)

Repositório derivado de [`1drey2drey3drey/MiniLang-MiniLexer`](https://github.com/1drey2drey3drey/MiniLang-MiniLexer) (preservando todo o histórico Git e os 135 testes da AV1), evoluído para atender integralmente à **Atividade Prática AV2 de Linguagens Formais e Autômatos** (CESUPA — Turma **CC6NA**, entrega e apresentação em **25/11/2026**).

- **Equipe:** Andrey Lourival Andrade Garcia e Igor Cecim Vilhena
- **Docente:** Prof. Daniel Leal Souza
- **Fonte de verdade formal da AV2:** [`MiniLang_AV2_Guia_Projeto.md`](MiniLang_AV2_Guia_Projeto.md)

---

## Visão Geral do Problema (AV2)

A aplicação valida cadeias formais da linguagem `MiniLang` em **duas etapas sequenciais**:

1. **Etapa 1 — `MiniParser` (GLC LL(1) + AP Determinístico de 9 estados):**
   - Valida a estrutura sintática $L_1 = \{ \texttt{p\{}\alpha\texttt{\}\#}w\texttt{:}u\texttt{;} \mid \alpha \in D_2^*, \, w, u \in \{\texttt{i}, \texttt{s}\}^+ \}$, exigindo cabeçalho `p`, blocos `{...}` e expressões `(...)` balanceados (linguagem livre de contexto **não-regular**), separador `#`, tipos da assinatura (`i` = `int`, `s` = `string`), `:`, tipos da chamada e terminador `;`.
   - Aceitação por **estado final (`q8`) com consumo integral da entrada** e rastreamento completo de `(estado, posição, pilha)`.
2. **Etapa 2 — `MiniSemantic` (LSC + ALL Determinístico de 11 estados):**
   - Executa **somente se o AP aceitar**. Recebe a fatia semântica `w:u` (entre `#` e `;`) em uma fita estritamente limitada de **$n$ células graváveis + 2 marcadores fixos de borda (`<` e `>`)**.
   - Valida $L_2 = \{ w\texttt{:}w \mid w \in \{\texttt{i}, \texttt{s}\}^+ \}$ (linguagem sensível ao contexto **não-livre de contexto**), garantindo **mesma aridade e mesma ordem posicional de tipos** entre assinatura e chamada de função, com rastreamento completo de `(estado, fita, cabeçote)`.

---

## Estrutura do Projeto

```text
MiniLang-Compiler/
├── MiniLang_AV2_Guia_Projeto.md     # Especificação formal (fonte de verdade AV2)
├── MiniLang_Guia_Projeto.md         # Especificação formal preservada (AV1)
├── README.md
├── COMANDOS_APRESENTACAO.md         # Roteiro de demonstração ao vivo (15 min)
├── CONTRIBUICOES.md                 # Registro de contribuições da equipe
├── DECLARACAO_IA.md                 # Declaração detalhada de uso de IA
├── requirements.txt                 # pytest>=8,<9 (motor e Web UI usam apenas stdlib)
├── examples/
│   ├── av2_cenarios.txt             # Cenários oficiais de integração e erro léxico (AV2)
│   ├── valido.min / invalido.min    # Exemplos preservados da AV1
├── src/
│   ├── av2/                         # Motor formal, CLI, Web UI e exportador JFLAP da AV2
│   │   ├── spec.py                  # Fonte única: GLC, AP (9 estados) e ALL (11 estados)
│   │   ├── glc.py                   # GLC + derivação mais à esquerda passo a passo
│   │   ├── ap.py                    # Simulador DPDA com trace e validação de alfabeto
│   │   ├── all_lba.py               # Simulador D-LBA com invariantes de fita limitada
│   │   ├── pipeline.py              # Fluxo integrado AP → extração → ALL + ponte MiniLang
│   │   ├── minilang_source.py       # Ponte MiniLexer (AV1) → Σ_AP + error_span + 50 códigos MiniLang
│   │   ├── cases.py                 # Catálogo dos 50 casos oficiais da lauda
│   │   ├── jflap_io.py              # Gerador e validador XML para JFLAP 7.1
│   │   ├── cli.py                   # Interface de linha de comando
│   │   ├── web.py                   # Servidor HTTP stdlib + API JSON
│   │   └── static/                  # Interface Web Hacker/Shell (7 sessões, grafos SVG, fullscreen)
│   └── (automata.py, lexer.py, patterns.py, tokens.py, main.py — preservados da AV1)
├── docs/
│   ├── diagramas/AV2/               # glc.jff, ap.jff, all.jff + diagramas Mermaid
│   ├── diagramas/ER-01..ER-06/      # Diagramas preservados da AV1
│   ├── relatorio_av2/               # Relatório técnico AV2 (LaTeX modular + HTML para PDF)
│   └── apresentacao_av2/            # Slides HTML (exportáveis p/ PDF) + guia de arguição
└── tests/
    ├── test_av2_glc.py              # Testes da GLC e derivações
    ├── test_av2_ap.py               # Testes do AP (10+10+2), estrutura e ap.jff
    ├── test_av2_all.py              # Testes do ALL (10+10+3), fita limitada, exaustivo e all.jff
    ├── test_av2_pipeline.py         # Integração (3 cenários), erro léxico, CLI e API Web
    ├── validate_av2_jflap_runtime.py / JflapAv2RuntimeCheck.java  # Validação real no JFLAP 7.1
    └── (testes preservados da AV1 — 135 testes aprovados)
```

---

## Instalação e Execução

Requer **Python 3.11+** (o motor formal e a Interface Web Interativa utilizam apenas a biblioteca padrão do Python; `pytest` é usado para a suíte automatizada).

```powershell
# 1. Criar ambiente virtual e instalar pytest
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 1. Interface Web Interativa (recomendada para demonstração ao vivo)

```powershell
.\.venv\Scripts\python.exe -m src.av2.web
```

Abre `http://127.0.0.1:8000/` com interface estilo shell/IDE em **7 sessões** (`./run`, `./ap`, `./all`, `./glc`, `./suite`, `./specs`, `./man`):
- **Editor `programa.min` + modo `raw` sincronizados:** destaque de erro com sublinhado ondulado estilo IDE (`~~~~`), projeção transparente de tokens do `MiniLexer` (AV1) para $\Sigma_{\text{AP}}$ e faixa visual colorida no modo `raw`;
- **Grafos SVG interativos dos autômatos (`AP` 9 estados e `ALL` 11 estados)** com destaque em tempo real do estado ativo, da aresta disparada e modo **`⛶ fullscreen`** (com controles de reprodução);
- Animação passo a passo da **Pilha vertical (AP)**, da **Fita Limitada com `<` e `>` (ALL)** e da **Derivação da GLC**;
- Bateria dos **50 casos oficiais da lauda** em `./suite` (cada caso com código `MiniLang` sintetizado via `code →` e simulação direta via `sim →`).

### 2. Interface de Linha de Comando (CLI)

```powershell
# Cenário 1: Aceito pelo AP e aceito pelo ALL (30 chars; fatia ALL de 19 chars)
.\.venv\Scripts\python.exe -m src.av2.cli "p{(()){}}#isisiisis:isisiisis;"

# Cenário 2: Rejeitado pelo AP (ALL não executa)
.\.venv\Scripts\python.exe -m src.av2.cli "p{(()){}#isisiisis:isisiisis;"

# Cenário 3: Aceito pelo AP e rejeitado pelo ALL (erro de ordem posicional)
.\.venv\Scripts\python.exe -m src.av2.cli "p{(()){}}#isisiisis:isisiissi;"

# Erro léxico (símbolo fora do alfabeto)
.\.venv\Scripts\python.exe -m src.av2.cli "p{(()){}}#isisi@isisi;"

# Modos isolados e bateria completa da lauda
.\.venv\Scripts\python.exe -m src.av2.cli --mode ap "p{(()){}}#isisi:isisi;"
.\.venv\Scripts\python.exe -m src.av2.cli --mode all "isisiisis:isisiisis"
.\.venv\Scripts\python.exe -m src.av2.cli --suite
```

### 3. Testes Automatizados (`pytest`)

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

Resultado esperado: **227 passed** (135 testes preservados da AV1 + 92 testes da AV2, incluindo enumeração exaustiva de 3.280 cadeias no ALL).

### 4. Validação Real no Motor Oficial do JFLAP 7.1

Requer JDK 11+ e o arquivo `JFLAP7.1.jar`:

```powershell
.\.venv\Scripts\python.exe .\tests\validate_av2_jflap_runtime.py "C:\caminho\para\JFLAP7.1.jar"
```

Resultado esperado:
```text
GLC (glc.jff): carregada pelo JFLAP 7.1 com 9 producoes
AP (ap.jff): 9 estados, 0 estados nao-deterministicos, 34 casos, 0 divergencias
ALL (all.jff): 11 estados, 384 casos, 0 divergencias
JFLAP AV2: 418 casos, 0 divergencias
```

---

## Originalidade, Origem dos Artefatos e Uso de Inteligência Artificial

A modelagem é própria e original (evolução da linguagem `MiniLang` da AV1 para validação sintática de escopos + checagem semântica posicional de assinatura/chamada de função, distinta dos exercícios de sala e do exemplo da lauda).

- **Herdado da AV1 ([`MiniLang-MiniLexer`](https://github.com/1drey2drey3drey/MiniLang-MiniLexer)):** analisador léxico (`src/automata.py`, `src/lexer.py`, `src/patterns.py`, `src/tokens.py`, `src/main.py`), diagramas `docs/diagramas/ER-01..ER-06/`, relatório da AV1 (`docs/relatorio/`), suíte de 135 testes da AV1 e o padrão do harness Java (`tests/JflapRuntimeCheck.java`).
- **Desenvolvido para a AV2:** todo o pacote `src/av2/` (motor formal `GLC`, `AP`, `ALL`, pipeline, ponte `MiniLang`, CLI e Interface Web Interativa com grafos SVG), `docs/diagramas/AV2/` (`glc.jff`, `ap.jff`, `all.jff` e diagramas Mermaid), `tests/test_av2_*.py`, `tests/JflapAv2RuntimeCheck.java`, `docs/relatorio_av2/` e `docs/apresentacao_av2/`.
- **Uso de IA:** ferramentas de IA foram utilizadas como apoio na estruturação, implementação e revisão de testes, conforme detalhado em [`DECLARACAO_IA.md`](DECLARACAO_IA.md). Toda a modelagem formal, as provas, os 227 testes automatizados e a validação real nos arquivos `.jff` via `JFLAP7.1.jar` foram verificados pela equipe.
