# Massa sintética — responsabilidade creditícia

**Data de referência:** 19/11/2026. **Status:** proposta de carga a ser reconciliada; nenhuma inserção foi executada.

## Premissas

- Seleção reproduzível de 40 PFs e 30 PJs, sorteadas dentre os 100 identificadores de cada natureza previamente definidos: PF ímpares de 101 a 299; PJ pares de 62 a 260.
- **70 clientes distintos, 70 operações fictícias, uma por cliente.** Representam 35% dos 200 cadastros (40% das PFs e 30% das PJs).
- `noper_cli` é fictício e único. Início anterior a 2025; término em **19/11/2027**, um ano após a data de referência da geração.
- Registros planejados com situação **ABERTO** na data de referência. Os nomes das colunas são um mapeamento lógico e devem ser ajustados ao esquema real antes de gerar a tabela.
- Antes da carga, validar se cada `cclub_cli` realmente existe, corresponde à natureza informada e possui estados cadastrais compatíveis. A seleção não garante que os CNPJs escolhidos sejam ativos.
- Conciliar clientes com o QSA e os grupos econômicos; responsabilidade de crédito não determina participação societária.

## Registros

| tipo | cclub_cli | noper_cli | dt_inicio_contrato | dt_fim_contrato | situacao_contrato |
|---|---:|---:|---|---|---|
| PF | 101 | 9701000001 | 2021-01-01 | 2027-11-19 | ABERTO |
| PF | 105 | 9701000002 | 2022-08-12 | 2027-11-19 | ABERTO |
| PF | 107 | 9701000003 | 2023-03-23 | 2027-11-19 | ABERTO |
| PF | 113 | 9701000004 | 2024-10-07 | 2027-11-19 | ABERTO |
| PF | 115 | 9701000005 | 2021-05-18 | 2027-11-19 | ABERTO |
| PF | 143 | 9701000006 | 2022-12-02 | 2027-11-19 | ABERTO |
| PF | 147 | 9701000007 | 2023-07-13 | 2027-11-19 | ABERTO |
| PF | 155 | 9701000008 | 2024-02-24 | 2027-11-19 | ABERTO |
| PF | 157 | 9701000009 | 2021-09-08 | 2027-11-19 | ABERTO |
| PF | 159 | 9701000010 | 2022-04-19 | 2027-11-19 | ABERTO |
| PF | 165 | 9701000011 | 2023-11-03 | 2027-11-19 | ABERTO |
| PF | 171 | 9701000012 | 2024-06-14 | 2027-11-19 | ABERTO |
| PF | 173 | 9701000013 | 2021-01-25 | 2027-11-19 | ABERTO |
| PF | 177 | 9701000014 | 2022-08-09 | 2027-11-19 | ABERTO |
| PF | 181 | 9701000015 | 2023-03-20 | 2027-11-19 | ABERTO |
| PF | 185 | 9701000016 | 2024-10-04 | 2027-11-19 | ABERTO |
| PF | 189 | 9701000017 | 2021-05-15 | 2027-11-19 | ABERTO |
| PF | 193 | 9701000018 | 2022-12-26 | 2027-11-19 | ABERTO |
| PF | 199 | 9701000019 | 2023-07-10 | 2027-11-19 | ABERTO |
| PF | 203 | 9701000020 | 2024-02-21 | 2027-11-19 | ABERTO |
| PF | 213 | 9701000021 | 2021-09-05 | 2027-11-19 | ABERTO |
| PF | 223 | 9701000022 | 2022-04-16 | 2027-11-19 | ABERTO |
| PF | 225 | 9701000023 | 2023-11-27 | 2027-11-19 | ABERTO |
| PF | 229 | 9701000024 | 2024-06-11 | 2027-11-19 | ABERTO |
| PF | 233 | 9701000025 | 2021-01-22 | 2027-11-19 | ABERTO |
| PF | 241 | 9701000026 | 2022-08-06 | 2027-11-19 | ABERTO |
| PF | 243 | 9701000027 | 2023-03-17 | 2027-11-19 | ABERTO |
| PF | 245 | 9701000028 | 2024-10-01 | 2027-11-19 | ABERTO |
| PF | 251 | 9701000029 | 2021-05-12 | 2027-11-19 | ABERTO |
| PF | 255 | 9701000030 | 2022-12-23 | 2027-11-19 | ABERTO |
| PF | 257 | 9701000031 | 2023-07-07 | 2027-11-19 | ABERTO |
| PF | 263 | 9701000032 | 2024-02-18 | 2027-11-19 | ABERTO |
| PF | 271 | 9701000033 | 2021-09-02 | 2027-11-19 | ABERTO |
| PF | 275 | 9701000034 | 2022-04-13 | 2027-11-19 | ABERTO |
| PF | 277 | 9701000035 | 2023-11-24 | 2027-11-19 | ABERTO |
| PF | 281 | 9701000036 | 2024-06-08 | 2027-11-19 | ABERTO |
| PF | 283 | 9701000037 | 2021-01-19 | 2027-11-19 | ABERTO |
| PF | 289 | 9701000038 | 2022-08-03 | 2027-11-19 | ABERTO |
| PF | 293 | 9701000039 | 2023-03-14 | 2027-11-19 | ABERTO |
| PF | 299 | 9701000040 | 2024-10-25 | 2027-11-19 | ABERTO |
| PJ | 74 | 9702000001 | 2023-01-01 | 2027-11-19 | ABERTO |
| PJ | 84 | 9702000002 | 2024-06-14 | 2027-11-19 | ABERTO |
| PJ | 88 | 9702000003 | 2021-11-27 | 2027-11-19 | ABERTO |
| PJ | 90 | 9702000004 | 2022-04-13 | 2027-11-19 | ABERTO |
| PJ | 94 | 9702000005 | 2023-09-26 | 2027-11-19 | ABERTO |
| PJ | 96 | 9702000006 | 2024-02-12 | 2027-11-19 | ABERTO |
| PJ | 102 | 9702000007 | 2021-07-25 | 2027-11-19 | ABERTO |
| PJ | 116 | 9702000008 | 2022-12-11 | 2027-11-19 | ABERTO |
| PJ | 136 | 9702000009 | 2023-05-24 | 2027-11-19 | ABERTO |
| PJ | 138 | 9702000010 | 2024-10-10 | 2027-11-19 | ABERTO |
| PJ | 140 | 9702000011 | 2021-03-23 | 2027-11-19 | ABERTO |
| PJ | 146 | 9702000012 | 2022-08-09 | 2027-11-19 | ABERTO |
| PJ | 150 | 9702000013 | 2023-01-22 | 2027-11-19 | ABERTO |
| PJ | 156 | 9702000014 | 2024-06-08 | 2027-11-19 | ABERTO |
| PJ | 160 | 9702000015 | 2021-11-21 | 2027-11-19 | ABERTO |
| PJ | 164 | 9702000016 | 2022-04-07 | 2027-11-19 | ABERTO |
| PJ | 168 | 9702000017 | 2023-09-20 | 2027-11-19 | ABERTO |
| PJ | 170 | 9702000018 | 2024-02-06 | 2027-11-19 | ABERTO |
| PJ | 174 | 9702000019 | 2021-07-19 | 2027-11-19 | ABERTO |
| PJ | 180 | 9702000020 | 2022-12-05 | 2027-11-19 | ABERTO |
| PJ | 194 | 9702000021 | 2023-05-18 | 2027-11-19 | ABERTO |
| PJ | 202 | 9702000022 | 2024-10-04 | 2027-11-19 | ABERTO |
| PJ | 210 | 9702000023 | 2021-03-17 | 2027-11-19 | ABERTO |
| PJ | 216 | 9702000024 | 2022-08-03 | 2027-11-19 | ABERTO |
| PJ | 226 | 9702000025 | 2023-01-16 | 2027-11-19 | ABERTO |
| PJ | 244 | 9702000026 | 2024-06-02 | 2027-11-19 | ABERTO |
| PJ | 246 | 9702000027 | 2021-11-15 | 2027-11-19 | ABERTO |
| PJ | 248 | 9702000028 | 2022-04-01 | 2027-11-19 | ABERTO |
| PJ | 250 | 9702000029 | 2023-09-14 | 2027-11-19 | ABERTO |
| PJ | 258 | 9702000030 | 2024-02-27 | 2027-11-19 | ABERTO |

## Validação da carga

1. Exatamente 40 PFs, 30 PJs, 70 `cclub_cli` distintos e 70 `noper_cli` distintos.
2. Uma única operação aberta por cliente, sem dados produtivos.
3. Todos os inícios anteriores a 2025 e todos os vencimentos em 2027-11-19.
4. Compatibilidade com os tipos, nomes e filtros temporais da tabela real de responsabilidade.
5. Reconciliar QSA, grupos e validade cadastral antes de E2E.