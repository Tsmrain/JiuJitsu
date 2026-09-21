"""Generador de diagramas PNG UML en Blanco y Negro para la documentación de Tesis UPSA."""
import os
import math
from PIL import Image, ImageDraw

def draw_arrow(draw, start, end, fill='#000000', width=2, arrow_length=12):
    draw.line([start, end], fill=fill, width=width)
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    if dx == 0 and dy == 0:
        return
    angle = math.atan2(dy, dx)
    x1 = end[0] - arrow_length * math.cos(angle - math.pi / 6)
    y1 = end[1] - arrow_length * math.sin(angle - math.pi / 6)
    x2 = end[0] - arrow_length * math.cos(angle + math.pi / 6)
    y2 = end[1] - arrow_length * math.sin(angle + math.pi / 6)
    draw.polygon([end, (x1, y1), (x2, y2)], fill=fill)

def draw_statechart():
    img = Image.new('RGB', (1200, 700), color='#ffffff')
    draw = ImageDraw.Draw(img)
    
    # Title
    draw.text((380, 25), "Diagrama de Estados — EvaluacionBiomecanica (Larman Cap. 29)", fill='#000000')
    
    # Initial state (black circle)
    draw.ellipse((20, 175, 45, 200), fill='#000000', outline='#000000')
    draw_arrow(draw, (45, 187), (80, 187), fill='#000000', width=2)
    
    # State boxes
    states = [
        ("Pendiente", (80, 150, 280, 230)),
        ("ValidandoBJJ", (430, 150, 630, 230)),
        ("ProcesandoYOLO", (780, 150, 1030, 230)),
        ("EvaluandoBio", (780, 360, 1030, 440)),
        ("GenerandoSintesis", (430, 360, 680, 440)),
        ("Completada", (80, 360, 280, 440)),
        ("Rechazada / Fallida", (430, 560, 680, 640)),
    ]
    
    # Final state (double circle)
    draw.ellipse((20, 385, 45, 410), fill='#ffffff', outline='#000000', width=2)
    draw.ellipse((26, 391, 39, 404), fill='#000000', outline='#000000')
    
    for name, box in states:
        draw.rectangle(box, outline='#000000', width=2, fill='#ffffff')
        draw.text((box[0] + 15, box[1] + 30), name, fill='#000000')
        
    # Transitions
    draw_arrow(draw, (280, 190), (430, 190), fill='#000000', width=2)
    draw.text((295, 165), "validarBJJ()", fill='#000000')
    
    draw_arrow(draw, (630, 190), (780, 190), fill='#000000', width=2)
    draw.text((645, 165), "[es_bjj == True]", fill='#000000')
    
    draw_arrow(draw, (905, 230), (905, 360), fill='#000000', width=2)
    draw.text((915, 280), "inferir_esqueleto_3d()", fill='#000000')
    
    draw_arrow(draw, (780, 400), (680, 400), fill='#000000', width=2)
    draw.text((690, 375), "evaluar_desviaciones()", fill='#000000')
    
    draw_arrow(draw, (430, 400), (280, 400), fill='#000000', width=2)
    draw.text((295, 375), "generar_consejo()", fill='#000000')
    
    draw_arrow(draw, (80, 400), (45, 400), fill='#000000', width=2)
    
    draw_arrow(draw, (530, 230), (530, 560), fill='#000000', width=2)
    draw.text((540, 280), "[error / no_bjj]", fill='#000000')
    
    os.makedirs("docs/Figuras", exist_ok=True)
    img.save("docs/Figuras/Statechart_Eval.png")
    print("[OK] Generado docs/Figuras/Statechart_Eval.png (Blanco y Negro)")


