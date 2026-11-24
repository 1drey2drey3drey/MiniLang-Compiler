# MiniLang-Compiler (AV2) — Guia Base e Especificação Formal

Este documento é a **fonte de verdade formal da AV2** do projeto `MiniLang-Compiler`, evolução direta do repositório `MiniLang-MiniLexer` (AV1). Toda implementação em `src/av2/spec.py`, os arquivos JFLAP em `docs/diagramas/AV2/`, os testes em `tests/test_av2_*.py` e o relatório técnico em `docs/relatorio_av2/` derivam exatamente desta especificação.

---

## 1. Contextualização e Hierarquia de Chomsky

O projeto completa os três níveis práticos de um mini-compilador para a linguagem educacional **MiniLang**:

| Fase do Compilador | Disciplina / Entrega | Nível de Chomsky | Formalismo | Módulo |
| :--- | :--- | :--- | :--- | :--- |
| Análise Léxica | AV1 (preservada) | Tipo 3 — Regular | ER + AFNε de Thompson | `src/lexer.py`, `src/automata.py` |
| **Análise Sintática** | **AV2 — Etapa 1** | **Tipo 2 — Livre de Contexto** | **GLC LL(1) + AP Determinístico (9 estados)** | `src/av2/glc.py`, `src/av2/ap.py` |
| **Análise Semântica** | **AV2 — Etapa 2** | **Tipo 1 — Sensível ao Contexto** | **LSC + ALL Determinístico (11 estados)** | `src/av2/all_lba.py` |

---

## 2. Etapa 1 — Linguagem Livre de Contexto ($L_1$), GLC e AP

