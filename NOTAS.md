## Documentação do tribunal
-sem duvidas

## schema.sql
- não existe restrição de duplicação de registro
-estorno:o enunciado diz que o script "soma cada valor ao total pago", como fica a soma ?
- limite de datas (muito a frente/ muito antigas)

## pagamentos.json
- arquivo pg com valor null, valor negativo
-datas com formatos diferentes
-registros duplicados ( ev 001 difícil saber qual vale)
-registros sem "dono"
-registro com formatos diferentes
## tribunal.csv / hub.csv
- ...

## Perguntas para o tribunal/operação
- sem duvidas

--------------------------------
ids com duplicata exata: 1
ids com versões diferentes 1
Tipos de 'valor:' {'float': 3, 'str': 2, 'int': 7, 'NoneType': 1}
Valores negativos ['ev-009']
valores zero []
Valores de 'tipo': {'pagamento': 12, 'estorno': 1}
Formatos de data: {'AAAA-MM-DD': 11, 'DD/MM/AAAA': 2}
Formatos de processo: {'com máscara CNJ': 11, '20 dígitos sem máscara': 1, 'vazio/nulo': 1}



===================
erro na data de pagamento limite:
o sistema usa < em vez de <= na comparação.
hub se mostra inconsistente no tratamento de fuso impactando nas datas limites de pagamento.


