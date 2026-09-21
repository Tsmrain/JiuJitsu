with open("docs/Documento.tex", "r") as f:
    lines = f.read().split("\n")

for i, line in enumerate(lines[715:735]):
    print(f"{715+i}: {line}")
