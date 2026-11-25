# Comandos e Roteiro Sincronizado — MiniLang-Compiler (AV2)

Roteiro 100% sincronizado com os **14 slides didáticos em pontos (ER · AP · ALL)** ([`slides.html`](docs/apresentacao_av2/slides.html) / [`slides_av2.pdf`](docs/apresentacao_av2/slides_av2.pdf)), a **Web IDE** e o **JFLAP 7.1** (~15 minutos totais: **8 min slides + 4,5 min Web IDE + 1,5 min JFLAP/testes + 1 min arguição**).

Execute os comandos a partir da **raiz do repositório** (`MiniLang-Compiler`).

---

## 0. Pré-Voo (2 minutos antes de começar)

1. **Aba 1 do navegador:** `docs/apresentacao_av2/slides.html` (tecla **`F`** tela cheia; **`←`/`→`** ou **`Espaço`** para navegar).
2. **Aba 2 do navegador (`http://127.0.0.1:8000/`):** subir a Web IDE:
   ```powershell
   .\.venv\Scripts\python.exe -m src.av2.web
   ```
3. **JFLAP 7.1** pré-aberto em segundo plano com:
   - `docs/diagramas/AV2/glc.jff`
   - `docs/diagramas/AV2/ap.jff`
   - `docs/diagramas/AV2/all.jff`

---

## 1. Parte 1 — Apresentação Oral nos Slides (0–8 min)

Cada slide tem **frase-tese no topo**, **pontos curtos** e **1 visual grande**.

### Igor — Slides 1 a 7 (~4 min)
- **Slide 1 (Capa — 0:20):** Equipe, disciplina e as 3 camadas (`ER → AP → ALL`).
- **Slide 2 (Conceito × Tema — 0:40):** Apontar o código `programa.min` e os 3 pontos: Léxico (ER), Escopos `{ } ( )` (AP) e Tipos na ordem (ALL).
- **Slide 3 (O que é ER no compilador — 0:35):** Explicar o papel da AV1 (`MiniLexer`): projeta `programa.min → Σ_AP` e barra `@` antes dos autômatos, mas não conta profundidade.
- **Slide 4 (Conexão AP → ALL — 0:35):** Anatomia de `INT-01` (30 chars) + 3 pontos (`INT-01` OK, `INT-02` AP trava e ALL skip, `INT-03` ALL rejeita).
- **Slide 5 (Chomsky & Bombeamento — 0:40):** Por que ER não resolve $L_1$ e por que Pilha (LIFO inverte) não resolve $L_2 = w\texttt{:}w$.
- **Slide 6 (O que é o AP no compilador — 0:35):** Pilha LIFO, papel do `MiniParser`, ficha técnica (9 estados, 20 transições, 0 não-det., $O(n)$).
- **Slide 7 (GLC LL(1) — 0:35):** 9 produções em 3 famílias + construção em 4 passos (`L(G) = L(AP)`).

### Andrey — Slides 8 a 12 (~2 min 50)
- **Slide 8 (Pilha na prática — 0:35):** 5 quadros da pilha empilhando/desempilhando até `Z` + erro `p{(()#i:i;` travando em `q2`.
- **Slide 9 (Diagrama do AP — 0:30):** Grafo completo (9 estados), destacando `ε,Z/Z` 100% determinística.
- **Slide 10 (O que é o ALL no compilador — 0:40):** Máquina de Turing limitada por `<` e `>`, papel do `MiniSemantic` (`w = u`), ficha técnica (11 estados, 28 transições, $O(n^2)$).
- **Slide 11 (Fita Limitada na prática — 0:35):** 3 fitas grandes de `isi:isi` (`i→I`, `s→S`) até `>` + erro `isi:iis` travando em `q5`.
- **Slide 12 (Diagrama do ALL — 0:30):** Grafo completo em 3 trilhas coloridas (`i→I` azul, `s→S` âmbar, retorno violeta, bordas verde).

### Andrey + Igor — Slides 13 e 14 (~1 min 10)
- **Slide 13 (Evidências & Limitações — 0:50 · Igor):** 4 KPIs (`50/50`, `92/92`, `418/418`, `3.280`), 4 cenários e 3 limitações.
- **Slide 14 (Equipe, IA & Transição — 0:20 · Ambos):** Divisão, `DECLARACAO_IA.md` e virar direto para a **Web IDE**.

---

## 2. Parte 2 — Plataforma Web IDE Ao Vivo (8–12,5 min)

Em `http://127.0.0.1:8000/`:
1. **`./run`:** clicar nos 4 cenários na barra `$ cenários:`:
   - **`--valid (INT-01)` (`matricula`):** aceito nas 3 etapas + abrir `token_projection.log`.
   - **`--err-scope (INT-02)` (`folha_pagamento`):** sublinhado vermelho no `{` aberto; AP rejeita em `q2`, ALL em **`SKIP`**.
   - **`--err-types (INT-03)` (`envio_pedido`):** sublinhado âmbar em `"rj"`; AP aceita, ALL rejeita em `q4`.
   - **`--err-lex (LEX-01)` (`autenticacao`):** `@` bloqueado no léxico.
   - Clicar em **`raw`** (pronto para cadeias ditadas pelo professor).
2. **`./ap` e `./all` (Andrey):** **`⛶ fullscreen`** nos grafos SVG + pilha vertical + fita `< >` (`⏭` até `q10`).
3. **`./glc` e `./suite` (Igor):** derivação (28 passos) e **50/50 casos** (`code →` em 1 caso rejeitado).

---

## 3. Parte 3 — JFLAP 7.1 + Testes Automatizados (12,5–14 min)

1. Mostrar rapidamente `glc.jff`, `ap.jff` (9 estados) e `all.jff` (11 estados) abertos no **JFLAP 7.1 GUI**.
2. Rodar no terminal:
   ```powershell
   .\.venv\Scripts\python.exe .\tests\validate_av2_jflap_runtime.py "C:\Users\Andrey\Downloads\JFLAP7.1.jar"
   .\.venv\Scripts\python.exe -m pytest -v
   ```
   Esperado: **`418 casos, 0 divergencias`** (`0 estados nao-deterministicos`) e **`92 passed`**.

---

## 4. Backup CLI (fora do navegador)

```powershell
.\.venv\Scripts\python.exe -m src.av2.cli "p{(()){}}#isisiisis:isisiisis;" --max-trace 20
.\.venv\Scripts\python.exe -m src.av2.cli "p{(()){}#isisiisis:isisiisis;"
.\.venv\Scripts\python.exe -m src.av2.cli "p{(()){}}#isisiisis:isisiissi;" --max-trace 25
.\.venv\Scripts\python.exe -m src.av2.cli "p{(()){}}#isisi@isisi;"
.\.venv\Scripts\python.exe -m src.av2.cli --suite
```
