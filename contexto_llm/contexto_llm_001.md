

--- ARCHIVO: .gitignore ---
# ─────────────────────────────────────────────────────────
# Python
# ─────────────────────────────────────────────────────────
venv/
env/
.venv/
__pycache__/
*.pyc
*.pyo
*.pyd
.pytest_cache/
.coverage
htmlcov/

# ─────────────────────────────────────────────────────────
# Node / Frontend
# ─────────────────────────────────────────────────────────
node_modules/
dist/
dist-ssr/
*.local
npm-debug.log*
yarn-debug.log*
yarn-error.log*
pnpm-debug.log*
lerna-debug.log*

# ─────────────────────────────────────────────────────────
# Secretos y variables de entorno
# ─────────────────────────────────────────────────────────
.env
*.env
!.env.example

# ─────────────────────────────────────────────────────────
# Datos generados (runtime)
# ─────────────────────────────────────────────────────────
qdrant_storage/
postgrest
postgrest.conf
data/embeddings/

# ─────────────────────────────────────────────────────────
# Archivos multimedia de prueba
# ─────────────────────────────────────────────────────────
*.mp4
*.avi
*.mov
*.mkv
*.webm

# ─────────────────────────────────────────────────────────
# Documentos generados
# ─────────────────────────────────────────────────────────
docs/TFGdocsLatex/
*.docx
*.log

