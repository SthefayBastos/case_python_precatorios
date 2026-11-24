-- O Schema nao foi testado, serve apenas como sugestão de melhoria. A versão final deve ser validada com os dados reais.
BEGIN;

-- 1. Idempotência: o evento passa a ter versão e identidade única
ALTER TABLE pagamento ADD COLUMN atualizado_em TIMESTAMPTZ;
UPDATE pagamento SET atualizado_em = criado_em WHERE atualizado_em IS NULL;
ALTER TABLE pagamento ALTER COLUMN atualizado_em SET NOT NULL;

-- Atenção: falha se já existirem evento_id repetidos. Deduplicar antes.
ALTER TABLE pagamento
  ADD CONSTRAINT pagamento_evento_id_uk UNIQUE (evento_id);

-- 2. Número do processo: só dígitos (a máscara é apresentação, não dado)
ALTER TABLE precatorio ALTER COLUMN numero_processo TYPE VARCHAR(20);
ALTER TABLE precatorio
  ADD CONSTRAINT precatorio_numero_formato
  CHECK (numero_processo ~ '^[0-9]{20}$');

-- 3. Data de apresentação e prazo calculado pelo banco
ALTER TABLE precatorio ADD COLUMN apresentado_em DATE;
ALTER TABLE precatorio ADD COLUMN prazo_pagamento DATE GENERATED ALWAYS AS (
  make_date(
    EXTRACT(YEAR FROM apresentado_em)::int
    + CASE WHEN apresentado_em <= make_date(EXTRACT(YEAR FROM apresentado_em)::int, 4, 2)
           THEN 1 ELSE 2 END,
    12, 31)
) STORED;

-- 4. Rejeitados deixam de sumir
CREATE TABLE importacao_rejeitada (
  id        BIGSERIAL PRIMARY KEY,
  arquivo   TEXT        NOT NULL,
  evento_id TEXT,
  motivo    TEXT        NOT NULL,
  registro  JSONB       NOT NULL,
  criado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 5. Total pago calculado sobre os eventos, com estorno subtraindo
CREATE VIEW precatorio_saldo AS
SELECT p.id, p.numero_processo, p.valor_face,
       COALESCE(SUM(CASE pg.tipo WHEN 'pagamento' THEN pg.valor
                                 WHEN 'estorno'   THEN -pg.valor END), 0) AS total_pago
FROM precatorio p
LEFT JOIN pagamento pg ON pg.precatorio_id = p.id
GROUP BY p.id;

COMMIT;