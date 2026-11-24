 Diagnóstico (do mais grave ao menos grave)
## P=Problema.
P1. Importação não idempotente: duplicatas e versões somadas

Evidência: pagamentos.json, processo 0012345-10.2019.8.26.0053: ev-002 aparece 2x, idêntico (R$ 2.500,50); ev-001 aparece 2x (R$ 15.000,00 atualizado em 10/03 e R$ 15.500,00 atualizado em 11/03). schema.sql: pagamento.evento_id sem UNIQUE.
Impacto: o total desse processo fica inflado em R$ 15.000,00 (ev-001) mais R$ 2.500,50 (ev-002). Com a janela de 7 dias reenviando eventos e o operador rodando o script de novo, o erro se repete a cada importação.
Relação: é causa de totais errados. Vem da falta de chave única no banco e de o script somar em vez de gravar eventos.

P2. Estorno somado como pagamento

Evidência: pagamentos.json, processo 0034567-32.2018.8.26.0405: ev-006 (pagamento, 5000) e ev-007 (estorno, 5000, positivo). A documentação diz que tipo é "sempre pagamento".
Impacto: o sistema registra R$ 10.000 pagos, quando o líquido é R$ 0. O precatório parece quitado sem ter sido pago.
Relação: consequência de documentação desatualizada. Ressalva: O código em questão não foi disponibilizado, então "o script soma sem olhar o tipo" é hipótese a partir do passo 2 do fluxo.

P3. Falhas de importação silenciosas

Evidência: passo 5 do fluxo ("ignora e segue, ninguém é avisado"). Candidatos a serem ignorados:
ev-004, processo 0023456-21.2020.8.26.0053: valor nulo, bloqueado pelo NOT NULL.
ev-009, processo 0056789-54.2017.4.03.6100: valor -200, bloqueado pelo CHECK (valor > 0).
ev-010: processo vazio.
ev-011, processo 0067890-65.2016.8.26.0053: ausente do hub.csv.
Impacto: pagamentos reais podem sumir do total sem rastro, e não dá para medir quanto dinheiro ficou de fora.
Relação: causa raiz de processo que esconde P1, P2 e P7.

P4. Prazo de pagamento errado no hub

Evidência: hub.csv:
Linha 2, 0012345-10.2019.8.26.0053: apresentado em 2025-04-02, prazo 2027-12-31. Deveria ser 2026-12-31, porque 2/4 ainda é "até 2 de abril".
Linha 6, 0056789-54.2017.4.03.6100: 2025-04-03T01:00:00Z equivale a 22:00 de 02/04 em Brasília, então o prazo deveria ser 2026-12-31, mas o hub traz 2027-12-31.
Linha 5, 0045678-43.2021.5.02.0011: 2025-04-02T23:30:00-03:00, prazo 2026-12-31, correto. Isso mostra a inconsistência no tratamento do fuso.
Impacto: esses dois precatórios aparecem com um ano a mais de folga, e a equipe prioriza a carteira por esse prazo.
Relação: causa de priorização errada. São duas causas separadas: o dia limite (hipótese: < no lugar de <=) e o fuso, que vem de apresentado_em misturar datas puras e datas com hora.

P5. Fontes divergentes entre tribunal.csv e hub.csv

Evidência:
0023456-21.2020.8.26.0053: valor de face 30.000,00 no tribunal (linha 3) e 31000.00 no hub (linha 3, escrito como 00234562120208260053).
0045678-43.2021.5.02.0011: "União" no tribunal (linha 5) e "Município de Santos" no hub (linha 5).
0056789-54.2017.4.03.6100: só no hub (linha 6).
0067890-65.2016.8.26.0053: só no tribunal (linha 6).
Impacto: o ev-011 (R$ 4.000) paga um precatório que o hub não conhece, sem prazo nem priorização. O ev-009 aponta para um precatório que o tribunal não lista. Valor de face e ente divergentes afetam saldo e cobrança.
Relação: consequência de a conferência semanal ser manual no Excel (P6), e talvez também de problemas na origem.

P6. Conferência manual e chave sem normalização

Evidência: passo 3 do fluxo (texto exato, Excel). hub.csv linha 3 e ev-005 usam 00234562120208260053, enquanto o resto usa 0023456-21.2020.8.26.0053. Nomes MUNICIPIO DE SAO PAULO (hub, linha 2) e Município de São Paulo (hub, linha 3).
Impacto: o mesmo processo e o mesmo ente parecem diferentes. O ev-005 (R$ 1.200) não casa com 0023456-21.2020.8.26.0053 numa comparação de texto, então tende a ser perdido (hipótese). O operador também não consegue ver as divergências reais no meio do ruído.
Relação: causa de P5 passar despercebido e consequência da falta de padrão de entrada.

P7. Dados inválidos e formatos fora do contrato

Evidência:
ev-002 (0012345-10.2019.8.26.0053): valor texto "2.500,50" e data 10/04/2025, ambígua.
ev-004 (0023456-21.2020.8.26.0053): valor nulo.
ev-009 (0056789-54.2017.4.03.6100): valor negativo.
ev-010: sem processo.
tribunal.csv: ;, vírgula decimal e � gravado (bytes EF BF BD), contra a documentação (UTF-8, vírgula, ponto).
Impacto: valores e datas lidos errado ou rejeitados, e nomes de ente irrecuperáveis sem fonte externa.
Relação: são os gatilhos de P3, que os transforma em perda silenciosa.

P8. Documentação e schema incompletos ou conflitantes

Evidência: tipo só "pagamento" na doc, mas o schema aceita estorno. atualizado_em está na doc e não no schema. hub.csv não é documentado. Data de apresentação e total pago não aparecem no schema. numero_processo CHAR(20) não comporta os 25 caracteres do formato com máscara, como 0012345-10.2019.8.26.0053.
Impacto: ninguém sabe o contrato real. Se o banco de produção for igual ao schema.sql, importar o número com máscara pode gerar erro de tamanho, o que, somado ao P3, faria processos inteiros serem ignorados.
Relação: causa de P2 e P3.