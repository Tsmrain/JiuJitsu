with open("docs/Documento.tex", "r") as f:
    lines = f.read().split("\n")

# Find the start of YOLO section
start = -1
end = -1
for i, line in enumerate(lines):
    if "Módulo de Visión Artificial: Suite YOLO26x-Pose" in line:
        start = i
    if "Infraestructura de Inferencia GPU" in line:
        end = i
        break

if start != -1 and end != -1:
    content = r"""\subsection{Módulo de Visión Artificial: Suite YOLO26x-Pose + YOLO26x-Depth}

\subsubsection{Tecnología Seleccionada}
Se seleccionó la suite combinada de \textbf{YOLO26x-Pose} (detección de 17 articulaciones anatómicas COCO) y \textbf{YOLO26x-Depth} (mapa de profundidad métrica monocular en metros reales absolutos).

\subsubsection{Alternativas Consideradas}
\begin{itemize}
    \item \textbf{OpenPose / MediaPipe:} Opciones tradicionales para estimación de pose 2D/3D.
    \item \textbf{Sensores RGB-D (Kinect / Intel RealSense):} Hardware especializado que captura profundidad.
\end{itemize}

\subsubsection{Justificación de la Selección}
\begin{table}[htbp]
\centering
\small
\begin{tabularx}{\textwidth}{|>{\bfseries}l|X|X|X|}
    \hline
    Criterio & YOLO26x-Pose + Depth & MediaPipe (Google) & OpenPose \\ \hline
    Contacto Corporal & Alto desempeño en agarres y oclusión. & Falla con solapamiento de dos personas. & Bueno pero muy lento en CPU. \\ \hline
    Profundidad 3D & Profundidad métrica real $Z$ vía YOLO Depth. & Sin profundidad métrica real absoluta. & Requiere calibración compleja. \\ \hline
    Velocidad / Latencia & Inferencia sincrónica en tiempo real sobre GPU. & Muy rápida en móvil. & Latencia elevada (baja velocidad). \\ \hline
\end{tabularx}
\caption{Cuadro Comparativo de Tecnologías de Estimación de Pose y Profundidad}
\label{tab:comp_pose}
\end{table}

\textbf{YOLO26x-Pose (Ultralytics, 2026):} Detector de pose de última generación optimizado para mantener un tracking confiable bajo oclusión moderada. Extrae los 17 keypoints COCO (índices 0 a 16) en cada fotograma a 30 FPS. Posteriormente, la \texttt{CalculadoraBiomecanica} evalúa exactamente 8 ángulos articulares tridimensionales (codos, rodillas, hombros y caderas, en sus lados izquierdo y derecho) a partir de esta topología. En videos de práctica cooperativa, YOLO26x opera en modo multi-persona: detecta dos esqueletos simultáneos, y el sistema asigna el esqueleto del alumno según la posición indicada manualmente en la PWA.

En Jiu-Jitsu Brasileño, dos practicantes interactúan en contacto físico estrecho, generando oclusiones constantes de extremidades. \textbf{MediaPipe} fue descartado debido a su baja tolerancia al solapamiento corporal y pérdida de seguimiento en posiciones de suelo. \textbf{OpenPose} fue descartado por requerir un consumo excesivo de memoria y latencias altas. La combinación de \textbf{YOLO26x-Pose + YOLO26x-Depth} permite obtener coordenadas reales $(X, Y, Z)$ en metros dentro del espacio tridimensional sin requerir sensores hardware RGB-D. La inferencia de YOLO26x-Pose + YOLO26x-Depth se delega a Google Colab Pro (GPU NVIDIA T4/A100) mediante un servidor Flask expuesto por túnel Ngrok. El backend FastAPI local consume el endpoint \texttt{POST /inferir} y recibe \texttt{keypoints\_3d + frame\_base64}. Si el túnel no está disponible, el sistema usa \texttt{AdaptadorYOLO} con \texttt{MockYOLOEngine} como fallback (ver \texttt{src/infrastructure/adapters/yolo\_adapter.py}).
"""
    lines = lines[:start] + content.split('\n') + [""] + lines[end:]

with open("docs/Documento.tex", "w") as f:
    f.write("\n".join(lines))
