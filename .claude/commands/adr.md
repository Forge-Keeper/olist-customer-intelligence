---
description: Rascunha um novo ADR seguindo o formato do ADR-001
allowed-tools: Read, Grep, Glob
---

Leia `docs/adr/ADR-001-liquid-clustering-bronze-weather.md` como
referência de formato e escreva um rascunho de ADR para a decisão que
eu descrever a seguir, salvando em
`docs/adr/ADR-{próximo número}-{slug-curto}.md`.

Estrutura obrigatória, na mesma ordem do ADR-001:

1. Título + metadados (Status, Date, Decision owners, Scope)
2. **Context** — por que essa decisão precisa ser tomada agora, que
   alternativa "óbvia" foi descartada e por quê
3. **Decision** — a decisão em si, de forma direta, com trecho de
   código/config se aplicável
4. **Rationale** — cada motivo como subseção própria, não um parágrafo
   único genérico
5. **Consequences** — Positive e Negative/Trade-offs separados; não
   omitir trade-offs reais só porque a decisão é a que eu já queria
   tomar
6. **Testing Impact** — o que testes locais devem validar vs. o que só
   dá pra validar em ambiente Databricks real
7. **Alternatives Considered** — listar pelo menos duas alternativas
   descartadas, com o motivo específico da rejeição (não "não
   escolhida" sem explicação)
8. **Revisit Criteria** — condições concretas e observáveis que
   justificariam reabrir essa decisão

Antes de escrever, se a decisão que descrevi tiver menos de duas
alternativas reais consideradas, pergunte-me qual é a segunda opção em
vez de inventar uma alternativa fraca só para preencher a seção.

Não decida por mim qual é a opção "certa" — meu objetivo com o /adr é
documentar e comparar trade-offs, não que você escolha por mim. Se eu
pedir explicitamente sua recomendação, aí sim dê uma, mas separada e
identificada como recomendação, não misturada ao registro da decisão.
