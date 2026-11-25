# Case técnico: precatórios

Análise dos arquivos `pagamentos.json`, `tribunal.csv` e `hub.csv`, com diagnóstico dos problemas, programa de limpeza em Python e proposta de prevenção.

O diagnóstico, a prevenção e as dúvidas estão em arquivos Markdown separados (tabela abaixo).

## Onde está cada entrega

| Entrega | Arquivo |
|---|---|

| Diagnóstico | `DIAGNOSTICO.md` |
| Prevenção (processo, script, banco) | `PREVENCAO.md` |
| SQL proposto e sua explicação | `Proposta SQL/migracao_sql.sql` e `Proposta SQL/Resolucao.md` |
| Dúvidas ao tribunal e à operação | `DUVIDAS.md` |
| Código da limpeza | `limpeza/` e `main.py` |
| Testes | `tests/` |
| Resultado da limpeza | `saida/` (inclui `relatorio.md`) |
| Scripts de exploração | `exploracao/` |
| Originais, sem alteração | `dados/` |

## Como rodar

Requer Python 3.10 ou mais recente (desenvolvi com 3.14.6, no Windows).

```
python -m venv .venv
.venv\Scripts\activate        # Mac/Linux: source .venv/bin/activate
pip install pytest tzdata
pytest
python main.py
```

`python main.py [pasta_dados] [pasta_saida]` lê os originais apenas em modo leitura e grava em `saida/`. O programa se recusa a gravar na pasta dos originais. Rodar duas vezes gera arquivos idênticos, porque o relatório não tem data nem hora.

## O que a limpeza faz

Cada pagamento vira `valido`, `corrigido`, `descartado` ou `duvida`. Quando não há conversão segura, o registro não é adivinhado: vai para dúvida e aparece em `saida/pagamentos_pendencias.csv`. O programa também cruza `tribunal.csv` com `hub.csv` pelo número do processo (20 dígitos), sem escolher qual fonte está certa, e recalcula os prazos do hub.

Resultado com os dados fornecidos: 13 pagamentos lidos (7 válidos, 1 corrigido, 2 descartados, 3 em dúvida) e 2 prazos do hub divergentes da regra (linhas 2 e 6).

## Premissas adotadas

Estão no fim de `saida/relatorio.md` e viram perguntas em `DUVIDAS.md`:

- A data de apresentação é o dia em `America/Sao_Paulo`.
- `DD/MM/AAAA` significa dia/mês.
- Para o mesmo `evento_id`, vale o `atualizado_em` mais recente. Se a versão mais nova é inválida, o evento todo vai para dúvida (não mantenho a antiga, porque não sei qual vale).
- Estorno chega com valor positivo e subtrai do saldo.
- Cada `�` do `tribunal.csv` substitui exatamente um caractere.
- O `ev-011` (processo que não está no `hub.csv`) entra no saldo com uma nota. É uma decisão discutível, registrada como dúvida 5.

## Uso de IA

Usei o Claude (Anthropic) durante todo o case, e ele escreveu boa parte do material.

**Para que usei:**
- Orientação do método: explorar os dados antes de codar e descrever cada problema com evidência, impacto e relação causa/consequência.
- Rascunho do diagnóstico, das dúvidas, do SQL, do código da limpeza e dos testes.

**O que fiz eu:**
- Li a documentação e o `schema.sql`, abri os três arquivos de dados no VS Code e anotei o que estranhei (valor nulo, valor negativo, formatos diferentes).
- Rodei os scripts de exploração e o teste de bytes do `tribunal.csv`.
- Decidi que, se a versão mais recente de um evento é inválida, o evento todo vai para dúvida.
- Decidi enxugar as dúvidas para as que mudam o tratamento de dinheiro ou prazo.
- Organizei o repositório, os commits e os arquivos de entrega.

**Onde a IA errou e eu conferi ou corrigi:**
- Ela supôs que o `tribunal.csv` estava em cp1252. O teste de bytes mostrou que o `�` está gravado no arquivo (bytes `EF BF BD`), então a hipótese caiu.
- Errou a contagem de testes esperados (disse 13, o `pytest` mostrou 14).
- Listou o `ev-005` como "corrigido"; depois ajustou para "válido", porque o problema dele é a comparação por texto exato, não o dado.
- Escreveu uma versão do SQL em que o `atualizado_em` nulo faria o upsert ignorar atualizações; a versão final preenche as linhas antigas antes do `NOT NULL`.

### Como conferi o que a IA produziu

- Rodei o `pytest` após cada etapa de código (leitura, normalização, regras, prazo, cruzamento e relatório), e nenhum teste falhou.
- Rodei `python main.py` com os arquivos reais e analisei o `saida/relatorio.md`, comparando saldos, cruzamento e prazos com o que eu esperava a partir da minha leitura dos dados.
- Conferi com `git status` que `dados/` não foi modificado.
- Os testes cobrem as regras mais arriscadas: dia limite 2/4, fuso, versões do mesmo `evento_id`, estorno e dados inválidos.

Os testes também foram escritos com ajuda da IA. Eles provam que o código faz o que o teste descreve, não que as regras estão certas. Por isso a conferência com os dados reais e a lista de premissas acima.

## Limitações

- O SQL **não foi executado** em um Postgres. Os trechos mais sujeitos a erro são a coluna gerada e a view.
- Não vi o código do script de importação atual nem o banco de produção. O que digo sobre eles é hipótese, a partir do fluxo descrito no enunciado.
- A causa do `�` no `tribunal.csv` é desconhecida (veio do tribunal ou surgiu depois do envio?).
- O dinheiro em dúvida é desconhecido: `ev-004` é nulo e `ev-009` é negativo; só o `ev-010` (R$ 750) tem valor legível.
- O saldo de `0023456-21.2020.8.26.0053` não inclui o `ev-004`, que está em dúvida.