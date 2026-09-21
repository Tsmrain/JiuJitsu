import pytest
import os

def test_ui_elementos_y_canvas():
    """
    Verifica estáticamente que los archivos index.html y app.js 
    tengan los elementos requeridos sin tener que ejecutar un browser real.
    """
    base_dir = "./frontend"
    index_path = os.path.join(base_dir, "index.html")
    app_path = os.path.join(base_dir, "app.js")
    
    with open(index_path, "r", encoding="utf-8") as f:
        html_content = f.read()
        
    with open(app_path, "r", encoding="utf-8") as f:
        js_content = f.read()

    # Verificar previsualizaciones en HTML
    assert "preview-video-profesor" in html_content, "Falta el tag de previsualizacion del profesor"
    assert "preview-video-alumno" in html_content, "Falta el tag de previsualizacion del alumno"
    
    # Verificar lógica en JS
    assert "fallaCritica" in js_content, "Falta la definicion de fallaCritica en app.js"
    assert "URL.createObjectURL" in js_content, "Falta el uso de URL.createObjectURL para las vistas previas"
