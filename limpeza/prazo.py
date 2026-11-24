"""Recalcula o prazo de pagamento e compara com o prazo do hub.csv.

Regra: apresentado até 2 de abril -> 31/12 do ano seguinte;
depois de 2 de abril -> 31/12 do ano subsequente.
Premissa (dúvida 10): a data de apresentação é o dia em America/Sao_Paulo.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from zoneinfo import ZoneInfo

from limpeza.leitura import Registro
from limpeza.normalizacao import normalizar_data, normalizar_processo

FUSO = ZoneInfo("America/Sao_Paulo")


def data_apresentacao(texto) -> date | None:
    """Dia da apresentação em Brasília, ou None se não for confiável.

    - 'AAAA-MM-DD' (sem hora): usada como está (premissa: já é o dia local).
    - Data-hora COM fuso: convertida para America/Sao_Paulo antes de pegar o dia.
    - Data-hora SEM fuso, formato DD/MM/AAAA ou texto inválido: None.
    """
    if not isinstance(texto, str):
        return None
    texto = texto.strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", texto):
        try:
            return date.fromisoformat(texto)
        except ValueError:
            return None
    try:
        dt = datetime.fromisoformat(texto.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        return None
    return dt.astimezone(FUSO).date()


def calcular_prazo(apresentacao: date) -> date:
    limite = date(apresentacao.year, 4, 2)
    anos = 1 if apresentacao <= limite else 2   # <=: o dia 2/4 ainda conta
    return date(apresentacao.year + anos, 12, 31)


@dataclass(frozen=True)
class ResultadoPrazo:
    registro: Registro
    processo: str | None
    data_usada: date | None
    prazo_calculado: date | None
    prazo_hub: date | None
    status: str          # ok | divergente | duvida
    motivo: str


def conferir_prazos(registros_hub: list[Registro]) -> list[ResultadoPrazo]:
    resultados = []
    for r in registros_hub:
        processo = normalizar_processo(r.dados.get("processo"))
        data = data_apresentacao(r.dados.get("apresentado_em"))
        prazo_hub = normalizar_data(r.dados.get("prazo_pagamento"))

        if data is None:
            resultados.append(ResultadoPrazo(
                r, processo, None, None, prazo_hub, "duvida",
                "apresentado_em ausente, inválido ou sem fuso"))
            continue

        calculado = calcular_prazo(data)
        if prazo_hub is None:
            status, motivo = "duvida", "prazo_pagamento do hub ausente ou inválido"
        elif prazo_hub == calculado:
            status, motivo = "ok", "prazo confere com a regra"
        else:
            status = "divergente"
            motivo = f"hub traz {prazo_hub}, a regra dá {calculado}"
        resultados.append(ResultadoPrazo(
            r, processo, data, calculado, prazo_hub, status, motivo))
    return resultados