# Tabelas-verdade e modelo de aceite

A tabela-verdade não é o log do motor: deve ser fixada antes da execução e assinada pelo negócio. Usar uma linha por decisão de componente e uma linha agregada por grupo/solicitação.

## Modelo obrigatório

| Campo | Origem | Regra |
|---|---|---|
| `id_cenario` | Catálogo | Chave F/I/E/U/C/P/B/FX/UX/EX/IX |
| `_id`, `cSoltcAtdmt` | Solicitação preparada | Chaves reais da entrada, sem reutilização indevida |
| `cAcaoGrpEconm` | Ação | 1 Formalização; 2 Inclusão; 3 Exclusão; 4 Unificação |
| `cGrpEconm` / primário / secundário | Fixture | Código real ou NOVO no caso da Formalização |
| `cTpoGrpEconm` | GE inicial | 1 Normal; 5 Isolado; 6 Gerencial |
| `cclub_cli`, CPF/CNPJ | Cadastros | Documento e natureza correspondem à tabela |
| Membros ativos antes | Fixture | Documento, papel e GE, mais overlays explícitos |
| QSA do CNPJ | Fixture / overlay | Titular, sócio, `cclub_cli` do sócio e %; total |
| Responsabilidade | Fixture / overlay | `noper_cli`, vigência e flag derivada |
| `retorno_solt` e mensagem | Oráculo | Por componente, com motivo exato |
| Componentes e tipo depois | Oráculo | Deltas esperados e preservação dos anteriores |
| Eventos grupo e componentes | Oráculo | Operação, chave, quantidade e destino |
| Status negócio | Aprovação funcional | Aprova, rejeita ou pede alteração |
| Evidência e defeito | Execução | Hash/snapshot, saída, eventos e estado persistido |

## Exemplos preenchidos

### F22 — Formalização de Isolado

- **Estado anterior:** nenhum GE alvo; PJ112 e PF281 livres.
- **Solicitar:** ação 1, tipo 5, PJ112 e PF281.
- **QSA do cenário:** PJ112 com PF281 = 100%.
- **Regra:** `valida_composicao_formalizacao` e `valida_socio_major_formalizacao`.
- **Resultado esperado pelo ramo recuperado:** APROVA. Código de GE gerado unicamente pelo motor; um grupo criado e dois vínculos adicionados. Validar `gera_codigo_grupo_formalizacao`.

### I01 — Inclusão PJ em grupo Normal

- **GE real:** 910101 (tipo 1).
- **Membros antes:** PJ62, PJ64 e PF101.
- **Solicitar:** ação 2, PJ112, CNPJ `20010176000131` (sem GE ativo).
- **QSA:** PJ112 com sócia PJ64 = 100%, além de matriz/ATIVA/natureza permitida.
- **Regra:** `valida_qsa` e regras de vínculo/validade.
- **Esperado:** APROVA, membros finais PJ62/PJ64/PJ112/PF101; um vínculo adicional. Confirmar contrato de evento UPDATE do grupo e INSERT do componente.

### E27 — Recusa por responsabilidade

- **GE real:** 910104 (tipo 1), com PJ74, PJ76 e PF107.
- **Solicitar:** ação 3, excluir PJ74, CNPJ `75538340000108`.
- **Snapshot:** situação BAIXADA e `flag_resp_empr=true` pela operação aberta.
- **Regra:** `valida_cnpj_responsabilidade`.
- **Esperado:** RECUSA, mensagem de responsabilidade ativa; nenhum evento de exclusão, grupo inalterado.

### U01 — Unificação Normal → Normal

- **Primário:** 910106 (tipo 1), PJ84/PJ88/PF111.
- **Secundário:** 910102 (tipo 1), PJ66/PJ68/PF103. **Snapshot de teste:** substituir a PJ68 (MEI) pela PJ112 (não MEI); secundário efetivo PJ66/PJ112/PF103.
- **QSA:** para PJ84, PJ88, PJ66 e PJ112, PF111=50% e PF103=50% cada; sem CNPJ MEI com vários sócios.
- **Regras:** `flag_ge_primario`, `valida_composicao_unificacao`, `valida_composicao_grupo_economico`.
- **Oráculo:** elegibilidade proposta; materialização e seleção de secundário ainda CONDICIONAL, aguardando validação de CRT. Nenhum DELETE/INSERT deve atingir componente recusado.

## Classificação de resultado

`PASS`: evidência completa e esperada; `FAIL`: divergência funcional ou técnica; `BLOCKED`: faltam contrato/dados/ambiente; `NOT_RUN`: não executado. Resultado `CONDICIONAL` no catálogo não é uma quinta aprovação; é impedimento até definição do negócio.

**A execução só é aceita depois de verificar o consumidor de eventos**, e não apenas uma linha em `resul_soltc`.
