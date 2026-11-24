# Declaração de Uso de Inteligência Artificial

## Projeto
**MiniLang-Compiler (AV1 + AV2)** — Disciplina de Linguagens Formais e Autômatos (CESUPA — CC6NA)  
**Integrantes:** Andrey Lourival Andrade Garcia e Igor Cecim Vilhena

---

## Declaração

Ferramentas de Inteligência Artificial foram utilizadas exclusivamente como **apoio técnico** durante o desenvolvimento do projeto, sem substituir a autoria, a revisão crítica, a validação experimental ou o domínio conceitual da equipe sobre os modelos formais entregues.

## Ferramentas Utilizadas

- **Google Antigravity / Gemini** (AV2): apoio na discussão de propostas originais de linguagens, revisão das provas de classificação na Hierarquia de Chomsky, organização da arquitetura em Python (motor formal, CLI e Interface Web Interativa), geração automatizada dos arquivos XML `.jff` a partir da fonte única de verdade (`src/av2/spec.py`) e estruturação do relatório técnico e dos slides.
- **Claude (Anthropic) / ChatGPT** (AV1, histórico preservado): apoio na organização de código, testes e documentação do analisador léxico `MiniLexer`.

## Tarefas Apoiadas na AV2

1. Refinamento da definição formal da GLC LL(1), do DPDA de 9 estados e do D-LBA de 11 estados.
2. Escrita da estrutura de código em `src/av2/`, do validador Java `JflapAv2RuntimeCheck.java` e da Interface Web Interativa.
3. Geração inicial de tabelas de casos de teste, documentação LaTeX/HTML e roteiro de apresentação.

## O que a Equipe Verificou e Validou

1. **Conformidade rigorosa com a lauda:** conferência de que tanto o AP (9 estados) quanto o ALL (11 estados) superam o mínimo de 8 estados, que todas as cadeias regulares e de integração possuem $\ge 18$ caracteres, e que a decisão provém exclusivamente das transições formais e operações reais de pilha/fita (sem atalhos).
2. **Provas teóricas e terminação:** revisão passo a passo das demonstrações pelo Lema do Bombeamento ($L_1 \notin \text{LR}$ e $L_2 \notin \text{LLC}$), equivalência $L(G)=L(M_{\text{AP}})$ e cotas de parada ($O(n)$ no AP e $O(n^2)$ no ALL).
3. **Execução de testes automatizados:** validação dos **227 testes no `pytest`** (135 da AV1 + 92 da AV2, incluindo verificação exaustiva de 3.280 cadeias no ALL e invariantes de fita limitada em cada passo do trace).
4. **Validação cruzada no JFLAP 7.1 real:** execução de `tests/validate_av2_jflap_runtime.py` contra `JFLAP7.1.jar`, confirmando **0 divergências** em 418 casos reais (34 no `ap.jff` com 0 estados não-determinísticos + 384 no `all.jff` + 9 produções em `glc.jff`).
5. **Inspeção visual e ensaio oral:** verificação manual dos rastreamentos passo a passo na Interface Web Interativa e preparo conjunto para a demonstração e arguição individual.
