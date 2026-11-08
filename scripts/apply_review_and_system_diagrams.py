# scripts/apply_review_and_system_diagrams.py
# -*- coding: utf-8 -*-
"""
Aplica las observaciones menores de la revisión y agrega la sección 5.9
con los 3 diagramas del sistema completo al final del Capítulo 5 en docs/ProyectoGrado.md.
"""

import re
from pathlib import Path

DOC_PATH = Path("docs/ProyectoGrado.md")

def get_seccion_5_9():
    import render_sistema_completo
    puml_actividad = render_sistema_completo.DIAGRAMS["sistema_completo_actividad"]
    puml_clases = render_sistema_completo.DIAGRAMS["sistema_completo_clases"]
    puml_casos_uso = render_sistema_completo.DIAGRAMS["sistema_completo_casos_uso"]
    
    return f"""
---

## 5.9. Diagramas de Arquitectura Consolidada del Sistema Completo
Como culminación de la fase de análisis y diseño orientado a objetos, se presentan los tres modelos arquitectónicos globales que consolidan la totalidad de las interacciones, componentes y casos de uso de la plataforma web de la academia "Corpo e Mente". Estos diagramas integran de forma coherente la interacción entre los actores humanos (Alumno, Profesor y Administrador), los motores de inteligencia artificial local (YOLOv26 y Qwen3-VL), la capa de servicios desacoplados en FastAPI y la persistencia híbrida (PostgreSQL y Qdrant).

### 5.9.1. Diagrama de Casos de Uso del Sistema Completo
El diagrama de casos de uso consolidado agrupa los ocho casos de uso funcionales (UC-01 a UC-08) estructurados por subsistemas temáticos (Autenticación, Análisis Biomecánico, Gestión de Técnicas, Conocimiento RAG, Progreso, Pase de Tatami, Sucursales y Soporte Técnico), explicitando sus dependencias `<<include>>` y `<<extend>>`, así como la interacción con los servicios de apoyo externos (Cloudflare Tunnel y OpenStreetMap Nominatim):

![Diagrama de Casos de Uso del Sistema Completo](diagramas/sistema_completo_casos_uso.png)

```plantuml
{puml_casos_uso}
```

---

### 5.9.2. Diagrama de Actividad con Carriles del Sistema Completo (Flujo Principal UC-02)
El diagrama de actividad con carriles (*Swimlanes Activity Diagram*) detalla la dinámica operativa completa del caso de uso central (UC-02: Analizar Técnica y Generar Feedback Biomecánico), cruzando las seis capas de ejecución del sistema: Alumno (Cliente), Frontend (React 19 + Vite Proxy), Backend (FastAPI), IA de Visión (YOLOv26 + ViCoS), IA de Conocimiento (DTW + Qwen3-VL en MLX) y Persistencia (PostgreSQL + Qdrant). Este flujo modela con rigor las bifurcaciones condicionales de validación de membresía, filtrado anti-spam, selección interactiva de silueta, recuperación RAG en dos etapas y la auditoría de fidelidad con degradación elegante (*Graceful Fallback*):

![Diagrama de Actividad con Carriles del Sistema Completo](diagramas/sistema_completo_actividad.png)

```plantuml
{puml_actividad}
```

---

### 5.9.3. Diagrama de Clases del Sistema Completo
El diagrama de clases estructural del sistema completo modela todas las clases participantes organizadas rigurosamente según sus responsabilidades por capas: Frontera de Presentación (*Boundary Frontend*), Frontera de API (*Boundary Backend*), Control de Aplicación (*Control Application*), Servicios de Dominio (*Domain Services*), Biomecánica, Entidades de Dominio (*Domain Entities*) y Adaptadores de Infraestructura (*Infrastructure AI, Persistencia y Video*):

![Diagrama de Clases del Sistema Completo](diagramas/sistema_completo_clases.png)

```plantuml
{puml_clases}
```
"""

