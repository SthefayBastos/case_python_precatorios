"""Regras de decisão: cada registro de pagamento vira
valido, corrigido, descartado ou duvida.

Princípio: na dúvida, não adivinha. Quem não tem conversão segura vai
para 'duvida' e aparece no relatório.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from limpeza.leitura import Registro
from limpeza.normalizacao import (
    normalizar_data,
    normalizar_processo,
    normalizar_valor,
)


@dataclass(frozen=True)
class Resultado:
    registro: Registro
    acao: str                  # valido | corrigido | descartado | duvida
    motivos: tuple[str, ...]
    evento: dict | None        # evento limpo; None se descartado ou duvida


def conjunto_processos(registros: list[Registro], campo: str) -> set[str]:
    """Processos (20 dígitos) presentes em um CSV. `campo` é o nome da coluna."""
    return {
        p for r in registros
        if (p := normalizar_processo(r.dados.get(campo))) is not None
    }


def _parse_ts(texto) -> datetime | None:
    """atualizado_em como data-hora COM fuso. Sem fuso ou inválido -> None."""
    if not isinstance(texto, str):
        return None
    try:
        dt = datetime.fromisoformat(texto.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt if dt.tzinfo is not None else None


def _validar(reg: Registro, tribunal: set[str], hub: set[str]) -> Resultado:
    """Valida UM registro (já escolhido como a versão que vale)."""
    d = reg.dados
    motivos: list[str] = []
    duvidas: list[str] = []
    correcoes: list[str] = []

    # Processo. Tirar a máscara é só trocar a representação (a forma
    # canônica tem 20 dígitos); não conta como correção.
    processo = normalizar_processo(d.get("processo"))
    if processo is None:
        duvidas.append("processo ausente ou fora do padrão CNJ")
    else:
        em_tribunal, em_hub = processo in tribunal, processo in hub
        if not em_tribunal and not em_hub:
            duvidas.append("processo não existe em tribunal.csv nem em hub.csv")
        elif em_tribunal and not em_hub:
            motivos.append("nota: processo só existe em tribunal.csv")
        elif em_hub and not em_tribunal:
            motivos.append("nota: processo só existe em hub.csv")

    # Valor
    valor = normalizar_valor(d.get("valor"))
    if valor is None:
        duvidas.append("valor ausente ou inválido")
    elif valor <= 0:
        duvidas.append("valor zero ou negativo (erro ou estorno mal classificado?)")
    elif isinstance(d.get("valor"), str):
        correcoes.append("valor em texto convertido para número")

    # Data
    bruta = d.get("data_pagamento")
    data = normalizar_data(bruta)
    if data is None:
        duvidas.append("data_pagamento ausente ou inválida")
    elif isinstance(bruta, str) and "/" in bruta:
        correcoes.append("data DD/MM/AAAA convertida (hipótese: dia/mês)")

    # Tipo
    tipo = d.get("tipo")
    if tipo not in ("pagamento", "estorno"):
        duvidas.append("tipo desconhecido")
    elif tipo == "estorno":
        motivos.append("nota: estorno contraria a documentação; subtrai no saldo")

    if duvidas:
        return Resultado(reg, "duvida", tuple(duvidas + correcoes + motivos), None)

    evento = {
        "evento_id": d["evento_id"],
        "processo": processo,
        "valor": valor,
        "data_pagamento": data,
        "tipo": tipo,
        "atualizado_em": d.get("atualizado_em"),
    }
    acao = "corrigido" if correcoes else "valido"
    return Resultado(reg, acao, tuple(correcoes + motivos), evento)


def _todas_em_duvida(regs: list[Registro], motivo: str) -> list[Resultado]:
    return [Resultado(r, "duvida", (motivo,), None) for r in regs]


def _processar_grupo(grupo: list[Registro], tribunal, hub) -> list[Resultado]:
    """Todos os registros que têm o mesmo evento_id."""
    resultados: list[Resultado] = []

    # 1. Cópias idênticas: mantém a primeira, descarta as demais.
    vistos: dict[str, Registro] = {}
    unicos: list[Registro] = []
    for reg in grupo:
        chave = json.dumps(reg.dados, sort_keys=True, ensure_ascii=False)
        if chave in vistos:
            original = vistos[chave]
            resultados.append(Resultado(
                reg, "descartado",
                (f"duplicata exata da posição {original.posicao} de {original.arquivo}",),
                None,
            ))
        else:
            vistos[chave] = reg
            unicos.append(reg)

    if len(unicos) == 1:
        resultados.append(_validar(unicos[0], tribunal, hub))
        return resultados

    # 2. Versões diferentes do mesmo evento: compara os INSTANTES (com fuso).
    marcas = [(_parse_ts(r.dados.get("atualizado_em")), r) for r in unicos]
    if any(ts is None for ts, _ in marcas):
        resultados += _todas_em_duvida(
            unicos, "versões diferentes do mesmo evento_id e atualizado_em ausente, inválido ou sem fuso")
        return resultados

    maximo = max(ts for ts, _ in marcas)
    topo = [r for ts, r in marcas if ts == maximo]
    if len(topo) > 1:
        resultados += _todas_em_duvida(
            unicos, "versões diferentes do mesmo evento_id com o mesmo atualizado_em")
        return resultados

    nova = topo[0]
    antigas = [r for r in unicos if r is not nova]
    res_nova = _validar(nova, tribunal, hub)
    resultados.append(res_nova)

    if res_nova.acao == "duvida":
        # Decisão B: versão mais recente inválida -> o evento todo vira dúvida.
        for antiga in antigas:
            resultados.append(Resultado(
                antiga, "duvida",
                (f"versão mais recente (posição {nova.posicao}) é inválida; "
                 "não sabemos qual vale",),
                None,
            ))
    else:
        for antiga in antigas:
            resultados.append(Resultado(
                antiga, "descartado",
                (f"versão substituída pela posição {nova.posicao} (atualizado_em mais recente)",),
                None,
            ))
    return resultados


def classificar_pagamentos(
    registros: list[Registro], tribunal: set[str], hub: set[str]
) -> list[Resultado]:
    """Classifica todos os registros de pagamentos.json, na ordem do arquivo."""
    grupos: dict[str, list[Registro]] = {}
    resultados: list[Resultado] = []

    for reg in registros:
        evento_id = reg.dados.get("evento_id")
        if not isinstance(evento_id, str) or not evento_id.strip():
            resultados.append(Resultado(reg, "duvida", ("evento_id ausente",), None))
        else:
            grupos.setdefault(evento_id, []).append(reg)

    for grupo in grupos.values():
        resultados += _processar_grupo(grupo, tribunal, hub)

    return sorted(resultados, key=lambda r: r.registro.posicao)


def saldo_por_processo(resultados: list[Resultado]) -> dict[str, Decimal]:
    """Total líquido por processo: pagamento soma, estorno subtrai.
    Só entram eventos limpos (valido/corrigido)."""
    saldos: dict[str, Decimal] = {}
    for r in resultados:
        if r.evento is None:
            continue
        sinal = 1 if r.evento["tipo"] == "pagamento" else -1
        p = r.evento["processo"]
        saldos[p] = saldos.get(p, Decimal("0")) + sinal * r.evento["valor"]
    return saldos