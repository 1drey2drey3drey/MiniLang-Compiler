# Registro de Contribuições

Este arquivo registra a divisão técnica de responsabilidades da equipe **CC6NA** no projeto **MiniLang-Compiler** (AV1 + AV2).

## Atividade Prática AV2 (GLC + AP e LSC + ALL)

| Integrante | Contribuições na AV2 |
| :--- | :--- |
| **Andrey Lourival Andrade Garcia** | Evolução da especificação `MiniLang` (`MiniLang_AV2_Guia_Projeto.md`); definição formal e implementação do núcleo em Python (`spec.py`, `glc.py`, `ap.py`, `all_lba.py`, `pipeline.py`, `minilang_source.py`); construção da CLI e da Interface Web Interativa (`cli.py`, `web.py`, `static/`); geração e validação estrutural/runtime dos arquivos JFLAP (`glc.jff`, `ap.jff`, `all.jff`, `JflapAv2RuntimeCheck.java`); suíte automatizada `pytest` e README. |
| **Igor Cecim Vilhena** | Pesquisa bibliográfica e fundamentação formal das provas na Hierarquia de Chomsky (Lema do Bombeamento para $L_1$ e $L_2$); revisão das derivações passo a passo da GLC e da matriz de casos de teste (aceitas, rejeitadas, casos-limite, integração e erro léxico); elaboração e revisão do relatório técnico (`docs/relatorio_av2/`); elaboração dos slides de apresentação (`docs/apresentacao_av2/`) e análise de limitações observadas. |

> A demonstração ao vivo (15 minutos) e a arguição individual são realizadas por **ambos os integrantes**, com domínio compartilhado sobre GLC, AP, ALL, fita limitada e casos de teste.

---

## Histórico Preservado — Atividade Prática AV1 (MiniLexer)

| Integrante | Contribuições na AV1 |
| :--- | :--- |
| **Andrey Lourival Andrade Garcia** | Especificação da MiniLang (`archive/av1/MiniLang_Guia_Projeto.md`); construção e validação dos AFNε de Thompson; implementação do simulador de AFNε e do MiniLexer; testes unitários/integrados; diagramas JFLAP e Mermaid; README e roteiro de comandos. |
| **Igor Cecim Vilhena** | Definição e formalização das Expressões Regulares (alfabetos, linguagens, notação formal e sintaxe Python); relatório técnico; slides da apresentação. |