def apply():
    content = DOC_PATH.read_text(encoding="utf-8")

    # 1. Corregir los 4 casos de Fuente vs Nota en tablas
    content = content.replace(
        "*Fuente: Elaboración propia a partir de pruebas empíricas del sistema (2026).*",
        "*Nota.* Elaboración propia (2026)."
    )
    content = content.replace(
        "*Fuente: Elaboración propia basada en Qwen AI Blog y pruebas del sistema (2026).*",
        "*Nota.* Elaboración propia (2026)."
    )
    content = content.replace(
        "*Fuente: Elaboración propia basada en documentación oficial y benchmarks de Qdrant (2026).*",
        "*Nota.* Elaboración propia (2026)."
    )
    content = content.replace(
        "*Fuente: Elaboración propia basada en pruebas empíricas del sistema (2026).*",
        "*Nota.* Elaboración propia (2026)."
    )

    # 2. Corregir cita en §3.9.3 (Michael V. Mannino -> (Mannino, 2018))
    content = content.replace(
        "Siguiendo las buenas prácticas de ingeniería de bases de datos (Michael V. Mannino),",
        "Siguiendo las buenas prácticas de ingeniería de bases de datos (Mannino, 2018),"
    )

    # 3. Corregir cita en §3.13.1 (Russell & Norvig, 2021)
    content = content.replace(
        "La **Inteligencia Artificial (IA)** es la rama de la ingeniería que permite a las computadoras realizar tareas que normalmente requieren inteligencia humana, como ver, comprender el lenguaje y analizar movimientos.",
        "La **Inteligencia Artificial (IA)** es la rama de la ingeniería que permite a las computadoras realizar tareas que normalmente requieren cognición e inteligencia humana (Russell & Norvig, 2021), tales como ver, comprender el lenguaje y analizar movimientos."
    )

    # 4. Ajustar §3.12.3 (134+ -> 132 passed de PlanEvaluacionIteraciones.md)
    content = content.replace(
        "1. **Verificación Real de Punta a Punta (134+ Pruebas Internas + Navegador Real):** Pytest comprueba en pocos segundos más de 134 escenarios internos del backend,",
        "1. **Verificación Real de Punta a Punta (132 Pruebas Superadas + Navegador Real):** Pytest comprueba en pocos segundos 132 escenarios unitarios y de integración del backend (`docs/PlanEvaluacionIteraciones.md`),"
    )

    # 5. Insertar Sección 5.9 al final del Capítulo 5 (antes de Capítulo VI)
    marker_cap6 = "# Capítulo VI: Desarrollo"
    assert marker_cap6 in content, f"No se encontró {marker_cap6}"

    parts = content.split(marker_cap6, 1)
    
    # Asegurar que no se inserte dos veces si se reejecuta
    if "## 5.9. Diagramas de Arquitectura Consolidada del Sistema Completo" not in parts[0]:
        seccion_5_9 = get_seccion_5_9()
        parts[0] = parts[0].rstrip() + "\n" + seccion_5_9 + "\n\n---\n\n"
        content = parts[0] + marker_cap6 + parts[1]

    # 6. Actualizar Tabla de Contenido para incluir 5.9
    toc_old_cap5 = r"""  \* 5\.8\. Caso de Uso 8: Entrar como otro Usuario / Impersonificación \(UC-08\)"""
    toc_new_cap5 = """  * 5.8. Caso de Uso 8: Entrar como otro Usuario / Impersonificación (UC-08)
  * 5.9. Diagramas de Arquitectura Consolidada del Sistema Completo
    * 5.9.1. Diagrama de Casos de Uso del Sistema Completo
    * 5.9.2. Diagrama de Actividad con Carriles del Sistema Completo (Flujo Principal UC-02)
    * 5.9.3. Diagrama de Clases del Sistema Completo"""
    
    content = re.sub(toc_old_cap5, toc_new_cap5, content)

    DOC_PATH.write_text(content, encoding="utf-8")
    print(f"Cambios aplicados exitosamente en {DOC_PATH}.")

if __name__ == "__main__":
    apply()

