"""Uso: python main.py [pasta_dados] [pasta_saida]
Lê os originais (só leitura) e grava tudo em pasta_saida."""
from __future__ import annotations

import sys
from pathlib import Path

from limpeza.cruzamento import cruzar
from limpeza.leitura import ler_hub, ler_pagamentos, ler_tribunal
from limpeza.prazo import conferir_prazos
from limpeza.regras import classificar_pagamentos, conjunto_processos, saldo_por_processo
from limpeza.relatorio import escrever_saida


def executar(pasta_dados="dados", pasta_saida="saida"):
    dados, saida = Path(pasta_dados), Path(pasta_saida)
    if saida.resolve() == dados.resolve():
        raise ValueError("a pasta de saída não pode ser a pasta dos originais")

    pagamentos = ler_pagamentos(dados / "pagamentos.json")
    tribunal = ler_tribunal(dados / "tribunal.csv")
    hub = ler_hub(dados / "hub.csv")

    resultados = classificar_pagamentos(
        pagamentos,
        conjunto_processos(tribunal, "numero_processo"),
        conjunto_processos(hub, "processo"),
    )
    cruzamento = cruzar(tribunal, hub)
    prazos = conferir_prazos(hub)
    saldos = saldo_por_processo(resultados)

    escrever_saida(saida, resultados, cruzamento, prazos, saldos)
    return resultados, cruzamento, prazos, saldos


if __name__ == "__main__":
    args = sys.argv[1:]
    resultados, cruzamento, prazos, _ = executar(*args)
    print(f"{len(resultados)} pagamentos classificados, "
          f"{len(cruzamento)} processos cruzados, {len(prazos)} prazos conferidos.")
    print("Saída gravada em", args[1] if len(args) > 1 else "saida")