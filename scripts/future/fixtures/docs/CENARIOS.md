# Catálogo resumido de cenários

**Versão vigente:** 217 cenários planejados, com fontes estruturadas em [catalogo_total.json](catalogo_total.json). A matriz completa, com GE real, componente, ação, QSA, regra e expectativa, está em [MATRIZ_DETALHADA.md](MATRIZ_DETALHADA.md).

## Composição da cobertura

| Família | IDs | Casos | Objetivo |
|---|---|---:|---|
| Formalização | F01–F48 | 48 | Tipo 1/5/6 × 0–3 PJ × 0–3 PF; código novo e recusa por composição |
| Inclusão | I01–I18 | 18 | Novo componente PF/PJ, grupo ativo, CPF/CNPJ, QSA, majoritário, tipo 6, duplicidade |
| Exclusão | E01–E30 | 30 | Remoção de 1–3 PJ, PF, cancelamento, tipo final, crédito e troca |
| Unificação | U01–U21 | 21 | 9 combinações de tipo, PF controlador comum, QSA, secundários e migração |
| Pares ordenados | C01–C16 | 16 | Quatro ações cruzadas em sequência, estado intermediário e pedidos repetidos |
| Integração | P01–P18 | 18 | MERGE, eventos, idempotência, concorrência, retorno e ambientes |
| Limites | B01–B36 | 36 | 0, 49,99, 50, 50,01, nulos, QSA 99,99/100/100,01, datas, responsabilidade |
| Variantes de regras | FX01–FX14, UX01–UX09, EX01–EX05, IX01–IX02 | 30 | Regras compartilhadas testadas especificamente em cada ação |
| **Total** | | **217** | |

## Relação entre catálogo e massa

- Cada caso usa `cclub_cli` dos 100 PF/100 PJ previstos e GEs reais da fixture.
- Somente Formalização cria GE novo; o código é atribuído pelo motor.
- Exclusão inclui versões com responsabilidade aberta/ausente, situação cadastral e `tem_acao_2`.
- Unificação usa QSA de duas PFs controladoras a 50/50 em PJs não MEI para os casos positivos propostos.
- Todos os overrides são por snapshot e não podem contaminar o próximo caso.

Os 151 cenários originais foram **preservados como famílias F/I/E/U/C/P**; os 66 restantes representam fronteiras (36) e variantes isoladas por regra (30).

## Aprovação

Os retornos `APROVA`/`RECUSA` são **expectativas derivadas de regras**, não resultados de execução; `CONDICIONAL`, `PARCIAL` e `PENDENTE` precisam de aceite específico antes de E2E. Não fechar casos com simples sucesso de job.

Veja [PLANO_TESTES.md](PLANO_TESTES.md), [REGRAS_E_COBERTURA.md](REGRAS_E_COBERTURA.md) e [TABELAS_VERDADE.md](TABELAS_VERDADE.md).
