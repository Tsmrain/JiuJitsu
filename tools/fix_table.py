with open("docs/Documento.tex", "r") as f:
    lines = f.read().split("\n")

# Find the start of the table
for i, line in enumerate(lines):
    if "\\begin{tabularx}{\\textwidth}{|>{\\bfseries}l|X|l|>{\\bfseries}l|}" in line:
        # Check what follows
        print("\n".join(lines[i:i+15]))
        break
