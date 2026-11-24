"""Funções de normalização. Cada uma devolve None quando não há
conversão segura; nunca adivinha."""
from __future__ import annotations

import re
import unicodedata
from datetime import date, datetime
from decimal import Decimal, InvalidOperation


def normalizar_processo(texto) -> str | None:
    """Devolve os 20 dígitos do número CNJ, ou None se não for válido."""
    if not isinstance(texto, str):
        return None
    texto = texto.strip()
    if re.fullmatch(r"\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}", texto):
        return re.sub(r"\D", "", texto)
    if re.fullmatch(r"\d{20}", texto):
        return texto
    return None


def normalizar_valor(valor) -> Decimal | None:
    """Aceita número JSON, '2500.50' e '2.500,50'. Nunca usa float."""
    if valor is None or isinstance(valor, bool):
        return None
    if isinstance(valor, (int, float)):
        return Decimal(str(valor))      # str() evita lixo binário do float
    if not isinstance(valor, str):
        return None
    texto = valor.strip()
    if re.fullmatch(r"\d{1,3}(\.\d{3})*,\d{1,2}", texto):     # 2.500,50
        texto = texto.replace(".", "").replace(",", ".")
    elif re.fullmatch(r"\d+(,\d{1,2})", texto):               # 2500,50
        texto = texto.replace(",", ".")
    elif not re.fullmatch(r"\d+(\.\d{1,2})?", texto):         # 2500.50
        return None
    try:
        return Decimal(texto)
    except InvalidOperation:
        return None


def normalizar_data(texto) -> date | None:
    """AAAA-MM-DD ou DD/MM/AAAA. Datas com hora/fuso ficam para prazo.py."""
    if not isinstance(texto, str):
        return None
    texto = texto.strip()
    for formato in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(texto, formato).date()
        except ValueError:
            pass
    return None


def tem_caractere_invalido(texto) -> bool:
    """True se o texto traz o caractere de substituição (perda de acento)."""
    return isinstance(texto, str) and "\ufffd" in texto


def chave_ente(texto) -> str | None:
    """Chave só para COMPARAR entes: sem acento, minúscula, espaços únicos.
    Devolve None se o nome tem '\ufffd' (não dá para comparar com segurança)."""
    if not isinstance(texto, str) or tem_caractere_invalido(texto):
        return None
    sem_acento = unicodedata.normalize("NFKD", texto)
    sem_acento = "".join(c for c in sem_acento if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", sem_acento).strip().lower()