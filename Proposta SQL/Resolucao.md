# Banco: o que muda e por quê

O SQL está em `migracao_sql.sql`, nesta pasta, numerado de 1 a 5 (as seções abaixo seguem a mesma numeração). É uma migração aplicada sobre o `dados/schema.sql` original, que não foi alterado, e roda numa única transação (tudo ou nada).

**O SQL não foi executado em um Postgres.** Os trechos mais sujeitos a erro são a coluna gerada (seção 3) e a view (seção 5). Se o banco de produção for diferente do `schema.sql` (dúvida 9), os comandos precisam ser revistos antes de aplicar.

## 1. Idempotência: evento com identidade única e versão (P1)

- **Problema:** `pagamento.evento_id` não tem `UNIQUE`, e o fluxo atual soma cada valor. Em `pagamentos.json`, o processo `0012345-10.2019.8.26.0053` traz `ev-002` duas vezes, idêntico, e `ev-001` duas vezes (R$ 15.000,00 e R$ 15.500,00). Somados, os totais podem ficar inflados.
- **Mudança:** coluna `atualizado_em` (versão do evento) e `UNIQUE (evento_id)`. A gravação usa o upsert descrito em `PREVENCAO.md`.
- **Detalhe necessário:** as linhas antigas recebem `criado_em` antes do `NOT NULL`. Com `atualizado_em` nulo, a comparação do upsert nunca seria verdadeira e uma correção como a do `ev-001` seria ignorada em silêncio.
- **Ressalva:** o `UNIQUE` falha se a produção já tiver `evento_id` repetido. É preciso deduplicar antes (dúvida 10: houve reimportações?). A regra "a versão mais recente vale" é premissa a confirmar (dúvida 1).

## 2. Número do processo: só dígitos (P8, reduz P6)

- **Problema:** `numero_processo CHAR(20)` não comporta o formato com máscara (25 caracteres, como `0012345-10.2019.8.26.0053`), e o mesmo processo aparece com e sem máscara: `ev-005` e a linha 3 do `hub.csv` usam `00234562120208260053`, enquanto o restante usa `0023456-21.2020.8.26.0053`. Pela comparação de texto exato do operador, parecem processos diferentes.
- **Mudança:** guardar só os 20 dígitos (a máscara é apresentação, não dado), com `CHECK` de formato. A conversão usa `USING regexp_replace(...)`, que remove os espaços que o `CHAR(20)` deixa à direita e qualquer máscara já gravada.
- **Ressalva:** se o `CHECK` ainda falhar, há número inválido na base, e isso precisa ser investigado, não forçado. O script de importação também deve remover a máscara antes de gravar.

## 3. Data de apresentação e prazo calculado pelo banco (P4)

- **Problema:** o `schema.sql` não guarda a data de apresentação, e o prazo no `hub.csv` está errado em dois casos. Linha 2 (`0012345-10.2019.8.26.0053`): apresentado em 2025-04-02, prazo 2027-12-31, quando a regra dá 2026-12-31. Linha 6 (`0056789-54.2017.4.03.6100`): `2025-04-03T01:00:00Z` é 22:00 de 02/04 em Brasília, e o prazo também deveria ser 2026-12-31.
- **Mudança:** coluna `apresentado_em` e `prazo_pagamento` gerada pela regra da Constituição (`<=` 2 de abril → 31/12 do ano seguinte; depois → ano subsequente), em um só lugar.
- **Ressalva 1:** `apresentado_em` é `DATE`, então o banco não resolve fuso. A conversão para o dia em `America/Sao_Paulo` fica no script de importação e depende da dúvida 7.
- **Ressalva 2:** se o Postgres recusar a coluna gerada, o prazo pode ser calculado na view ou no script.

## 4. Rejeitados deixam de sumir (P3)

- **Problema:** pelo passo 5 do fluxo, o evento que não pode ser importado é ignorado sem aviso. Candidatos em `pagamentos.json`: `ev-004` (valor nulo), `ev-009` (valor -200) e `ev-010` (processo vazio). Que o script de fato os ignora é hipótese (dúvida 9).
- **Mudança:** tabela `importacao_rejeitada`, com arquivo, `evento_id`, motivo e o registro original em JSON.
- **Ressalva:** a tabela só funciona se alguém a revisar. O responsável e o alerta estão em `PREVENCAO.md`.

## 5. Total pago calculado sobre os eventos (P2)

- **Problema:** o `schema.sql` aceita `estorno` com `valor > 0`, e o fluxo atual soma cada valor. No processo `0034567-32.2018.8.26.0405`, `ev-006` (pagamento, 5000) e `ev-007` (estorno, 5000) resultam em R$ 10.000 somados, quando o líquido é R$ 0.
- **Mudança:** não guardar o total, e sim calculá-lo na view `precatorio_saldo`, com o estorno subtraindo.
- **Ressalva:** a view assume que o estorno chega positivo e reduz o total. É hipótese a confirmar com o tribunal (dúvida 2).

## Limitações

- **Empate de versão:** o upsert só atualiza se `atualizado_em` for estritamente maior. Mesmo `evento_id` e mesmo `atualizado_em` com valor diferente seria ignorado pelo banco, então o script deve detectar o caso e enviá-lo a `importacao_rejeitada`.
- **Total acima do `valor_face`:** um `CHECK` não alcança isso, pois depende de somar várias linhas. A proposta é a consulta de alerta no fim do `migracao_sql.sql`, sobre `precatorio_saldo`.
- **Nome do ente:** continua texto livre (`MUNICIPIO DE SAO PAULO` contra `Município de São Paulo`). Uma tabela de entes com chave própria resolveria, mas depende de saber qual é a fonte oficial (dúvida 4).