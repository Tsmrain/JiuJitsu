# scripts/update_capitulo_5_plantuml.py
# -*- coding: utf-8 -*-
"""
Script para transformar el Capítulo 5 de docs/ProyectoGrado.md:
1. Reemplazar diagramas de caso de uso y secuencia con PlantUML y enlazar las imágenes PNG.
2. Eliminar completamente la sigla y letras BCE en todo el capítulo.
3. Asegurar consistencia absoluta con el código base y la arquitectura.
"""

import re
import sys
from pathlib import Path
from generate_plantuml_diagrams import DIAGRAMS

def build_updated_capitulo_5():
    # Leer el texto base de build_capitulo_5.py
    import build_capitulo_5
    raw_cap5 = build_capitulo_5.get_capitulo_5_markdown()
    
    # 1. Modificar encabezado general
    raw_cap5 = raw_cap5.replace(
        "3. **Diagrama de Clases de Diseño (Participantes):** Modelado estructural de las clases involucradas organizadas bajo el patrón **BCE (Boundary, Control, Entity)**, especificando sus atributos y métodos esenciales.",
        "3. **Diagrama de Clases de Diseño (Participantes):** Modelado estructural de las clases involucradas organizadas según la distribución de responsabilidades de **Frontera, Control y Entidad**, especificando sus atributos y métodos esenciales."
    )
    raw_cap5 = raw_cap5.replace(
        "4. **Diagrama de Secuencia del Caso de Uso (Patrón BCE):** Modelado dinámico de la interacción temporal y la distribución de responsabilidades entre la capa de Frontera/Interfaz (*Boundary*), la capa de Control/Servicios (*Control*) y la capa de Dominio/Entidades (*Entity*).",
        "4. **Diagrama de Secuencia del Caso de Uso:** Modelado dinámico de la interacción temporal y la distribución de responsabilidades entre la capa de Frontera/Interfaz (*Boundary*), la capa de Control/Servicios (*Control*) y la capa de Dominio/Entidades (*Entity*)."
    )
    
    # 2. Iterar sobre cada uno de los 8 Casos de Uso
    for i in range(1, 9):
        cu_code = f"cu0{i}"
        cu_tag = f"UC-0{i}"
        
        # --- A. Actualizar 5.i.2 Diagrama de Caso de Uso ---
        # Buscar sección 5.i.2 hasta 5.i.3
        pattern_cu = rf"(### 5\.{i}\.2 Diagrama de Caso de Uso {cu_tag}\n)(.*?)(?=\n---\n\n### 5\.{i}\.3)"
        puml_caso_uso = DIAGRAMS[f"{cu_code}_caso_uso"]
        replacement_cu = (
            f"\\1"
            f"![Diagrama de Caso de Uso {cu_tag}](diagramas/{cu_code}_caso_uso.png)\n\n"
            f"```plantuml\n{puml_caso_uso}\n```"
        )
        raw_cap5, count = re.subn(pattern_cu, replacement_cu, raw_cap5, flags=re.DOTALL)
        assert count == 1, f"No se pudo reemplazar 5.{i}.2 Diagrama de Caso de Uso"
        
        # --- B. Actualizar 5.i.3 Diagrama de Clases ---
        # Cambiar título
        old_cl_title = f"### 5.{i}.3 Diagrama de Clases (Patrón BCE) {cu_tag}"
        new_cl_title = f"### 5.{i}.3 Diagrama de Clases de Diseño (Participantes) {cu_tag}"
        assert old_cl_title in raw_cap5, f"No se encontró título {old_cl_title}"
        raw_cap5 = raw_cap5.replace(old_cl_title, new_cl_title)
        
        # Reemplazar descripción de Boundary-Control-Entity
        raw_cap5 = raw_cap5.replace(
            "estructuradas bajo el patrón Boundary-Control-Entity:",
            "estructuradas bajo la distribución de responsabilidades de Frontera (Boundary), Control y Entidad (Entity):"
        )
        raw_cap5 = raw_cap5.replace(
            "* **Boundary:**",
            "* **Frontera (Boundary):**"
        )
        raw_cap5 = raw_cap5.replace(
            "* **Entity:**",
            "* **Entidad (Entity):**"
        )
        
        # --- C. Actualizar 5.i.4 Diagrama de Secuencia ---
        old_sq_title = f"### 5.{i}.4 Diagrama de Secuencia BCE {cu_tag}"
        new_sq_title = f"### 5.{i}.4 Diagrama de Secuencia {cu_tag}"
        assert old_sq_title in raw_cap5, f"No se encontró título {old_sq_title}"
        
        pattern_sq = rf"({re.escape(old_sq_title)}\n)(.*?)(?=\n---\n\n### 5\.{i}\.5)"
        puml_secuencia = DIAGRAMS[f"{cu_code}_secuencia"]
        replacement_sq = (
            f"{new_sq_title}\n\n"
            f"![Diagrama de Secuencia {cu_tag}](diagramas/{cu_code}_secuencia.png)\n\n"
            f"```plantuml\n{puml_secuencia}\n```"
        )
        raw_cap5, count = re.subn(pattern_sq, replacement_sq, raw_cap5, flags=re.DOTALL)
        assert count == 1, f"No se pudo reemplazar 5.{i}.4 Diagrama de Secuencia"
        
    # 3. Verificación final de que NO queden las letras BCE en raw_cap5
    bce_matches = re.findall(r'\bBCE\b', raw_cap5, re.IGNORECASE)
    if bce_matches:
        print(f"ALERTA: Se encontraron coincidencias de BCE: {bce_matches}")
        for m in re.finditer(r'\bBCE\b', raw_cap5, re.IGNORECASE):
            snippet = raw_cap5[max(0, m.start()-40):min(len(raw_cap5), m.end()+40)]
            print(f" -> ...{snippet}...")
        sys.exit(1)
        
    print("Éxito: Cero ocurrencias de BCE en el Capítulo 5 generado.")
    return raw_cap5

