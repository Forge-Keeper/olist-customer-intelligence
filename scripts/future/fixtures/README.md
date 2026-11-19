# Fixtures sintéticas de Grupo Econômico

**Dados de teste, sem escrita automática em tabelas.** Pacote de preparação e homologação com **217 casos** das quatro ações (Formalização, Inclusão, Exclusão e Unificação), além de integração, limites e testes de ramos.

## Dados versionados

| Arquivo | Conteúdo |
|---|---|
| `dados_nomes_pj.py` | Nomes fixos para 100 PJs (IDs pares 62–260) |
| `dados_grupos_ativos.py` | 18 GEs físicos: seis Normal (1), seis Isolado (5), seis Gerencial (6) |
| `dados_componentes_ativos.py` | 48 componentes ativos (30 PJs e 18 PFs) |
| `dados_quadro_societario.py` | 54 vínculos QSA de 27 PJs não MEI, todos somando 100%; seis Isolados com PF ativa majoritária |
| `dados_responsabilidade.py` | 70 operações fictícias abertas: 40 PF e 30 PJ, uma por cliente |
| `dados_pf_cenarios.py` | Dez PFs reservadas (281–299), com CPF sintético fixo para os cenários |

## Regras de integridade

- Cada `cclub_cli` representa um cliente. No QSA, `cclub_cli` é o **sócio**; `ccnpj_empr` é a **empresa titular**.
- Os 100 cadastros PF/PJ existentes no ambiente não são sobrescritos automaticamente. Conciliar os documentos do catálogo, principalmente as dez PFs reservadas; substituir/upsert controlado em teste se necessário.
- QSA de MEIs está em fonte separada: importar uma vez por titular e não duplicar vínculos. Os casos de Unificação evitam gerar dois sócios para MEIs.
- Não usar o QSA para inferir responsabilidade de crédito. Operações de responsabilidade representam contratos, não participações societárias.
- Toda mudança de QSA, cadastro, responsabilidade ou composição indicada num caso é **overlay sobre snapshot isolado**, não alteração permanente da massa-base.
- O prazo fixo das operações documentadas é 19/11/2027: revalidar quando executar em outra data.
- Caso com situação `PENDENTE` ou `CONDICIONAL` não possui oráculo de negócio fechado.

## Executar as verificações offline

Da raiz do checkout:

```bash
python -m unittest discover -s scripts/future/fixtures/tests -v
```

Os testes não acessam Spark nem bancos de dados. Para integração, conferir antes o schema e o roteamento das tabelas sintéticas. O pacote não habilita nenhuma escrita em produção.

## Documentação

Comece por [docs/README.md](docs/README.md), [docs/PLANO_TESTES.md](docs/PLANO_TESTES.md) e [docs/MATRIZ_DETALHADA.md](docs/MATRIZ_DETALHADA.md). O catálogo integral estruturado está em [docs/catalogo_total.json](docs/catalogo_total.json).

## Preparar um snapshot lógico por cenário

O materializador **não escreve** nas tabelas e não substitui o contrato físico da solicitação. Ele lê o catálogo e combina os dados fixos com o overlay do caso:

```bash
python scripts/future/fixtures/materializar_cenario.py I01
python scripts/future/fixtures/materializar_cenario.py U01 --saida U01.json
```

A saída inclui componentes, QSA, responsabilidade, indicadores de preparo e o oráculo. Os casos que têm preparação textual/contrato ainda pendente emitem avisos. Consulte [materializar_cenario.py](materializar_cenario.py) e [tests/test_materializar_cenario.py](tests/test_materializar_cenario.py).
