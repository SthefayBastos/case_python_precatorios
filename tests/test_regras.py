from decimal import Decimal

import pytest

from limpeza.leitura import Registro
from limpeza.regras import classificar_pagamentos, saldo_por_processo

PROC_A = "0012345-10.2019.8.26.0053"
PROC_A_20 = "00123451020198260053"
PROC_B_20 = "00234562120208260053"      # 0023456-21.2020.8.26.0053
PROC_C = "0034567-32.2018.8.26.0405"
PROC_C_20 = "00345673220188260405"
CONHECIDOS = {PROC_A_20, PROC_B_20, PROC_C_20}


def reg(pos, **campos):
    dados = {
        "evento_id": "ev-001",
        "processo": PROC_A,
        "valor": 100,
        "data_pagamento": "2025-03-10",
        "tipo": "pagamento",
        "atualizado_em": "2025-03-10T10:00:00-03:00",
    }
    dados.update(campos)
    return Registro("pagamentos.json", pos, dados)


def classificar(regs, tribunal=CONHECIDOS, hub=CONHECIDOS):
    return classificar_pagamentos(regs, tribunal, hub)


def test_duplicata_exata_descarta_a_copia():  # caso ev-002
    regs = [
        reg(1, evento_id="ev-002", valor="2.500,50", data_pagamento="10/04/2025"),
        reg(2, evento_id="ev-002", valor="2.500,50", data_pagamento="10/04/2025"),
    ]
    res = classificar(regs)
    assert [r.acao for r in res] == ["corrigido", "descartado"]
    assert res[0].evento["valor"] == Decimal("2500.50")


def test_versao_mais_recente_vale():  # caso ev-001
    regs = [
        reg(1, valor=15000.0),
        reg(2, valor=15500.0, atualizado_em="2025-03-11T09:00:00-03:00"),
    ]
    res = classificar(regs)
    assert [r.acao for r in res] == ["descartado", "valido"]
    assert res[1].evento["valor"] == Decimal("15500.0")


def test_mesmo_atualizado_em_com_conteudo_diferente_vai_para_duvida():
    res = classificar([reg(1, valor=100), reg(2, valor=200)])
    assert [r.acao for r in res] == ["duvida", "duvida"]


def test_versao_nova_invalida_manda_o_evento_todo_para_duvida():  # decisão B
    regs = [
        reg(1, valor=100),
        reg(2, valor=None, atualizado_em="2025-03-11T09:00:00-03:00"),
    ]
    res = classificar(regs)
    assert [r.acao for r in res] == ["duvida", "duvida"]


def test_atualizado_em_compara_instantes_e_nao_texto():
    # Pos 1 = 2025-03-11 02:00Z. Pos 2 = 2025-03-11 01:00Z.
    # Como texto, "2025-03-11..." > "2025-03-10...", mas o instante da pos 1 é mais novo.
    regs = [
        reg(1, valor=200, atualizado_em="2025-03-10T23:00:00-03:00"),
        reg(2, valor=100, atualizado_em="2025-03-11T01:00:00Z"),
    ]
    res = classificar(regs)
    assert [r.acao for r in res] == ["valido", "descartado"]


def test_estorno_subtrai_no_saldo():  # ev-006 e ev-007
    regs = [
        reg(1, evento_id="ev-006", processo=PROC_C, valor=5000),
        reg(2, evento_id="ev-007", processo=PROC_C, valor=5000, tipo="estorno"),
    ]
    res = classificar(regs)
    assert [r.acao for r in res] == ["valido", "valido"]
    assert saldo_por_processo(res)[PROC_C_20] == Decimal("0")


@pytest.mark.parametrize("campo,valor", [
    ("valor", None),     # ev-004
    ("valor", -200),     # ev-009
    ("valor", 0),
    ("processo", ""),    # ev-010
])
def test_dado_invalido_vai_para_duvida(campo, valor):
    res = classificar([reg(1, **{campo: valor})])
    assert res[0].acao == "duvida"
    assert res[0].evento is None


def test_processo_sem_mascara_casa_com_o_conhecido():  # ev-005
    res = classificar([reg(1, processo=PROC_B_20)])
    assert res[0].acao == "valido"
    assert res[0].evento["processo"] == PROC_B_20


def test_processo_desconhecido_vai_para_duvida():
    res = classificar([reg(1, processo="0099999-99.2020.8.26.0053")])
    assert res[0].acao == "duvida"


def test_processo_so_em_uma_fonte_e_mantido_com_nota():  # ev-011
    res = classificar([reg(1)], tribunal={PROC_A_20}, hub=set())
    assert res[0].acao == "valido"
    assert any("só existe em tribunal.csv" in m for m in res[0].motivos)


def test_evento_id_ausente_vai_para_duvida():
    res = classificar([reg(1, evento_id=None)])
    assert res[0].acao == "duvida"


def test_saldo_ignora_duvida_e_descartado():
    regs = [
        reg(1, evento_id="ev-1", valor=100),
        reg(2, evento_id="ev-2", valor=None),
    ]
    assert saldo_por_processo(classificar(regs))[PROC_A_20] == Decimal("100")