"""Cruza tribunal.csv e hub.csv pelo número do processo (20 dígitos)."""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from limpeza.leitura import Registro
from limpeza.normalizacao import normalizar_processo, normalizar_valor


@dataclass(frozen=True)
class ResultadoCruzamento:
    processo: str | None
    tribunal: Registro | None
    hub: Registro | None
    status: str                 # ok | divergente | so_tribunal | so_hub | duvida
    motivos: tuple[str, ...]


def _base(texto: str) -> str:
    sem = unicodedata.normalize("NFKD", texto)
    sem = "".join(c for c in sem if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", sem).strip().lower()


def comparar_entes(tribunal, hub) -> str:
    """igual | compativel | diferente | indeterminado.

    'compativel': o tribunal perdeu acentos (U+FFFD) e o nome do hub
    casa se cada U+FFFD valer UM caractere. Isso NÃO confirma que é o
    mesmo ente; só mostra que não há contradição (premissa)."""
    if not isinstance(tribunal, str) or not isinstance(hub, str) or "\ufffd" in hub:
        return "indeterminado"
    t, h = _base(tribunal), _base(hub)
    if "\ufffd" not in t:
        return "igual" if t == h else "diferente"
    padrao = "".join("." if c == "\ufffd" else re.escape(c) for c in t)
    return "compativel" if re.fullmatch(padrao, h) else "diferente"


def _indexar(registros: list[Registro], campo: str):
    indice: dict[str, list[Registro]] = {}
    invalidos: list[Registro] = []
    for r in registros:
        p = normalizar_processo(r.dados.get(campo))
        if p is None:
            invalidos.append(r)
        else:
            indice.setdefault(p, []).append(r)
    return indice, invalidos


def _comparar(p: str, t: Registro, h: Registro) -> ResultadoCruzamento:
    status, motivos = "ok", []

    vt = normalizar_valor(t.dados.get("valor_face"))
    vh = normalizar_valor(h.dados.get("valor_face"))
    if vt is None or vh is None:
        status = "duvida"
        motivos.append("valor_face ausente ou inválido em uma das fontes")
    elif vt != vh:
        status = "divergente"
        motivos.append(f"valor_face: tribunal {vt}, hub {vh}")

    ente_t, ente_h = t.dados.get("ente_devedor"), h.dados.get("ente")
    ente = comparar_entes(ente_t, ente_h)
    if ente == "diferente":
        status = "divergente"
        motivos.append(f"ente: tribunal {ente_t!r}, hub {ente_h!r}")
    elif ente == "compativel":
        motivos.append("nota: ente compatível, mas o tribunal perdeu acentos; não confirmado")
    elif ente == "indeterminado":
        motivos.append("nota: ente não comparável")

    return ResultadoCruzamento(p, t, h, status, tuple(motivos))


def cruzar(tribunal: list[Registro], hub: list[Registro]) -> list[ResultadoCruzamento]:
    it, inval_t = _indexar(tribunal, "numero_processo")
    ih, inval_h = _indexar(hub, "processo")
    res: list[ResultadoCruzamento] = []

    for r in inval_t:
        res.append(ResultadoCruzamento(None, r, None, "duvida",
                   ("processo ausente ou fora do padrão CNJ em tribunal.csv",)))
    for r in inval_h:
        res.append(ResultadoCruzamento(None, None, r, "duvida",
                   ("processo ausente ou fora do padrão CNJ em hub.csv",)))

    for p in sorted(set(it) | set(ih)):
        t, h = it.get(p, []), ih.get(p, [])
        if len(t) > 1 or len(h) > 1:
            res.append(ResultadoCruzamento(p, t[0] if t else None, h[0] if h else None,
                       "duvida", ("processo repetido no mesmo arquivo",)))
        elif t and not h:
            res.append(ResultadoCruzamento(p, t[0], None, "so_tribunal",
                       ("processo existe só em tribunal.csv",)))
        elif h and not t:
            res.append(ResultadoCruzamento(p, None, h[0], "so_hub",
                       ("processo existe só em hub.csv",)))
        else:
            res.append(_comparar(p, t[0], h[0]))
    return res