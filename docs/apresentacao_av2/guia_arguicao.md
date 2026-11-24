# Guia de Arguição Individual — MiniLang-Compiler (AV2)

A demonstração (0,90 pt) e a **arguição individual (1,20 pt)** somam **70% da nota (2,10 de 3,00 pts)**. A lauda avisa exatamente o que o professor vai cobrar de **cada integrante** (Andrey e Igor):

1. **Explicar a relação entre a GLC e o AP.**
2. **Justificar a regra do ALL e o limite da fita.**
3. **Prever a decisão para uma entrada nova proposta pelo professor na hora**, sustentando a resposta pelas operações reais da pilha ou da fita.
4. **Comentar uma limitação observada nos testes.**

---

## 1. Divisão sugerida dos 15 minutos de apresentação

- **Minutos 0–3 (Igor):** Contextualização (evolução do `MiniLexer` da AV1 → Hierarquia de Chomsky completa), definição das linguagens $L_1$ e $L_2$ e provas pelo Lema do Bombeamento.
- **Minutos 3–6 (Igor):** GLC ($P_1$–$P_9$), derivação passo a passo de `p{(()){}}#isisi:isisi;` e relação com o AP de 9 estados.
- **Minutos 6–9 (Andrey):** ALL de 11 estados, fita estritamente limitada (`<` e `>` fixos, $n$ células graváveis), determinismo e prova de terminação ($O(n)$ e $O(n^2)$).
- **Minutos 9–13 (Andrey + Igor juntos):** Demo ao vivo na Interface Web Interativa:
  - Cenário 1 (`p{(()){}}#isisiisis:isisiisis;`) — mostrar animação da Pilha e da Fita Limitada + derivação.
  - Cenário 2 (`p{(()){}#isisiisis:isisiisis;`) — mostrar AP rejeitando em `q2` e ALL sem execução.
  - Cenário 3 (`p{(()){}}#isisiisis:isisiissi;`) — mostrar AP aceitando e ALL rejeitando em `q4`.
  - Erro léxico (`p{(()){}}#isisi@isisi;`).
- **Minutos 13–15 (Igor + Andrey):** Bateria de testes (50 casos oficiais, 227 no `pytest`, 418 no `JFLAP7.1.jar` com 0 divergências) + limitações observadas.

---

## 2. Respostas diretas às perguntas garantidas da arguição

### P1: "Qual é a relação entre a GLC e o AP de vocês?"
- **Resposta curta:** A GLC gera `p{ B }# T : T ;` (onde `B` gera blocos `{}` e parênteses `()` balanceados e `T` gera `{i,s}+`). No AP:
  - `q0 → q1 → q2` consome `p{` e empilha `{` sobre `Z`.
  - Em `q2`, toda vez que abre `{` ou `(`, o AP **empilha**; toda vez que fecha `}` ou `)`, ele **desempilha** o símbolo correspondente do topo — mantendo na pilha exatamente os escopos abertos de `B`.
  - Quando o `}` externo fecha, a pilha volta para `Z`, disparando a única $\varepsilon$-transição determinística `(q2, ε, Z) → (q3, Z)`.
  - De `q3` a `q8`, o AP valida `#`, `T` (`q4→q5`), `:`, `T` (`q6→q7`) e `;` (`q8`, estado final com consumo total da entrada).

### P2: "Por que o AP não consegue fazer o trabalho do ALL?"
- **Resposta curta:** A pilha do AP é **LIFO** (último a entrar, primeiro a sair) — ela consegue casar **espelhamento/palíndromo** ($w w^R$), mas não consegue casar **cópia direta na mesma ordem** ($w\texttt{:}w$) porque o primeiro símbolo de `w` fica no fundo da pilha! Formalmente, provamos pelo Lema do Bombeamento para LLCs em $z = \texttt{i}^p\texttt{s}^p\texttt{:}\texttt{i}^p\texttt{s}^p$ que $L_2 \notin \text{LLC}$.

