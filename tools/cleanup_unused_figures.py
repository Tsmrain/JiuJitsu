import os
import re
from pathlib import Path

def main():
    tex_path = Path("docs/Documento.tex")
    tex_content = tex_path.read_text(encoding="utf-8")
    
    # Pattern to match \includegraphics[...]{path} or \includegraphics{path}
    pattern = re.compile(r"\\includegraphics(?:\[.*?\])?\{([^}]+)\}")
    matches = pattern.findall(tex_content)
    
    print("Referenced images in Documento.tex:")
    referenced_stems = set()
    for m in matches:
        clean_path = m.strip()
        filename = os.path.basename(clean_path)
        stem = os.path.splitext(filename)[0]
        referenced_stems.add(stem)
        print(f"  - {clean_path} (stem: {stem})")
        
    figuras_dir = Path("docs/Figuras")
    diagramas_dir = Path("docs/Diagramas")
    
    deleted_figuras = []
    if figuras_dir.exists():
        for f in figuras_dir.glob("*"):
            if f.is_file():
                if f.stem not in referenced_stems:
                    print(f"[REMOVING UNUSED FIGURA] {f.name}")
                    f.unlink()
                    deleted_figuras.append(f.name)
                else:
                    print(f"[KEEPING FIGURA] {f.name}")
                    
    deleted_diagramas = []
    if diagramas_dir.exists():
        for f in diagramas_dir.glob("*"):
            if f.is_file():
                if f.stem not in referenced_stems:
                    print(f"[REMOVING UNUSED DIAGRAMA] {f.name}")
                    f.unlink()
                    deleted_diagramas.append(f.name)
                else:
                    print(f"[KEEPING DIAGRAMA] {f.name}")
                    
    print(f"\nCleaned {len(deleted_figuras)} unused figure files and {len(deleted_diagramas)} unused diagram files.")

if __name__ == "__main__":
    main()
