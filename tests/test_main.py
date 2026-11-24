import hashlib
import json
from decimal import Decimal

from main import executar


def _montar(tmp_path):
    dados = tmp_path / "dados"
    dados.mkdir()
    eventos = [
        {"evento_id": "ev-001", "processo": "0012345-10.2019.8.26.0053", "valor": 15000.0,
         "data_pagamento": "2025-03-10", "tipo": "pagamento",
         "atualizado_em": "2025-03-10T10:00:00-03:00"},
        {"evento_id": "ev-004", "processo": "0012345-10.2019.8.26.0053", "valor": None,
         "data_pagamento": "2025-05-03", "tipo": "pagamento",
         "atualizado_em": "2025-05-03T08:00:00-03:00"},
    ]
    (dados / "pagamentos.json").write_text(json.dumps(eventos), encoding="utf-8")
    (dados / "tribunal.csv").write_text(
        "numero_processo;ente_devedor;valor_face\n"
        "0012345-10.2019.8.26.0053;Munic\ufffdpio de S\ufffdo Paulo;45.000,00\n", encoding="utf-8")
    (dados / "hub.csv").write_text(
        "processo,ente,valor_face,apresentado_em,prazo_pagamento\n"
        "0012345-10.2019.8.26.0053,MUNICIPIO DE SAO PAULO,45000.00,2025-04-02,2027-12-31\n",
        encoding="utf-8")
    return dados


def _hashes(pasta):
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(pasta.iterdir())}


def test_executar_gera_saida_e_nao_altera_originais(tmp_path):
    dados, saida = _montar(tmp_path), tmp_path / "saida"
    antes = _hashes(dados)

    resultados, cruzamento, prazos, saldos = executar(dados, saida)

    assert _hashes(dados) == antes
    for nome in ("pagamentos_limpos.csv", "pagamentos_pendencias.csv",
                 "cruzamento.csv", "prazos.csv", "relatorio.md"):
        assert (saida / nome).exists()
    assert saldos["00123451020198260053"] == Decimal("15000.0")
    assert [r.acao for r in resultados] == ["valido", "duvida"]
    assert prazos[0].status == "divergente"      # 2/4 ainda é "até 2 de abril"


def test_executar_duas_vezes_gera_o_mesmo_resultado(tmp_path):
    dados = _montar(tmp_path)
    executar(dados, tmp_path / "s1")
    executar(dados, tmp_path / "s2")
    assert _hashes(tmp_path / "s1") == _hashes(tmp_path / "s2")


def test_recusa_gravar_na_pasta_dos_originais(tmp_path):
    import pytest
    dados = _montar(tmp_path)
    with pytest.raises(ValueError):
        executar(dados, dados)
        