### 2.1 Alfabeto e Regra de Formação
$$\Sigma_{\text{AP}} = \{ \texttt{p}, \texttt{\{}, \texttt{\}}, \texttt{(}, \texttt{)}, \texttt{\#}, \texttt{i}, \texttt{s}, \texttt{:}, \texttt{;} \}$$
- `p`: cabeçalho `program`;
- `{`, `}`: abertura/fechamento de blocos de escopo;
- `(`, `)`: abertura/fechamento de expressões/condições;
- `#`: separador entre a estrutura sintática de escopos e a declaração/chamada de função;
- `i`, `s`: tipos `int` e `string` da `MiniLang`;
- `:`: separador entre assinatura declarada e argumentos da chamada;
- `;`: terminador da unidade.

$$L_1 = \{ \texttt{p\{} \, \alpha \, \texttt{\}\#} \, w \, \texttt{:} \, u \, \texttt{;} \mid \alpha \in D_2^*, \; w \in \{\texttt{i}, \texttt{s}\}^+, \; u \in \{\texttt{i}, \texttt{s}\}^+ \}$$

onde $D_2^*$ é a linguagem de Dyck de blocos `{}` e parênteses `()` bem balanceados.

### 2.2 Prova de Não-Regularidade ($L_1 \notin \text{LR}$)
Pelo **Lema do Bombeamento para Linguagens Regulares** (Sipser, 2013; Hopcroft et al., 2007): suponha que $L_1$ seja regular com comprimento de bombeamento $p \ge 3$. Considere a cadeia $z = \texttt{p\{(}^p\texttt{)}^p\texttt{\}\#i:i;} \in L_1$. Para toda decomposição $z = xyz$ com $|xy| \le p$ e $|y| \ge 1$, o fator $y$ ocorre inteiramente no prefixo $\texttt{p\{(}^{p-2}$. Ao bombear $xy^2z$:
1. Se $y$ contém `p`, surgem múltiplos cabeçalhos `p` (fora de $L_1$);
2. Se $y$ contém `{`, há mais chaves abertas `{` do que fechadas `}` (fora de $L_1$);
3. Se $y \in \texttt{(}^+$, há estritamente mais `(` do que `)` (desbalanceado, fora de $L_1$).

Em todos os casos $xy^2z \notin L_1$. Contradição. Logo, $L_1$ não é regular.

### 2.3 Gramática Livre de Contexto ($G$)
$$G = (V, T, P, S)$$
- $V = \{S, B, T, R\}$
- $T = \Sigma_{\text{AP}} = \{\texttt{p}, \texttt{\{}, \texttt{\}}, \texttt{(}, \texttt{)}, \texttt{\#}, \texttt{i}, \texttt{s}, \texttt{:}, \texttt{;}\}$
- Símbolo inicial: $S$
- Produções $P$:
  - `P1`: $S \to \texttt{p\{} \, B \, \texttt{\}\#} \, T \, \texttt{:} \, T \, \texttt{;}$
  - `P2`: $B \to \texttt{\{} \, B \, \texttt{\}} \, B$
  - `P3`: $B \to \texttt{(} \, B \, \texttt{)} \, B$
  - `P4`: $B \to \varepsilon$
  - `P5`: $T \to \texttt{i} \, R$
  - `P6`: $T \to \texttt{s} \, R$
  - `P7`: $R \to \texttt{i} \, R$
  - `P8`: $R \to \texttt{s} \, R$
  - `P9`: $R \to \varepsilon$

### 2.4 Autômato de Pilha Determinístico ($M_{\text{AP}}$ — 9 estados)
$$M_{\text{AP}} = (Q_{\text{AP}}, \Sigma_{\text{AP}}, \Gamma_{\text{AP}}, \delta_{\text{AP}}, q_0, Z, F_{\text{AP}})$$
- $Q_{\text{AP}} = \{q_0, q_1, q_2, q_3, q_4, q_5, q_6, q_7, q_8\}$ (9 estados $\ge 8$ exigidos)
- $\Gamma_{\text{AP}} = \{Z, \texttt{\{}, \texttt{(}\}$
- Configuração inicial: $(q_0, w, Z)$
- **Critério de aceitação:** por **estado final** ($F_{\text{AP}} = \{q_8\}$) com **consumo integral da entrada** (pilha final igual a `Z`).
- **Equivalência $L(G) = L(M_{\text{AP}})$:** o prefixo `p{` corresponde à transição `q0 → q1 → q2` (empilhando `{` sobre `Z`); o laço em `q2` mantém como invariante que a pilha acima de `Z` registra exatamente os delimitadores abertos ainda não fechados, o que caracteriza $D_2^*$ gerado por $B$; a transição $\varepsilon$ determinística `(q2, ε, Z) → (q3, Z)` dispara exatamente quando o escopo principal `{...}` se fecha; os estados `q3 → q4 → q5 → q6 → q7 → q8` reconhecem exatamente `#`, $T$ (`{i,s}+`), `:`, $T$ (`{i,s}+`) e `;`.
- **Terminação:** toda transição consome 1 símbolo da entrada, exceto `(q2, ε, Z) → (q3, Z)`, que abandona `q2` definitivamente. Assim, $M_{\text{AP}}$ sempre para em no máximo $n + 1$ passos ($O(n)$).

---

## 3. Etapa 2 — Linguagem Sensível ao Contexto ($L_2$) e ALL

### 3.1 Alfabeto e Regra de Aceitação
- Alfabeto de entrada: $\Sigma_{\text{ALL}} = \{\texttt{i}, \texttt{s}, \texttt{:}\}$
- Alfabeto da fita: $\Gamma_{\text{ALL}} = \{\texttt{<}, \texttt{>}, \texttt{i}, \texttt{s}, \texttt{:}, \texttt{I}, \texttt{S}\}$
- Regra de aceitação:
  $$L_2 = \{ w \texttt{:} w \mid w \in \{\texttt{i}, \texttt{s}\}^+ \}$$

### 3.2 Prova de Não-Livre de Contexto ($L_2 \notin \text{LLC}$)
Pelo **Lema do Bombeamento para Linguagens Livres de Contexto** (Sipser, 2013): suponha $L_2$ livre de contexto com constante $p \ge 1$. Tome $z = \texttt{i}^p \texttt{s}^p \texttt{:} \texttt{i}^p \texttt{s}^p \in L_2$ e decomponha $z = uvwxy$ com $|vwx| \le p$ e $|vx| \ge 1$.
1. Se $vwx$ está inteiramente à esquerda (ou à direita) de `:`, então $uv^2wx^2y$ altera o comprimento de apenas um lado $\notin L_2$.
2. Se $vwx$ cruza `:`, como $|vwx| \le p$, ele só pode atingir o bloco $\texttt{s}^p$ à esquerda e o bloco $\texttt{i}^p$ à direita. Se `:` pertence a $v$ ou $x$, $uv^0wx^0y$ perde `:` $\notin L_2$. Caso contrário, $v \in \texttt{s}^*$ e $x \in \texttt{i}^*$, de modo que $uv^2wx^2y$ aumenta `s` à esquerda e/ou `i` à direita sem alterar `s` à direita nem `i` à esquerda, impossibilitando a igualdade das metades $\notin L_2$.

Contradição. Como $L_2$ é reconhecida pelo ALL $M_{\text{ALL}}$ sobre fita linearmente limitada, $L_2 \in \text{LSC} \setminus \text{LLC}$.

### 3.3 Autômato Linearmente Limitado Determinístico ($M_{\text{ALL}}$ — 11 estados)
$$M_{\text{ALL}} = (Q_{\text{ALL}}, \Sigma_{\text{ALL}}, \Gamma_{\text{ALL}}, \texttt{<}, \texttt{>}, \delta_{\text{ALL}}, q_0, F_{\text{ALL}})$$
- $Q_{\text{ALL}} = \{q_0, q_1, \dots, q_{10}\}$ (11 estados $\ge 8$ exigidos), $F_{\text{ALL}} = \{q_{10}\}$.
- **Fita estritamente limitada:** para uma entrada $x$ de $n$ símbolos, a fita tem exatamente $n + 2$ células: posição `0` com marcador fixo `<`, posições `1..n` graváveis com $x$, e posição `n+1` com marcador fixo `>`.
- **Respeito às bordas:** apenas `(q0, <) → (q1, <, R)` lê `<` (mantém `<` e move `R`) e apenas `(q9, >) → (q10, >, L)` lê `>` (mantém `>` e move `L`). Em `q7`, o cabeçote sempre encontra um marcador `I`/`S` já gravado antes de alcançar `<`.
- **Terminação:** cada iteração marca irreversivelmente 1 símbolo em cada metade (`i→I`, `s→S`), com no máximo $\lfloor n/2 \rfloor$ iterações e varreduras monotônicas de tamanho $\le n + 1$, garantindo parada determinística em $O(n^2)$ passos.
