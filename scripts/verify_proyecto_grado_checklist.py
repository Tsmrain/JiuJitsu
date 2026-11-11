# scripts/verify_proyecto_grado_checklist.py
# -*- coding: utf-8 -*-
"""
Auditoría y verificación automática del checklist de docs/ProyectoGrado.md:
- 8 capítulos y Tabla de Contenido actualizada (5.1 a 5.11, UC-01 a UC-10)
- 26 tablas APA intactas y sin pies 'Fuente:'
- Cero bloques de código de diagramas (@startuml, ```plantuml, ```mermaid, classDiagram) en Markdown
- Externalización completa de las 45 fuentes en docs/diagramas/codigo/ (*.puml / *.mmd)
- Todas las imágenes PNG referenciadas en el Markdown existen y son válidas en docs/diagramas/
- Rigor de Craig Larman: Nivel de Análisis puro en 5.X.1 / 5.X.2 / 5.X.4 (sin términos de implementación)
- Principio DIP en diagramas de paquetes y ausencia de la sigla 'BCE'
"""

import re
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DOC_PATH = ROOT_DIR / "docs" / "ProyectoGrado.md"
DIAGRAM_DIR = ROOT_DIR / "docs" / "diagramas"
CODE_DIR = DIAGRAM_DIR / "codigo"

FORBIDDEN_ANALYSIS_TERMS = [
    r"\bJWT\b",
    r"\bbcrypt\b",
    r"\bFastAPI\b",
    r"\bReact\b",
    r"\bPostgreSQL\b",
    r"\bPostgREST\b",
    r"\bQdrant\b",
    r"\bYOLOv?26\b",
    r"\bYOLO\b",
    r"\bQwen\d?-?VL\b",
    r"\bQwen\b",
    r"\bDTW\b",
    r"\bMLX\b",
    r"\bOpenCV\b",
    r"\bOpenStreetMap\b",
    r"\bNominatim\b",
    r"\bLeaflet\b",
    r"\bHTTP\b",
    r"\bJSON\b",
    r"\bREST\b",
    r"\bSQL\b",
    r"\bendpoint\b",
    r"\bendpoints\b",
    r"\bRAG\b",
    r"\bVLM\b",
    r"\bLLM\b",
    r"\bAPI\b",
    r"\bdatabase\b",
    r"\bPDF\b",
    r"\bregex\b",
]


