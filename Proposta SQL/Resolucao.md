### 1. Idempotência: evento com identidade única e versão (resolve P1)

Hoje `pagamento.evento_id` não tem `UNIQUE`, então o mesmo evento pode entrar
várias vezes. Foi o que inflou o processo `0012345-10.2019.8.26.0053` com
`ev-001` (R$ 15.000,00 e R$ 15.500,00) e `ev-002` (duplicata exata).
A proposta é guardar `atualizado_em` e tornar `evento_id` único.

```sql
ALTER TABLE pagamento ADD COLUMN atualizado_em TIMESTAMPTZ;
UPDATE pagamento SET atualizado_em = criado_em WHERE atualizado_em IS NULL;
ALTER TABLE pagamento ALTER COLUMN atualizado_em SET NOT NULL;

ALTER TABLE pagamento
  ADD CONSTRAINT pagamento_evento_id_uk UNIQUE (evento_id);
```

O preenchimento das linhas antigas antes do `NOT NULL` é necessário: com
`atualizado_em` nulo, o upsert nunca atualizaria um registro existente.
**Ressalva:** o `UNIQUE` falha se a produção já tiver `evento_id` repetido.
Antes é preciso deduplicar (dúvida 14: houve reimportações?).

### 2. Número do processo: só dígitos (resolve P8 e reduz P6)

`numero_processo CHAR(20)` não comporta o formato com máscara, de 25
caracteres (`0012345-10.2019.8.26.0053`), e a mesma pessoa/processo aparece
com e sem máscara (`ev-005` e `hub.csv` usam `00234562120208260053`, enquanto o
restante usa `0023456-21.2020.8.26.0053`). A proposta é guardar só os 20
dígitos e deixar a máscara para a apresentação.

```sql
ALTER TABLE precatorio ALTER COLUMN numero_processo TYPE VARCHAR(20);
ALTER TABLE precatorio
  ADD CONSTRAINT precatorio_numero_formato
  CHECK (numero_processo ~ '^[0-9]{20}$');
```

**Ressalva:** o `CHECK` falha se já houver números com máscara gravados; é
preciso normalizá-los antes. O script de importação também deve remover a
máscara antes de gravar.

### 3. Data de apresentação e prazo calculado pelo banco (resolve P4)

O prazo no `hub.csv` está errado em dois casos: `0012345-10.2019.8.26.0053`
(apresentado em 2025-04-02, prazo 2027-12-31, deveria ser 2026-12-31) e
`0056789-54.2017.4.03.6100` (`2025-04-03T01:00:00Z`, que é 02/04 em Brasília,
prazo 2027-12-31, deveria ser 2026-12-31). A proposta é guardar a data de
apresentação e calcular o prazo com a regra da Constituição (`<= 2 de abril`),
em um só lugar.

```sql
ALTER TABLE precatorio ADD COLUMN apresentado_em DATE;
ALTER TABLE precatorio ADD COLUMN prazo_pagamento DATE GENERATED ALWAYS AS (
  make_date(
    EXTRACT(YEAR FROM apresentado_em)::int
    + CASE WHEN apresentado_em <= make_date(EXTRACT(YEAR FROM apresentado_em)::int, 4, 2)
           THEN 1 ELSE 2 END,
    12, 31)
) STORED;
```

**Ressalva:** `apresentado_em` é `DATE`, então o banco não resolve o fuso. A
conversão de `2025-04-03T01:00:00Z` para o dia em `America/Sao_Paulo` deve
acontecer no script de importação, e depende da resposta à dúvida 10 (qual
fuso define a data de apresentação).

### 4. Rejeitados deixam de sumir (resolve P3)

Hoje o evento que não pode ser importado é ignorado sem aviso (passo 5 do
fluxo). Isso vale para `ev-004` (valor nulo), `ev-009` (valor -200), `ev-010`
(processo vazio) e `ev-011` (processo `0067890-65.2016.8.26.0053`, ausente do
hub). A proposta é gravar cada rejeição, com o motivo e o registro original.

```sql
CREATE TABLE importacao_rejeitada (
  id        BIGSERIAL PRIMARY KEY,
  arquivo   TEXT        NOT NULL,
  evento_id TEXT,
  motivo    TEXT        NOT NULL,
  registro  JSONB       NOT NULL,
  criado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

A tabela só funciona se alguém olhar para ela: o processo deve incluir um
responsável e um alerta quando houver rejeições novas.

### 5. Total pago calculado sobre os eventos (resolve P2)

O `schema.sql` aceita `estorno` com `valor > 0`, e o fluxo atual soma cada
valor. No processo `0034567-32.2018.8.26.0405`, `ev-006` (pagamento, 5000) e
`ev-007` (estorno, 5000) resultam em R$ 10.000 somados, quando o líquido é
R$ 0. A proposta é não guardar o total, e sim calculá-lo sobre os eventos,
com o estorno subtraindo.

```sql
CREATE VIEW precatorio_saldo AS
SELECT p.id, p.numero_processo, p.valor_face,
       COALESCE(SUM(CASE pg.tipo WHEN 'pagamento' THEN pg.valor
                                 WHEN 'estorno'   THEN -pg.valor END), 0) AS total_pago
FROM precatorio p
LEFT JOIN pagamento pg ON pg.precatorio_id = p.id
GROUP BY p.id;
```

**Ressalva:** a view assume que estorno chega positivo e que reduz o total;
isso é hipótese a confirmar com o tribunal (dúvida 2).

### Limitações desta proposta

- **Empate de versão:** o upsert só atualiza se `atualizado_em` for
  estritamente maior. Mesmo `evento_id`, mesmo `atualizado_em` e valor
  diferente seria ignorado pelo banco; o script deve detectar o caso e
  enviá-lo para `importacao_rejeitada`.
- **Total acima do `valor_face`:** um `CHECK` não alcança isso (depende de
  somar várias linhas). A proposta é uma consulta de alerta sobre
  `precatorio_saldo`.
- **Nome do ente:** continua texto livre (`MUNICIPIO DE SAO PAULO` contra
  `Município de São Paulo`). Uma tabela de entes com chave própria resolveria,
  mas depende de saber qual é a fonte oficial (dúvida 11).