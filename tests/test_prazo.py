from datetime import date

import pytest

from limpeza.leitura import Registro
from limpeza.prazo import calcular_prazo, conferir_prazos, data_apresentacao


def test_dia_limite_2_de_abril_ainda_e_ate_2_de_abril():
    assert calcular_prazo(date(2025, 4, 2)) == date(2026, 12, 31)


def test_3_de_abril_pula_um_ano():
    assert calcular_prazo(date(2025, 4, 3)) == date(2027, 12, 31)


def test_bissexto_antes_do_limite():
    assert calcular_prazo(date(2024, 2, 29)) == date(2025, 12, 31)


def test_data_sem_hora_e_usada_como_esta():
    assert data_apresentacao("2025-04-02") == date(2025, 4, 2)


def test_fuso_menos_tres_mantem_o_dia():
    assert data_apresentacao("2025-04-02T23:30:00-03:00") == date(2025, 4, 2)


def test_utc_converte_para_o_dia_de_brasilia():
    # 01:00Z = 22:00 do dia anterior em Brasília
    assert data_apresentacao("2025-04-03T01:00:00Z") == date(2025, 4, 2)


def test_data_hora_sem_fuso_devolve_none():
    assert data_apresentacao("2025-04-02T23:30:00") is None


@pytest.mark.parametrize("texto", ["", None, "02/04/2025"])
def test_data_invalida_devolve_none(texto):
    assert data_apresentacao(texto) is None


def _hub(pos, processo, apresentado, prazo):
    return Registro("hub.csv", pos, {
        "processo": processo,
        "apresentado_em": apresentado,
        "prazo_pagamento": prazo,
    })


def test_conferencia_dos_cinco_casos_do_hub():
    regs = [
        _hub(2, "0012345-10.2019.8.26.0053", "2025-04-02", "2027-12-31"),
        _hub(3, "00234562120208260053", "2025-04-03", "2027-12-31"),
        _hub(4, "0034567-32.2018.8.26.0405", "2024-02-29", "2025-12-31"),
        _hub(5, "0045678-43.2021.5.02.0011", "2025-04-02T23:30:00-03:00", "2026-12-31"),
        _hub(6, "0056789-54.2017.4.03.6100", "2025-04-03T01:00:00Z", "2027-12-31"),
    ]
    res = conferir_prazos(regs)
    assert [r.status for r in res] == ["divergente", "ok", "ok", "ok", "divergente"]
    assert res[0].prazo_calculado == date(2026, 12, 31)
    assert res[4].prazo_calculado == date(2026, 12, 31)


def test_prazo_do_hub_invalido_vai_para_duvida():
    res = conferir_prazos([_hub(2, "00123451020198260053", "2025-04-02", "")])
    assert res[0].status == "duvida"
    assert res[0].prazo_calculado == date(2026, 12, 31)