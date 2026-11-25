# Guia de Arguição Individual — MiniLang-Compiler (AV2)

A demonstração (0,90 pt) e a **arguição individual (1,20 pt)** somam **70% da nota (2,10 de 3,00 pts)**. A lauda avisa exatamente os 4 pontos cobrados de **cada integrante** (Andrey e Igor):

1. **Explicar a relação entre a GLC e o AP.**
2. **Justificar a regra do ALL e o limite da fita.**
3. **Prever a decisão para uma entrada nova proposta pelo professor na hora**, sustentando a resposta pelas operações reais da pilha ou da fita.
4. **Comentar uma limitação observada nos testes.**

---

## 1. Cronograma Sincronizado dos 15 Minutos (14 Slides → Web IDE → JFLAP)

| Bloco | Tempo | Responsável | Conteúdo / O que apontar |
|---|---|---|---|
| **Slides 1–7** | 0:00 – 4:00 | **Igor** | Capa → Conceito × Tema → **O que é ER** → Conexão AP→ALL → Bombeamento ($L_1, L_2$) → **O que é AP** → GLC LL(1). |
| **Slides 8–12** | 4:00 – 6:50 | **Andrey** | Pilha na prática (5 quadros) → Grafo AP (9 estados) → **O que é ALL** → Fita Limitada na prática (3 fitas) → Grafo ALL (11 estados). |
| **Slides 13–14** | 6:50 – 8:00 | **Igor + Andrey** | **Slide 13 (Igor):** 50/50 lauda, 92 `pytest`, 418 JFLAP, 4 cenários e **3 limitações**. **Slide 14 (Ambos):** equipe, IA e transição para demo. |
| **Web IDE** | 8:00 – 12:30 | **Andrey + Igor** | `./run` nos 4 cenários + `token_projection.log` + modo `raw`; `./ap` e `./all` em **`⛶ fullscreen`**; `./glc` e `./suite` (`50/50` + `code →`). |
| **JFLAP & Testes** | 12:30 – 14:00 | **Andrey + Igor** | Mostrar `glc.jff`, `ap.jff`, `all.jff` no JFLAP 7.1 GUI + rodar `validate_av2_jflap_runtime.py` (`418 casos, 0 divergências`) e `pytest` (`92 passed`). |
| **Arguição** | 14:00 – 15:00+ | **Ambos** | Prever **antes de executar** qualquer entrada nova ditada pelo professor e comprovar em `./run` (`raw`). |

---

## 2. Respostas Diretas às Perguntas Garantidas da Arguição

### P1: "Qual é a relação entre a GLC e o AP de vocês?"
- A GLC gera `p{ B }# T : T ;` (`B` gera `{}` e `()` balanceados; `T` gera `{i,s}+`).
- No AP: `q0 → q1 → q2` consome `p{` e empilha `{` sobre `Z`. Em `q2`, abre `{`/`(` empilha e fecha `}`/`)` desempilha — espelhando exatamente `B`. Quando o `}` externo fecha, a pilha volta a `Z`, disparando a única $\varepsilon$-transição determinística `(q2, ε, Z) → (q3, Z)`. De `q3` a `q8`, valida `#`, `T`, `:`, `T` e `;` (`q8` final com consumo integral da entrada).

### P2: "Essa transição `(q2, ε, Z) → (q3, Z)` não deixa o AP não-determinístico?"
- **Não!** Em `q2`, todas as transições de leitura exigem topo `{` ou `(` — nenhuma lê `Z`. Logo, com topo `Z`, existe apenas essa saída. O `PDANondeterminismDetector` do JFLAP 7.1 confirmou **0 estados não-determinísticos**.

### P3: "O tradutor de `MiniLang` não está fazendo o trabalho do AP/ALL fora dos autômatos?"
- **Não!** Ele apenas tokeniza com o `MiniLexer` (AV1) e projeta símbolos 1:1 (visível em `token_projection.log`), sem checar balanceamento nem comparar tipos. E no modo **`raw`**, CLI e JFLAP, os autômatos rodam diretamente sobre $\Sigma_{\text{AP}}$ e $\Sigma_{\text{ALL}}$.

### P4: "Como o ALL respeita o limite da fita e por que sempre termina?"
- Para entrada `w:u` de tamanho $n$, aloca exatamente $n$ células graváveis (`1..n`) + `<` (pos `0`) e `>` (pos `n+1`). Apenas `(q0, <) → (q1, <, R)` lê `<` e apenas `(q9, >) → (q10, >, L)` lê `>`. Em `q7`, existe sempre um `I`/`S` já marcado à direita de `<`, impedindo tocar a borda esquerda.
- **Terminação:** AP para em $\le n + 1$ passos ($O(n)$); ALL marca irreversivelmente 1 par `{i,s} → {I,S}` por ciclo ⇒ no máximo $\lfloor n/2 \rfloor$ ciclos ⇒ $O(n^2)$.

### P5: "Qual limitação vocês observaram nos testes?"
- **1) Crescimento quadrático $O(n^2)$ em fita única:** fatia de 19 chars (`INT-01`) exige **201 passos** no ALL.
- **2) Subconjunto de 2 tipos (`i`, `s`):** cada novo tipo (`float`, `bool`) exigiria +2 estados no ALL.
- **3) Assinatura única por unidade:** múltiplas funções exigiriam identificadores e tabela auxiliar na fita.

---

## 3. Checklist Rápido para Prever Qualquer Entrada Nova na Hora

1. **Alfabeto ($\Sigma_{\text{AP}}$):** caractere fora de `{p, {, }, (, ), #, i, s, :, ;}` → **Erro léxico** (AP e ALL não executam).
2. **Etapa 1 (AP — Pilha):**
   - Começa com `p{`? Simule a pilha nos `{ } ( )`.
   - Fechou `}` externo antes de `#` (ex.: `p{}{}#i:i;`) → topo vira `Z` → `q3` espera `#` e **rejeita** em `{`.
   - Sobrou `{`/`(` na pilha ao chegar em `#` → **rejeita em `q2`** (ALL não executa).
   - Assinatura/chamada vazia, falta `;`, ou sobra após `;` → **rejeita em `q4..q8`**.
3. **Etapa 2 (ALL — Fita `< w:u >`):** *(só se o AP aceitou!)*
   - 1º símbolo diferente (`i` vs `s`): **`q4`/`q5` rejeita** (tipo/ordem).
   - Direita menor (`|u| < |w|`): **`q4`/`q5` bate em `>` e rejeita** (aridade menor).
   - Direita maior (`|u| > |w|`): **`q9` encontra `i`/`s` sobrando antes de `>` e rejeita** (aridade maior).
   - Iguais (`w = u`): **`q9` lê `>`, move `L` e aceita em `q10`**.
