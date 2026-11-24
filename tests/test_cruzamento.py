from limpeza.cruzamento import comparar_entes, cruzar
from limpeza.leitura import Registro


def t(pos, proc, ente, valor):
    return Registro("tribunal.csv", pos, {"numero_processo": proc, "ente_devedor": ente, "valor_face": valor})


def h(pos, proc, ente, valor):
    return Registro("hub.csv", pos, {"processo": proc, "ente": ente, "valor_face": valor})


def test_entes_iguais_ignorando_caixa_e_acento():
    assert comparar_entes("Município de São Paulo", "MUNICIPIO DE SAO PAULO") == "igual"


def test_ente_com_perda_de_acento_e_compativel_mas_nao_confirmado():
    assert comparar_entes("Munic\ufffdpio de S\ufffdo Paulo", "MUNICIPIO DE SAO PAULO") == "compativel"


def test_uniao_nao_e_municipio_de_santos():
    assert comparar_entes("Uni\ufffdo", "Município de Santos") == "diferente"


def test_valor_face_divergente():  # 0023456-21.2020.8.26.0053
    res = cruzar([t(3, "0023456-21.2020.8.26.0053", "Estado", "30.000,00")],
                 [h(3, "00234562120208260053", "Estado", "31000.00")])
    assert res[0].status == "divergente"
    assert "valor_face" in res[0].motivos[0]


def test_mesmo_valor_em_formatos_diferentes_nao_diverge():
    res = cruzar([t(2, "0012345-10.2019.8.26.0053", "Estado", "45.000,00")],
                 [h(2, "0012345-10.2019.8.26.0053", "Estado", "45000.00")])
    assert res[0].status == "ok"


def test_processo_em_uma_fonte_so():
    res = cruzar([t(6, "0067890-65.2016.8.26.0053", "X", "7.000,00")],
                 [h(6, "0056789-54.2017.4.03.6100", "Y", "22000.00")])
    assert sorted(r.status for r in res) == ["so_hub", "so_tribunal"]


def test_processo_repetido_no_mesmo_arquivo_vai_para_duvida():
    res = cruzar([t(2, "0012345-10.2019.8.26.0053", "A", "1,00"),
                  t(3, "0012345-10.2019.8.26.0053", "A", "1,00")], [])
    assert res[0].status == "duvida"