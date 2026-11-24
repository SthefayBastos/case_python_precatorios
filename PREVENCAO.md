Prevenção

Processo

Pedir ao tribunal um formato estável (JSON/CSV conforme contrato versionado) e um canal automatizado, em vez de e-mail.
Acabar com a conferência manual no Excel: trocar por uma reconciliação automática que normaliza e lista só as divergências reais.
Tornar o relatório de rejeitados obrigatório, com alguém responsável por tratá-lo.
Atualizar a documentação (versão 2.1 está desatualizada) e documentar o hub.csv.

Script de importação

Idempotente: gravar eventos (upsert por evento_id), nunca somar totais.
Validar e normalizar na entrada; rejeitar com motivo registrado e alerta, nunca ignorar.
Uma transação por arquivo (ou por lote), para que uma falha no meio não deixe importação parcial. Assim, rodar de novo com o mesmo arquivo é seguro.
Modo --dry-run.

Para a gravação, proponho um upsert por `evento_id`, em vez de somar totais:

```sql
INSERT INTO pagamento (precatorio_id, evento_id, tipo, valor, pago_em, atualizado_em)
VALUES (%s, %s, %s, %s, %s, %s)
ON CONFLICT (evento_id) DO UPDATE
  SET valor = EXCLUDED.valor, pago_em = EXCLUDED.pago_em,
      tipo = EXCLUDED.tipo, atualizado_em = EXCLUDED.atualizado_em
  WHERE EXCLUDED.atualizado_em > pagamento.atualizado_em;
```

Isso resolve o P1: reenviar o mesmo arquivo, ou receber o `ev-001` de novo,
não soma duas vezes. O banco recusa o duplicado e só aceita a versão com
`atualizado_em` mais recente. Depende da constraint `UNIQUE (evento_id)`,
descrita na seção de banco.



## Ver arquivo schema_proposto.sql na pasta Proposta SQL, com atualizações pertinentes para melhoria do cenário atual.