def apply_to_proyecto_grado():
    doc_path = Path("docs/ProyectoGrado.md")
    content = doc_path.read_text(encoding="utf-8")
    
    cap5_text = build_updated_capitulo_5()
    
    # Identificar dónde empieza el Capítulo 5 y dónde termina
    target_start = "# CAPÍTULO V: ANÁLISIS Y DISEÑO ORIENTADO A OBJETOS"
    target_end = "# Referencias Bibliográficas"
    
    assert target_start in content, "No se encontró el inicio de Cap 5 en docs/ProyectoGrado.md"
    assert target_end in content, "No se encontró el inicio de Referencias en docs/ProyectoGrado.md"
    
    part_before = content.split(target_start)[0]
    part_after = content.split(target_end)[1]
    
    new_doc_content = part_before + cap5_text.strip() + "\n\n---\n\n" + target_end + part_after
    
    doc_path.write_text(new_doc_content, encoding="utf-8")
    print(f"docs/ProyectoGrado.md actualizado exitosamente con Capítulo 5.")
    
    # Verificación final sobre el archivo completo
    final_content = doc_path.read_text(encoding="utf-8")
    matches = re.findall(r'\bBCE\b', final_content, re.IGNORECASE)
    print(f"Total de apariciones de 'BCE' en todo el documento: {len(matches)}")
    assert len(matches) == 0, f"Error: Quedaron {len(matches)} apariciones de BCE"
    
    # Verificar existencia de todas las imágenes referenciadas
    img_refs = re.findall(r'!\[.*?\]\((diagramas/cu0\d_.*?\.png)\)', final_content)
    print(f"Total de imágenes referenciadas en Cap 5: {len(img_refs)}")
    assert len(img_refs) == 16, f"Se esperaban 16 imágenes, se encontraron {len(img_refs)}"
    
    for img in img_refs:
        img_path = Path("docs") / img
        assert img_path.exists(), f"Imagen {img_path} no existe en disco"
        assert img_path.stat().st_size > 5000, f"Imagen {img_path} parece dañada o vacía ({img_path.stat().st_size} bytes)"
        
    print("Todas las 16 imágenes existen y tienen tamaño válido (> 5 KB).")

if __name__ == "__main__":
    apply_to_proyecto_grado()