### P3: "Como funciona o limite da fita do ALL e por que o cabeçote nunca escapa?"
- **Resposta curta:** Para uma entrada `w:u` de $n$ símbolos, a fita tem exatamente **$n$ células graváveis** (`1..n`) + **2 marcadores fixos** (`<` na posição `0` e `>` na posição `n+1`). Todo o casamento é feito **in-place** trocando `i→I` e `s→S` nas próprias células da entrada.
  - Em `<`, só existe `(q0, <) → (q1, <, R)` (nunca move `L`, nunca sobrescreve `<`).
  - Em `>`, só existe `(q9, >) → (q10, >, L)` (nunca move `R`, nunca sobrescreve `>`).
  - Ao voltar à esquerda em `q7`, sempre há um `I` ou `S` já marcado à direita de `<`, então o cabeçote para antes de `<` e vai para `q8`.

### P4: "Por que o programa sempre termina? E se houver não-determinismo?"
- **Resposta curta:** Ambos os autômatos são **100% determinísticos** (0 estados não-determinísticos confirmados pelo `PDANondeterminismDetector` do JFLAP 7.1), então há um único caminho por entrada.
  - **AP:** toda transição consome 1 símbolo, exceto `(q2, ε, Z) → (q3, Z)` que sai de `q2` para sempre → para em no máximo $n + 1$ passos ($O(n)$).
  - **ALL:** cada volta marca irreversivelmente 1 símbolo de cada lado (`{i,s} → {I,S}`), com varreduras lineares monotônicas → no máximo $\lfloor n/2 \rfloor$ ciclos → sempre para em $O(n^2)$ passos.

---

## 3. Checklist rápido para prever uma entrada nova do professor na hora!

Quando o professor escrever uma cadeia nova no quadro, siga estes 4 passos falando em voz alta:

1. **Alfabeto ($\Sigma_{\text{AP}}$):** Tem algum caractere fora de `{p, {, }, (, ), #, i, s, :, ;}`?
   - **Se sim:** *Rejeita por erro léxico antes de rodar AP e ALL.*
2. **Etapa 1 (AP — Pilha):**
   - Começa com `p{`? (`q0→q1→q2`, pilha `{Z`).
   - Simule a pilha nos `{ } ( )`: abriu empilha, fechou desempilha o mesmo tipo.
   - Se o `}` externo fechar **antes** de `#` (ex.: `p{}{}#...`), em `q2` o topo vira `Z` → `q3` espera `#` e **rejeita** ao ler `{`!
   - Se sobrar `{` ou `(` na pilha ao chegar em `#`, `q2` não tem transição para `#` → **rejeita em `q2`** (ALL não executa)!
   - Depois de `#`, tem pelo menos 1 `{i,s}`, um único `:`, pelo menos 1 `{i,s}` e termina exatamente em `;` (sem sobras)? Se faltar algo, **rejeita em `q3..q8`** (ALL não executa)!
3. **Etapa 2 (ALL — Fita `< w:u >`):** *(só se o AP aceitou!)*
   - Compare `w` e `u` **posição por posição**:
   - **1º símbolo diferente** (`i` na esq. vs `s` na dir., ou vice-versa): `q2→q4` lê `s` (ou `q3→q5` lê `i`) → **rejeita por incompatibilidade de tipo/ordem**!
   - **Direita mais curta** (`|u| < |w|`): `q4` ou `q5` bate no marcador `>` → **rejeita por erro de aridade**!
   - **Direita mais longa** (`|u| > |w|`): `q8` lê `:` e entra na varredura final `q9`, que encontra `i` ou `s` sobrando antes de `>` → **rejeita por erro de aridade**!
   - **Exatamente iguais (`w = u`):** `q9` passa por todos os `I`/`S`, lê `>`, move `L` e entra em **`q10` → ACEITA**!