# ─────────────────────────────────────────────────────────
# Sistema operativo / Editor
# ─────────────────────────────────────────────────────────
.DS_Store
.idea/
.vscode/*
!.vscode/extensions.json
*.suo
*.ntvs*
*.njsproj
*.sln
*.sw?



--- ARCHIVO: add_capitulo_5_to_docx.py ---
import docx
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

def set_cell_margins(cell, top=120, bottom=120, left=140, right=140):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
    tcPr.append(tcMar)

def set_cell_shading(cell, color_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
    tcPr.append(shd)

def set_table_borders(table, color="B0B0B0", sz="6"):
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'  <w:top w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'  <w:bottom w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'  <w:insideH w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'  <w:insideV w:val="none"/>'
        f'  <w:left w:val="none"/>'
        f'  <w:right w:val="none"/>'
        f'</w:tblBorders>'
    )
    tblPr.append(borders)

def add_p(doc, text="", align=WD_ALIGN_PARAGRAPH.JUSTIFY, font_name="Arial", size_pt=12, bold=False, italic=False, space_before_pt=0, space_after_pt=10, line_spacing=1.5):
    p = doc.add_paragraph()
    p.alignment = align
    p.paragraph_format.space_before = Pt(space_before_pt)
    p.paragraph_format.space_after = Pt(space_after_pt)
    p.paragraph_format.line_spacing = line_spacing
    if text:
        r = p.add_run(text)
        r.font.name = font_name
        r.font.size = Pt(size_pt)
        r.bold = bold
        r.italic = italic
    return p

def add_page_break(doc):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.0
    r = p.add_run()
    r.add_break(docx.enum.text.WD_BREAK.PAGE)
    return p

def add_h1(doc, text):
    return add_p(doc, text, align=WD_ALIGN_PARAGRAPH.LEFT, font_name="Arial", size_pt=14, bold=True, space_before_pt=18, space_after_pt=8, line_spacing=1.15)

def add_h2(doc, text):
    return add_p(doc, text, align=WD_ALIGN_PARAGRAPH.LEFT, font_name="Arial", size_pt=12, bold=True, space_before_pt=14, space_after_pt=6, line_spacing=1.15)

def add_h3(doc, text):
    return add_p(doc, text, align=WD_ALIGN_PARAGRAPH.LEFT, font_name="Arial", size_pt=12, bold=True, italic=True, space_before_pt=10, space_after_pt=4, line_spacing=1.15)

def add_bullet_p(doc, bold_prefix="", text="", font_name="Arial", size_pt=12, space_before_pt=0, space_after_pt=8, line_spacing=1.5):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.space_before = Pt(space_before_pt)
    p.paragraph_format.space_after = Pt(space_after_pt)
    p.paragraph_format.line_spacing = line_spacing
    if bold_prefix:
        r1 = p.add_run(bold_prefix)
        r1.font.name = font_name
        r1.font.size = Pt(size_pt)
        r1.bold = True
    if text:
        r2 = p.add_run(text)
        r2.font.name = font_name
        r2.font.size = Pt(size_pt)
        r2.bold = False
    return p

def add_figure(doc, image_path, width_inches=5.0, caption_title=None, caption_source="Fuente: Elaboración propia (2026)"):
    p_img = doc.add_paragraph()
    p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img.paragraph_format.space_before = Pt(10)
    p_img.paragraph_format.space_after = Pt(4)
    r_img = p_img.add_run()
    r_img.add_picture(image_path, width=Inches(width_inches))

    if caption_title:
        p_cap = doc.add_paragraph()
        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap.paragraph_format.space_before = Pt(6)
        p_cap.paragraph_format.space_after = Pt(3)
        r_cap = p_cap.add_run(caption_title)
        r_cap.font.name = "Arial"
        r_cap.font.size = Pt(11)
        r_cap.bold = True

    if caption_source:
        p_src = doc.add_paragraph()
        p_src.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_src.paragraph_format.space_before = Pt(0)
        p_src.paragraph_format.space_after = Pt(16)
        r_src = p_src.add_run(caption_source)
        r_src.font.name = "Arial"
        r_src.font.size = Pt(10)
        r_src.bold = False

def add_table_custom(doc, headers, data, col_widths, caption_title=None, caption_source="Fuente: Elaboración propia (2026)"):
    if caption_title:
        p_cap = doc.add_paragraph()
        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap.paragraph_format.space_before = Pt(16)
        p_cap.paragraph_format.space_after = Pt(6)
        r_cap = p_cap.add_run(caption_title)
        r_cap.font.name = "Arial"
        r_cap.font.size = Pt(11)
        r_cap.bold = True

    table = doc.add_table(rows=len(data) + 1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(table, color="B0B0B0", sz="6")

    # Header Row
    hdr_cells = table.rows[0].cells
    for i, h in enumerate(headers):
        hdr_cells[i].text = ""
        p = hdr_cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1.0
        r = p.add_run(h)
        r.font.name = "Arial"
        r.font.size = Pt(10)
        r.bold = True
        set_cell_shading(hdr_cells[i], "EAEFF5")
        set_cell_margins(hdr_cells[i], top=140, bottom=140, left=140, right=140)
        hdr_cells[i].vertical_alignment = WD_ALIGN_VERTICAL.CENTER

    # Data Rows
    for r_idx, row_data in enumerate(data):
        row_cells = table.rows[r_idx + 1].cells
        for c_idx, val in enumerate(row_data):
            row_cells[c_idx].text = ""
            p = row_cells[c_idx].paragraphs[0]
            if c_idx == 0 and len(val) <= 12 and ("-" in val or val.isdigit() or val.startswith("UC") or val.startswith("IE") or val.startswith("RD") or val.startswith("RF") or val.startswith("Principio") or val == "Caso de Uso" or val == "Actores Principales" or val == "Precondición" or val == "Garantía de Éxito (Postcondiciones)" or val == "Partes Interesadas e Intereses"):
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.15
            r = p.add_run(val)
            r.font.name = "Arial"
            r.font.size = Pt(9.5)
            if c_idx == 0:
                r.bold = True
            set_cell_shading(row_cells[c_idx], "FFFFFF")
            set_cell_margins(row_cells[c_idx], top=120, bottom=120, left=140, right=140)
            row_cells[c_idx].vertical_alignment = WD_ALIGN_VERTICAL.CENTER

    # Set column widths
    for row in table.rows:
        for idx, width in enumerate(col_widths):
            row.cells[idx].width = Inches(width)

    if caption_source:
        p_src = doc.add_paragraph()
        p_src.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_src.paragraph_format.space_before = Pt(4)
        p_src.paragraph_format.space_after = Pt(16)
        r_src = p_src.add_run(caption_source)
        r_src.font.name = "Arial"
        r_src.font.size = Pt(10)
        r_src.bold = False

    return table

def main():
    doc_path = 'Libros/Capitulo_1_2_3_y_4_Tesis_Santiago_Borda.docx'
    doc = docx.Document(doc_path)

    # 1. Extract bibliography paragraphs from end
    bib_paragraphs = []
    found_bib = False
    bib_start_idx = None
    for i, p in enumerate(doc.paragraphs):
        if 'FUENTES DOCUMENTALES Y BIBLIOGRÁFICAS' in p.text.upper():
            found_bib = True
            bib_start_idx = i
        if found_bib:
            bib_paragraphs.append((p.text, p.alignment, p.paragraph_format.space_before, p.paragraph_format.space_after, p.paragraph_format.line_spacing))

    # Remove existing Chapter 5 if already added
    c5_start_idx = None
    for i, p in enumerate(doc.paragraphs):
        if p.text.strip().upper() == 'CAPÍTULO V' or p.text.strip().upper().startswith('CAPÍTULO V:'):
            c5_start_idx = i - 1 if (i > 0 and not doc.paragraphs[i-1].text.strip()) else i
            break

    if c5_start_idx is not None:
        for idx in reversed(range(c5_start_idx, len(doc.paragraphs))):
            p_elem = doc.paragraphs[idx]._p
            p_elem.getparent().remove(p_elem)
        while len(doc.tables) > 16:
            tbl_elem = doc.tables[-1]._tbl
            tbl_elem.getparent().remove(tbl_elem)
    elif bib_start_idx is not None:
        # Remove bib paragraphs from end
        for idx in reversed(range(bib_start_idx - 1 if (bib_start_idx > 0 and not doc.paragraphs[bib_start_idx-1].text.strip()) else bib_start_idx, len(doc.paragraphs))):
            p_elem = doc.paragraphs[idx]._p
            p_elem.getparent().remove(p_elem)

    while doc.paragraphs and not doc.paragraphs[-1].text.strip():
        p_last = doc.paragraphs[-1]._p
        p_last.getparent().remove(p_last)

    # 2. Add Chapter 5
    add_page_break(doc)
    add_p(doc, "CAPÍTULO V", align=WD_ALIGN_PARAGRAPH.CENTER, font_name="Arial", size_pt=16, bold=True, space_before_pt=24, space_after_pt=6, line_spacing=1.15)
    add_p(doc, "ANÁLISIS Y DISEÑO ORIENTADO A OBJETOS", align=WD_ALIGN_PARAGRAPH.CENTER, font_name="Arial", size_pt=16, bold=True, space_before_pt=0, space_after_pt=14, line_spacing=1.15)

    # 5.1 Introducción
    add_h1(doc, "5.1. Introducción")

    # 5.1.1 Propósito
    add_h2(doc, "5.1.1. Propósito")
    add_p(doc, "El presente capítulo establece el análisis y diseño orientado a objetos del Sistema de Análisis Biomecánico de Técnicas de Jiu-Jitsu Brasileño mediante Inteligencia Artificial para la academia Corpo e Mente. Se aplican rigurosamente los principios del Proceso Unificado Ágil (Agile UP) descrito por Craig Larman en 'Applying UML and Patterns', complementados por el diseño de bases de datos normalizado de Michael V. Mannino.")
    add_p(doc, "La metodología adoptada es iterativa e incremental, con ciclos acotados en tiempo (timeboxed) que entregan incrementos probados de software. Cada caso de uso se aborda como una iteración de la fase de Elaboración, produciendo los siguientes artefactos de análisis y diseño:")
    add_bullet_p(doc, "1. Caso de Uso Detallado (fully dressed): ", "Especificación completa con actores, intereses, precondiciones, flujo principal, flujos alternativos y postcondiciones.")
    add_bullet_p(doc, "2. Diagrama de Caso de Uso (PlantUML): ", "Representación UML del actor, el caso de uso y sus relaciones <<include>> / <<extend>>.")
    add_bullet_p(doc, "3. Diagrama de Clases de Interfaz (Mermaid): ", "Clases de frontera (boundary) que el actor manipula directamente, junto con los DTOs de entrada/salida.")
    add_bullet_p(doc, "4. Diagrama de Secuencia (Mermaid): ", "Interacción detallada entre actor, capa de presentación, aplicación, dominio e infraestructura, incluyendo flujos alternativos.")
    add_bullet_p(doc, "5. Diagrama de Paquetes (PlantUML): ", "Organización de los paquetes de la arquitectura en capas que participan en el caso de uso.")

    # 5.1.2 Principios Rectores del Proceso Unificado Ágil
    add_h2(doc, "5.1.2. Principios Rectores del Proceso Unificado Ágil")
    t51_data = [
        ["Iteraciones acotadas en tiempo", "Cada caso de uso se diseña en una sesión, entregando valor tangible."],
        ["Desarrollo dirigido por riesgos", "Los casos de uso con mayor incertidumbre técnica (UC2: Análisis Biomecánico) se abordan con mayor profundidad."],
        ["Desarrollo centrado en la arquitectura", "Se materializa la arquitectura en capas (Presentación, Aplicación, Dominio, Infraestructura) en cada iteración."],
        ["Feedback continuo", "Cada caso de uso se verifica contra servicios reales (PostgreSQL, Qdrant, Colab Worker, Gemini API)."],
        ["Adaptación continua", "Los artefactos de una iteración informan el diseño de la siguiente."]
    ]
    add_table_custom(doc, ["Principio", "Aplicación en el Proyecto"], t51_data, [2.2, 3.7], caption_title="Tabla 5.1: Principios Rectores del Proceso Unificado Ágil")

    # 5.1.3 Visión General del Capítulo
    add_h2(doc, "5.1.3. Visión General del Capítulo")
    add_p(doc, "El capítulo se estructura en una sección por cada caso de uso identificado en el Capítulo IV:")
    add_bullet_p(doc, "• Sección 5.2 — ", "UC1: Autenticarse en la Plataforma")
    add_bullet_p(doc, "• Sección 5.3 — ", "UC2: Analizar Técnica y Generar Feedback Biomecánico")
    add_bullet_p(doc, "• Sección 5.4 — ", "UC3: Gestionar Técnicas y Videos de Referencia")
    add_bullet_p(doc, "• Sección 5.5 — ", "UC4: Gestionar Teoría RAG")
    add_bullet_p(doc, "• Sección 5.6 — ", "UC5: Visualizar Progreso de Alumnos")
    add_bullet_p(doc, "• Sección 5.7 — ", "UC6: Gestionar Sucursales y Coordenadas Geográficas")
    add_bullet_p(doc, "• Sección 5.8 — ", "UC7: Administrar Usuarios e Impersonificación")
    add_p(doc, "Cada caso de uso presenta los cinco artefactos definidos en 5.1.1, seguidos de una breve conclusión de la iteración.")

    # 5.2 Caso de Uso 1: Autenticarse en la Plataforma
    add_h1(doc, "5.2. Caso de Uso 1: Autenticarse en la Plataforma")

    # 5.2.1 Caso de Uso Detallado
    add_h2(doc, "5.2.1. Caso de Uso Detallado")
    t52_data = [
        ["Caso de Uso", "UC1: Autenticarse en la Plataforma"],
        ["Actores Principales", "Alumno, Profesor, Administrador"],
        ["Partes Interesadas e Intereses", "Usuario: Desea acceder de forma segura a su panel personalizado (alumno, profesor o administrador) sin demoras excesivas.\nAcademia: Requiere garantizar que solo personal autorizado acceda a información sensible de alumnos y evaluaciones.\nAdministrador del Sistema: Requiere trazabilidad de accesos, prevención de ataques de fuerza bruta y control de sesiones."],
        ["Precondición", "El usuario no está autenticado en el sistema. La base de datos PostgreSQL está operativa y los RPCs authenticate y get_user_profile están creados (02_auth_jwt.sql)."],
        ["Garantía de Éxito (Postcondiciones)", "El usuario obtiene un JWT firmado con HS256, válido por 24 horas, con los claims uid, role, email y sucursal_id. El frontend almacena la sesión y redirige al panel correspondiente según el rol."]
    ]
    add_table_custom(doc, ["Campo", "Descripción"], t52_data, [1.8, 4.1], caption_title="Tabla 5.2: Especificación Detallada del Caso de Uso UC1")

    add_p(doc, "Flujo Principal (Escenario Principal de Éxito):", bold=True)
    add_bullet_p(doc, "1. ", "El usuario presiona el avatar en el header de la aplicación, abriendo LoginModal.jsx.")
    add_bullet_p(doc, "2. ", "El usuario ingresa su username o email y su contraseña en el formulario.")
    add_bullet_p(doc, "3. ", "El usuario presiona 'Ingresar'. El frontend ejecuta handleLoginSubmit().")
    add_bullet_p(doc, "4. ", "El frontend envía POST /api/v1/auth/login con {username_or_email, password}.")
    add_bullet_p(doc, "5. ", "El AuthController (FastAPI) recibe la petición y valida el esquema con Pydantic (LoginRequest).")
    add_bullet_p(doc, "6. ", "El controlador invoca PostgrestClient.rpc('authenticate', {email, password}).")
    add_bullet_p(doc, "7. ", "PostgreSQL ejecuta la función authenticate (SECURITY DEFINER) que busca al usuario por email o username.")
    add_bullet_p(doc, "8. ", "PostgreSQL verifica la contraseña con crypt(password, password_hash) (bcrypt/pgcrypto).")
    add_bullet_p(doc, "9. ", "Si el hash coincide, PostgreSQL retorna un token legado JSON con {role, email, uid, sucursal_id}.")
    add_bullet_p(doc, "10. ", "El AuthController parsea el token legado y firma un JWT real con _sign_token() usando JWT_SECRET_KEY (HS256, expiración 24h).")
    add_bullet_p(doc, "11. ", "El controlador invoca PostgrestClient.rpc('get_user_profile', {user_id: uid}) para obtener el perfil completo.")
    add_bullet_p(doc, "12. ", "El controlador consulta la tabla sucursales para obtener el sucursal_nombre.")
    add_bullet_p(doc, "13. ", "El controlador retorna LoginResponse con token, user_id, nombre_completo, username, email, rol, avatar_url, sucursal_id, sucursal_nombre.")
    add_bullet_p(doc, "14. ", "El frontend ejecuta onLoginSuccess(userData) y onClose().")
    add_bullet_p(doc, "15. ", "El App.jsx redirige según el rol: alumno → VideoUpload, profesor → ProfesorTecnicas, admin → AdminSucursales.")

    add_p(doc, "Extensiones (Flujos Alternativos y de Excepción):", bold=True)
    add_bullet_p(doc, "• 8a. Contraseña incorrecta: ", "crypt(password, password_hash) retorna un hash diferente. El RPC authenticate retorna NULL. El AuthController retorna HTTP 401 con mensaje genérico 'Nombre de usuario o contraseña incorrectos'.")
    add_bullet_p(doc, "• 7a. Usuario no existe: ", "El RPC authenticate retorna NULL tras no encontrar el email o username. El AuthController retorna HTTP 401 con el mismo mensaje genérico.")
    add_bullet_p(doc, "• 10a. Error de firma JWT: ", "Si JWT_SECRET_KEY no está configurado o es inválido, se lanza excepción y se retorna HTTP 500 con logging del error.")
    add_bullet_p(doc, "• 11a. Perfil no encontrado tras autenticación exitosa: ", "El AuthController retorna un LoginResponse con datos mínimos derivados del token legado (fallback defensivo).")
    add_bullet_p(doc, "• 12a. Sucursal eliminada: ", "El sistema asigna sucursal_nombre = 'Sucursal Eliminada' y permite el acceso con advertencia.")

    add_p(doc, "Requisitos Especiales:", bold=True)
    add_bullet_p(doc, "• IE-SW-10: ", "El sistema debe autenticar todas las peticiones al backend mediante JWT firmado con HS256.")
    add_bullet_p(doc, "• IE-SW-11: ", "El sistema debe validar el token JWT en cada endpoint protegido, verificando uid, role y sucursal_id.")
    add_bullet_p(doc, "• RF-03: ", "El sistema debe autenticar usuarios mediante username o email y contraseña, retornando un JWT firmado con expiración de 24 horas.")
    add_bullet_p(doc, "• RF-04: ", "El sistema debe hashear las contraseñas con bcrypt (pgcrypto) antes de almacenarlas.")
    add_bullet_p(doc, "• ", "El sistema debe usar RPCs SECURITY DEFINER para no exponer la tabla usuarios al rol anon.")
    add_bullet_p(doc, "• ", "El sistema debe retornar mensajes genéricos en caso de error de credenciales (prevención de enumeración de usuarios).")

    add_p(doc, "Lista de Variaciones Tecnológicas y de Datos:", bold=True)
    add_bullet_p(doc, "• ", "El username_or_email puede ser un username (ej. admin, mike, santi) o un email (ej. admin@corpocmente.com).")
    add_bullet_p(doc, "• ", "El rol puede ser alumno, profesor o admin.")
    add_bullet_p(doc, "• ", "El idioma preferido se recupera del estado del frontend (por defecto es).")

    add_p(doc, "Frecuencia de Ocurrencia: Muy alta (múltiples veces al día por usuario).", italic=True)

    # 5.2.2 Diagrama de Caso de Uso
    add_h2(doc, "5.2.2. Diagrama de Caso de Uso (PlantUML)")
    add_p(doc, "En la Figura 5.1 se presenta el modelo UML del caso de uso UC1, detallando las relaciones de inclusión con las operaciones de validación en PostgreSQL, generación criptográfica de JWT, recuperación de perfil y redirección dinámica por roles:")
    
    add_figure(doc, "Libros/figuras/capitulo_5/figura_5_1_caso_de_uso_uc1.png", width_inches=4.8,
               caption_title="Figura 5.1: Diagrama de Caso de Uso UC1 — Autenticarse en la Plataforma",
               caption_source="Fuente: Elaboración propia (2026)")

    # 5.2.3 Diagrama de Clases de Interfaz
    add_h2(doc, "5.2.3. Diagrama de Clases de Interfaz (Mermaid)")
    add_p(doc, "El diagrama de clases de interfaz muestra las clases de frontera (boundary) que el actor manipula directamente, junto con los DTOs (Data Transfer Objects) que cruzan la frontera entre la capa de Presentación y la capa de Aplicación:")

    add_figure(doc, "Libros/figuras/capitulo_5/figura_5_2_clases_interfaz_uc1.png", width_inches=5.2,
               caption_title="Figura 5.2: Diagrama de Clases de Interfaz del UC1",
               caption_source="Fuente: Elaboración propia (2026)")

    t53_data = [
        ["Usuario", "Actor", "Persona que interactúa con la UI para autenticarse."],
        ["LoginModal", "Boundary (React)", "Modal de la UI que captura credenciales y gestiona el estado del formulario."],
        ["LoginRequest", "DTO (Pydantic)", "Objeto de transferencia con username_or_email y password."],
        ["LoginResponse", "DTO (Pydantic)", "Objeto de transferencia con los datos de sesión completos."],
        ["AuthController", "Boundary (FastAPI)", "Controlador que expone el endpoint POST /auth/login y firma el JWT."],
        ["PostgrestClient", "Adapter", "Cliente HTTP que consume los RPCs de PostgreSQL vía PostgREST."],
        ["JWTSecret", "Configuration", "Configuración externa (variables de entorno) con las claves de firma."]
    ]
    add_table_custom(doc, ["Clase", "Estereotipo", "Responsabilidad"], t53_data, [1.5, 1.5, 2.9], caption_title="Tabla 5.3: Descripción de las Clases de Frontera del UC1")

    # 5.2.4 Diagrama de Secuencia
    add_h2(doc, "5.2.4. Diagrama de Secuencia (Mermaid)")
    add_p(doc, "El diagrama de secuencia muestra la interacción detallada entre el actor, la capa de Presentación (React), la capa de Aplicación (FastAPI), la capa de Infraestructura (PostgrestClient) y el motor PostgreSQL, incluyendo los flujos alternativos:")

    add_figure(doc, "Libros/figuras/capitulo_5/figura_5_3_secuencia_uc1.png", width_inches=4.8,
               caption_title="Figura 5.3: Diagrama de Secuencia del UC1 — Autenticarse en la Plataforma",
               caption_source="Fuente: Elaboración propia (2026)")

    add_p(doc, "Notas del Diagrama de Secuencia:", bold=True)
    add_bullet_p(doc, "• ", "Los pasos 1–6 modelan la interacción del usuario con la UI.")
    add_bullet_p(doc, "• ", "Los pasos 7–13 modelan la orquestación en el backend.")
    add_bullet_p(doc, "• ", "Los pasos 14–18 modelan la firma del JWT.")
    add_bullet_p(doc, "• ", "Los pasos 19–22 modelan la recuperación del perfil completo.")
    add_bullet_p(doc, "• ", "Los pasos 23–26 modelan la respuesta exitosa al frontend.")
    add_bullet_p(doc, "• ", "El bloque alt modela el flujo alternativo de credenciales inválidas (pasos 28–31).")

    # 5.2.5 Diagrama de Paquetes
    add_h2(doc, "5.2.5. Diagrama de Paquetes (PlantUML)")
    add_p(doc, "El diagrama de paquetes muestra la organización de la arquitectura en capas y las dependencias entre paquetes que participan en el caso de uso UC1:")

    add_figure(doc, "Libros/figuras/capitulo_5/figura_5_4_paquetes_uc1.png", width_inches=5.2,
               caption_title="Figura 5.4: Diagrama de Paquetes del UC1",
               caption_source="Fuente: Elaboración propia (2026)")

    t54_data = [
        ["Capa de Presentación (UI)", "Presentación", "Renderizar el modal de login, capturar credenciales, gestionar el estado del formulario y las traducciones ES/PT."],
        ["Capa de Aplicación", "Aplicación", "Exponer el endpoint REST, validar DTOs, orquestar la autenticación, firmar el JWT y aplicar guards de autorización."],
        ["Capa de Dominio", "Dominio", "Representar conceptualmente al Usuario, la Sesion y el Rol."],
        ["Capa de Infraestructura", "Infraestructura", "Proveer el cliente PostgREST, ejecutar los RPCs, aplicar bcrypt en PostgreSQL y leer la clave JWT desde variables de entorno."]
    ]
    add_table_custom(doc, ["Paquete", "Capa", "Responsabilidad en UC1"], t54_data, [1.8, 1.3, 2.8], caption_title="Tabla 5.4: Descripción de los Paquetes del UC1")

    # 5.2.6 Conclusión de la Iteración UC1
    add_h2(doc, "5.2.6. Conclusión de la Iteración UC1")
    add_p(doc, "La iteración correspondiente al caso de uso UC1: Autenticarse en la Plataforma ha producido los siguientes artefactos de análisis y diseño:")
    t55_data = [
        ["1", "Caso de Uso Detallado (fully dressed)", "Completado"],
        ["2", "Diagrama de Caso de Uso (PlantUML)", "Completado"],
        ["3", "Diagrama de Clases de Interfaz (Mermaid)", "Completado"],
        ["4", "Diagrama de Secuencia (Mermaid)", "Completado"],
        ["5", "Diagrama de Paquetes (PlantUML)", "Completado"]
    ]
    add_table_custom(doc, ["#", "Artefacto", "Estado"], t55_data, [0.6, 3.8, 1.5], caption_title="Tabla 5.5: Artefactos Entregados en la Iteración UC1")

    add_p(doc, "Decisiones Arquitectónicas Clave:", bold=True)
    add_bullet_p(doc, "• Seguridad por RPCs SECURITY DEFINER: ", "La tabla usuarios no se expone al rol anon; todo acceso se realiza mediante funciones RPC (authenticate, get_user_profile). Esto mitiga el riesgo de enumeración de usuarios y filtración de password_hash.")
    add_bullet_p(doc, "• Doble token: ", "PostgreSQL retorna un token legado (JSON string), que el AuthController re-firma como JWT real con expiración y claims estándar. Esto desacopla la lógica de autenticación de la lógica de sesión.")
    add_bullet_p(doc, "• Fallback defensivo: ", "Si el perfil no se encuentra tras autenticación exitosa (caso anómalo), el sistema retorna datos mínimos derivados del token legado en lugar de fallar.")
    add_bullet_p(doc, "• Mensajes genéricos: ", "Los errores de credenciales retornan HTTP 401 con el mismo mensaje sin distinguir si el fallo fue por usuario inexistente o contraseña incorrecta.")

    add_p(doc, "Riesgos Mitigados:", bold=True)
    add_bullet_p(doc, "• ", "Exposición de la tabla usuarios a anon → Mitigado con RPCs SECURITY DEFINER.")
    add_bullet_p(doc, "• ", "Enumeración de usuarios → Mitigado con mensajes genéricos.")
    add_bullet_p(doc, "• ", "Fuerza bruta → Mitigado parcialmente; pendiente rate limiting explícito en iteración futura.")
    add_bullet_p(doc, "• ", "JWT sin expiración → Mitigado con JWT_EXPIRATION_HOURS=24.")

    add_p(doc, "Deuda Técnica Registrada:", bold=True)
    add_bullet_p(doc, "• ", "Implementar rate limiting explícito en el endpoint /auth/login (ej. 5 intentos por minuto por IP).")
    add_bullet_p(doc, "• ", "Implementar 2FA para administradores (registrado en Requisitos Futuros).")
    add_bullet_p(doc, "• ", "Implementar refresh tokens para sesiones de larga duración.")

    # 3. Add Bibliography back at the end
    add_page_break(doc)
    add_p(doc, "FUENTES DOCUMENTALES Y BIBLIOGRÁFICAS", align=WD_ALIGN_PARAGRAPH.CENTER, font_name="Arial", size_pt=14, bold=True, space_before_pt=18, space_after_pt=14, line_spacing=1.15)
    for text, align, s_before, s_after, l_spacing in bib_paragraphs[1:]:
        if text.strip():
            add_p(doc, text, align=WD_ALIGN_PARAGRAPH.JUSTIFY, font_name="Arial", size_pt=11, bold=False, space_before_pt=0, space_after_pt=10, line_spacing=1.5)

    # 4. Update Indices
    t_contents = doc.tables[1]
    # Keep up to Chapter 4 (51 rows, removing old bibliography)
    while len(t_contents.rows) > 51:
        row_elem = t_contents.rows[-1]._tr
        row_elem.getparent().remove(row_elem)

    c5_toc = [
        ("CAPÍTULO V: ANÁLISIS Y DISEÑO ORIENTADO A OBJETOS", "30"),
        ("5.1. Introducción", "30"),
        ("   5.1.1. Propósito", "30"),
        ("   5.1.2. Principios Rectores del Proceso Unificado Ágil", "30"),
        ("   5.1.3. Visión General del Capítulo", "31"),
        ("5.2. Caso de Uso 1: Autenticarse en la Plataforma", "31"),
        ("   5.2.1. Caso de Uso Detallado", "31"),
        ("   5.2.2. Diagrama de Caso de Uso (PlantUML)", "33"),
        ("   5.2.3. Diagrama de Clases de Interfaz (Mermaid)", "34"),
        ("   5.2.4. Diagrama de Secuencia (Mermaid)", "35"),
        ("   5.2.5. Diagrama de Paquetes (PlantUML)", "36"),
        ("   5.2.6. Conclusión de la Iteración UC1", "37"),
        ("FUENTES DOCUMENTALES Y BIBLIOGRÁFICAS", "39")
    ]

    for title, page in c5_toc:
        row = t_contents.add_row()
        row.cells[0].text = title
        row.cells[1].text = page
        row.cells[0].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.LEFT
        row.cells[1].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
        row.cells[0].width = Inches(5.2)
        row.cells[1].width = Inches(0.7)

    # Update Table 2 (Índice de Figuras)
    t_figures = doc.tables[2]
    while len(t_figures.rows) > 5:
        row_elem = t_figures.rows[-1]._tr
        row_elem.getparent().remove(row_elem)

    c5_figures = [
        ("Figura 5.1: Diagrama de Caso de Uso UC1 — Autenticarse en la Plataforma", "33"),
        ("Figura 5.2: Diagrama de Clases de Interfaz del UC1", "34"),
        ("Figura 5.3: Diagrama de Secuencia del UC1 — Autenticarse en la Plataforma", "35"),
        ("Figura 5.4: Diagrama de Paquetes del UC1", "36")
    ]
    for title, page in c5_figures:
        row = t_figures.add_row()
        row.cells[0].text = title
        row.cells[1].text = page
        row.cells[0].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.LEFT
        row.cells[1].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
        row.cells[0].width = Inches(5.2)
        row.cells[1].width = Inches(0.7)

    # Update Table 3 (Índice de Tablas)
    t_tables = doc.tables[3]
    while len(t_tables.rows) > 11:
        row_elem = t_tables.rows[-1]._tr
        row_elem.getparent().remove(row_elem)

    c5_tables = [
        ("Tabla 5.1: Principios Rectores del Proceso Unificado Ágil", "30"),
        ("Tabla 5.2: Especificación Detallada del Caso de Uso UC1", "31"),
        ("Tabla 5.3: Descripción de las Clases de Frontera del UC1", "34"),
        ("Tabla 5.4: Descripción de los Paquetes del UC1", "36"),
        ("Tabla 5.5: Artefactos Entregados en la Iteración UC1", "37")
    ]
    for title, page in c5_tables:
        row = t_tables.add_row()
        row.cells[0].text = title
        row.cells[1].text = page
        row.cells[0].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.LEFT
        row.cells[1].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
        row.cells[0].width = Inches(5.2)
        row.cells[1].width = Inches(0.7)

    # Save both files
    out_path_orig = 'Libros/Capitulo_1_2_y_3_Tesis_Santiago_Borda.docx'
    out_path_new = 'Libros/Capitulo_1_2_3_4_y_5_Tesis_Santiago_Borda.docx'
    
    doc.save(out_path_orig)
    doc.save(out_path_new)
    print("Capitulo 5 (5.1 y 5.2) added to docx successfully.")

if __name__ == '__main__':
    main()



--- ARCHIVO: build_upsa_tesis.py ---
import os
import docx
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    """Set cell padding in twips."""
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def set_table_borders(table, color="CCCCCC", sz="4", val="single"):
    """Set subtle, professional borders for tables."""
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>\n'
        f'  <w:top w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>\n'
        f'  <w:bottom w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>\n'
        f'  <w:insideH w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>\n'
        f'  <w:insideV w:val="none"/>\n'
        f'  <w:left w:val="none"/>\n'
        f'  <w:right w:val="none"/>\n'
        f'</w:tblBorders>'
    )
    tblPr.append(borders)

def set_cell_shading(cell, color_hex="F2F4F7"):
    """Set background color of a cell."""
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
    tcPr.append(shd)

def add_page_number_to_section(section, fmt='decimal', start=1):
    """Configure footer page numbering according to UPSA Art. 138."""
    footer = section.footer
    footer.is_linked_to_previous = False
    p = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p.text = ""
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.space_before = Pt(0)
    run = p.add_run()
    run.font.name = 'Arial'
    run.font.size = Pt(10)
    run.font.color.rgb = RGBColor(0, 0, 0)
    
    fld = parse_xml(r'<w:fldSimple %s w:instr="PAGE"/>' % nsdecls('w'))
    p._p.append(fld)
    
    sectPr = section._sectPr
    pgNumType = sectPr.find(qn('w:pgNumType'))
    if pgNumType is None:
        pgNumType = OxmlElement('w:pgNumType')
        sectPr.append(pgNumType)
    pgNumType.set(qn('w:fmt'), fmt)
    if start is not None:
        pgNumType.set(qn('w:start'), str(start))

def set_section_margins(section):
    """Configure page size Letter and exact margins (Art. 137, 142)."""
    section.page_width = Inches(8.5)   # 21.59 cm
    section.page_height = Inches(11.0) # 27.94 cm
    section.top_margin = Cm(2.5)
    section.bottom_margin = Cm(2.5)
    section.left_margin = Cm(4.0)
    section.right_margin = Cm(2.5)

def format_run(run, font_name='Arial', size_pt=12, bold=False, italic=False, color_rgb=(0,0,0)):
    run.font.name = font_name
    run.font.size = Pt(size_pt)
    run.bold = bold
    run.italic = italic
    run.font.color.rgb = RGBColor(*color_rgb)

def add_p(doc, text="", style='Normal', align=WD_ALIGN_PARAGRAPH.JUSTIFY, 
          space_before=0, space_after=14, line_spacing=1.5, bold=False, italic=False, size_pt=12):
    p = doc.add_paragraph()
    p.alignment = align
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = line_spacing
    p.paragraph_format.first_line_indent = Pt(0)
    p.paragraph_format.left_indent = Pt(0)
    p.paragraph_format.right_indent = Pt(0)
    if text:
        run = p.add_run(text)
        format_run(run, font_name='Arial', size_pt=size_pt, bold=bold, italic=italic)
    return p

def add_bullet_p(doc, title="", desc=""):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(10)
    p.paragraph_format.line_spacing = 1.5
    p.paragraph_format.left_indent = Cm(0.8)
    p.paragraph_format.first_line_indent = Cm(-0.5)
    
    r_bullet = p.add_run("• ")
    format_run(r_bullet, font_name='Arial', size_pt=12, bold=True)
    
    if title:
        r_title = p.add_run(f"{title}: ")
        format_run(r_title, font_name='Arial', size_pt=12, bold=True)
    
    if desc:
        r_desc = p.add_run(desc)
        format_run(r_desc, font_name='Arial', size_pt=12, bold=False)
    return p

def add_chapter_title(doc, chapter_num_str, chapter_title_str):
    """Art. 139, 143: Mayúsculas, negrita, centrados, tamaño 16."""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(24)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.line_spacing = 1.15
    r1 = p.add_run(chapter_num_str.upper())
    format_run(r1, font_name='Arial', size_pt=16, bold=True)
    
    p2 = doc.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p2.paragraph_format.space_before = Pt(0)
    p2.paragraph_format.space_after = Pt(24)
    p2.paragraph_format.line_spacing = 1.15
    r2 = p2.add_run(chapter_title_str.upper())
    format_run(r2, font_name='Arial', size_pt=16, bold=True)

def add_heading_2(doc, text):
    """Art. 139, 144: Negrita, tamaño 14, alineados a la izquierda con espacio antes y después."""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_before = Pt(18)
    p.paragraph_format.space_after = Pt(8)
    p.paragraph_format.line_spacing = 1.15
    run = p.add_run(text)
    format_run(run, font_name='Arial', size_pt=14, bold=True)
    return p

def add_heading_3(doc, text):
    """Art. 139, 144: Negrita, tamaño 12, alineados a la izquierda."""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.line_spacing = 1.15
    run = p.add_run(text)
    format_run(run, font_name='Arial', size_pt=12, bold=True)
    return p

print("Builder helper functions initialized.")



--- ARCHIVO: create_and_render_all_diagrams.py ---
import os
import subprocess

BASE_DIR = "/home/santiago/Desktop/Documentar Proyecto"
DIAGRAMS_DIR = os.path.join(BASE_DIR, "Libros", "Diagramas")
FIGURAS_C5_DIR = os.path.join(BASE_DIR, "Libros", "figuras", "capitulo_5")
PLANTUML_JAR = "/home/santiago/.vscode/extensions/jebbs.plantuml-2.18.1/plantuml.jar"
MMDC_BIN = "/home/santiago/.nvm/versions/node/v24.18.0/bin/mmdc"

os.makedirs(DIAGRAMS_DIR, exist_ok=True)
os.makedirs(FIGURAS_C5_DIR, exist_ok=True)

DIAGRAMS = {}

# ==========================================
# GENERAL: DIAGRAMA DE CASOS DE USO GLOBAL
# ==========================================
os.makedirs(os.path.join(DIAGRAMS_DIR, "CU-General"), exist_ok=True)
DIAGRAMS["CU-General/01_casos_de_uso_general.puml"] = """@startuml
skinparam dpi 300
skinparam defaultFontName "Arial"
skinparam defaultFontSize 11
skinparam packageStyle rectangle
skinparam shadowing true
skinparam roundCorner 10

skinparam actor {
    BackgroundColor #EAEFF5
    BorderColor #1A365D
}
skinparam usecase {
    BackgroundColor #FFFFFF
    BorderColor #2B6CB0
    ArrowColor #2B6CB0
}

left to right direction

actor "Alumno" as act_alumno
actor "Profesor" as act_profesor
actor "Administrador" as act_admin
actor "Google Colab GPU / Gemini" as act_ai <<System>>

rectangle "Corpo e Mente Biomechanics AI" {
    usecase "UC1: Autenticarse en la Plataforma" as UC1
    usecase "UC2: Analizar Técnica y Feedback" as UC2
    usecase "UC3: Gestionar Técnicas y Videos" as UC3
    usecase "UC4: Gestionar Teoría RAG" as UC4
    usecase "UC5: Visualizar Progreso Alumnos" as UC5
    usecase "UC6: Gestionar Sucursales y Geoposición" as UC6
    usecase "UC7: Administrar Usuarios e Impersonificación" as UC7

    usecase "Validar Anti-Spam (Gemini)" as UC_Spam
    usecase "Extraer Keypoints (YOLO26)" as UC_YOLO
    usecase "Generar Feedback Pedagógico (Gemini)" as UC_Feed
}

act_alumno --> UC1
act_alumno --> UC2

act_profesor --> UC1
act_profesor --> UC3
act_profesor --> UC4
act_profesor --> UC5

act_admin --> UC1
act_admin --> UC6
act_admin --> UC7

UC2 ..> UC_Spam : <<include>>
UC2 ..> UC_YOLO : <<include>>
UC2 ..> UC_Feed : <<extend>> (si similitud < 85%)

UC_Spam ..> act_ai : <<invoca>>
UC_YOLO ..> act_ai : <<invoca>>
UC_Feed ..> act_ai : <<invoca>>

@enduml
"""

# ==========================================
# CU-1: AUTENTICARSE EN LA PLATAFORMA
# ==========================================
os.makedirs(os.path.join(DIAGRAMS_DIR, "CU-1"), exist_ok=True)
DIAGRAMS["CU-1/01_caso_de_uso_uc1.puml"] = """@startuml
skinparam dpi 300
skinparam defaultFontName "Arial"
skinparam defaultFontSize 12
skinparam packageStyle rectangle
skinparam shadowing true

actor "Usuario\\n(Alumno / Profesor / Admin)" as user
actor "Sistema de Autenticación" as auth_sys <<Sistema>>

rectangle "Caso de Uso 1: Autenticación" {
    usecase "UC1: Autenticarse en la Plataforma" as UC1
    usecase "Validar Credenciales\\n(bcrypt)" as UC_Val
    usecase "Generar Token JWT\\n(HS256 - 24h)" as UC_JWT
    usecase "Cambiar Idioma de Interfaz\\n(ES / PT)" as UC_Lang
}

user --> UC1
user --> UC_Lang
UC1 ..> UC_Val : <<include>>
UC1 ..> UC_JWT : <<include>>
UC_Val ..> auth_sys : <<ejecuta>>
@enduml
"""

DIAGRAMS["CU-1/02_clases_interfaz_uc1.mmd"] = """classDiagram
    direction TB
    class LoginView {
        +username_or_email: string
        +password: string
        +current_language: LanguageEnum
        +onLoginSubmit(): void
        +onLanguageToggle(lang: string): void
        +displayErrorMessage(msg: string): void
    }
    class AuthController {
        +login(request: LoginRequest): TokenResponse
        +refresh_token(token: string): TokenResponse
        +get_current_user(token: string): UserDTO
    }
    class LoginRequest {
        +username_or_email: string
        +password: string
    }
    class TokenResponse {
        +access_token: string
        +token_type: string
        +expires_in: int
        +user: UserDTO
    }
    class UserDTO {
        +id: int
        +username: string
        +email: string
        +role: RoleEnum
        +branch_id: int
        +belt_rank: BeltRankEnum
    }
    LoginView ..> AuthController : "HTTP POST /api/v1/auth/login"
    AuthController ..> LoginRequest : "Valida con Pydantic"
    AuthController ..> TokenResponse : "Retorna JWT"
    TokenResponse *-- UserDTO : "Contiene datos de sesión"
"""

DIAGRAMS["CU-1/03_secuencia_uc1.mmd"] = """sequenceDiagram
    autonumber
    actor U as Usuario
    participant UI as LoginView (React 19)
    participant AC as AuthController (FastAPI)
    participant AS as AuthService
    participant UR as UserRepository
    participant DB as PostgreSQL
    participant SEC as SecurityUtils (bcrypt/JWT)

    U->>UI: Ingresa usuario/email y password
    UI->>AC: POST /api/v1/auth/login
    AC->>AS: authenticate_user(username_or_email, password)
    AS->>UR: get_by_username_or_email(identifier)
    UR->>DB: SELECT * FROM users WHERE username = id OR email = id
    DB-->>UR: UserRecord / None
    UR-->>AS: User entity

    alt Usuario no encontrado o inactivo
        AS-->>AC: HTTP 401 Unauthorized
        AC-->>UI: Mensaje de error (Credenciales inválidas)
        UI-->>U: Muestra alerta en rojo
    else Usuario existe
        AS->>SEC: verify_password(plain_pwd, hashed_pwd)
        alt Password no coincide
            SEC-->>AS: False
            AS-->>AC: HTTP 401 Unauthorized
            AC-->>UI: Credenciales inválidas
            UI-->>U: Muestra alerta en pantalla
        else Password correcto
            SEC-->>AS: True
            AS->>SEC: create_access_token(user_id, role, branch_id)
            SEC-->>AS: JWT Token (exp: 24h)
            AS-->>AC: TokenResponse(access_token, user_data)
            AC-->>UI: HTTP 200 OK + JSON Token
            UI->>UI: Guarda JWT en localStorage & actualiza AuthState
            UI-->>U: Redirige al Dashboard según Rol
        end
    end
"""

DIAGRAMS["CU-1/04_paquetes_uc1.puml"] = """@startuml
skinparam dpi 300
skinparam defaultFontName "Arial"
skinparam packageStyle rectangle

package "Capa de Presentación (Frontend React 19)" #EBF8FF {
    [LoginView]
    [LanguageSelector]
    [AuthContext]
    [AxiosClient]
}

package "Capa de Aplicación y API (FastAPI)" #E6FFFA {
    [AuthController]
    [AuthService]
    [LoginRequestDTO]
    [TokenResponseDTO]
}

package "Capa de Dominio (Domain Layer)" #FAF5FF {
    [User]
    [RoleEnum]
    [BeltRankEnum]
    [IUserRepository]
}

package "Capa de Infraestructura (Infrastructure Layer)" #FFF5F5 {
    [UserRepositoryImpl]
    [PostgreSQL Database]
    [SecurityUtils (bcrypt / PyJWT)]
}

[LoginView] ..> [AxiosClient]
[AxiosClient] ..> [AuthController] : HTTP POST /api/v1/auth/login
[AuthController] ..> [LoginRequestDTO]
[AuthController] ..> [AuthService]
[AuthService] ..> [IUserRepository]
[AuthService] ..> [SecurityUtils (bcrypt / PyJWT)]
[AuthService] ..> [User]
[UserRepositoryImpl] ..|> [IUserRepository]
[UserRepositoryImpl] ..> [PostgreSQL Database] : SQLAlchemy ORM
@enduml
"""

# ==========================================
# CU-2: ANALIZAR TÉCNICA Y FEEDBACK BIOMECÁNICO
# ==========================================
os.makedirs(os.path.join(DIAGRAMS_DIR, "CU-2"), exist_ok=True)
DIAGRAMS["CU-2/01_caso_de_uso_uc2.puml"] = """@startuml
skinparam dpi 300
skinparam defaultFontName "Arial"
skinparam defaultFontSize 11
skinparam packageStyle rectangle
skinparam shadowing true

actor "Alumno" as alumno
actor "Google Colab GPU" as colab <<Worker AI>>
actor "Google Gemini 2.5 Flash" as gemini <<LLM Service>>

rectangle "Caso de Uso 2: Análisis Biomecánico y Feedback" {
    usecase "UC2: Analizar Técnica y Generar Feedback" as UC2
    usecase "Seleccionar Profesor y Técnica" as UC_Sel
    usecase "Validar Video Anti-Spam (BJJ)" as UC_Spam
    usecase "Extraer Keypoints 3D (YOLO26-pose/depth)" as UC_YOLO
    usecase "Calcular Similitud Coseno y MSE" as UC_Calc
    usecase "Generar Retroalimentación LLM (Gemini)" as UC_Gem
    usecase "Visualizar Gráfico y Reporte" as UC_Rep
}

alumno --> UC2
UC2 ..> UC_Sel : <<include>>
UC2 ..> UC_Spam : <<include>>
UC2 ..> UC_YOLO : <<include>>
UC2 ..> UC_Calc : <<include>>
UC2 ..> UC_Rep : <<include>>
UC2 ..> UC_Gem : <<extend>>\\n(si Similitud < 85%)

UC_Spam ..> gemini : <<invoca>>
UC_YOLO ..> colab : <<invoca>>
UC_Gem ..> gemini : <<invoca>>
@enduml
"""

DIAGRAMS["CU-2/02_clases_interfaz_uc2.mmd"] = """classDiagram
    direction TB
    class VideoUploadView {
        +selectedProfessorId: int
        +selectedTechniqueId: int
        +videoFile: File
        +previewUrl: string
        +onVideoSelect(file: File): void
        +onSubmitAnalysis(): void
    }
    class EvaluationDetailView {
        +similarityScore: float
        +referenceVideoUrl: string
        +studentVideoUrl: string
        +feedbackText: string
        +jointDiscrepancies: List~JointDiscrepancy~
        +renderCircularGauge(): void
    }
    class EvaluationController {
        +analyze_video(professor_id: int, technique_id: int, file: UploadFile): EvaluationDTO
        +get_evaluation_detail(eval_id: int): EvaluationDTO
    }
    class BiomechanicsService {
        +validate_bjj_content(video_bytes: bytes): bool
        +process_biomechanics(student_video: bytes, ref_kp: Matrix): BiomechanicsResult
        +generate_llm_feedback(result: BiomechanicsResult, lang: str): str
    }
    class EvaluationDTO {
        +id: int
        +student_id: int
        +technique_name: string
        +professor_name: string
        +similarity_score: float
        +gemini_feedback: string
        +created_at: datetime
    }
    VideoUploadView ..> EvaluationController : "POST /api/v1/evaluations/analyze"
    EvaluationController ..> BiomechanicsService : "Coordina análisis"
    EvaluationController ..> EvaluationDTO : "Retorna reporte"
    EvaluationDetailView ..> EvaluationDTO : "Renderiza métricas"
"""

DIAGRAMS["CU-2/03_secuencia_uc2.mmd"] = """sequenceDiagram
    autonumber
    actor A as Alumno
    participant UI as VideoUploadView (React)
    participant EC as EvaluationController (FastAPI)
    participant BS as BiomechanicsService
    participant GEM as Gemini 2.5 Flash API
    participant COL as Colab Worker (YOLO26)
    participant DB as PostgreSQL
    participant QDR as Qdrant Vector DB

    A->>UI: Selecciona Profesor, Técnica y sube video
    UI->>EC: POST /api/v1/evaluations/analyze (Multipart)
    EC->>BS: analyze_execution(student_id, prof_id, tech_id, video)
    
    BS->>GEM: Validar Video Anti-Spam (¿Es Jiu-Jitsu?)
    alt Video no es Jiu-Jitsu (Spam/Inválido)
        GEM-->>BS: is_valid = False
        BS-->>EC: HTTP 422 (Video no contiene BJJ)
        EC-->>UI: Error: Contenido no reconocido como técnica de BJJ
        UI-->>A: Muestra alerta de rechazo
    else Video válido de BJJ
        GEM-->>BS: is_valid = True
        BS->>DB: Obtener Video y Keypoints de Referencia del Profesor
        DB-->>BS: ReferenceKeypoints (133 dims por frame)
        BS->>COL: POST /infer (video_bytes) -> YOLO26-pose + depth
        COL-->>BS: StudentKeypoints (133 dims por frame)
        BS->>BS: Calcular Similitud Coseno y MSE de ángulos articulares
        
        alt Similitud >= 85.0 (Excelente técnica)
            BS->>BS: Asignar feedback felicitación ("¡Excelente ejecución biomecánica!")
        else Similitud < 85.0 (Requiere corrección)
            BS->>QDR: Buscar teoría RAG de la técnica (Top-3 Chunks)
            QDR-->>BS: Contexto doctrinal y biomecánico
            BS->>GEM: Generar Feedback Pedagógico (Ángulos + Chunks RAG + Idioma)
            GEM-->>BS: Texto de Feedback estructurado con corrección articular
        end

        BS->>DB: INSERT INTO evaluation_records (similitud, feedback, keypoints)
        DB-->>BS: Record Persistido (id)
        BS-->>EC: EvaluationDTO(score, feedback, ref_video_url)
        EC-->>UI: HTTP 200 OK + EvaluationDTO
        UI-->>A: Muestra Reporte con Gauge Circular, Video Ref y Feedback
    end
"""

DIAGRAMS["CU-2/04_paquetes_uc2.puml"] = """@startuml
skinparam dpi 300
skinparam defaultFontName "Arial"
skinparam packageStyle rectangle

package "Capa de Presentación (React 19)" #EBF8FF {
    [VideoUploadView]
    [EvaluationDetailView]
    [CircularGaugeComponent]
    [VideoComparisonPlayer]
}

package "Capa de Aplicación (FastAPI)" #E6FFFA {
    [EvaluationController]
    [BiomechanicsService]
    [FeedbackOrchestrator]
}

package "Capa de Dominio" #FAF5FF {
    [EvaluationRecord]
    [Technique]
    [PoseKeypoints]
    [AngularMetric]
}

package "Capa de Infraestructura y Servicios Externos" #FFF5F5 {
    [ColabGPUWorker (YOLO26)]
    [GeminiFlashClient (2.5)]
    [QdrantVectorClient]
    [PostgresEvaluationRepo]
}

[VideoUploadView] ..> [EvaluationController]
[EvaluationController] ..> [BiomechanicsService]
[BiomechanicsService] ..> [ColabGPUWorker (YOLO26)]
[BiomechanicsService] ..> [GeminiFlashClient (2.5)]
[BiomechanicsService] ..> [QdrantVectorClient]
[BiomechanicsService] ..> [PostgresEvaluationRepo]
[PostgresEvaluationRepo] ..> [EvaluationRecord]
@enduml
"""

# ==========================================
# CU-3: GESTIONAR TÉCNICAS Y VIDEOS DE REFERENCIA
# ==========================================
os.makedirs(os.path.join(DIAGRAMS_DIR, "CU-3"), exist_ok=True)
DIAGRAMS["CU-3/01_caso_de_uso_uc3.puml"] = """@startuml
skinparam dpi 300
skinparam defaultFontName "Arial"
skinparam defaultFontSize 11
skinparam packageStyle rectangle
skinparam shadowing true

actor "Profesor" as prof
actor "Google Colab GPU" as colab <<Worker AI>>

rectangle "Caso de Uso 3: Gestión de Técnicas y Referencias" {
    usecase "UC3: Gestionar Técnicas y Videos" as UC3
    usecase "Crear / Editar Técnica (Nombre, Faixa)" as UC_Create
    usecase "Cargar Video de Referencia Maestro" as UC_Video
    usecase "Extraer y Cachear Keypoints de Referencia" as UC_Extract
    usecase "Eliminar Técnica del Catálogo" as UC_Del
}

prof --> UC3
UC3 ..> UC_Create : <<include>>
UC3 ..> UC_Video : <<include>>
UC3 ..> UC_Extract : <<include>>
UC3 ..> UC_Del : <<extend>>

UC_Extract ..> colab : <<invoca>>
@enduml
"""

DIAGRAMS["CU-3/02_clases_interfaz_uc3.mmd"] = """classDiagram
    direction TB
    class TechniqueManagementView {
        +techniquesList: List~TechniqueDTO~
        +onCreateClick(): void
        +onEditClick(id: int): void
        +onDeleteClick(id: int): void
        +onUploadReference(id: int, file: File): void
    }
    class TechniqueFormModal {
        +name: string
        +belt_rank: BeltRankEnum
        +description: string
        +videoFile: File
        +onSave(): void
    }
    class TechniqueController {
        +list_techniques(belt: Optional~BeltRankEnum~): List~TechniqueDTO~
        +create_technique(dto: CreateTechniqueDTO): TechniqueDTO
        +upload_reference_video(tech_id: int, file: UploadFile): TechniqueDTO
        +delete_technique(tech_id: int): void
    }
    class TechniqueService {
        +save_technique(dto: CreateTechniqueDTO, professor_id: int): Technique
        +process_reference_video(tech_id: int, video_bytes: bytes): void
    }
    class TechniqueDTO {
        +id: int
        +name: string
        +belt_rank: string
        +has_reference_video: bool
        +professor_name: string
    }
    TechniqueManagementView ..> TechniqueController : "HTTP REST"
    TechniqueManagementView *-- TechniqueFormModal : "Contiene"
    TechniqueController ..> TechniqueService : "Lógica de negocio"
    TechniqueController ..> TechniqueDTO : "Serializa"
"""

DIAGRAMS["CU-3/03_secuencia_uc3.mmd"] = """sequenceDiagram
    autonumber
    actor P as Profesor
    participant UI as TechniqueManagementView
    participant TC as TechniqueController
    participant TS as TechniqueService
    participant COL as Colab Worker (YOLO26)
    participant FS as Local Media Storage
    participant DB as PostgreSQL

    P->>UI: Completa formulario de técnica y adjunta video maestro
    UI->>TC: POST /api/v1/techniques (Multipart DTO + Video)
    TC->>TS: register_technique_with_reference(prof_id, tech_data, video)
    TS->>FS: Guardar archivo de video (MP4/MOV)
    FS-->>TS: video_storage_path
    TS->>COL: POST /extract-reference-keypoints (video_bytes)
    COL-->>TS: ReferenceKeypointsMatrix (133 dims x N frames)
    TS->>DB: INSERT INTO techniques (name, belt, video_url, keypoints_json, prof_id)
    DB-->>TS: Technique Entity (id)
    TS-->>TC: TechniqueDTO
    TC-->>UI: HTTP 201 Created + TechniqueDTO
    UI-->>P: Muestra técnica en el catálogo con badge de video verificado
"""

DIAGRAMS["CU-3/04_paquetes_uc3.puml"] = """@startuml
skinparam dpi 300
skinparam defaultFontName "Arial"
skinparam packageStyle rectangle

package "Capa de Presentación (Frontend)" #EBF8FF {
    [TechniqueManagementView]
    [TechniqueFormModal]
    [VideoPreviewComponent]
}

package "Capa de Aplicación (Backend)" #E6FFFA {
    [TechniqueController]
    [TechniqueService]
    [VideoProcessingPipeline]
}

package "Capa de Dominio" #FAF5FF {
    [Technique]
    [BeltRank]
    [ITechniqueRepository]
}

package "Capa de Infraestructura" #FFF5F5 {
    [PostgresTechniqueRepo]
    [FileStorageService]
    [ColabPoseWorkerClient]
}

[TechniqueManagementView] ..> [TechniqueController]
[TechniqueController] ..> [TechniqueService]
[TechniqueService] ..> [ITechniqueRepository]
[TechniqueService] ..> [FileStorageService]
[TechniqueService] ..> [ColabPoseWorkerClient]
[PostgresTechniqueRepo] ..|> [ITechniqueRepository]
@enduml
"""

# ==========================================
# CU-4: GESTIONAR TEORÍA RAG
# ==========================================
os.makedirs(os.path.join(DIAGRAMS_DIR, "CU-4"), exist_ok=True)
DIAGRAMS["CU-4/01_caso_de_uso_uc4.puml"] = """@startuml
skinparam dpi 300
skinparam defaultFontName "Arial"
skinparam defaultFontSize 11
skinparam packageStyle rectangle
skinparam shadowing true

actor "Profesor" as prof
actor "Google Colab GPU (Qwen3-VL)" as qwen <<Embeddings AI>>
actor "Qdrant Vector DB" as qdrant <<Vector Engine>>

rectangle "Caso de Uso 4: Gestión de Teoría Doctrinal RAG" {
    usecase "UC4: Gestionar Teoría RAG" as UC4
    usecase "Cargar Texto / Manual del Maestro" as UC_Input
    usecase "Fragmentar en Chunks Semánticos" as UC_Chunk
    usecase "Generar Embeddings Vectoriales (Qwen)" as UC_Embed
    usecase "Persistir en Qdrant y PostgreSQL" as UC_Persist
    usecase "Auditar / Eliminar Chunks de Teoría" as UC_Manage
}

prof --> UC4
UC4 ..> UC_Input : <<include>>
UC4 ..> UC_Chunk : <<include>>
UC4 ..> UC_Embed : <<include>>
UC4 ..> UC_Persist : <<include>>
UC4 ..> UC_Manage : <<extend>>

UC_Embed ..> qwen : <<invoca>>
UC_Persist ..> qdrant : <<almacena>>
@enduml
"""

DIAGRAMS["CU-4/02_clases_interfaz_uc4.mmd"] = """classDiagram
    direction TB
    class TheoryManagementModal {
        +techniqueId: int
        +theoryText: string
        +chunksList: List~TheoryChunkDTO~
        +onAddTheory(): void
        +onDeleteAllTheory(): void
        +onPreviewChunks(): void
    }
    class TheoryController {
        +upload_theory(tech_id: int, payload: TheoryUploadDTO): TheoryResponseDTO
        +get_theory_chunks(tech_id: int): List~TheoryChunkDTO~
        +delete_theory(tech_id: int): void
    }
    class RagTheoryService {
        +chunk_text(raw_text: str, chunk_size: int, overlap: int): List~str~
        +generate_embeddings(chunks: List~str~): List~Vector~
        +upsert_to_qdrant_and_postgres(tech_id: int, chunks: List~str~, vectors: List~Vector~): void
        +purge_technique_theory(tech_id: int): void
    }
    class TheoryChunkDTO {
        +id: str
        +chunk_index: int
        +content: str
        +vector_dim: int
        +created_at: datetime
    }
    TheoryManagementModal ..> TheoryController : "HTTP REST"
    TheoryController ..> RagTheoryService : "Orquesta pipeline"
    TheoryController ..> TheoryChunkDTO : "Visualiza"
"""

DIAGRAMS["CU-4/03_secuencia_uc4.mmd"] = """sequenceDiagram
    autonumber
    actor P as Profesor
    participant UI as TheoryManagementModal
    participant TC as TheoryController
    participant RS as RagTheoryService
    participant COL as Colab Worker (Qwen3-VL-2B)
    participant QDR as Qdrant Vector DB
    participant DB as PostgreSQL

    P->>UI: Pega el manual de técnica y presiona 'Procesar Teoría'
    UI->>TC: POST /api/v1/techniques/{id}/theory (raw_text)
    TC->>RS: process_and_index_theory(tech_id, prof_id, raw_text)
    RS->>RS: Chunking semántico (tamaño: 500 chars, solapamiento: 50)
    RS->>COL: POST /vectorize-chunks (list_of_chunks)
    COL-->>RS: List of Dense Vectors (dim = 1536)
    RS->>DB: BEGIN TRANSACTION -> INSERT INTO theory_chunks
    DB-->>RS: Chunks IDs
    RS->>QDR: Upsert Points (payload: {tech_id, prof_id, text}, vector: v)
    QDR-->>RS: 200 OK (Points Indexed)
    RS->>DB: COMMIT TRANSACTION
    RS-->>TC: IndexingSummary(total_chunks, status='SUCCESS')
    TC-->>UI: HTTP 200 OK + Chunks List
    UI-->>P: Muestra modal de confirmación con los chunks vectorizados
"""

DIAGRAMS["CU-4/04_paquetes_uc4.puml"] = """@startuml
skinparam dpi 300
skinparam defaultFontName "Arial"
skinparam packageStyle rectangle

package "Capa de Presentación" #EBF8FF {
    [TheoryManagementModal]
    [ChunkViewerComponent]
}

package "Capa de Aplicación (RAG Pipeline)" #E6FFFA {
    [TheoryController]
    [RagTheoryService]
    [SemanticChunker]
}

package "Capa de Dominio" #FAF5FF {
    [TheoryChunk]
    [VectorEmbedding]
    [IRagRepository]
}

package "Capa de Infraestructura" #FFF5F5 {
    [QdrantVectorAdapter]
    [PostgresTheoryRepo]
    [QwenEmbeddingClient (Colab)]
}

[TheoryManagementModal] ..> [TheoryController]
[TheoryController] ..> [RagTheoryService]
[RagTheoryService] ..> [SemanticChunker]
[RagTheoryService] ..> [QwenEmbeddingClient (Colab)]
[RagTheoryService] ..> [QdrantVectorAdapter]
[RagTheoryService] ..> [PostgresTheoryRepo]
[QdrantVectorAdapter] ..|> [IRagRepository]
@enduml
"""

# ==========================================
# CU-5: VISUALIZAR PROGRESO DE ALUMNOS
# ==========================================
os.makedirs(os.path.join(DIAGRAMS_DIR, "CU-5"), exist_ok=True)
DIAGRAMS["CU-5/01_caso_de_uso_uc5.puml"] = """@startuml
skinparam dpi 300
skinparam defaultFontName "Arial"
skinparam defaultFontSize 11
skinparam packageStyle rectangle
skinparam shadowing true

actor "Profesor" as prof

rectangle "Caso de Uso 5: Visualización de Progreso Biomecánico" {
    usecase "UC5: Visualizar Progreso de Alumnos" as UC5
    usecase "Filtrar por Sucursal y Nivel de Cinturón" as UC_Filter
    usecase "Ver Lista de Alumnos y Promedios de Similitud" as UC_List
    usecase "Inspeccionar Historial de Evaluaciones y Gráfico Temporal" as UC_Hist
    usecase "Revisar Detalle Articular y Feedback de Gemini" as UC_Detail
}

prof --> UC5
UC5 ..> UC_Filter : <<include>>
UC5 ..> UC_List : <<include>>
UC5 ..> UC_Hist : <<include>>
UC5 ..> UC_Detail : <<extend>>
@enduml
"""

DIAGRAMS["CU-5/02_clases_interfaz_uc5.mmd"] = """classDiagram
    direction TB
    class StudentProgressView {
        +selectedBranchId: int
        +studentsList: List~StudentSummaryDTO~
        +onSelectStudent(studentId: int): void
        +onFilterBelt(belt: string): void
    }
    class EvaluationHistoryModal {
        +studentEvaluations: List~EvaluationDTO~
        +progressChartData: ChartTimeSeriesData
        +onViewEvaluationDetail(evalId: int): void
    }
    class ProgressController {
        +get_branch_students(branch_id: int): List~StudentSummaryDTO~
        +get_student_history(student_id: int): StudentHistoryDTO
        +get_evaluation_detail(eval_id: int): EvaluationDTO
    }
    class ProgressService {
        +calculate_student_stats(student_id: int): StudentStatsDTO
        +get_evaluations_timeline(student_id: int): List~EvaluationRecord~
    }
    StudentProgressView ..> ProgressController : "HTTP GET"
    StudentProgressView *-- EvaluationHistoryModal : "Abre"
    ProgressController ..> ProgressService : "Calcula estadísticas"
"""

DIAGRAMS["CU-5/03_secuencia_uc5.mmd"] = """sequenceDiagram
    autonumber
    actor P as Profesor
    participant UI as StudentProgressView
    participant PC as ProgressController
    participant PS as ProgressService
    participant DB as PostgreSQL

    P->>UI: Selecciona sucursal y visualiza panel de alumnos
    UI->>PC: GET /api/v1/progress/branch/{branch_id}/students
    PC->>PS: fetch_students_with_metrics(branch_id)
    PS->>DB: SELECT u.*, AVG(e.similitud) FROM users u JOIN evaluations e ...
    DB-->>PS: Lista de Alumnos + Métricas de Promedio
    PS-->>PC: List of StudentSummaryDTO
    PC-->>UI: HTTP 200 OK + JSON
    UI-->>P: Renderiza tabla con porcentaje promedio y badge de graduación
    
    P->>UI: Clic en alumno específico para ver curva de aprendizaje
    UI->>PC: GET /api/v1/progress/student/{id}/history
    PC->>PS: get_student_evaluation_history(student_id)
    PS->>DB: SELECT * FROM evaluations WHERE student_id = ? ORDER BY created_at ASC
    DB-->>PS: Evaluation Records
    PS-->>PC: StudentHistoryDTO(evaluations, evolution_trend)
    PC-->>UI: HTTP 200 OK
    UI-->>P: Muestra gráfico de línea temporal y tabla de intentos
"""

DIAGRAMS["CU-5/04_paquetes_uc5.puml"] = """@startuml
skinparam dpi 300
skinparam defaultFontName "Arial"
skinparam packageStyle rectangle

package "Capa de Presentación" #EBF8FF {
    [StudentProgressView]
    [EvaluationHistoryModal]
    [TimelineChartComponent]
}

package "Capa de Aplicación" #E6FFFA {
    [ProgressController]
    [ProgressService]
    [AnalyticsEngine]
}

package "Capa de Dominio" #FAF5FF {
    [StudentProgressAggregate]
    [EvaluationRecord]
    [IEvaluationRepository]
}

package "Capa de Infraestructura" #FFF5F5 {
    [PostgresEvaluationRepo]
    [PostgresUserRepo]
}

[StudentProgressView] ..> [ProgressController]
[ProgressController] ..> [ProgressService]
[ProgressService] ..> [AnalyticsEngine]
[ProgressService] ..> [IEvaluationRepository]
[PostgresEvaluationRepo] ..|> [IEvaluationRepository]
@enduml
"""

# ==========================================
# CU-6: GESTIONAR SUCURSALES Y COORDENADAS
# ==========================================
os.makedirs(os.path.join(DIAGRAMS_DIR, "CU-6"), exist_ok=True)
DIAGRAMS["CU-6/01_caso_de_uso_uc6.puml"] = """@startuml
skinparam dpi 300
skinparam defaultFontName "Arial"
skinparam defaultFontSize 11
skinparam packageStyle rectangle
skinparam shadowing true

actor "Administrador" as admin
actor "OpenStreetMap / Leaflet" as osm <<Map Service>>
actor "Nominatim API" as nom <<Geocoding Service>>

rectangle "Caso de Uso 6: Gestión de Sucursales y Geoposición" {
    usecase "UC6: Gestionar Sucursales y Geoposición" as UC6
    usecase "Crear / Editar Sucursal (Nombre, Ciudad, Dirección)" as UC_CRUD
    usecase "Capturar Coordenadas en Mapa Interactivo (Leaflet)" as UC_Map
    usecase "Pegar Enlace de Google Maps y Extraer Coordenadas" as UC_GMap
    usecase "Geocodificación Inversa y Generación de Plus Code" as UC_Geo
    usecase "Eliminar Sucursal" as UC_Del
}

admin --> UC6
UC6 ..> UC_CRUD : <<include>>
UC6 ..> UC_Map : <<include>>
UC6 ..> UC_GMap : <<extend>>
UC6 ..> UC_Geo : <<include>>
UC6 ..> UC_Del : <<extend>>

UC_Map ..> osm : <<renderiza>>
UC_Geo ..> nom : <<invoca>>
@enduml
"""

DIAGRAMS["CU-6/02_clases_interfaz_uc6.mmd"] = """classDiagram
    direction TB
    class BranchManagementView {
        +branchesList: List~BranchDTO~
        +onAddBranchClick(): void
        +onEditBranchClick(id: int): void
        +onDeleteBranchClick(id: int): void
    }
    class BranchFormModal {
        +name: string
        +city: string
        +address: string
        +latitude: float
        +longitude: float
        +plus_code: string
        +googleMapsUrl: string
        +onPasteGoogleMapsUrl(url: string): void
        +onMapMarkerDrag(lat: float, lng: float): void
    }
    class BranchController {
        +list_branches(): List~BranchDTO~
        +create_branch(dto: CreateBranchDTO): BranchDTO
        +parse_maps_url(payload: UrlPayload): CoordinatesDTO
        +reverse_geocode(lat: float, lng: float): AddressDTO
    }
    class BranchService {
        +extract_coords_from_url(url: str): Tuple~float, float~
        +query_nominatim_reverse(lat: float, lng: float): str
        +generate_plus_code(lat: float, lng: float): str
        +save_branch(dto: CreateBranchDTO): Branch
    }
    BranchManagementView ..> BranchController : "HTTP REST"
    BranchManagementView *-- BranchFormModal : "Contiene"
    BranchController ..> BranchService : "Lógica de negocio"
"""

DIAGRAMS["CU-6/03_secuencia_uc6.mmd"] = """sequenceDiagram
    autonumber
    actor A as Administrador
    participant UI as BranchFormModal (Leaflet Map)
    participant BC as BranchController (FastAPI)
    participant BS as BranchService
    participant NOM as Nominatim OpenStreetMap API
    participant DB as PostgreSQL

    A->>UI: Pega enlace de Google Maps (o arrastra pin en Leaflet)
    UI->>BC: POST /api/v1/branches/parse-maps-url { url: "https://maps.app.goo.gl/..." }
    BC->>BS: extract_coordinates_from_url(url)
    BS->>BS: Regex parsing / HTTP redirect expansion (@lat,lng)
    BS->>NOM: GET /reverse?lat={lat}&lon={lng}&format=json
    NOM-->>BS: ReverseGeocodingResult(address="Av. Banzer esq. 4to Anillo")
    BS->>BS: Compute Plus Code (ej: "8553+CJ Santa Cruz de la Sierra")
    BS-->>BC: ResolvedLocationDTO(lat, lng, address, plus_code)
    BC-->>UI: HTTP 200 OK + JSON
    UI-->>A: Actualiza pin en el mapa y autocompleta formulario
    
    A->>UI: Presiona 'Guardar Sucursal'
    UI->>BC: POST /api/v1/branches (CreateBranchDTO)
    BC->>BS: create_branch(dto)
    BS->>DB: INSERT INTO branches (name, city, address, lat, lng, plus_code)
    DB-->>BS: Branch Entity (id)
    BS-->>BC: BranchDTO
    BC-->>UI: HTTP 201 Created
    UI-->>A: Cierra modal y refresca lista con marcador activo
"""

DIAGRAMS["CU-6/04_paquetes_uc6.puml"] = """@startuml
skinparam dpi 300
skinparam defaultFontName "Arial"
skinparam packageStyle rectangle

package "Capa de Presentación" #EBF8FF {
    [BranchManagementView]
    [BranchFormModal]
    [LeafletMapViewComponent]
}

package "Capa de Aplicación" #E6FFFA {
    [BranchController]
    [BranchService]
    [UrlParserService]
}

package "Capa de Dominio" #FAF5FF {
    [Branch]
    [GeoLocation]
    [IBranchRepository]
}

package "Capa de Infraestructura" #FFF5F5 {
    [PostgresBranchRepo]
    [NominatimClient]
    [OpenLocationCodeUtil]
}

[BranchManagementView] ..> [BranchController]
[BranchController] ..> [BranchService]
[BranchService] ..> [UrlParserService]
[BranchService] ..> [NominatimClient]
[BranchService] ..> [OpenLocationCodeUtil]
[BranchService] ..> [IBranchRepository]
[PostgresBranchRepo] ..|> [IBranchRepository]
@enduml
"""

# ==========================================
# CU-7: ADMINISTRAR USUARIOS E IMPERSONIFICACIÓN
# ==========================================
os.makedirs(os.path.join(DIAGRAMS_DIR, "CU-7"), exist_ok=True)
DIAGRAMS["CU-7/01_caso_de_uso_uc7.puml"] = """@startuml
skinparam dpi 300
skinparam defaultFontName "Arial"
skinparam defaultFontSize 11
skinparam packageStyle rectangle
skinparam shadowing true

actor "Administrador" as admin

rectangle "Caso de Uso 7: Administración de Usuarios e Impersonificación" {
    usecase "UC7: Administrar Usuarios e Impersonificación" as UC7
    usecase "Listar y Filtrar Usuarios (Rol, Sucursal, Estado)" as UC_List
    usecase "Crear / Modificar Usuario y Asignar Cinturón" as UC_Edit
    usecase "Impersonificar Usuario No-Admin (Sin Contraseña)" as UC_Imp
    usecase "Mostrar Banner Persistente de Impersonificación" as UC_Banner
    usecase "Revertir Sesión y Restaurar Contexto Admin" as UC_Rev
}

admin --> UC7
UC7 ..> UC_List : <<include>>
UC7 ..> UC_Edit : <<include>>
UC7 ..> UC_Imp : <<include>>
UC7 ..> UC_Banner : <<include>>
UC7 ..> UC_Rev : <<include>>
@enduml
"""

DIAGRAMS["CU-7/02_clases_interfaz_uc7.mmd"] = """classDiagram
    direction TB
    class UserManagementView {
        +usersList: List~UserAdminDTO~
        +onSearch(query: string): void
        +onFilterRole(role: string): void
        +onImpersonateUser(targetUserId: int): void
        +onEditUser(userId: int): void
    }
    class ImpersonationBanner {
        +impersonatedUserName: string
        +impersonatedRole: string
        +originalAdminName: string
        +onRevertSession(): void
    }
    class AdminUserController {
        +list_users(page: int, limit: int): UserListResponse
        +create_user(dto: CreateUserDTO): UserAdminDTO
        +impersonate_user(target_user_id: int): ImpersonationTokenResponse
        +revert_impersonation(admin_token: str): TokenResponse
    }
    class ImpersonationService {
        +validate_admin_rights(current_user: User): bool
        +create_impersonation_token(admin_user: User, target_user: User): str
        +audit_impersonation_event(admin_id: int, target_id: int, action: str): void
    }
    UserManagementView ..> AdminUserController : "HTTP REST"
    ImpersonationBanner ..> AdminUserController : "POST /revert"
    AdminUserController ..> ImpersonationService : "Genera JWT firmado"
"""

DIAGRAMS["CU-7/03_secuencia_uc7.mmd"] = """sequenceDiagram
    autonumber
    actor A as Administrador
    participant UI as UserManagementView (React)
    participant BAN as ImpersonationBanner
    participant AC as AdminUserController
    participant IS as ImpersonationService
    participant SEC as SecurityUtils (PyJWT)
    participant AUD as AuditLogger
    participant DB as PostgreSQL

    A->>UI: Clic en botón 'Impersonificar' en la fila del alumno/profesor
    UI->>AC: POST /api/v1/admin/impersonate/{target_user_id}
    AC->>IS: start_impersonation(current_admin, target_user_id)
    IS->>DB: SELECT * FROM users WHERE id = target_user_id
    DB-->>IS: TargetUser Entity (role != 'ADMIN')
    IS->>AUD: log_event(admin_id, target_id, 'IMPERSONATION_STARTED')
    IS->>SEC: create_token(sub=target_id, role=target_role, original_admin_id=admin_id)
    SEC-->>IS: ImpersonationJWT (24h)
    IS-->>AC: ImpersonationTokenResponse(jwt, target_user_data, original_admin_id)
    AC-->>UI: HTTP 200 OK + JSON
    UI->>UI: Guarda JWT temporal y activa estado isImpersonating=true
    UI-->>BAN: Renderiza banner persistente ("Sesión actuando como [Alumno]")
    UI-->>A: Redirige a la vista del usuario impersonificado
    
    A->>BAN: Clic en botón 'Salir de Impersonación / Restaurar Admin'
    BAN->>AC: POST /api/v1/admin/revert-impersonation
    AC->>IS: restore_admin_session(original_admin_id)
    IS->>AUD: log_event(admin_id, target_id, 'IMPERSONATION_ENDED')
    IS->>SEC: create_access_token(admin_id, role='ADMIN')
    SEC-->>IS: AdminJWT
    IS-->>AC: TokenResponse(access_token)
    AC-->>BAN: HTTP 200 OK
    BAN->>UI: Restaura JWT de administrador y desactiva banner
    UI-->>A: Redirige de vuelta al panel de Administración de Usuarios
"""

DIAGRAMS["CU-7/04_paquetes_uc7.puml"] = """@startuml
skinparam dpi 300
skinparam defaultFontName "Arial"
skinparam packageStyle rectangle

package "Capa de Presentación" #EBF8FF {
    [UserManagementView]
    [ImpersonationBanner]
    [UserEditModal]
}

package "Capa de Aplicación" #E6FFFA {
    [AdminUserController]
    [ImpersonationService]
    [UserManagementService]
}

package "Capa de Dominio" #FAF5FF {
    [User]
    [RoleEnum]
    [AuditLog]
    [IUserRepository]
    [IAuditLogRepository]
}

package "Capa de Infraestructura" #FFF5F5 {
    [PostgresUserRepo]
    [PostgresAuditRepo]
    [SecurityUtils (JWT Claims)]
}

[UserManagementView] ..> [AdminUserController]
[ImpersonationBanner] ..> [AdminUserController]
[AdminUserController] ..> [ImpersonationService]
[AdminUserController] ..> [UserManagementService]
[ImpersonationService] ..> [SecurityUtils (JWT Claims)]
[ImpersonationService] ..> [IUserRepository]
[ImpersonationService] ..> [IAuditLogRepository]
[PostgresUserRepo] ..|> [IUserRepository]
[PostgresAuditRepo] ..|> [IAuditLogRepository]
@enduml
"""

# ==========================================
# 1. WRITE ALL DIAGRAM FILES
# ==========================================
print("Writing diagram source files...")
for rel_path, content in DIAGRAMS.items():
    full_path = os.path.join(DIAGRAMS_DIR, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\\n")
    print(f" - Created: {rel_path}")

# ==========================================
# 2. COMPILE ALL DIAGRAMS TO PNG
# ==========================================
print("\\nCompiling all diagrams to PNG images in Libros/figuras/capitulo_5/ ...")

# Mapping from diagram file to chapter 5 figure output name
FIGURE_MAP = {
    # General (Capítulo 4 & 5 overview)
    "CU-General/01_casos_de_uso_general.puml": os.path.join(BASE_DIR, "Libros", "figuras", "capitulo_4_figura_4_1_casos_de_uso.png"),
    
    # CU-1
    "CU-1/01_caso_de_uso_uc1.puml": os.path.join(FIGURAS_C5_DIR, "figura_5_1_caso_de_uso_uc1.png"),
    "CU-1/02_clases_interfaz_uc1.mmd": os.path.join(FIGURAS_C5_DIR, "figura_5_2_clases_interfaz_uc1.png"),
    "CU-1/03_secuencia_uc1.mmd": os.path.join(FIGURAS_C5_DIR, "figura_5_3_secuencia_uc1.png"),
    "CU-1/04_paquetes_uc1.puml": os.path.join(FIGURAS_C5_DIR, "figura_5_4_paquetes_uc1.png"),
    
    # CU-2
    "CU-2/01_caso_de_uso_uc2.puml": os.path.join(FIGURAS_C5_DIR, "figura_5_5_caso_de_uso_uc2.png"),
    "CU-2/02_clases_interfaz_uc2.mmd": os.path.join(FIGURAS_C5_DIR, "figura_5_6_clases_interfaz_uc2.png"),
    "CU-2/03_secuencia_uc2.mmd": os.path.join(FIGURAS_C5_DIR, "figura_5_7_secuencia_uc2.png"),
    "CU-2/04_paquetes_uc2.puml": os.path.join(FIGURAS_C5_DIR, "figura_5_8_paquetes_uc2.png"),
    
    # CU-3
    "CU-3/01_caso_de_uso_uc3.puml": os.path.join(FIGURAS_C5_DIR, "figura_5_9_caso_de_uso_uc3.png"),
    "CU-3/02_clases_interfaz_uc3.mmd": os.path.join(FIGURAS_C5_DIR, "figura_5_10_clases_interfaz_uc3.png"),
    "CU-3/03_secuencia_uc3.mmd": os.path.join(FIGURAS_C5_DIR, "figura_5_11_secuencia_uc3.png"),
    "CU-3/04_paquetes_uc3.puml": os.path.join(FIGURAS_C5_DIR, "figura_5_12_paquetes_uc3.png"),
    
    # CU-4
    "CU-4/01_caso_de_uso_uc4.puml": os.path.join(FIGURAS_C5_DIR, "figura_5_13_caso_de_uso_uc4.png"),
    "CU-4/02_clases_interfaz_uc4.mmd": os.path.join(FIGURAS_C5_DIR, "figura_5_14_clases_interfaz_uc4.png"),
    "CU-4/03_secuencia_uc4.mmd": os.path.join(FIGURAS_C5_DIR, "figura_5_15_secuencia_uc4.png"),
    "CU-4/04_paquetes_uc4.puml": os.path.join(FIGURAS_C5_DIR, "figura_5_16_paquetes_uc4.png"),
    
    # CU-5
    "CU-5/01_caso_de_uso_uc5.puml": os.path.join(FIGURAS_C5_DIR, "figura_5_17_caso_de_uso_uc5.png"),
    "CU-5/02_clases_interfaz_uc5.mmd": os.path.join(FIGURAS_C5_DIR, "figura_5_18_clases_interfaz_uc5.png"),
    "CU-5/03_secuencia_uc5.mmd": os.path.join(FIGURAS_C5_DIR, "figura_5_19_secuencia_uc5.png"),
    "CU-5/04_paquetes_uc5.puml": os.path.join(FIGURAS_C5_DIR, "figura_5_20_paquetes_uc5.png"),
    
    # CU-6
    "CU-6/01_caso_de_uso_uc6.puml": os.path.join(FIGURAS_C5_DIR, "figura_5_21_caso_de_uso_uc6.png"),
    "CU-6/02_clases_interfaz_uc6.mmd": os.path.join(FIGURAS_C5_DIR, "figura_5_22_clases_interfaz_uc6.png"),
    "CU-6/03_secuencia_uc6.mmd": os.path.join(FIGURAS_C5_DIR, "figura_5_23_secuencia_uc6.png"),
    "CU-6/04_paquetes_uc6.puml": os.path.join(FIGURAS_C5_DIR, "figura_5_24_paquetes_uc6.png"),
    
    # CU-7
    "CU-7/01_caso_de_uso_uc7.puml": os.path.join(FIGURAS_C5_DIR, "figura_5_25_caso_de_uso_uc7.png"),
    "CU-7/02_clases_interfaz_uc7.mmd": os.path.join(FIGURAS_C5_DIR, "figura_5_26_clases_interfaz_uc7.png"),
    "CU-7/03_secuencia_uc7.mmd": os.path.join(FIGURAS_C5_DIR, "figura_5_27_secuencia_uc7.png"),
    "CU-7/04_paquetes_uc7.puml": os.path.join(FIGURAS_C5_DIR, "figura_5_28_paquetes_uc7.png"),
}

for rel_src, out_png in FIGURE_MAP.items():
    src_file = os.path.join(DIAGRAMS_DIR, rel_src)
    os.makedirs(os.path.dirname(out_png), exist_ok=True)
    if rel_src.endswith(".puml"):
        # Run PlantUML
        cmd = ["java", "-jar", PLANTUML_JAR, "-tpng", "-o", os.path.dirname(out_png), src_file]
        res = subprocess.run(cmd, capture_output=True, text=True)
        # Rename output if needed
        default_png = os.path.join(os.path.dirname(out_png), os.path.splitext(os.path.basename(src_file))[0] + ".png")
        if os.path.exists(default_png) and default_png != out_png:
            os.replace(default_png, out_png)
        print(f" [PlantUML] {rel_src} -> {os.path.basename(out_png)} (Status: {res.returncode})")
    elif rel_src.endswith(".mmd"):
        # Run Mermaid
        cmd = [MMDC_BIN, "-i", src_file, "-o", out_png, "-b", "white", "-s", "3"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        print(f" [Mermaid]  {rel_src} -> {os.path.basename(out_png)} (Status: {res.returncode})")
        if res.returncode != 0:
            print("   Error:", res.stderr)

print("\\nAll diagrams written and compiled successfully.")



--- ARCHIVO: exportar_contexto_llm.py ---
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
exportar_contexto_llm.py

Recorre un proyecto y exporta el contenido de archivos de texto para dar contexto a LLMs.

Genera:
  contexto_llm/
    00_INDICE.txt
    00_OMITIDOS.txt
    contexto_llm.jsonl
    contexto_llm_001.md
    contexto_llm_002.md
    ...

Uso:
  python exportar_contexto_llm.py
  python exportar_contexto_llm.py /ruta/proyecto -o contexto_llm --max-chars 150000
  python exportar_contexto_llm.py --incluir-todo
"""

import argparse
import datetime
import json
import os
import sys
from pathlib import Path

EXCLUIR_DIRS = {
    ".git", ".hg", ".svn", ".idea", ".vscode",
    "node_modules", "bower_components",
    "venv", ".venv", "env", ".env", "virtualenv",
    "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".tox",
    "dist", "build", "target", "out", "coverage", ".nyc_output",
    "qdrant_storage", ".qdrant", "storage",
    ".next", ".nuxt", ".cache", ".parcel-cache",
    "site-packages", "Lib", "Scripts", "include", "share", "lib64",
}

EXCLUIR_EXT = {
    ".pyc", ".pyo", ".pyd", ".so", ".dll", ".dylib", ".a", ".o", ".obj",
    ".class", ".jar", ".war", ".exe", ".bin", ".dat", ".mmap", ".node", ".wasm",
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".ico", ".tif", ".tiff",
    ".mp3", ".mp4", ".mov", ".avi", ".mkv", ".wav", ".ogg", ".flac",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".zip", ".tar", ".gz", ".tgz", ".bz2", ".xz", ".7z", ".rar",
    ".sqlite", ".sqlite3", ".db", ".mdb", ".lock", ".map",
}

EXCLUIR_NOMBRES = {
    ".DS_Store", "Thumbs.db", "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
    ".env", ".env.local", ".env.development", ".env.production", ".env.test",
}

INCLUIR_EXT_DEFAULT = {
    ".py", ".pyi", ".pyx", ".pxd",
    ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx",
    ".json", ".jsonl", ".md", ".txt", ".rst",
    ".yml", ".yaml", ".toml", ".ini", ".cfg", ".conf",
    ".sql", ".html", ".htm", ".css", ".scss", ".sass", ".less",
    ".sh", ".bash", ".zsh", ".fish", ".ps1", ".bat", ".cmd",
    ".xml", ".csv", ".tsv", ".graphql", ".gql",
    ".java", ".kt", ".kts", ".go", ".rs", ".rb", ".php", ".c", ".h", ".cpp", ".hpp",
}

INCLUIR_NOMBRES_DEFAULT = {
    "Dockerfile", "Makefile", "Procfile", "README", "LICENSE",
    ".gitignore", ".dockerignore", ".env.example",
    "requirements.txt", "pyproject.toml", "setup.py", "setup.cfg",
    "Pipfile", "Pipfile.lock", "package.json", "tsconfig.json",
}


def es_binario(data: bytes) -> bool:
    """Heurística simple para detectar binarios."""
    if not data:
        return False
    if b"\0" in data:
        return True
    textchars = bytearray({7, 8, 9, 10, 12, 13, 27} | set(range(0x20, 0x100)))
    return bool(data.translate(None, textchars))


def leer_archivo_texto(path: Path, max_file_bytes: int):
    try:
        size = path.stat().st_size
    except OSError as e:
        return None, f"error stat: {e}", 0

    if size > max_file_bytes:
        return None, f"omitido por tamaño ({size} bytes)", size

    try:
        data = path.read_bytes()
    except OSError as e:
        return None, f"error lectura: {e}", size

    if es_binario(data):
        return None, "omitido por binario", size

    for enc in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return data.decode(enc), None, size
        except UnicodeDecodeError:
            continue

    return data.decode("utf-8", errors="replace"), None, size


class Exportador:
    def __init__(self, root: Path, outdir: Path, max_chars: int):
        self.root = root
        self.outdir = outdir
        self.max_chars = max_chars
        self.part = 1
        self.current = []
        self.current_chars = 0
        self.files = []
        self.jsonl_path = outdir / "contexto_llm.jsonl"
        self.jsonl = open(self.jsonl_path, "w", encoding="utf-8")

    def add(self, relpath: str, content: str, size: int):
        record = {"archivo": relpath, "bytes": size, "contenido": content}
        self.jsonl.write(json.dumps(record, ensure_ascii=False) + "\n")

        header = f"\n\n--- ARCHIVO: {relpath} ---\n"
        block = header + content + "\n"

        if self.current_chars + len(block) > self.max_chars and self.current:
            self.flush()

        self.current.append(block)
        self.current_chars += len(block)
        self.files.append({"archivo": relpath, "bytes": size})

    def flush(self):
        if not self.current:
            return
        part_path = self.outdir / f"contexto_llm_{self.part:03d}.md"
        part_path.write_text("".join(self.current), encoding="utf-8")
        self.current = []
        self.current_chars = 0
        self.part += 1

    def close(self):
        self.flush()
        self.jsonl.close()

        index_path = self.outdir / "00_INDICE.txt"
        with index_path.open("w", encoding="utf-8") as f:
            f.write(f"Proyecto: {self.root}\n")
            f.write(f"Generado: {datetime.datetime.now().isoformat(timespec='seconds')}\n")
            f.write(f"Total archivos: {len(self.files)}\n\n")
            for item in self.files:
                f.write(f"{item['bytes']:>10}  {item['archivo']}\n")


def parse_args():
    p = argparse.ArgumentParser(
        description="Exporta el contenido de archivos de texto de un proyecto para LLMs."
    )
    p.add_argument("root", nargs="?", default=".", help="Raíz del proyecto (default: .)")
    p.add_argument("-o", "--out", default="contexto_llm", help="Directorio de salida")
    p.add_argument("--max-chars", type=int, default=150_000,
                   help="Máximo de caracteres por parte Markdown")
    p.add_argument("--max-file-bytes", type=int, default=2_000_000,
                   help="Máximo de bytes por archivo")
    p.add_argument("--incluir-todo", action="store_true",
                   help="Incluir todos los archivos de texto, sin filtrar por extensión")
    p.add_argument("--ext", nargs="*", default=[],
                   help="Extensiones extra a incluir, ej: .log .csv")
    return p.parse_args()


def main():
    args = parse_args()
    root = Path(args.root).resolve()
    outdir = Path(args.out).resolve()

    if not root.is_dir():
        print(f"Error: {root} no es un directorio", file=sys.stderr)
        sys.exit(1)

    outdir.mkdir(parents=True, exist_ok=True)

    incluir_ext = set(INCLUIR_EXT_DEFAULT)
    for e in args.ext:
        if not e.startswith("."):
            e = "." + e
        incluir_ext.add(e.lower())

    exp = Exportador(root, outdir, args.max_chars)
    omitidos = []

    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirpath_p = Path(dirpath)

        dirnames[:] = sorted([
            d for d in dirnames
            if not (dirpath_p / d).is_symlink()
            and d not in EXCLUIR_DIRS
            and (dirpath_p / d).resolve() != outdir
        ])

        for filename in sorted(filenames):
            p = dirpath_p / filename

            if p.is_symlink():
                continue

            rel = str(p.relative_to(root))

            if filename in EXCLUIR_NOMBRES:
                omitidos.append((rel, "excluido por nombre"))
                continue

            if filename.startswith(".env") and filename != ".env.example":
                omitidos.append((rel, "excluido por posible secreto .env"))
                continue

            ext = p.suffix.lower()

            if ext in EXCLUIR_EXT:
                omitidos.append((rel, f"excluido por extensión {ext}"))
                continue

            if not args.incluir_todo:
                if ext not in incluir_ext and filename not in INCLUIR_NOMBRES_DEFAULT:
                    omitidos.append((rel, f"no incluido por filtro ({ext or 'sin ext'})"))
                    continue

            content, err, size = leer_archivo_texto(p, args.max_file_bytes)
            if err:
                omitidos.append((rel, err))
                continue

            exp.add(rel, content, size)

    exp.close()

    omitidos_path = outdir / "00_OMITIDOS.txt"
    with omitidos_path.open("w", encoding="utf-8") as f:
        f.write(f"Archivos omitidos: {len(omitidos)}\n\n")
        for rel, motivo in omitidos:
            f.write(f"{rel}\t{motivo}\n")

    print(f"Listo. Archivos exportados: {len(exp.files)}")
    print(f"Salida: {outdir}")
    print("Partes Markdown: contexto_llm_*.md")
    print(f"JSONL: {exp.jsonl_path.name}")
    print("Índice: 00_INDICE.txt")
    print("Omitidos: 00_OMITIDOS.txt")


if __name__ == "__main__":
    main()


--- ARCHIVO: ProyectoGrado/.gitignore ---
# Documentos de grado generados
docs/TFGdocsLatex/
*.docx
!requirements.txt
postgrest
postgrest.conf



--- ARCHIVO: ProyectoGrado/docker-compose.yml ---
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: corpocmente_qdrant
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - ./qdrant_storage:/qdrant/storage
    restart: unless-stopped



--- ARCHIVO: ProyectoGrado/codigo_fuente/backend/.env.example ---
# Archivo de variables de entorno locales (.env.example)
# Plantilla base para el desarrollo local del backend

GEMINI_API_KEY="AIzaSy..."
POSTGREST_JWT_SECRET="tu_secreto_super_seguro_aqui"

QDRANT_HOST="localhost"
QDRANT_PORT=6333
QDRANT_COLLECTION="vectores_poses_jiujitsu"

POSTGREST_URL="http://localhost:3001"
REDIS_URL="redis://localhost:6379/0"

# Trabajador Remoto de Inteligencia Artificial
COLAB_TUNNEL_URL="https://xxxx-xx-xx-xx-xx.ngrok-free.app"
NGROK_AUTH_TOKEN="tu_token_ngrok_aqui"

# CORS — orígenes permitidos separados por coma
ALLOWED_ORIGINS="http://localhost:5173,http://localhost:3000,http://localhost:4173"

# Worker Service Token (shared secret entre backend y Colab Worker)
WORKER_SERVICE_TOKEN="cambia_este_token_en_produccion"

# JWT — firma de tokens de usuario (mínimo 32 caracteres en producción)
JWT_SECRET_KEY="cambia_este_secreto_en_produccion_min_32_chars"
JWT_ALGORITHM="HS256"
JWT_EXPIRATION_HOURS=24



--- ARCHIVO: ProyectoGrado/codigo_fuente/backend/.gitignore ---
# Entornos virtuales
venv/
env/
.venv/

# Variables de entorno
.env

# Archivos compilados Python
__pycache__/
*.pyc
*.pyo
*.pyd

# Testing
.pytest_cache/
.coverage
htmlcov/



--- ARCHIVO: ProyectoGrado/codigo_fuente/backend/postgrest.conf ---
db-uri = "postgres://postgres:postgres@localhost:5432/corpocmente"
db-schema = "public"
db-anon-role = "anon"
server-port = 3001



--- ARCHIVO: ProyectoGrado/codigo_fuente/backend/pytest.ini ---
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto



--- ARCHIVO: ProyectoGrado/codigo_fuente/backend/requirements.txt ---
fastapi==0.115.0
pydantic==2.9.2
pydantic-settings==2.5.2
google-genai==0.2.1
qdrant-client==1.11.3
pytest==8.3.3
pytest-asyncio==0.24.0
python-multipart==0.0.12
ultralytics==8.1.0
opencv-python-headless==4.9.0.80
PyJWT==2.9.0
psycopg2-binary==2.9.13
requests==2.34.2



--- ARCHIVO: ProyectoGrado/codigo_fuente/backend/corpocmente/__init__.py ---



--- ARCHIVO: ProyectoGrado/codigo_fuente/backend/corpocmente/config.py ---
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator

class Settings(BaseSettings):
    # App Settings
    APP_NAME: str = "Corpo e Mente Biomechanics AI"
    ENVIRONMENT: str = "development"
    
    # Gemini API
    GEMINI_API_KEY: str = ""
    
    # Qdrant DB
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION: str = "vectores_poses_jiujitsu"
    
    # Colab Worker Tunnel URL
    COLAB_TUNNEL_URL: str = ""
    
    # PostgreSQL / PostgREST
    POSTGREST_URL: str = "http://localhost:3000"
    POSTGREST_JWT_SECRET: str = ""
    
    # Redis / Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # CORS — lista separada por comas de orígenes permitidos
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://localhost:4173"
    
    # Worker Service Token (para autenticar al Colab Worker)
    WORKER_SERVICE_TOKEN: str = "dev_worker_token_change_in_prod"
    
    # JWT para autenticación de usuarios
    JWT_SECRET_KEY: str = "dev_jwt_secret_change_in_prod_min_32_chars_long"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @field_validator("GEMINI_API_KEY", "POSTGREST_JWT_SECRET")
    @classmethod
    def check_not_empty(cls, v: str, info):
        if not v or v.strip() == "":
            raise ValueError(f"La variable de entorno {info.field_name} no puede estar vacía.")
        return v

settings = Settings()



--- ARCHIVO: ProyectoGrado/codigo_fuente/backend/corpocmente/main.py ---
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from corpocmente.config import settings
from corpocmente.ui.api.routes import router as evaluaciones_router
from corpocmente.ui.api.auth_routes import router as auth_router
from corpocmente.ui.api.tecnicas_routes import router as tecnicas_router

app = FastAPI(
    title=settings.APP_NAME,
    description="API RESTful Backend para la plataforma Corpo e Mente (Análisis Biomecánico con IA)",
    version="1.0.0"
)

# Configuración de CORS para permitir peticiones desde la aplicación Web / Frontend
allowed_origins = [
    origin.strip()
    for origin in settings.ALLOWED_ORIGINS.split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# Montar carpeta pública para videos de referencia
import os
from fastapi.staticfiles import StaticFiles

UPLOAD_DIR = "/tmp/corpocmente_videos"
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/static/videos", StaticFiles(directory=UPLOAD_DIR), name="videos")

# Registrar rutas del dominio
app.include_router(evaluaciones_router)
app.include_router(auth_router)
app.include_router(tecnicas_router)

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "app": settings.APP_NAME, "environment": settings.ENVIRONMENT}



--- ARCHIVO: ProyectoGrado/codigo_fuente/backend/corpocmente/application/__init__.py ---
"""Application Layer - Corpo e Mente."""



--- ARCHIVO: ProyectoGrado/codigo_fuente/backend/corpocmente/application/dtos/__init__.py ---
"""Application DTOs."""



--- ARCHIVO: ProyectoGrado/codigo_fuente/backend/corpocmente/application/dtos/knowledge_dtos.py ---
from pydantic import BaseModel

class IngestionRequest(BaseModel):
    """DTO de entrada para la ingestión de teoría RAG."""
    tecnica_id: str
    contenido_texto: str

class IngestionResponse(BaseModel):
    """DTO de salida para la respuesta de ingestión."""
    status: str
    chunks_procesados: int



--- ARCHIVO: ProyectoGrado/codigo_fuente/backend/corpocmente/application/use_cases/__init__.py ---
"""Application Use Cases."""



--- ARCHIVO: ProyectoGrado/codigo_fuente/backend/corpocmente/application/use_cases/delete_theory_use_case.py ---
import logging
from typing import Dict
from fastapi import HTTPException
from corpocmente.infrastructure.persistence.postgrest_client import PostgrestClient
from corpocmente.infrastructure.persistence.qdrant_rag_adapter import QdrantRAGAdapter

logger = logging.getLogger(__name__)


class DeleteTheoryUseCase:
    """
    Caso de Uso: Eliminar toda la teoría que un profesor subió para una técnica.

    Orquesta:
    1. Obtener los qdrant_point_ids asociados (vía RPC que hace SELECT + DELETE en Postgres).
    2. Borrar los puntos correspondientes en Qdrant.
    """

    def __init__(self):
        self.db = PostgrestClient()
        self.qdrant_rag = QdrantRAGAdapter()

    def execute(self, tecnica_id: str, profesor_id: str) -> Dict:
        logger.info(f"Eliminando teoría de técnica {tecnica_id} para profesor {profesor_id}")

        try:
            result = self.db.rpc("admin_delete_teoria_by_tecnica_profesor", {
                "p_tecnica_id": tecnica_id,
                "p_profesor_id": profesor_id,
            })
        except Exception as e:
            logger.error(f"Error eliminando metadata en Postgres: {e}")
            raise HTTPException(status_code=500, detail=f"Error eliminando teoría en Postgres: {str(e)}")

        # PostgREST devuelve [{"deleted_qdrant_ids": [...]}] o similar
        deleted_ids = []
        if result:
            if isinstance(result, list) and result:
                deleted_ids = result[0].get("deleted_qdrant_ids") or []
            elif isinstance(result, dict):
                deleted_ids = result.get("deleted_qdrant_ids") or []

        # Borrar en Qdrant (best-effort: si falla, loggeamos pero no rompemos la respuesta)
        qdrant_deleted = 0
        if deleted_ids:
            try:
                qdrant_deleted = self.qdrant_rag.eliminar_puntos(deleted_ids)
            except Exception as e:
                logger.error(f"Postgres OK pero falló borrado en Qdrant: {e}")

        return {
            "chunks_eliminados_postgres": len(deleted_ids),
            "chunks_eliminados_qdrant": qdrant_deleted,
        }



--- ARCHIVO: ProyectoGrado/codigo_fuente/backend/corpocmente/application/use_cases/ingest_knowledge_use_case.py ---
import logging
import requests
from fastapi import HTTPException
from corpocmente.infrastructure.persistence.qdrant_rag_adapter import QdrantRAGAdapter
from corpocmente.infrastructure.persistence.postgrest_client import PostgrestClient
from corpocmente.application.dtos.knowledge_dtos import IngestionResponse
from corpocmente.config import settings

logger = logging.getLogger(__name__)


class IngestKnowledgeUseCase:
    """
    Caso de Uso: Ingestión de material teórico (libros/manuales) al sistema RAG.

    Orquesta:
    1. Delegar la vectorización al Worker de Colab (Qwen3-VL-Embedding-2B).
    2. Persistir los chunks en Qdrant (búsqueda vectorial).
    3. Persistir la metadata de cada chunk en PostgreSQL (trazabilidad + CRUD).
    """

    def __init__(self, qdrant_rag_adapter: QdrantRAGAdapter = None):
        self.qdrant_rag = qdrant_rag_adapter or QdrantRAGAdapter()
        self.worker_url = settings.COLAB_TUNNEL_URL
        self.db = PostgrestClient()

    def execute(
        self,
        tecnica_id: str,
        contenido_texto: str,
        profesor_id: str = None,
        sucursal_id: str = None,
    ) -> IngestionResponse:
        logger.info(f"Iniciando ingestión RAG para técnica {tecnica_id}")

        if not self.worker_url or "placeholder" in self.worker_url:
            raise HTTPException(status_code=503, detail="COLAB_TUNNEL_URL no configurada.")

        try:
            response = requests.post(
                f"{self.worker_url.rstrip('/')}/embed_text",
                data={"texto": contenido_texto},
                timeout=120
            )
            response.raise_for_status()
            embed_data = response.json()

            # 1. Persistir en Qdrant
            qdrant_result = self.qdrant_rag.ingestar_desde_respuesta(embed_data, tecnica_id)
            point_ids = qdrant_result["point_ids"]
            chunks = qdrant_result["chunks"]

            # 2. Persistir metadata en PostgreSQL (si tenemos profesor/sucursal)
            if profesor_id and sucursal_id:
                for i, (chunk, pid) in enumerate(zip(chunks, point_ids)):
                    try:
                        self.db.rpc("admin_save_teoria_chunk", {
                            "p_tecnica_id": tecnica_id,
                            "p_profesor_id": profesor_id,
                            "p_sucursal_id": sucursal_id,
                            "p_chunk_index": i,
                            "p_contenido_texto": chunk,
                            "p_qdrant_point_id": pid,
                        })
                    except Exception as e:
                        logger.warning(f"No se pudo registrar chunk {i} en Postgres: {e}")

            return IngestionResponse(
                status="success",
                chunks_procesados=len(chunks)
            )

        except requests.exceptions.RequestException as e:
            logger.error(f"Error comunicando con Colab: {e}")
            raise HTTPException(status_code=503, detail=f"Worker de Colab no disponible: {str(e)}")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error en ingestión RAG: {e}")
            raise HTTPException(status_code=500, detail=f"Error interno en ingestión: {str(e)}")



--- ARCHIVO: ProyectoGrado/codigo_fuente/backend/corpocmente/application/use_cases/list_theory_use_case.py ---
import logging
from typing import List, Dict
from corpocmente.infrastructure.persistence.postgrest_client import PostgrestClient

logger = logging.getLogger(__name__)


class ListTheoryUseCase:
    """
    Caso de Uso: Listar chunks de teoría de una técnica.

    El profesor usa esto para ver qué subió. Devuelve metadata + preview del texto.
    """

    def __init__(self):
        self.db = PostgrestClient()

    def execute(self, tecnica_id: str, profesor_id: str = None) -> List[Dict]:
        """
        Lista chunks de teoría de una técnica.
        Si profesor_id viene, filtra solo los del profesor (vista "mis aportes").
        Si no, devuelve todos los aportes de la técnica (vista "material de la técnica").
        """
        logger.info(f"Listando teoría para técnica {tecnica_id} (filtro profesor: {profesor_id})")

        try:
            chunks = self.db.rpc("admin_list_teoria_by_tecnica", {
                "p_tecnica_id": tecnica_id
            })
        except Exception as e:
            logger.error(f"Error consultando teoría en Postgres: {e}")
            return []

        if not chunks:
            return []

        if profesor_id:
            chunks = [c for c in chunks if str(c.get("profesor_id")) == str(profesor_id)]

        return chunks



--- ARCHIVO: ProyectoGrado/codigo_fuente/backend/corpocmente/domain/__init__.py ---



--- ARCHIVO: ProyectoGrado/codigo_fuente/backend/corpocmente/domain/entities/__init__.py ---



--- ARCHIVO: ProyectoGrado/codigo_fuente/backend/corpocmente/domain/entities/models.py ---
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from uuid import UUID

class EsqueletoBiomecanico(BaseModel):
    frame_idx: int = 0
    keypoints133: List[float] = Field(..., min_length=133, max_length=133)
    angulos_articulares: Dict[str, float] = Field(default_factory=dict)
    
    def calcular_angulo_articular(self, articulacion_a: str, articulacion_b: str) -> float:
        pass
        
    def to_vector_array(self) -> List[float]:
        """
        Retorna el vector crudo de 133 dims para comparación por similitud coseno
        contra la colección Qdrant `vectores_poses_jiujitsu` (size=133).
        """
        return list(self.keypoints133)

class Evaluacion(BaseModel):
    id: UUID
    alumno_id: UUID
    tecnica_id: UUID
    porcentaje_similitud: Optional[float] = None
    feedback_gemini_es: Optional[str] = None
    feedback_gemini_pt: Optional[str] = None
    estado: str = "procesando"
    
    def actualizar_resultado(self, similitud: float, feedback_es: str, feedback_pt: str) -> None:
        pass
        
    def marcar_estado(self, nuevo_estado: str) -> None:
        pass

class AnalisisResultDTO(BaseModel):
    similitud: float
    feedback: str



--- ARCHIVO: ProyectoGrado/codigo_fuente/backend/corpocmente/domain/services/__init__.py ---



--- ARCHIVO: ProyectoGrado/codigo_fuente/backend/corpocmente/domain/services/intelligence_facade.py ---
import logging
from corpocmente.domain.entities.models import AnalisisResultDTO
from corpocmente.infrastructure.ai.adapters import YOLOPoseAdapter, GeminiApiAdapter
from corpocmente.infrastructure.ai.qwen_adapter import QwenEmbeddingAdapter
from corpocmente.infrastructure.persistence.qdrant_adapter import QdrantVectorAdapter
from corpocmente.domain.strategies.prompt_strategies import SpanishPromptStrategy
from uuid import UUID

logger = logging.getLogger(__name__)

class IntelligenceAnalysisFacade:
    def __init__(self, 
                 yolo_adapter: YOLOPoseAdapter, 
                 qdrant_adapter: QdrantVectorAdapter, 
                 gemini_adapter: GeminiApiAdapter,
                 qwen_adapter: QwenEmbeddingAdapter = None):
        self.yolo = yolo_adapter
        self.qdrant = qdrant_adapter
        self.gemini = gemini_adapter
        self.qwen = qwen_adapter

    def ejecutar_analisis_completo(self, video_path: str, tecnica_id: UUID, tecnica_nombre: str) -> AnalisisResultDTO:
        # 1. Extraer esqueleto con YOLO (frame a frame)
        esqueletos_frames = self.yolo.extraer_keypoints(video_path)
        if not esqueletos_frames:
            raise ValueError("No se pudo detectar el esqueleto biomecánico.")

        # 2. Buscar similitud matemática del fotograma con mayor diferencia (en Qdrant)
        resultado_comparacion = self.qdrant.buscar_maxima_diferencia(esqueletos_frames, tecnica_id)
        
        similitud = resultado_comparacion.score
        UMBRAL_ACEPTABLE = 85.0  # escala 0–100 (score ya viene multiplicado ×100)

        # 3. Lógica Condicional para evitar invocar a la IA si está bien
        if similitud >= UMBRAL_ACEPTABLE:
            feedback_texto = "¡Técnica ejecutada correctamente. Excelente trabajo!"
        else:
            # 4. Dibujar/Resaltar el error en el fotograma crítico usando YOLO
            frame_resaltado = self.yolo.dibujar_error_en_frame(
                resultado_comparacion.frame_path, 
                resultado_comparacion.discrepancias
            )

            # 5. Recuperar teoría RAG desde Qdrant usando una query textual (C11.4)
            # Se construye una query con el nombre de la técnica + las discrepancias detectadas,
            # se vectoriza con Qwen (endpoint /embed_text) y se buscan los chunks más similares.
            contexto_profundo = ""
            if self.qwen:
                try:
                    discrepancias_str = "; ".join(resultado_comparacion.discrepancias) if resultado_comparacion.discrepancias else "sin detalles específicos"
                    query_textual = (
                        f"Técnica de Jiu-Jitsu: {tecnica_nombre}. "
                        f"Errores biomecánicos detectados: {discrepancias_str}. "
                        f"¿Cuál es la forma correcta de ejecutar esta técnica y cómo corregir estos errores?"
                    )
                    logger.info(f"Construyendo query textual para RAG: {query_textual[:120]}...")
                    
                    embedding_qwen = self.qwen.generar_embedding_texto(query_textual)
                    teoria = self.qdrant.recuperar_contexto_rag(embedding_qwen, tecnica_id)
                    
                    if teoria:
                        contexto_profundo = f"\n\n[Teoría Biomecánica Recuperada (RAG)]:\n{teoria}"
                        logger.info(f"Contexto RAG recuperado: {len(teoria)} caracteres.")
                    else:
                        logger.info("Sin teoría RAG adicional para esta técnica.")
                except Exception as e:
                    logger.warning(f"Fallo en recuperación RAG (no bloqueante): {e}")

            # 6. Usar estrategia de idioma en español y pasar contexto de la técnica
            strategy = SpanishPromptStrategy()
                
            prompt = strategy.construir_prompt_evaluacion(tecnica_nombre, resultado_comparacion.discrepancias)
            if contexto_profundo:
                prompt += contexto_profundo

            # 6. Generar feedback pedagógico con Gemini API usando el frame dibujado
            feedback_texto = self.gemini.generar_texto_feedback(prompt, frame_resaltado)

        return AnalisisResultDTO(
            similitud=similitud,
            feedback=feedback_texto
        )



--- ARCHIVO: ProyectoGrado/codigo_fuente/backend/corpocmente/domain/strategies/__init__.py ---



--- ARCHIVO: ProyectoGrado/codigo_fuente/backend/corpocmente/domain/strategies/prompt_strategies.py ---
from abc import ABC, abstractmethod
from typing import List

class IPromptStrategy(ABC):
    @abstractmethod
    def construir_prompt_evaluacion(self, tecnica_nombre: str, discrepancias: List[str]) -> str:
        """Construye el prompt en el idioma correspondiente."""
        pass

class SpanishPromptStrategy(IPromptStrategy):
    def construir_prompt_evaluacion(self, tecnica_nombre: str, discrepancias: List[str]) -> str:
        prompt = (
            f"Eres un maestro cinturón negro de Jiu-Jitsu Brasileño. "
            f"La técnica evaluada es: {tecnica_nombre}. "
            f"La imagen adjunta es EL FOTOGRAMA CRÍTICO donde el alumno cometió el mayor error biomecánico. "
            f"Los errores detectados por análisis de pose son:\n"
        )
        for d in discrepancias:
            prompt += f"- {d}\n"
        prompt += (
            "Analiza visualmente la imagen y proporciona instrucciones correctivas claras, "
            "específicas y accionables en español. Menciona qué articulación ajustar y hacia dónde."
        )
        return prompt



--- ARCHIVO: ProyectoGrado/codigo_fuente/backend/corpocmente/infrastructure/__init__.py ---



--- ARCHIVO: ProyectoGrado/codigo_fuente/backend/corpocmente/infrastructure/ai/__init__.py ---



--- ARCHIVO: ProyectoGrado/codigo_fuente/backend/corpocmente/infrastructure/ai/adapters.py ---
from typing import List, Optional
import os
import logging
from google import genai
from google.genai import types
from google.genai.errors import APIError

from corpocmente.domain.entities.models import EsqueletoBiomecanico

logger = logging.getLogger(__name__)

class GeminiRateLimitError(Exception):
    """Excepción lanzada cuando se supera el límite de cuota (Rate Limit 429) de Gemini API."""
    pass

class YOLOPoseAdapter:
    def __init__(self, colab_url: str = None):
        self.colab_url = colab_url if colab_url is not None else os.getenv("COLAB_TUNNEL_URL", "").strip()

    def extraer_keypoints(self, video_path: str) -> List[EsqueletoBiomecanico]:
        """Extrae el esqueleto biomecánico de los frames del video usando YOLO (Colab remoto)."""
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video no encontrado: {video_path}")
            
        if not self.colab_url or self.colab_url.startswith("https://placeholder"):
            logger.info("YOLOv26 (Colab) no configurado. Usando fallback local determinista.")
            return [EsqueletoBiomecanico(keypoints133=[0.5]*133, angulos_articulares={})]
            
        import requests
        try:
            endpoint = f"{self.colab_url.rstrip('/')}/extraer_poses"
            with open(video_path, 'rb') as f:
                resp = requests.post(endpoint, files={"video": f}, timeout=120)
            resp.raise_for_status()
            
            data = resp.json()
            esqueletos_dict = data.get("esqueletos", [])
            
            esqueletos = []
            for item in esqueletos_dict:
                esqueletos.append(EsqueletoBiomecanico(**item))
                
            return esqueletos
        except Exception as e:
            logger.error(f"Error llamando a YOLOv26 en Colab: {e}")
            return [EsqueletoBiomecanico(keypoints133=[0.5]*133, angulos_articulares={})]

    def dibujar_error_en_frame(self, frame_path: str, discrepancias: List[str]) -> str:
        """
        Utiliza YOLOv26 en Colab para dibujar la discrepancia sobre la imagen.
        Retorna la ruta temporal de la imagen modificada.
        """
        if not os.path.exists(frame_path):
            return frame_path
            
        if not self.colab_url or self.colab_url.startswith("https://placeholder"):
            return frame_path
            
        import requests
        import uuid
        try:
            endpoint = f"{self.colab_url.rstrip('/')}/dibujar_error"
            with open(frame_path, 'rb') as f:
                resp = requests.post(endpoint, files={"imagen": f}, data={"discrepancias": str(discrepancias)}, timeout=60)
            resp.raise_for_status()
            
            resaltado_path = f"/tmp/resaltado_{uuid.uuid4().hex[:8]}.jpg"
            with open(resaltado_path, "wb") as f:
                f.write(resp.content)
            return resaltado_path
        except Exception as e:
            logger.error(f"Error pidiendo a YOLOv26 dibujar el error: {e}")
            return frame_path

from corpocmente.config import settings

class GeminiApiAdapter:
    """
    Adaptador (GoF Adapter) para encapsular las llamadas a la API de Google Gemini
    utilizando el SDK oficial google-genai.
    
    Aísla al dominio de los detalles de red, autenticación y manejo de tokens.
    """
    
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-2.5-flash-lite"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or settings.GEMINI_API_KEY
        if not self.api_key:
            raise ValueError("Se requiere una API Key válida para instanciar GeminiApiAdapter.")
        
        self.model_name = model_name
        self.client = genai.Client(api_key=self.api_key)

    def validar_es_jiujitsu(self, video_path: str) -> bool:
        """
        Valida mediante visión multimodal de Gemini si el video corresponde a una técnica de Jiu-Jitsu.
        Resuelve el paso 2 del Flujo Principal y el Flujo Alternativo 2a (Prevención de SPAM).
        """
        if not os.path.exists(video_path):
            logger.error(f"El archivo de video no existe en la ruta: {video_path}")
            return False

        prompt_validacion = (
            "Analiza brevemente este video. ¿El contenido muestra a personas practicando o ejecutando "
            "una técnica, movimiento o lucha de Jiu-Jitsu Brasileño (BJJ) o Artes Marciales Grappling? "
            "Responde estrictamente con la palabra 'SI' o 'NO'."
        )

        try:
            # Cargar el archivo utilizando la Files API de Gemini para procesamiento multimodal
            video_file = self.client.files.upload(path=video_path)
            
            # Si el video está en estado PROCESSING, esperar a que pase a ACTIVE
            import time
            while video_file.state == "PROCESSING":
                time.sleep(1)
                video_file = self.client.files.get(name=video_file.name)

            if video_file.state == "FAILED":
                logger.error("El archivo de video falló en el procesamiento de Gemini.")
                return False

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[video_file, prompt_validacion]
            )
            
            # Limpieza del archivo temporal en la nube de Google
            try:
                self.client.files.delete(name=video_file.name)
            except Exception as del_err:
                logger.warning(f"No se pudo eliminar el archivo temporal de Gemini: {del_err}")
            
            resultado = response.text.strip().upper() if response.text else "NO"
            return "SI" in resultado or "SÍ" in resultado

        except APIError as e:
            if getattr(e, "code", None) == 429 or "RESOURCE_EXHAUSTED" in str(e):
                logger.warning("Límite de cuota superado en la API de Gemini durante la validación.")
                raise GeminiRateLimitError("Cuota de Gemini API agotada (429).") from e
            logger.error(f"Error de API al validar video con Gemini: {e}")
            return False
        except Exception as e:
            logger.error(f"Error inesperado en validar_es_jiujitsu: {e}")
            return False

    def generar_texto_feedback(self, prompt: str, frame_image_path: str) -> str:
        """
        Genera la evaluación cualitativa estructurada en el idioma seleccionado (ES/PT)
        enviando el prompt de la estrategia y la imagen del fotograma con la discrepancia clave.
        """
        if not os.path.exists(frame_image_path):
            raise FileNotFoundError(f"Fotograma de análisis no encontrado en: {frame_image_path}")

        try:
            # Cargar el fotograma estático (JPG/PNG) para la inspección visual de Gemini
            image_file = self.client.files.upload(path=frame_image_path)

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[image_file, prompt],
                config=types.GenerateContentConfig(
                    temperature=0.2, # Baja temperatura para respuestas consistentes y técnicas
                    max_output_tokens=800
                )
            )

            # Limpiar la imagen subida
            self.client.files.delete(name=image_file.name)

            if response.text:
                return response.text.strip()
            else:
                raise ValueError("Gemini API retornó una respuesta vacía.")

        except APIError as e:
            if getattr(e, "code", None) == 429 or "RESOURCE_EXHAUSTED" in str(e):
                logger.warning("Límite de cuota (429) alcanzado al generar feedback.")
                raise GeminiRateLimitError("Límite de velocidad/cuota excedido en Gemini API.") from e
            logger.error(f"Error en llamada a Gemini API: {e}")
            raise e





--- ARCHIVO: ProyectoGrado/codigo_fuente/backend/corpocmente/infrastructure/ai/qwen_adapter.py ---
import os
import requests
from typing import List
import logging

logger = logging.getLogger(__name__)

class QwenEmbeddingAdapter:
    """Adaptador para Qwen3-VL-Embedding-2B (Google Colab Remoto / Fallback Local)."""

    def __init__(self, colab_url: str = None):
        self._dim = 2048
        self.colab_url = colab_url if colab_url is not None else os.getenv("COLAB_TUNNEL_URL", "").strip()

    def generar_embedding(self, image_path: str) -> List[float]:
        """
        DEPRECATED (C11.4): Este método apunta al endpoint `/embed` que no existe
        en el Worker de Colab actual (solo existe `/embed_text`).
        
        El pipeline RAG actual usa `generar_embedding_texto` con una query textual
        construida a partir del nombre de la técnica + discrepancias detectadas.
        
        Se mantiene por compatibilidad con tests existentes. NO USAR en código nuevo.
        """
        logger.warning(
            "QwenEmbeddingAdapter.generar_embedding (imagen) está DEPRECATED. "
            "Usar generar_embedding_texto en su lugar."
        )
        if not self.colab_url or self.colab_url.startswith("https://placeholder"):
            logger.info("Usando fallback de Qwen: vector determinista 2048-dim.")
            return [0.05] * self._dim

        # Invocación remota al Worker de Colab
        try:
            endpoint = f"{self.colab_url.rstrip('/')}/embed"
            
            # Asumiendo que enviamos la imagen en base64 o como multipart
            # Por simplicidad en la arquitectura actual del worker, enviaremos la ruta local
            # o se simula si es un POST a /embed
            # (en un entorno distribuido real subiríamos el bytearray)
            resp = requests.post(endpoint, json={"image_path": image_path}, timeout=60)
            resp.raise_for_status()
            
            data = resp.json()
            vectores = data.get("embeddings", [])
            
            if vectores and len(vectores[0]) == self._dim:
                return vectores[0]
            else:
                logger.warning("Colab Qwen retornó dimensiones inesperadas.")
                return [0.05] * self._dim
                
        except Exception as e:
            logger.error(f"Error llamando a Qwen en Colab: {e}")
            return [0.05] * self._dim

    def generar_embedding_texto(self, texto: str) -> List[float]:
        """Genera un embedding de texto de 2048 dimensiones para la teoría (RAG)."""
        if not self.colab_url or self.colab_url.startswith("https://placeholder"):
            logger.info("Usando fallback de Qwen texto: vector determinista 2048-dim.")
            return [0.07] * self._dim

        try:
            endpoint = f"{self.colab_url.rstrip('/')}/embed_text"
            resp = requests.post(endpoint, data={"texto": texto}, timeout=60)
            resp.raise_for_status()
            
            data = resp.json()
            vectores = data.get("embeddings", [])
            
            if vectores and len(vectores[0]) == self._dim:
                return vectores[0]
            else:
                logger.warning("Colab Qwen retornó dimensiones inesperadas para texto.")
                return [0.07] * self._dim
                
        except Exception as e:
            logger.error(f"Error llamando a Qwen texto en Colab: {e}")
            return [0.07] * self._dim



--- ARCHIVO: ProyectoGrado/codigo_fuente/backend/corpocmente/infrastructure/persistence/__init__.py ---



--- ARCHIVO: ProyectoGrado/codigo_fuente/backend/corpocmente/infrastructure/persistence/postgrest_client.py ---
import os
import requests

class PostgrestClient:
    def __init__(self, base_url: str = None):
        self.base_url = base_url or os.getenv("POSTGREST_URL", "http://localhost:3001")

    def get(self, table: str, params: dict = None, token: str = None):
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        response = requests.get(f"{self.base_url}/{table}", params=params, headers=headers)
        response.raise_for_status()
        return response.json()

    def post(self, table: str, data: dict, token: str = None):
        headers = {"Prefer": "return=representation"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        response = requests.post(f"{self.base_url}/{table}", json=data, headers=headers)
        response.raise_for_status()
        return response.json()

    def patch(self, table: str, filters: dict, data: dict, token: str = None):
        """Actualiza filas que coincidan con los filtros. Retorna la representación actualizada."""
        headers = {"Prefer": "return=representation"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        params = {k: v for k, v in filters.items()}
        response = requests.patch(f"{self.base_url}/{table}", params=params, json=data, headers=headers)
        response.raise_for_status()
        return response.json()

    def delete(self, table: str, filters: dict, token: str = None):
        """Elimina filas que coincidan con los filtros. Retorna la representación eliminada."""
        headers = {"Prefer": "return=representation"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        params = {k: v for k, v in filters.items()}
        response = requests.delete(f"{self.base_url}/{table}", params=params, headers=headers)
        response.raise_for_status()
        return response.json()

    def rpc(self, function_name: str, params: dict, token: str = None):
        """Llama a una función almacenada de PostgreSQL vía el endpoint /rpc/ de PostgREST."""
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        response = requests.post(f"{self.base_url}/rpc/{function_name}", json=params, headers=headers)
        response.raise_for_status()
        return response.json()



--- ARCHIVO: ProyectoGrado/codigo_fuente/backend/corpocmente/infrastructure/persistence/qdrant_adapter.py ---
import logging
import numpy as np
from typing import List, Dict, Optional
from uuid import UUID
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue

from corpocmente.config import settings

logger = logging.getLogger(__name__)

class VectorSearchResultDTO:
    def __init__(self, score: float, frame_path: str, discrepancias: List[str]):
        self.score = score
        self.frame_path = frame_path
        self.discrepancias = discrepancias

class QdrantVectorAdapter:
    """
    Adaptador (GoF Adapter) para encapsular las búsquedas por similitud vectorial (HNSW + Coseno)
    en Qdrant DB, aislando el dominio del cliente nativo de Qdrant.
    """

    def __init__(self, 
                 host: Optional[str] = None, 
                 port: Optional[int] = None, 
                 collection_name: Optional[str] = None,
                 client: Optional[QdrantClient] = None):
        self.host = host or settings.QDRANT_HOST
        self.port = port or settings.QDRANT_PORT
        self.collection_name = collection_name or settings.QDRANT_COLLECTION
        self.rag_collection = "rag_knowledge"
        self._client = client

    @property
    def client(self) -> QdrantClient:
        if self._client is None:
            self._client = QdrantClient(host=self.host, port=self.port)
        return self._client

    def asegurar_coleccion(self, vector_size: int = 133) -> None:
        """Crea la colección en Qdrant con métrica de Coseno si no existe previamente."""
        collections = [c.name for c in self.client.get_collections().collections]
        if self.collection_name not in collections:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
            )
            logger.info(f"Colección Qdrant '{self.collection_name}' creada con dimensión {vector_size}.")

    def insertar_vector(self, vector_id: UUID, vector: List[float], payload: Dict) -> None:
        """Inserta o actualiza un vector biomecánico con sus metadatos (payload)."""
        point = PointStruct(
            id=str(vector_id),
            vector=vector,
            payload=payload
        )
        self.client.upsert(
            collection_name=self.collection_name,
            points=[point]
        )

    def buscar_similitud_pose(self, vector_alumno: List[float], tecnica_id: UUID) -> VectorSearchResultDTO:
        """
        Busca el fotograma de referencia más similar en Qdrant filtrando por la técnica.
        Retorna el score de similitud, la ruta de la imagen patrón y sus discrepancias técnicas.
        """
        filtro_tecnica = Filter(
            must=[
                FieldCondition(
                    key="tecnica_id",
                    match=MatchValue(value=str(tecnica_id))
                )
            ]
        )

        resultados = self.client.search(
            collection_name=self.collection_name,
            query_vector=vector_alumno,
            query_filter=filtro_tecnica,
            limit=1
        )

        if not resultados:
            raise ValueError(f"No se encontraron vectores de referencia para la técnica ID {tecnica_id}")

        mejor_coincidencia = resultados[0]
        payload = mejor_coincidencia.payload or {}

        # Mapeo a DTO desacoplado
        return VectorSearchResultDTO(
            score=round(float(mejor_coincidencia.score) * 100, 2),  # Porcentaje de similitud
            frame_path=payload.get("frame_path", ""),
            discrepancias=payload.get("discrepancias", [])
        )

    def buscar_maxima_diferencia(
        self,
        esqueletos_alumno: List['EsqueletoBiomecanico'],
        tecnica_id: UUID
    ) -> VectorSearchResultDTO:
        """
        Descarga UNA VEZ todos los vectores de referencia de la técnica desde Qdrant
        y compara cada frame del alumno contra ellos mediante similitud coseno local
        con numpy. Devuelve el par (frame alumno ↔ frame referencia) con MENOR
        similitud (peor ejecución) y su payload.
        """
        if not esqueletos_alumno:
            raise ValueError("La lista de esqueletos del alumno está vacía.")

        # 1. Descargar TODAS las referencias con scroll (no search)
        filtro = Filter(must=[
            FieldCondition(key="tecnica_id", match=MatchValue(value=str(tecnica_id)))
        ])
        referencias, _ = self.client.scroll(
            collection_name=self.collection_name,
            scroll_filter=filtro,
            limit=10000,
            with_vectors=True,
            with_payload=True,
        )
        if not referencias:
            raise ValueError(
                f"No hay vectores de referencia en Qdrant para la técnica {tecnica_id}. "
                f"Ejecutar scripts/ingest_reference_video.py primero."
            )

        ref_vectors = np.array([p.vector for p in referencias], dtype=np.float32)
        ref_norms = np.linalg.norm(ref_vectors, axis=1, keepdims=True) + 1e-9
        ref_normed = ref_vectors / ref_norms

        # 2. Iterar frames del alumno localmente
        peor_similitud = 1.0
        peor_payload = None
        peor_frame_alumno = None

        for idx, esqueleto in enumerate(esqueletos_alumno):
            vec = np.array(esqueleto.to_vector_array(), dtype=np.float32)
            vec_n = vec / (np.linalg.norm(vec) + 1e-9)
            sims = ref_normed @ vec_n                 # coseno contra todas las refs
            j = int(np.argmin(sims))
            if float(sims[j]) < peor_similitud:
                peor_similitud = float(sims[j])
                peor_frame_alumno = idx
                peor_payload = referencias[j].payload or {}

        logger.info(
            f"Peor frame alumno: #{peor_frame_alumno} (similitud coseno = {peor_similitud:.4f})"
        )

        return VectorSearchResultDTO(
            score=round(peor_similitud * 100, 2),      # escala 0–100
            frame_path=peor_payload.get("frame_path", ""),
            discrepancias=peor_payload.get("discrepancias", []),
        )

    def recuperar_contexto_rag(self, vector_multimodal: List[float], tecnica_id: UUID) -> str:
        """
        Busca en la colección RAG (vectores de 2048 dims generados por Qwen) la teoría
        de libros o manuales más relevante para la query textual del análisis.

        Retorna los top-3 chunks concatenados con separador '---' para dar contexto
        enriquecido a Gemini. Retorna cadena vacía si no hay resultados o si falla.
        """
        filtro = Filter(
            must=[
                FieldCondition(
                    key="tecnica_id",
                    match=MatchValue(value=str(tecnica_id))
                )
            ]
        )
        try:
            resultados = self.client.search(
                collection_name=self.rag_collection,
                query_vector=("dense", vector_multimodal),
                query_filter=filtro,
                limit=3
            )
            if not resultados:
                return ""
            
            chunks = []
            for r in resultados:
                if r.payload and r.payload.get("contenido_texto"):
                    chunks.append(r.payload["contenido_texto"])
            
            return "\n\n---\n\n".join(chunks)
        except Exception as e:
            logger.warning(f"No se pudo recuperar contexto RAG de Qdrant: {e}")
            return ""



--- ARCHIVO: ProyectoGrado/codigo_fuente/backend/corpocmente/infrastructure/persistence/qdrant_rag_adapter.py ---
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from typing import List, Dict, Any
import uuid
import json

class QdrantRAGAdapter:
    def __init__(self, host="localhost", port=6333):
        self.client = QdrantClient(host=host, port=port)
        self.collection_name = "rag_knowledge"
        self._asegurar_coleccion()

    def _asegurar_coleccion(self):
        collections = [c.name for c in self.client.get_collections().collections]
        if self.collection_name not in collections:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config={"dense": VectorParams(size=2048, distance=Distance.COSINE)}
            )

    def ingestar_desde_respuesta(self, data: dict, tecnica_id: str) -> dict:
        """
        Ingesta chunks + embeddings en Qdrant.
        Retorna dict con chunks_count y lista de point_ids generados.
        """
        chunks = data["chunks"]
        embeddings = data["embeddings"]
        puntos = []
        point_ids = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            pid = str(uuid.uuid4())
            point_ids.append(pid)
            puntos.append(PointStruct(
                id=pid,
                vector={"dense": embedding},
                payload={"tecnica_id": tecnica_id, "contenido_texto": chunk, "chunk_index": i}
            ))
        self.client.upsert(collection_name=self.collection_name, points=puntos)
        return {"chunks_count": len(puntos), "point_ids": point_ids, "chunks": chunks}

    def ingestar_desde_json(self, json_path: str, tecnica_id: str) -> int:
        """Compatibilidad para ingesta desde archivos JSON guardados localmente."""
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return self.ingestar_desde_respuesta(data, tecnica_id)

    def recuperar_contexto(self, query_embedding: list, tecnica_id: str, top_k: int = 3) -> list:
        filtro = Filter(must=[FieldCondition(key="tecnica_id", match=MatchValue(value=tecnica_id))])
        resultados = self.client.search(
            collection_name=self.collection_name,
            query_vector=("dense", query_embedding),
            query_filter=filtro,
            limit=top_k
        )
        return [r.payload["contenido_texto"] for r in resultados]

    def eliminar_puntos(self, point_ids: list) -> int:
        """
        Elimina puntos de la colección RAG por sus IDs.
        Retorna la cantidad de IDs solicitados para eliminar.
        """
        if not point_ids:
            return 0
        from qdrant_client.models import PointIdsList
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=PointIdsList(points=point_ids)
        )
        return len(point_ids)




--- ARCHIVO: ProyectoGrado/codigo_fuente/backend/corpocmente/infrastructure/queue/__init__.py ---



--- ARCHIVO: ProyectoGrado/codigo_fuente/backend/corpocmente/infrastructure/queue/worker.py ---
import os
import time
import logging
from uuid import UUID
import requests

from corpocmente.config import settings
from corpocmente.domain.services.intelligence_facade import IntelligenceAnalysisFacade
from corpocmente.infrastructure.ai.adapters import YOLOPoseAdapter, GeminiApiAdapter
from corpocmente.infrastructure.ai.qwen_adapter import QwenEmbeddingAdapter
from corpocmente.infrastructure.persistence.qdrant_adapter import QdrantVectorAdapter

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ColabGPUWorker")

class ColabAIWorker:
    """
    Worker Asíncrono de Inferencia Pesada diseñado para ejecutarse en Google Colab Pro.
    
    Orquesta los componentes de IA:
    1. YOLO (Pose 3D + Depth Estimation)
    2. Qdrant Vector DB (Búsqueda por similitud de 133 keypoints)
    3. Qwen3-VL-Reranker-2B (Re-ranking Multimodal RAG)
    4. Gemini API (Cerebro Pedagógico en ES/PT)
    """

    def __init__(self, poll_interval_seconds: int = 5):
        self.poll_interval = poll_interval_seconds
        
        logger.info("Inicializando Adaptadores e Interfaces de IA en el Worker...")
        self.yolo = YOLOPoseAdapter()
        self.qdrant = QdrantVectorAdapter()
        self.gemini = GeminiApiAdapter()
        self.qwen = QwenEmbeddingAdapter()
        
        self.facade = IntelligenceAnalysisFacade(
            yolo_adapter=self.yolo,
            qdrant_adapter=self.qdrant,
            gemini_adapter=self.gemini,
            qwen_adapter=self.qwen
        )

    def ejecutar_bucle_principal(self):
        """Escucha continuamente tareas pendientes y ejecuta la inferencia multimodal."""
        logger.info(f"Worker de IA (Colab Pro) iniciado. Escuchando backend en: {settings.POSTGREST_URL}")
        
        while True:
            try:
                # Simulación / Polling de tareas pendientes en estado 'procesando'
                # En un entorno con PostgREST o FastAPI, consulta la tabla de evaluaciones_alumnos.
                logger.debug("Comprobando tareas pendientes en cola...")
                time.sleep(self.poll_interval)
            except KeyboardInterrupt:
                logger.info("Worker detenido por el usuario.")
                break
            except Exception as e:
                logger.error(f"Error inesperado en el bucle del Worker: {e}")
                time.sleep(self.poll_interval)

if __name__ == "__main__":
    worker = ColabAIWorker()
    worker.ejecutar_bucle_principal()



--- ARCHIVO: ProyectoGrado/codigo_fuente/backend/corpocmente/ui/__init__.py ---



--- ARCHIVO: ProyectoGrado/codigo_fuente/backend/corpocmente/ui/api/__init__.py ---

