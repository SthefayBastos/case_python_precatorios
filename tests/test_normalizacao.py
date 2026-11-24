from datetime import date
from decimal import Decimal

from limpeza.normalizacao import (
    chave_ente, normalizar_data, normalizar_processo, normalizar_valor,
    tem_caractere_invalido,
)


def test_processo_com_e_sem_mascara_viram_o_mesmo():
    assert normalizar_processo("0023456-21.2020.8.26.0053") == "00234562120208260053"
    assert normalizar_processo("00234562120208260053") == "00234562120208260053"


def test_processo_invalido_devolve_none():
    assert normalizar_processo("") is None
    assert normalizar_processo(None) is None
    assert normalizar_processo("123") is None


def test_valor_formatos():
    assert normalizar_valor(15000.0) == Decimal("15000.0")
    assert normalizar_valor(8000) == Decimal("8000")
    assert normalizar_valor("2.500,50") == Decimal("2500.50")
    assert normalizar_valor("2500.50") == Decimal("2500.50")


def test_valor_nulo_ou_lixo_devolve_none():
    assert normalizar_valor(None) is None
    assert normalizar_valor("abc") is None
    assert normalizar_valor(True) is None


def test_valor_negativo_nao_e_decidido_aqui():
    # a função converte; quem rejeita negativo é regras.py
    assert normalizar_valor(-200) == Decimal("-200")


def test_data_dois_formatos():
    assert normalizar_data("2025-04-10") == date(2025, 4, 10)
    assert normalizar_data("10/04/2025") == date(2025, 4, 10)


def test_data_invalida_e_bissexto():
    assert normalizar_data("2024-02-29") == date(2024, 2, 29)   # 2024 foi bissexto
    assert normalizar_data("2025-02-29") is None                # 2025 não foi
    assert normalizar_data("2025-04-03T01:00:00Z") is None      # fuso é do prazo.py


def test_caractere_invalido():
    assert tem_caractere_invalido("Munic\ufffdpio")
    assert not tem_caractere_invalido("Município")


def test_chave_ente_iguala_variacoes_de_caixa_e_acento():
    assert chave_ente("MUNICIPIO DE SAO PAULO") == chave_ente("Município de São Paulo")


def test_chave_ente_nao_compara_nome_com_perda_de_acento():
    assert chave_ente("Munic\ufffdpio de S\ufffdo Paulo") is None