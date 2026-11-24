"""Escreve a saída: CSVs e relatorio.md. Determinístico (sem timestamps)."""
from __future__ import annotations

import csv
from collections import Counter
from decimal import Decimal
from pathlib import Path

from limpeza.cruzamento import ResultadoCruzamento
from limpeza.normalizacao import normalizar_valor
from limpeza.prazo import ResultadoPrazo
from limpeza.regras import Resultado


def _s(v) -> str:
    return "" if v is None else str(v)


def _md(texto) -> str:
    return _s(texto).replace("|", "\\|").replace("\n", " ")


def _csv(caminho: Path, cabecalho: list[str], linhas: list[list]) -> None:
    with open(caminho, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(cabecalho)
        w.writerows([[_s(c) for c in linha] for linha in linhas])


def valor_em_duvida(resultados: list[Resultado]) -> Decimal:
    """Soma dos valores LEGÍVEIS e positivos de eventos em dúvida
    (estorno subtrai). É só uma ordem de grandeza do que ficou de fora."""
    total = Decimal("0")
    for r in resultados:
        if r.acao != "duvida":
            continue
        v = normalizar_valor(r.registro.dados.get("valor"))
        if v is None or v <= 0:
            continue
        total += -v if r.registro.dados.get("tipo") == "estorno" else v
    return total


def gerar_markdown(resultados, cruzamento, prazos, saldos) -> str:
    L: list[str] = ["# Relatório de limpeza", ""]

    cont = Counter(r.acao for r in resultados)
    L += ["## Pagamentos: resumo", "", "| Ação | Qtde |", "|---|---|"]
    for acao in ("valido", "corrigido", "descartado", "duvida"):
        L.append(f"| {acao} | {cont.get(acao, 0)} |")
    L += ["", f"Total de registros lidos: {len(resultados)}.", "",
          f"Valor legível em eventos em dúvida: R$ {valor_em_duvida(resultados)} "
          "(ordem de grandeza; não entra no saldo).", ""]

    L += ["## Pagamentos: registro a registro", "",
          "| Arquivo | Posição | evento_id | Ação | Motivos |", "|---|---|---|---|---|"]
    for r in resultados:
        L.append(f"| {_md(r.registro.arquivo)} | {r.registro.posicao} | "
                 f"{_md(r.registro.dados.get('evento_id'))} | {r.acao} | "
                 f"{_md('; '.join(r.motivos))} |")
    L.append("")

    L += ["## Saldo líquido por processo (só eventos válidos ou corrigidos)", "",
          "| Processo (20 dígitos) | Saldo (R$) |", "|---|---|"]
    for p in sorted(saldos):
        L.append(f"| {p} | {saldos[p]} |")
    L.append("")

    cont_c = Counter(c.status for c in cruzamento)
    L += ["## Cruzamento tribunal.csv x hub.csv", "",
          "Resumo: " + ", ".join(f"{k}: {v}" for k, v in sorted(cont_c.items())), "",
          "| Processo | tribunal.csv (linha) | hub.csv (linha) | Status | Motivos |",
          "|---|---|---|---|---|"]
    for c in cruzamento:
        L.append(f"| {_s(c.processo)} | {_s(c.tribunal.posicao if c.tribunal else None)} | "
                 f"{_s(c.hub.posicao if c.hub else None)} | {c.status} | "
                 f"{_md('; '.join(c.motivos))} |")
    L.append("")

    L += ["## Prazos do hub.csv recalculados", "",
          "| Linha | Processo | Data usada | Prazo calculado | Prazo no hub | Status | Motivo |",
          "|---|---|---|---|---|---|---|"]
    for p in prazos:
        L.append(f"| {p.registro.posicao} | {_s(p.processo)} | {_s(p.data_usada)} | "
                 f"{_s(p.prazo_calculado)} | {_s(p.prazo_hub)} | {p.status} | {_md(p.motivo)} |")
    L.append("")

    L += ["## Premissas (viram dúvidas ao tribunal/operação)", "",
          "- A data de apresentação é o dia em America/Sao_Paulo.",
          "- `DD/MM/AAAA` significa dia/mês.",
          "- Para o mesmo `evento_id`, vale o `atualizado_em` mais recente; "
          "se a versão mais nova é inválida, o evento todo vai para dúvida.",
          "- Estorno chega com valor positivo e subtrai do saldo.",
          "- Cada `�` do tribunal.csv substitui exatamente um caractere.",
          "- `tribunal.csv` usa `;` e vírgula decimal, ao contrário da documentação.", ""]
    return "\n".join(L)


def escrever_saida(pasta: Path, resultados, cruzamento, prazos, saldos) -> None:
    pasta.mkdir(parents=True, exist_ok=True)

    _csv(pasta / "pagamentos_limpos.csv",
         ["evento_id", "processo", "valor", "data_pagamento", "tipo", "atualizado_em", "acao"],
         [[r.evento["evento_id"], r.evento["processo"], r.evento["valor"],
           r.evento["data_pagamento"].isoformat(), r.evento["tipo"],
           r.evento["atualizado_em"], r.acao]
          for r in resultados if r.evento is not None])

    _csv(pasta / "pagamentos_pendencias.csv",
         ["arquivo", "posicao", "evento_id", "acao", "motivos"],
         [[r.registro.arquivo, r.registro.posicao, r.registro.dados.get("evento_id"),
           r.acao, "; ".join(r.motivos)]
          for r in resultados if r.acao in ("descartado", "duvida")])

    _csv(pasta / "cruzamento.csv",
         ["processo", "linha_tribunal", "linha_hub", "status", "motivos"],
         [[c.processo, c.tribunal.posicao if c.tribunal else None,
           c.hub.posicao if c.hub else None, c.status, "; ".join(c.motivos)]
          for c in cruzamento])

    _csv(pasta / "prazos.csv",
         ["linha_hub", "processo", "data_usada", "prazo_calculado", "prazo_hub", "status", "motivo"],
         [[p.registro.posicao, p.processo, p.data_usada, p.prazo_calculado,
           p.prazo_hub, p.status, p.motivo] for p in prazos])

    (pasta / "relatorio.md").write_text(
        gerar_markdown(resultados, cruzamento, prazos, saldos), encoding="utf-8")