def verify():
    assert DOC_PATH.exists(), f"No existe {DOC_PATH}"
    content = DOC_PATH.read_text(encoding="utf-8")

    print("=== 1. VERIFICACIÓN DE CAPÍTULOS ===")
    capitulos = re.findall(r"^(# Capítulo [IVXLCDM]+:.*)$", content, re.MULTILINE)
    for c in capitulos:
        print("  ", c)
    assert len(capitulos) == 8, f"Se esperaban 8 capítulos, se encontraron {len(capitulos)}"

    print("\n=== 2. VERIFICACIÓN DE TABLA DE CONTENIDO ===")
    toc_match = re.search(r"## TABLA DE CONTENIDO(.*?)# Capítulo I:", content, re.DOTALL)
    assert toc_match, "Tabla de contenido no encontrada"
    toc_text = toc_match.group(1)
    for roman in ["I", "II", "III", "IV", "V", "VI", "VII", "VIII"]:
        assert f"Capítulo {roman}:" in toc_text, f"Falta Capítulo {roman} en TOC"
    for n in range(1, 11):
        assert f"5.{n}. Caso de Uso {n}:" in toc_text, f"Falta 5.{n} en TOC"
        assert f"(UC-{n:02d})" in toc_text, f"Falta UC-{n:02d} en TOC"
    assert "5.11. Diagramas de Arquitectura Consolidada del Sistema Completo" in toc_text
    print("  TOC contiene Capítulos I–VIII, UC-01..UC-10 y sección 5.11 correctamente.")

    print("\n=== 3. VERIFICACIÓN DE TABLAS APA ===")
    tablas = re.findall(r"^(Tabla \d+)\n\*(.*?)\*", content, re.MULTILINE)
    print(f"  Total de tablas APA encontradas: {len(tablas)}")
    assert len(tablas) == 26, f"Se esperaban exactamente 26 tablas, se encontraron {len(tablas)}"
    fuente_matches = [line for line in content.splitlines() if line.startswith("*Fuente:")]
    assert len(fuente_matches) == 0, f"Quedan pies de tabla con 'Fuente:': {fuente_matches}"
    print("  26 tablas APA verificadas sin 'Fuente:'.")

    print("\n=== 4. VERIFICACIÓN DE MATRIZ DE TRAZABILIDAD (CAPÍTULO IV) ===")
    t17_match = re.search(r"Tabla 17\n\*Matriz de Trazabilidad.*?\n(.*?)\n\*Nota\.\*", content, re.DOTALL)
    assert t17_match, "Tabla 17 no encontrada"
    t17_text = t17_match.group(1)
    for n in range(1, 11):
        assert f"UC-{n:02d}" in t17_text, f"Falta UC-{n:02d} en Tabla 17"
    print("  Matriz de Trazabilidad cubre UC-01..UC-10 completo.")

    print("\n=== 5. VERIFICACIÓN DE VISTA PREVIA LIMPIA EN MARKDOWN ===")
    forbidden_md_tokens = ["```plantuml", "```mermaid", "@startuml", "@enduml", "classDiagram"]
    for tok in forbidden_md_tokens:
        count = content.count(tok)
        assert count == 0, f"Token prohibido '{tok}' encontrado {count} veces en {DOC_PATH}"
    print("  Cero bloques PlantUML/Mermaid/código de diagramas en docs/ProyectoGrado.md.")

    print("\n=== 6. VERIFICACIÓN DE IMÁGENES Y FUENTES EXTERNALIZADAS ===")
    imgs = re.findall(r"!\[.*?\]\((diagramas/[^)]+\.png)\)", content)
    print(f"  Total de imágenes referenciadas en Markdown: {len(imgs)}")
    assert len(imgs) == 45, f"Se esperaban 45 imágenes (1 dominio + 40 de UC-01..UC-10 + 3 consolidadas + 1 seguridad), hay {len(imgs)}"
    assert len(set(imgs)) == 45, "Existen referencias de imagen duplicadas"
    for img in imgs:
        img_p = ROOT_DIR / "docs" / img
        assert img_p.exists(), f"No existe imagen física: {img_p}"
        data = img_p.read_bytes()
        assert data.startswith(b"\x89PNG\r\n\x1a\n"), f"Archivo no es PNG válido: {img_p}"
        assert len(data) > 5000, f"Imagen sospechosamente pequeña ({len(data)} bytes): {img_p}"
        stem = img_p.stem
        puml_p = CODE_DIR / f"{stem}.puml"
        mmd_p = CODE_DIR / f"{stem}.mmd"
        assert puml_p.exists() or mmd_p.exists(), f"Falta archivo fuente en docs/diagramas/codigo/ para {stem}"
    print("  Las 45 imágenes PNG y sus 45 archivos fuente en /codigo existen y son válidos.")

    print("\n=== 7. VERIFICACIÓN DE PUREZA DE NIVEL DE ANÁLISIS (LARMAN / ECB) ===")
    for n in range(1, 11):
        cu_pattern = rf"### 5\.{n}\.1\. .*?\n(.*?)\n### 5\.{n}\.2\."
        m = re.search(cu_pattern, content, re.DOTALL)
        assert m, f"No se encontró sección de análisis 5.{n}.1"
        spec_text = m.group(1)
        for pat in FORBIDDEN_ANALYSIS_TERMS:
            hits = re.findall(pat, spec_text, re.IGNORECASE)
            assert not hits, f"Término de implementación {hits} encontrado en análisis 5.{n}.1"

        cu_code = f"cu{n:02d}"
        seq_puml = (CODE_DIR / f"{cu_code}_secuencia.puml").read_text(encoding="utf-8")
        assert "boundary " in seq_puml and "control " in seq_puml and "entity " in seq_puml, (
            f"Faltan estereotipos ECB en {cu_code}_secuencia.puml"
        )
        assert "database " not in seq_puml, f"database encontrado en análisis {cu_code}_secuencia.puml"
        for pat in FORBIDDEN_ANALYSIS_TERMS:
            hits = re.findall(pat, seq_puml, re.IGNORECASE)
            assert not hits, f"Término de implementación {hits} encontrado en {cu_code}_secuencia.puml"

        pkg_mmd = (CODE_DIR / f"{cu_code}_paquetes.mmd").read_text(encoding="utf-8")
        assert "Presentacion --> Aplicacion" in pkg_mmd
        assert "Infraestructura --> Aplicacion" in pkg_mmd
        assert "Infraestructura --> Dominio" in pkg_mmd
        assert "Aplicacion --> Dominio" in pkg_mmd
        assert "Dominio --> Infraestructura" not in pkg_mmd
    print("  Pureza de Nivel de Análisis, estereotipos ECB y principio DIP verificados en UC-01..UC-10.")

    print("\n=== 8. VERIFICACIÓN DE REFERENCIAS BIBLIOGRÁFICAS APA ===")
    ref_section = content.split("# Referencias Bibliográficas")[1]
    refs = [r.strip() for r in ref_section.strip().split("\n\n") if r.strip()]
    print(f"  Total de referencias bibliográficas APA: {len(refs)}")
    assert len(refs) >= 35, f"Se esperaban >= 35 referencias, se encontraron {len(refs)}"

    print("\n=== 9. VERIFICACIÓN DE CITAS, CROSS-REFS Y AUSENCIA DE BCE ===")
    assert "(Mannino, 2018)" in content
    assert "(Russell & Norvig, 2021)" in content
    assert "desarrollo evolutivo de los diez casos de uso" in content
    assert "(ver §5.10.1)" in content
    assert b"\r" not in DOC_PATH.read_bytes(), "Se encontraron bytes CR (\\r) en docs/ProyectoGrado.md"
    expected_arrow = r"$\rightarrow$ Diseño"
    arrow_count = content.count(expected_arrow)
    assert arrow_count == 30, f"Se esperaban 30 correspondencias ECB -> Diseño, se encontraron {arrow_count}"
    bce_matches = re.findall(r"\bBCE\b", content, re.IGNORECASE)
    assert len(bce_matches) == 0, f"Quedaron apariciones de BCE: {bce_matches}"
    print("  Citas APA, referencias cruzadas, LaTeX ECB y ausencia de 'BCE' verificadas.")

    print("\n¡TODAS LAS VERIFICACIONES DEL CHECKLIST PASARON AL 100%!")


if __name__ == "__main__":
    verify()
