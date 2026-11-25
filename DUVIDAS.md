# Dúvidas antes de colocar a limpeza em produção

Só as perguntas cuja resposta muda o que a limpeza faz com dinheiro ou prazo.
Enquanto não forem respondidas, valem as premissas do `saida/relatorio.md`.

## Ao tribunal

**1. Reenvio do mesmo `evento_id` com valor diferente é correção? A versão mais recente sempre vale?**
Evidência: `ev-001`, processo `0012345-10.2019.8.26.0053`: R$ 15.000,00
(atualizado em 2025-03-10) e R$ 15.500,00 (2025-03-11).
Muda: a regra de versão da limpeza e o upsert proposto.

**2. Estornos existem? Chegam com valor positivo? Como se ligam ao pagamento original?**
Evidência: `ev-006` (pagamento, 5000) e `ev-007` (estorno, 5000), processo
`0034567-32.2018.8.26.0405`; a documentação diz que `tipo` é sempre "pagamento".
Muda: o sinal no saldo (limpeza e view `precatorio_saldo`).

**3. O que significam `valor` nulo, negativo e processo vazio? Serão reenviados corrigidos?**
Evidência: `ev-004` (nulo, `0023456-21.2020.8.26.0053`), `ev-009` (-200,
`0056789-54.2017.4.03.6100`), `ev-010` (processo vazio, R$ 750).
Muda: hoje ficam em dúvida e fora do saldo; o total de dinheiro em dúvida é desconhecido.

**4. Qual é o valor de face e o ente corretos nos processos divergentes?**
Evidência: `0023456-21.2020.8.26.0053` tem 30.000,00 no `tribunal.csv` (linha 3) e
31000.00 no `hub.csv` (linha 3). `0045678-43.2021.5.02.0011` é "União" no
`tribunal.csv` (linha 5) e "Município de Santos" no `hub.csv` (linha 5).
Muda: qual fonte corrigir; hoje nenhuma é escolhida.

**5. Os processos que aparecem em só uma lista são válidos?**
Evidência: `0056789-54.2017.4.03.6100` só no `hub.csv` (linha 6); `0067890-65.2016.8.26.0053`
só no `tribunal.csv` (linha 6), com o `ev-011` (R$ 4.000) pago nele.
Muda: se o `ev-011` entra no saldo (hoje entra, com nota) e de onde vem o prazo.

**6. O `tribunal.csv` já sai com `�` e com `;` e vírgula decimal, ou isso surge depois do envio? Qual é o formato oficial?**
Evidência: bytes `EF BF BD` no lugar dos acentos, contra a documentação (UTF-8, vírgula, ponto).
Muda: se o tribunal precisa reenviar ou se o problema está no passo do Excel.

## À operação

**7. Qual fuso define a data de apresentação, e de onde vem `apresentado_em`?**
Evidência: `hub.csv` linha 2 (`0012345-10.2019.8.26.0053`, 2025-04-02) e linha 6
(`0056789-54.2017.4.03.6100`, `2025-04-03T01:00:00Z`, que é 22:00 de 02/04 em Brasília).
Muda: o prazo da linha 6 (hoje a limpeza assume Brasília).

**8. Os prazos errados do hub já foram usados para priorizar a carteira?**
Evidência: `hub.csv` linhas 2 e 6 trazem 2027-12-31; a regra dá 2026-12-31.
Muda: se é preciso rever decisões já tomadas.

**9. Como o script e o banco atuais funcionam de fato?**
O banco de produção é igual ao `schema.sql`? O script lê `tipo` e normaliza o
número do processo (`ev-005` usa `00234562120208260053`)? Onde ficam os logs dos
eventos ignorados?
Muda: confirma ou derruba as hipóteses de P2, P3 e P6 e se a migração se aplica.

**10. Houve reimportações no passado? Dá para comparar os totais atuais com os eventos?**
Muda: mede o estrago já feito e exige deduplicar antes de aplicar o `UNIQUE`.