# Testes de Grupo Econômico — índice de homologação

**Estado em 19/11/2026:** 217 casos preparados, com dados de referência e regras rastreadas. **E2E não executado e resultados não homologados.**

## Comece aqui

- [Plano integral e gates](PLANO_TESTES.md)
- [Matriz detalhada consolidada](MATRIZ_DETALHADA.md)
- [Regras reais e cobertura](REGRAS_E_COBERTURA.md)
- [Modelo e exemplos de tabelas-verdade](TABELAS_VERDADE.md)
- [Catálogo integral JSON](catalogo_total.json)

## Matrizes por trilha

| Trilha | Casos | Matriz | JSON |
|---|---:|---|---|
| Formalização | 48 | [Detalhes](MATRIZ_FORMALIZACAO.md) | [Dados](catalogo_formalizacao.json) |
| Inclusão | 18 | [Detalhes](MATRIZ_INCLUSAO.md) | [Dados](catalogo_inclusao.json) |
| Exclusão | 30 | [Detalhes](MATRIZ_EXCLUSAO.md) | [Dados](catalogo_exclusao.json) |
| Unificação | 21 | [Detalhes](MATRIZ_UNIFICACAO.md) | [Dados](catalogo_unificacao.json) |
| Pares de ações + integração | 34 | [Detalhes](MATRIZ_INTEGRACAO.md) | [Dados](catalogo_integracao.json) |
| Limites e exceções | 36 | [Detalhes](MATRIZ_LIMITES.md) | [Dados](catalogo_limites.json) |
| Variantes por regra | 30 | [Detalhes](MATRIZ_REGRAS_VARIANTES.md) | [Dados](catalogo_variantes_regras.json) |
| **Total** | **217** | | |

## Demais referências

- [Massas, tabelas e mapeamento](MASSAS.md)
- [Catálogo resumido](CENARIOS.md)
- [Visão E2E](ESTUDO_E2E.md)
- [Roteiro de execução e evidência](EXECUCAO.md)
- [Massa de responsabilidade](massa-responsabilidade-70-clientes-2026-11-19.md)
- [Inclusão — nota de migração da matriz anterior](homologacao-inclusao-I01-I18-2026-11-19.md)

**Convenção:** funções reais da configuração mantêm seus nomes exatos. Nomes `ORACULO_*` são testes de comportamento sem função comprovada, não regras implementadas.
