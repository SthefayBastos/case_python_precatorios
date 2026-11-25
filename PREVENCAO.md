# Prevenção

## Processo

- Pedir ao tribunal um formato estável (JSON/CSV conforme contrato versionado) e um canal automatizado, em vez de e-mail (dúvida 6).
- Acabar com a conferência manual no Excel: trocar por uma reconciliação automática que normaliza o número do processo e lista só as divergências reais.
- Tornar o relatório de rejeitados obrigatório, com um responsável por tratá-lo.
- Atualizar a documentação (a versão 2.1 está desatualizada) e documentar o `hub.csv`.

### Responsável pelas rejeições

A tabela `importacao_rejeitada` e o arquivo `saida/pagamentos_pendencias.csv` só ajudam se alguém os revisar. Proposta: definir um responsável na operação, com revisão a cada importação e alerta quando surgir rejeição nova. Sem isso, a falha silenciosa (P3) apenas muda de lugar.

## Script de importação

- **Idempotente:** gravar eventos (upsert por `evento_id`), nunca somar totais.
- **Validar e normalizar na entrada:** rejeitar com motivo registrado e alerta, nunca ignorar. Remover a máscara do número do processo antes de gravar e converter `atualizado_em` e `apresentado_em` com fuso explícito (dúvida 7).
- **Uma transação por arquivo (ou por lote):** uma falha no meio não deixa importação parcial, e rodar de novo com o mesmo arquivo é seguro.
- **Modo `--dry-run`:** mostra o que seria gravado e rejeitado, sem alterar o banco.

Para a gravação, proponho um upsert por `evento_id`, em vez de somar totais:

```sql
INSERT INTO pagamento (precatorio_id, evento_id, tipo, valor, pago_em, atualizado_em)
VALUES (%s, %s, %s, %s, %s, %s)
ON CONFLICT (evento_id) DO UPDATE
  SET valor = EXCLUDED.valor, pago_em = EXCLUDED.pago_em,
      tipo = EXCLUDED.tipo, atualizado_em = EXCLUDED.atualizado_em
  WHERE EXCLUDED.atualizado_em > pagamento.atualizado_em;
```

Isso resolve o P1: reenviar o mesmo arquivo, ou receber o `ev-001` de novo, não soma duas vezes. O banco recusa o duplicado e só aceita a versão com `atualizado_em` mais recente. Depende da constraint `UNIQUE (evento_id)`, descrita na seção Banco. A regra "a versão mais recente vale" é uma premissa a confirmar com o tribunal (dúvida 1).

**Limitação:** o upsert só atualiza se `atualizado_em` for estritamente maior. Se chegar o mesmo `evento_id` com o mesmo `atualizado_em` e valor diferente, o banco ignora em silêncio. O script deve detectar esse caso antes e gravá-lo em `importacao_rejeitada` como dúvida.

## Banco

## Banco

A migração está em `Proposta SQL/migracao_sql.sql`, e o motivo de cada mudança (problema, evidência e ressalvas) em `Proposta SQL/Resolucao.md`. O `dados/schema.sql` original não foi alterado. O SQL não foi executado em um Postgres.

Resumo: `UNIQUE (evento_id)` e `atualizado_em` (P1), número do processo só com 20 dígitos (P6 e P8), prazo calculado pelo banco (P4), tabela de rejeitados (P3) e saldo calculado por view (P2).
