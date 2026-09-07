#!/bin/bash
echo "======================================================="
echo "  JiuJitsu Tesis - Setup Local (Arquitectura Edge-Colab)"
echo "======================================================="

# Crear entorno virtual si no existe
if [ ! -d ".venv" ]; then
    echo "🐍 Creando entorno virtual .venv..."
    python3 -m venv .venv
fi

source .venv/bin/activate

# Instalar dependencias
echo "📦 Instalando dependencias desde requirements.txt..."
pip install --upgrade pip
pip install -r requirements.txt

# Crear directorios canónicos locales
echo "📁 Inicializando estructura de directorios locales..."
mkdir -p uploads data Videos modelos resultados/fotogramas resultados/csv resultados/graficas

# Inicializar Base de Datos SQLite (Mannino)
echo "🗄️ Inicializando base de datos SQLite (data/bjj_analysis.db)..."
python3 -c "from src.infrastructure.repositories import SQLiteDB; SQLiteDB(); print('   ✅ Tablas SQLite verificadas e inicializadas.')"

echo ""
echo "======================================================="
echo "✅ Setup local completado exitosamente!"
echo "👉 Para activar el entorno: source .venv/bin/activate"
echo "👉 Para iniciar la UI: streamlit run src/ui/streamlit_app.py"
echo "======================================================="
