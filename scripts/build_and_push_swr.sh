#!/bin/bash
# ==============================================================================
# Script de Construcción y Publicación de Contenedor en Huawei Cloud SWR
# Proyecto: Corpo & Mente Bolivia - Análisis Biomecánico BJJ
# ==============================================================================
# 
# Requisitos previos:
# 1. Tener Docker instalado y corriendo.
# 2. Obtener un token de inicio de sesión temporal desde la consola de Huawei Cloud SWR:
#    (SWR Console -> My Images -> Upload Through Client -> Generate Login Command).
#
# Variables a configurar por el desarrollador / operador:
REGION="la-south-2"                                 # Región de Huawei Cloud (ej. la-south-2 Santiago, cn-north-4)
REGISTRY="swr.${REGION}.myhuaweicloud.com"          # Endpoint de registro SWR
ORGANIZACION="{tu-organizacion}"                     # Nombre de la organización creada en SWR
IMAGEN_NOMBRE="corpoemente-pipeline"                # Nombre de la imagen del repositorio
TAG="v1.0"                                          # Versión / Tag del artefacto

echo "======================================================================"
echo "🚀 SWR BUILD & PUSH: ${REGISTRY}/${ORGANIZACION}/${IMAGEN_NOMBRE}:${TAG}"
echo "======================================================================"

# 1. Login en Huawei Cloud SWR (Descomentar e ingresar credenciales / token)
# echo "[*] Iniciando sesión en Huawei Cloud SWR..."
# docker login -u ${REGION}@{usuario_o_ak} -p {token_temporal_swr} ${REGISTRY}

# 2. Construcción optimizada de la imagen Docker
echo "[*] Construyendo imagen de contenedor optimizada (UID 1003, PyTorch CPU-Only)..."
docker build -t ${REGISTRY}/${ORGANIZACION}/${IMAGEN_NOMBRE}:${TAG} .

if [ $? -ne 0 ]; then
    echo "❌ Error durante la construcción de la imagen Docker."
    exit 1
fi

echo "✅ Imagen construida exitosamente."

# 3. Push de la imagen al registro privado de Huawei Cloud SWR
# Descomentar una vez autenticado:
# echo "[*] Publicando imagen en Huawei Cloud SWR..."
# docker push ${REGISTRY}/${ORGANIZACION}/${IMAGEN_NOMBRE}:${TAG}
# 
# if [ $? -eq 0 ]; then
#     echo "✅ Imagen publicada con éxito en SWR: ${REGISTRY}/${ORGANIZACION}/${IMAGEN_NOMBRE}:${TAG}"
# else
#     echo "❌ Error al publicar la imagen en SWR."
#     exit 1
# fi

echo "======================================================================"
echo "Para desplegar en Huawei Cloud FunctionGraph:"
echo "1. Selecciona 'Custom Image' como Runtime."
echo "2. Apunta al URI: ${REGISTRY}/${ORGANIZACION}/${IMAGEN_NOMBRE}:${TAG}"
echo "3. Configura el puerto de escucha en 8000."
echo "======================================================================"
