from pathlib import Path

bruto = Path("dados/tribunal.csv").read_bytes()

print("BOM no início:", bruto[:3] == b"\xef\xbb\xbf")
print("bytes EF BF BD (�):", bruto.count(b"\xef\xbf\xbd"))
print()

for encoding in ["utf-8", "cp1252", "latin-1"]:
    try:
        texto = bruto.decode(encoding)
        segunda_linha = texto.splitlines()[1]
        print(f"{encoding}: OK -> {segunda_linha!r}")
    except UnicodeDecodeError as erro:
        print(f"{encoding}: FALHOU -> {erro}")