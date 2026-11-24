import json
import re
from collections import Counter
from pathlib import Path


CAMINHO = Path("dados/pagamentos.json")

with open ( CAMINHO, encoding="utf-8") as f: eventos = json.load(f)

print ("Total de Registros", len (eventos))

# =--- identidade dos eventos ---

por_id = {}
for e in eventos:
    por_id.setdefault(e.get("evento_id"), []).append(e)

print ("evento_id distintos:", len(por_id))

duplicatas_exatas = 0
versoes_diferentes = 0
for id_, regs in por_id.items():
    if len(regs) > 1:

        distintos = { json.dumps(r, sort_keys=True)for r in regs}
        if len (distintos) == 1:
            duplicatas_exatas += 1
        else:
            versoes_diferentes += 1
            print(" versões diferentes:", id_)

print ("ids com duplicata exata:", duplicatas_exatas)
print ("ids com versões diferentes", versoes_diferentes)


#-- valor

tipos_valor = Counter (type(e.get("valor")).__name__ for e in eventos)
print ("Tipos de 'valor:'", dict (tipos_valor))

negativos = [e["evento_id"] for e in eventos
             if isinstance(e.get("valor"), (int, float)) and e ["valor"] < 0]
zeros = [e["eventos_id"] for e in eventos
         if isinstance(e.get("valor"), (int, float)) and e ["valor"] == 0]
print("Valores negativos", negativos)
print("valores zero", zeros)
# --- 3. Campo tipo ---
print("Valores de 'tipo':", dict(Counter(e.get("tipo") for e in eventos)))

# --- 4. Formato das datas ---
def formato_data(s):
    if not isinstance(s, str):
        return "não é texto"
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
        return "AAAA-MM-DD"
    if re.fullmatch(r"\d{2}/\d{2}/\d{4}", s):
        return "DD/MM/AAAA"
    return "outro"

print("Formatos de data:",
      dict(Counter(formato_data(e.get("data_pagamento")) for e in eventos)))

# --- 5. Formato do número do processo ---
def formato_processo(s):
    if not s:
        return "vazio/nulo"
    if re.fullmatch(r"\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}", s):
        return "com máscara CNJ"
    if re.fullmatch(r"\d{20}", s):
        return "20 dígitos sem máscara"
    return "outro"

print("Formatos de processo:",
      dict(Counter(formato_processo(e.get("processo")) for e in eventos)))

# --- 6. Campos faltando ---
esperados = {"evento_id", "processo", "valor", "data_pagamento", "tipo", "atualizado_em"}
for e in eventos:
    faltando = esperados - set(e.keys())
    extras = set(e.keys()) - esperados
    if faltando or extras:
        print("campos diferentes em", e.get("evento_id"), "faltando:", faltando, "extras:", extras)