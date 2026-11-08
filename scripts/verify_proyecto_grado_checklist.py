# scripts/verify_proyecto_grado_checklist.py
# -*- coding: utf-8 -*-
"""
Auditoría y verificación automática del checklist de ProyectoGrado.md
incluyendo la nueva sección 5.9 con los 3 diagramas del sistema completo.
"""

import re
from pathlib import Path

def verify():
    doc_path = Path("docs/ProyectoGrado.md")
    assert doc_path.exists(), "No existe docs/ProyectoGrado.md"
    content = doc_path.read_text(encoding="utf-8")
    
    print("=== 1. VERIFICACIÓN DE CAPÍTULOS ===")
    capitulos = re.findall(r"^(# Capítulo [IVXLCDM]+:.*)$", content, re.MULTILINE)
    for c in capitulos:
        print("  ", c)
    assert len(capitulos) == 8, f"Se esperaban 8 capítulos, se encontraron {len(capitulos)}"

    print("\n=== 2. VERIFICACIÓN DE TABLA DE CONTENIDO ===")
    toc_match = re.search(r"## TABLA DE CONTENIDO(.*?)# Capítulo I:", content, re.DOTALL)
    assert toc_match, "Tabla de contenido no encontrada"
    toc_text = toc_match.group(1)
    for roman in ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII']:
        assert f"Capítulo {roman}:" in toc_text, f"Falta Capítulo {roman} en TOC"
    assert "5.9. Diagramas de Arquitectura Consolidada del Sistema Completo" in toc_text
    print("  TOC contiene Capítulos I al VIII y la sección 5.9 con formato correcto.")

    print("\n=== 3. VERIFICACIÓN DE TABLAS APA ===")
    tablas = re.findall(r"^(Tabla \d+)\n\*(.*?)\*", content, re.MULTILINE)
    print(f"  Total de tablas APA encontradas: {len(tablas)}")
    for t_num, t_title in tablas:
        print(f"   {t_num}: {t_title}")
    assert len(tablas) == 26, f"Se esperaban exactamente 26 tablas, se encontraron {len(tablas)}"
    
    # Verificar que no queden 'Fuente:' en los pies de tabla
    fuente_matches = [line for line in content.splitlines() if line.startswith("*Fuente:")]
    print(f"  Pies de tabla con 'Fuente:': {len(fuente_matches)}")
    assert len(fuente_matches) == 0, f"Quedan pies de tabla con 'Fuente:': {fuente_matches}"

    print("\n=== 4. VERIFICACIÓN DE DIAGRAMAS PLANTUML E IMÁGENES ===")
    imgs = re.findall(r"!\[.*?\]\((diagramas/.*?\.png)\)", content)
    print(f"  Total de imágenes de diagramas referenciadas: {len(imgs)}")
    assert len(imgs) == 19, f"Se esperaban 19 imágenes (16 de CU/secuencia + 3 de sistema completo), se encontraron {len(imgs)}"
    for img in imgs:
        img_p = Path("docs") / img
        assert img_p.exists(), f"No existe {img_p}"
        assert img_p.stat().st_size > 5000, f"Imagen inválida {img_p} ({img_p.stat().st_size} bytes)"
    print("  Todas las 19 imágenes existen y están intactas.")

    start_count = content.count("@startuml")
    end_count = content.count("@enduml")
    print(f"  Bloques PlantUML (@startuml / @enduml): {start_count} / {end_count}")
    assert start_count == 19 and end_count == 19, f"Se esperaban 19 bloques PlantUML, hay {start_count}"

    print("\n=== 5. VERIFICACIÓN DE REFERENCIAS BIBLIOGRÁFICAS APA ===")
    ref_section = content.split("# Referencias Bibliográficas")[1]
    refs = [r.strip() for r in ref_section.strip().split("\n\n") if r.strip()]
    print(f"  Total de referencias bibliográficas APA: {len(refs)}")
    assert len(refs) >= 35, f"Se esperaban >= 35 referencias, se encontraron {len(refs)}"

    print("\n=== 6. VERIFICACIÓN DE OBSERVACIONES DE REVISIÓN RESUELTAS ===")
    assert "(Mannino, 2018)" in content, "Falta cita (Mannino, 2018)"
    assert "(Russell & Norvig, 2021)" in content, "Falta cita (Russell & Norvig, 2021)"
    assert "132 escenarios unitarios" in content or "132 Pruebas Superadas" in content, "Falta ajuste de 132 pruebas"
    assert "Diagrama_Actividad_Sistema_Completo" in content
    assert "Diagrama_Clases_Sistema_Completo" in content
    assert "Diagrama_Casos_Uso_Sistema_Completo" in content
    print("  Todas las observaciones de revisión y los 3 diagramas del sistema completo están verificados.")

    print("\n=== 7. VERIFICACIÓN DE AUSENCIA DE LA SIGLA BCE ===")
    bce_matches = re.findall(r"\bBCE\b", content, re.IGNORECASE)
    print(f"  Coincidencias de BCE: {len(bce_matches)}")
    assert len(bce_matches) == 0, f"Error: Quedaron {len(bce_matches)} apariciones de BCE"

    print("\n¡TODAS LAS VERIFICACIONES DEL CHECKLIST PASARON AL 100%!")

if __name__ == "__main__":
    verify()
