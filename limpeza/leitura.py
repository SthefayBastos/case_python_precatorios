"""Leitura dos arquivos originais, exatamente como vieram.

Este módulo não corrige nada: só lê e guarda de onde cada registro veio,
para o relatório poder citar arquivo e posição.
"""
from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Registro:
    arquivo: str   # nome do arquivo de origem
    posicao: int   # JSON: posição no array (1 = primeiro). CSV: nº da linha no arquivo
    dados: dict    # campos exatamente como lidos (sem strip, sem conversão)


def ler_pagamentos(caminho: str | Path) -> list[Registro]:
    caminho = Path(caminho)
    with open(caminho, encoding="utf-8-sig") as f:
        eventos = json.load(f)
    return [Registro(caminho.name, i, e) for i, e in enumerate(eventos, start=1)]


def _ler_csv(caminho: str | Path, delimitador: str) -> list[Registro]:
    caminho = Path(caminho)
    registros = []
    with open(caminho, encoding="utf-8-sig", newline="") as f:
        leitor = csv.DictReader(f, delimiter=delimitador)
        for linha in leitor:
            registros.append(Registro(caminho.name, leitor.line_num, dict(linha)))
    return registros


def ler_tribunal(caminho: str | Path) -> list[Registro]:
    # A documentação promete vírgula, mas o arquivo real usa ponto e vírgula.
    return _ler_csv(caminho, ";")


def ler_hub(caminho: str | Path) -> list[Registro]:
    return _ler_csv(caminho, ",")