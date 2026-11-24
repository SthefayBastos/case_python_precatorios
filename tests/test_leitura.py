import json

from limpeza.leitura import ler_hub, ler_pagamentos, ler_tribunal


def test_pagamentos_preserva_valores_como_vieram(tmp_path):
    arquivo = tmp_path / "pagamentos.json"
    eventos = [
        {"evento_id": "ev-002", "valor": "2.500,50"},
        {"evento_id": "ev-004", "valor": None},
    ]
    arquivo.write_text(json.dumps(eventos), encoding="utf-8")

    regs = ler_pagamentos(arquivo)

    assert [r.posicao for r in regs] == [1, 2]
    assert regs[0].dados["valor"] == "2.500,50"   # continua texto
    assert regs[1].dados["valor"] is None          # continua nulo


def test_tribunal_usa_ponto_e_virgula_e_linha_comeca_em_2(tmp_path):
    arquivo = tmp_path / "tribunal.csv"
    arquivo.write_text(
        "numero_processo;ente_devedor;valor_face\n"
        "0012345-10.2019.8.26.0053;Município de São Paulo;45.000,00\n",
        encoding="utf-8",
    )

    regs = ler_tribunal(arquivo)

    assert regs[0].posicao == 2
    assert regs[0].dados["valor_face"] == "45.000,00"  # texto, sem conversão


def test_tribunal_preserva_caractere_de_substituicao(tmp_path):
    arquivo = tmp_path / "tribunal.csv"
    arquivo.write_text(
        "numero_processo;ente_devedor;valor_face\n"
        "0045678-43.2021.5.02.0011;Uni\ufffdo;9.800,00\n",
        encoding="utf-8",
    )

    regs = ler_tribunal(arquivo)

    assert "\ufffd" in regs[0].dados["ente_devedor"]  # não esconde o problema


def test_hub_usa_virgula_e_aceita_bom(tmp_path):
    arquivo = tmp_path / "hub.csv"
    arquivo.write_bytes(
        b"\xef\xbb\xbfprocesso,ente,valor_face,apresentado_em,prazo_pagamento\n"
        b"00234562120208260053,Munic,31000.00,2025-04-03,2027-12-31\n"
    )

    regs = ler_hub(arquivo)

    assert regs[0].dados["processo"] == "00234562120208260053"  # sem "\ufeff" no cabeçalho