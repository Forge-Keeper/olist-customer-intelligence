# Plano de testes e validação

## 1. Testes locais

Executar a partir de scripts/future:

```bash
python -m py_compile mock_table.py example_people.py tests/test_mock_table.py
python -m pytest -q tests/test_mock_table.py
```

Os testes pytest requerem PySpark, mas usam MagicMock para SparkSession; nenhum teste lê catálogo real ou escreve Delta. Sem PySpark instalado, pytest usa importorskip e não confirma comportamento operacional.

## 2. Matriz de critérios

| Cenário | Esperado | Situação do pacote |
|---|---|---|
| Colunas selecionadas e comentários | Schema com somente campos declarados | Teste unitário incluso |
| Criação de tabela vazia | CREATE TABLE sem copiar dados | Teste unitário incluso |
| Reexecução de create_table | Não emitir DDL destrutivo | Teste unitário incluso |
| Destino fora de _wks ou allowlist | Falha antes de acesso ao catálogo | Teste unitário incluso |
| Drift de tipo ou campo ausente | Erro explicativo | Teste unitário incluso |
| DataFrame com campos incompatíveis | Rejeição | Teste unitário incluso |
| Insert/Merge/Update/Delete reais | Eventos persistidos conforme chaves | Pendente Databricks |
| Alteração aditiva de schema | Adicionar apenas nullable ao final | Pendente Databricks |
| Comment/Delta properties | Comentários e selo de mock corretos | Pendente Databricks |
| Testes E2E do sistema consumidor | Fluxo completa até retorno do resultado | Fora deste pacote, integrar posteriormente |

## 3. Smoke no Databricks — namespace fictício

1. Ajustar a classe de exemplo para uma tabela de origem permitida e somente campos existentes.
2. Escolher um catálogo/schema _wks autorizado e confirmar permissões e isolamento.
3. Instanciar MockPeople; revisar describe_contract antes de qualquer DDL.
4. Chamar create_table e comprovar ausência de registros no destino.
5. Criar um DataFrame estritamente sintético; chamar set_dataframe e validate.
6. Executar insert, merge, update e delete em uma tabela de teste dedicada, com verificações entre cada operação.
7. Confirmar estabilidade em reexecuções e a rejeição de chaves duplicadas.
8. Testar evolve_schema com coluna nova nullable e testar rejeição de mudança incompatível.
9. Registrar DESCRIBE DETAIL, DESCRIBE TABLE EXTENDED e evidências dos resultados.

## 4. Gates de aceite

- Nenhum dado de origem copiado automaticamente.
- Escrita somente no namespace autorizado.
- Tabela criada vazia por padrão.
- Contrato e metadados revisados.
- CRUD Delta funcional e sem regressões.
- Fluxo E2E real validado somente após integração do sistema consumidor.

**Status:** compilação estática do artefato original foi realizada; integração Delta/Databricks não executada neste contexto.