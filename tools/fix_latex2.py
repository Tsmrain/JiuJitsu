with open("docs/Documento.tex", "r") as f:
    lines = f.read().split("\n")

for i, line in enumerate(lines[450:525]):
    print(f"{450+i}: {line}")