def draw_activity_diagram():
    img = Image.new('RGB', (1200, 820), color='#ffffff')
    draw = ImageDraw.Draw(img)
    
    # Header
    draw.text((340, 20), "Diagrama de Actividad — Flujo CU-02 Evaluacion Biomecanica (Larman Cap. 38)", fill='#000000')
    
    # Swimlanes
    lanes = [
        ("Alumno PWA", 40, 310),
        ("FastAPI Server", 330, 600),
        ("Worker & GPU Colab", 620, 890),
        ("RAG & Gemini / DB", 910, 1180)
    ]
    
    for title, x1, x2 in lanes:
        draw.rectangle((x1, 60, x2, 780), outline='#000000', width=2, fill='#ffffff')
        draw.rectangle((x1, 60, x2, 100), outline='#000000', width=2, fill='#f0f0f0')
        draw.text((x1 + 20, 72), title, fill='#000000')
        
    # Start Node
    draw.ellipse((165, 115, 185, 135), fill='#000000', outline='#000000')
    draw_arrow(draw, (175, 135), (175, 160), fill='#000000', width=2)
    
    # Action boxes
    draw.rectangle((65, 160, 285, 220), outline='#000000', width=2, fill='#ffffff')
    draw.text((75, 185), "1. Sube Video MP4", fill='#000000')
    
    draw.rectangle((355, 160, 575, 220), outline='#000000', width=2, fill='#ffffff')
    draw.text((365, 185), "2. Encola Tarea Async", fill='#000000')
    
    draw.rectangle((645, 260, 865, 320), outline='#000000', width=2, fill='#ffffff')
    draw.text((655, 285), "3. YOLO26x Pose 3D", fill='#000000')
    
    draw.rectangle((645, 380, 865, 440), outline='#000000', width=2, fill='#ffffff')
    draw.text((655, 405), "4. Calculadora Bio", fill='#000000')
    
    draw.rectangle((935, 500, 1155, 560), outline='#000000', width=2, fill='#ffffff')
    draw.text((945, 525), "5. RAG Qdrant + Gemini", fill='#000000')
    
    draw.rectangle((935, 620, 1155, 680), outline='#000000', width=2, fill='#ffffff')
    draw.text((945, 645), "6. Persiste JSONB BCNF", fill='#000000')
    
    draw.rectangle((65, 620, 285, 680), outline='#000000', width=2, fill='#ffffff')
    draw.text((75, 645), "7. Recibe Reporte PWA", fill='#000000')
    
    # Final Node
    draw.ellipse((165, 715, 185, 735), fill='#ffffff', outline='#000000', width=2)
    draw.ellipse((170, 720, 180, 730), fill='#000000', outline='#000000')
    
    # Arrows
    draw_arrow(draw, (285, 190), (355, 190), fill='#000000', width=2)
    
    draw.line([(465, 220), (465, 290)], fill='#000000', width=2)
    draw_arrow(draw, (465, 290), (645, 290), fill='#000000', width=2)
    
    draw_arrow(draw, (755, 320), (755, 380), fill='#000000', width=2)
    
    draw.line([(755, 440), (755, 530)], fill='#000000', width=2)
    draw_arrow(draw, (755, 530), (935, 530), fill='#000000', width=2)
    
    draw_arrow(draw, (1045, 560), (1045, 620), fill='#000000', width=2)
    
    draw_arrow(draw, (935, 650), (285, 650), fill='#000000', width=2)
    
    draw_arrow(draw, (175, 680), (175, 715), fill='#000000', width=2)
    
    img.save("docs/Figuras/Activity_CU02.png")
    print("[OK] Generado docs/Figuras/Activity_CU02.png (Blanco y Negro)")


def draw_datamodel():
    img = Image.new('RGB', (1200, 750), color='#ffffff')
    draw = ImageDraw.Draw(img)
    
    draw.text((380, 20), "Modelo de Datos Relacional (Larman Cap. 34)", fill='#000000')
    
    tables = [
        ("«Table» usuarios", (40, 90, 360, 290), [
            "+ id_usuario : varchar <<PK>>",
            "+ email : varchar",
            "+ password_hash : varchar",
            "+ rol : varchar",
            "+ fecha_creacion : timestamp"
        ]),
        ("«Table» profesores", (440, 90, 760, 290), [
            "+ id_profesor : varchar <<PK>>",
            "+ nombre : varchar",
            "+ email : varchar",
            "+ fecha_alta : timestamp"
        ]),
        ("«Table» tecnicas_patron", (840, 90, 1160, 310), [
            "+ id_tecnica : varchar <<PK>>",
            "+ nombre : varchar",
            "+ categoria : varchar",
            "+ descripcion : text",
            "+ id_profesor : varchar <<FK>>",
            "+ fecha_registro : timestamp"
        ]),
        ("«Table» fuentes_conocimiento", (230, 410, 600, 630), [
            "+ id_fuente : varchar <<PK>>",
            "+ titulo : varchar",
            "+ id_instructor : varchar <<FK>>",
            "+ contenido_fragmento : text",
            "+ fecha_indexacion : timestamp"
        ]),
        ("«Table» evaluaciones_alumno", (680, 410, 1080, 630), [
            "+ id_evaluacion : uuid <<PK>>",
            "+ id_alumno : varchar",
            "+ id_tecnica : varchar <<FK>>",
            "+ score_similitud : float",
            "+ reporte_json : jsonb",
            "+ fecha_evaluacion : timestamp"
        ]),
    ]
    
    for name, box, fields in tables:
        draw.rectangle(box, outline='#000000', width=2, fill='#ffffff')
        draw.rectangle((box[0], box[1], box[2], box[1] + 35), outline='#000000', width=2, fill='#f0f0f0')
        draw.text((box[0] + 15, box[1] + 8), name, fill='#000000')
        
        y = box[1] + 45
        for f in fields:
            draw.text((box[0] + 15, y), f, fill='#000000')
            y += 25
            
    # Relationships
    draw_arrow(draw, (760, 180), (840, 180), fill='#000000', width=2)
    draw.text((780, 155), "1..*", fill='#000000')
    
    draw_arrow(draw, (600, 290), (415, 410), fill='#000000', width=2)
    draw.text((505, 340), "1..*", fill='#000000')
    
    draw_arrow(draw, (980, 310), (880, 410), fill='#000000', width=2)
    draw.text((940, 350), "1..*", fill='#000000')
    
    img.save("docs/Figuras/DataModel.png")
    print("[OK] Generado docs/Figuras/DataModel.png (Blanco y Negro)")


if __name__ == "__main__":
    draw_statechart()
    draw_activity_diagram()
    draw_datamodel()
