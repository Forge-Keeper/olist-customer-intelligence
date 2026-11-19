# Matriz de Inclusão — I01 a I18 (R3 consolidada)

**Ação:** `cAcaoGrpEconm=2`. Grupos e componentes correspondem às fixtures canônicas; documentos dos PFs adicionais são os de `../dados_pf_cenarios.py` e devem ser sincronizados no cadastro de teste.

| ID | GE alvo | Tipo | Membros ativos antes (`cclub_cli`) | Solicitar (`cclub_cli`) | QSA / cadastro a preparar | Regra principal | Esperado | Estado final / evento |
|---|---:|---:|---|---|---|---|---|---|
| I01 | 910101 | 1 | 62,64,101 | 112 | QSA base; atributos válidos | `valida_qsa` | APROVA | 62,64,101,112; UPDATE (confirmar CRT) |
| I02 | 910104 | 1 | 74,76,107 | 299 | PJ74=107:50%+299:50% | `valida_socio_major` | APROVA | 74,76,107,299; UPDATE (confirmar CRT) |
| I03 | 910502 | 5 | 92,115 | 118 | QSA base; atributos válidos | `valida_qsa` | CONDICIONAL | depende de aceite; UPDATE (confirmar CRT) |
| I04 | 910505 | 5 | 98,121 | 297 | PJ98=121:50%+297:50% | `valida_socio_major` | CONDICIONAL | depende de aceite; UPDATE (confirmar CRT) |
| I05 | 910605 | 6 | 126,128,133 | 112 | QSA base; atributos válidos | `valida_cnpj_natureza_jurid` | CONDICIONAL | depende de aceite; UPDATE (confirmar CRT) |
| I06 | 910604 | 6 | 122,124,131 | 295 | PJ124=295:50%+117:25%+119:25% | `valida_socios_sao_pf` | RECUSA | 122,124,131; NENHUM |
| I07 | 910101 | 1 | 62,64,101 | 62 | QSA base; atributos válidos | `valida_cnpj_em_outro_grupo` | RECUSA | 62,64,101; NENHUM |
| I08 | 910102 | 1 | 66,68,103 | 64 | QSA base; atributos válidos | `valida_cnpj_em_outro_grupo` | RECUSA | 66,68,103; NENHUM |
| I09 | 910103 | 1 | 70,72,105 | 113 | QSA base; atributos válidos | `valida_cpf_em_outro_grupo` | RECUSA | 70,72,105; NENHUM |
| I10 | 910104 | 1 | 74,76,107 | 291 | PJ74=107:50%+291:50%; 291:cindcd_cpf_valid | `valida_cpf_ativo_receita` | RECUSA | 74,76,107; NENHUM |
| I11 | 910103 | 1 | 70,72,105 | 112 | 112:cindcd_cnpj_valid | `valida_cnpj_ativo_receita` | RECUSA | 70,72,105; NENHUM |
| I12 | 910105 | 1 | 80,82,109 | 112 | 112:rsit_docto_recta | `valida_cnpj_ativo_receita` | RECUSA | 80,82,109; NENHUM |
| I13 | 910106 | 1 | 84,88,111 | 112 | 112:rmtriz_flial_cnpj | `valida_cnpj_matriz` | RECUSA | 84,88,111; NENHUM |
| I14 | 910102 | 1 | 66,68,103 | 112 | 112:rnatur_jurid | `valida_cnpj_natureza_jurid` | RECUSA | 66,68,103; NENHUM |
| I15 | 910103 | 1 | 70,72,105 | 112 | PJ112=64:90% | `valida_qsa` | RECUSA | 70,72,105; NENHUM |
| I16 | 910505 | 5 | 98,121 | 289 | PJ98=121:60%+289:40% | `valida_socio_major` | RECUSA | 98,121; NENHUM |
| I17 | 910101 | 1 | 62,64,101 | 112,287 | PJ112=64:50%+287:50% | `valida_socio_major` | CONDICIONAL | depende de aceite; UPDATE (confirmar CRT) |
| I18 | 910106 | 1 | 84,88,111 | 112,112 | QSA base; atributos válidos | `deduplicacao_solicitacao_inclusao` | PENDENTE | depende de aceite; UPDATE (confirmar CRT) |

## Política do oráculo e homologação

- `valida_cnpj_natureza_jurid` **está incluída na configuração real de Inclusão**; I14 é recusa válida pelo ramo recuperado.
- `valida_cpf_em_outro_grupo`/`valida_cnpj_em_outro_grupo` usam `flag_comp_ativo_grpecon`: distinguimos próprio GE e outro GE no preparo, não na condição de recusa.
- `valida_socio_major` depende de `flag_socio_major` derivada do QSA da PJ pertinente; não fixar artificialmente essa flag em testes positivos.
- Para I03/I04/I05 e I17, as regras de elegibilidade são verificáveis, mas tipo final e/ou eventos CRT seguem condicionais até homologação.
- O mesmo candidato livre pode aparecer em cenários diferentes **somente** com snapshot inicial restaurado.
- I18 testa repetição na solicitação; nenhum comportamento de deduplicação ou recusa é afirmado sem regra oficial.

## Critérios de aceite

Solicitação por componente + mensagens, grupo/tipo antes-depois, vínculos ativos e histórico de eventos do GE e componentes. Não basta `retorno_solt=OK` se a persistência divergir.
