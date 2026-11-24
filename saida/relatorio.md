# Relatório de limpeza

## Pagamentos: resumo

| Ação | Qtde |
|---|---|
| valido | 7 |
| corrigido | 1 |
| descartado | 2 |
| duvida | 3 |

Total de registros lidos: 13.

Valor legível em eventos em dúvida: R$ 750 (ordem de grandeza; não entra no saldo).

## Pagamentos: registro a registro

| Arquivo | Posição | evento_id | Ação | Motivos |
|---|---|---|---|---|
| pagamentos.json | 1 | ev-001 | descartado | versão substituída pela posição 9 (atualizado_em mais recente) |
| pagamentos.json | 2 | ev-002 | corrigido | valor em texto convertido para número; data DD/MM/AAAA convertida (hipótese: dia/mês) |
| pagamentos.json | 3 | ev-003 | valido |  |
| pagamentos.json | 4 | ev-002 | descartado | duplicata exata da posição 2 de pagamentos.json |
| pagamentos.json | 5 | ev-004 | duvida | valor ausente ou inválido |
| pagamentos.json | 6 | ev-005 | valido |  |
| pagamentos.json | 7 | ev-006 | valido |  |
| pagamentos.json | 8 | ev-007 | valido | nota: estorno contraria a documentação; subtrai no saldo |
| pagamentos.json | 9 | ev-001 | valido |  |
| pagamentos.json | 10 | ev-008 | valido |  |
| pagamentos.json | 11 | ev-009 | duvida | valor zero ou negativo (erro ou estorno mal classificado?); nota: processo só existe em hub.csv |
| pagamentos.json | 12 | ev-010 | duvida | processo ausente ou fora do padrão CNJ |
| pagamentos.json | 13 | ev-011 | valido | nota: processo só existe em tribunal.csv |

## Saldo líquido por processo (só eventos válidos ou corrigidos)

| Processo (20 dígitos) | Saldo (R$) |
|---|---|
| 00123451020198260053 | 18000.50 |
| 00234562120208260053 | 9200.0 |
| 00345673220188260405 | 0 |
| 00456784320215020011 | 3000 |
| 00678906520168260053 | 4000 |

## Cruzamento tribunal.csv x hub.csv

Resumo: divergente: 2, ok: 2, so_hub: 1, so_tribunal: 1

| Processo | tribunal.csv (linha) | hub.csv (linha) | Status | Motivos |
|---|---|---|---|---|
| 00123451020198260053 | 2 | 2 | ok | nota: ente compatível, mas o tribunal perdeu acentos; não confirmado |
| 00234562120208260053 | 3 | 3 | divergente | valor_face: tribunal 30000.00, hub 31000.00; nota: ente compatível, mas o tribunal perdeu acentos; não confirmado |
| 00345673220188260405 | 4 | 4 | ok | nota: ente compatível, mas o tribunal perdeu acentos; não confirmado |
| 00456784320215020011 | 5 | 5 | divergente | ente: tribunal 'Uni�o', hub 'Município de Santos' |
| 00567895420174036100 |  | 6 | so_hub | processo existe só em hub.csv |
| 00678906520168260053 | 6 |  | so_tribunal | processo existe só em tribunal.csv |

## Prazos do hub.csv recalculados

| Linha | Processo | Data usada | Prazo calculado | Prazo no hub | Status | Motivo |
|---|---|---|---|---|---|---|
| 2 | 00123451020198260053 | 2025-04-02 | 2026-12-31 | 2027-12-31 | divergente | hub traz 2027-12-31, a regra dá 2026-12-31 |
| 3 | 00234562120208260053 | 2025-04-03 | 2027-12-31 | 2027-12-31 | ok | prazo confere com a regra |
| 4 | 00345673220188260405 | 2024-02-29 | 2025-12-31 | 2025-12-31 | ok | prazo confere com a regra |
| 5 | 00456784320215020011 | 2025-04-02 | 2026-12-31 | 2026-12-31 | ok | prazo confere com a regra |
| 6 | 00567895420174036100 | 2025-04-02 | 2026-12-31 | 2027-12-31 | divergente | hub traz 2027-12-31, a regra dá 2026-12-31 |

## Premissas (viram dúvidas ao tribunal/operação)

- A data de apresentação é o dia em America/Sao_Paulo.
- `DD/MM/AAAA` significa dia/mês.
- Para o mesmo `evento_id`, vale o `atualizado_em` mais recente; se a versão mais nova é inválida, o evento todo vai para dúvida.
- Estorno chega com valor positivo e subtrai do saldo.
- Cada `�` do tribunal.csv substitui exatamente um caractere.
- `tribunal.csv` usa `;` e vírgula decimal, ao contrário da documentação.
