# Massas sintéticas, chaves e consistência

## Inventário validável offline

| Massa | Registros | Fonte |
|---|---:|---|
| Cadastros PF existentes | 100 previstos | Fonte cadastral de teste; conciliar antes da carga |
| Cadastros PJ existentes | 100 previstos | Fonte cadastral de teste; conciliar situação de 20 PJs não ativas |
| Nomes das PJs | 100 | `../dados_nomes_pj.py` |
| Grupos ativos | 18 | `../dados_grupos_ativos.py` |
| Componentes ativos | 48 | `../dados_componentes_ativos.py` |
| QSA não MEI | 54 em 27 PJs | `../dados_quadro_societario.py` |
| QSA MEI | Fonte separada | Conferir e importar sem duplicar |
| Responsabilidade | 70 operações | `../dados_responsabilidade.py` e [lista completa](massa-responsabilidade-70-clientes-2026-11-19.md) |
| PFs reservadas para cenários | 10 | `../dados_pf_cenarios.py`; dentro da faixa PF 281–299 |

**Não presumir que os 100 cadastros foram importados:** a correspondência com as tabelas físicas ainda é um gate. As PFs reservadas substituem logicamente os mesmos IDs de cadastro na massa de teste, sem append duplicado.

## Grupos

- **Normal:** 910101–910106, duas PJ e uma PF cada.
- **Isolado:** 910501–910506, uma PJ e uma PF cada.
- **Gerencial:** 910601–910606, duas PJ e uma PF cada.
- Nenhum documento está ativo em dois GEs no estado-base.

As seis PFs dos Isolados foram reconciliadas com os QSA das suas PJs; cada PF aparece como sócia com **participação >=50%**. Para GEs Normal/Gerencial, a participação da PF ativa pode refletir outros estados, e o QSA é ajustado **no snapshot** quando um teste requer controlador específico. Não projetar regras que não estejam no motor.

## QSA

A tupla é: `ccnpj_empr, pprtcp_soctr, cindcd_quadr_soctr, ipartc_empr, dfim_prtcp_soctr, cclub_cli, ccpf_cnpj_pssoa_soctr, dptcao_orige`.

**`cclub_cli` identifica o sócio**, não o CNPJ titular. Todos os 27 QSA não MEI totalizam 100%. Para testar 90%, 99,99%, 100,01% ou ausência de QSA, usar apenas o overlay do caso; nunca adulterar o baseline.

Os MEIs têm uma única pessoa titular no QSA original. Os casos de Unificação que exigem duas PFs controladoras usam PJs não MEI e, no U01, substituem o MEI do secundário por uma PJ não MEI **apenas no snapshot**.

## Responsabilidade

- 40 PF e 30 PJ distintos (70 de 200 cadastros, ou 35% do total).
- Um `noper_cli` fictício único por cliente, data inicial anterior a 2025 e vencimento em 19/11/2027.
- A referência de contrato aberto é a data de geração. Em testes futuros, recalcular a validade conforme o contrato do motor.
- A presença de contrato não modifica QSA nem prova controle societário; pode bloquear **Exclusão de PJ** segundo `valida_cnpj_responsabilidade`.

## Documentos, chaves e segurança de carga

| Estrutura | Chave | Gate |
|---|---|---|
| PF | `cclub_cli` ímpar, `ccpf_pssoa` 11 dígitos | Correspondência exata com as solicitações |
| PJ | `cclub_cli` par, `ccnpj_empr` 14 dígitos | Matriz, status e natureza jurídica corretos |
| QSA | `ccnpj_empr` + documento do sócio | Sem duplicação; 100% baseline |
| Grupo | `cgrp_econm` | Tipo 1/5/6 consistente |
| Componente | `cgrp_econm` + documento | Unicidade por documento no estado ativo |
| Responsabilidade | Cliente + `noper_cli` | Sem contrato duplicado, status e período coerentes |
| Solicitação | `_id`, `cSoltcAtdmt` | Chaves estáveis em todas as etapas |

**Nenhuma escrita no ambiente foi executada por este pacote.** Os contratos reais das tabelas devem ser validados antes de qualquer carga. Testes de integridade estão em `../tests/`.
