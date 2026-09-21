import sys

def insert_after(lines, search_text, text_to_insert):
    for i, line in enumerate(lines):
        if search_text in line:
            # Find the end of this environment/block.
            # Usually the figure or itemize ends a few lines later.
            # But wait, the user's instructions say: "insertar los bloques en estas posiciones exactas (buscando el encabezado anterior)".
            # He probably meant "find the end of the previous subsection's content".
            # Or simpler: just find the next "\subsection" or "\section" and insert BEFORE it.
            for j in range(i + 1, len(lines)):
                if lines[j].startswith("\\section") or lines[j].startswith("\\subsection") or lines[j].startswith("\\subsubsection"):
                    return lines[:j] + text_to_insert.split('\n') + [""] + lines[j:]
            # If not found, insert at end
            return lines + text_to_insert.split('\n') + [""]
    print(f"Warning: could not find {search_text}")
    return lines

with open("docs/Documento.tex", "r") as f:
    lines = f.read().split("\n")

block1 = r"""\subsection{SSD para el Caso de Uso CU-04: Panel de Analítica}
\label{subsec:ssd-cu04}

La Figura \ref{fig:ssd-cu04} presenta el SSD para el CU-04, donde el Instructor solicita las métricas y el sistema retorna el análisis grupal.

\begin{figure}[H]
    \centering
    \includegraphics[width=0.8\textwidth]{Figuras/SSD_CU04.png}
    \caption{SSD para CU-04: Panel de Analítica. Fuente: Elaboración propia.}
    \label{fig:ssd-cu04}
\end{figure}"""

block2 = r"""\subsection{Contrato CO-03: obtenerDebilidadesGrupales}
\label{subsec:contrato-co03}

\textbf{Operación:} \texttt{obtenerDebilidadesGrupales(id\_tecnica)} \\
\textbf{Referencias Cruzadas:} Casos de Uso: CU-04. \\
\textbf{Precondiciones:} 
\begin{itemize}
    \item Existe un historial de evaluaciones almacenadas en el sistema.
\end{itemize}
\textbf{Postcondiciones:} 
\begin{itemize}
    \item Se han calculado las frecuencias y promedios de desviación por articulación.
    \item Se ha devuelto un resumen estadístico ordenado por mayor frecuencia de error.
\end{itemize}"""

block3 = r"""\subsection{Realización del CU-04: Panel de Analítica}
\label{subsec:realizacion-cu04}

La interacción principal para el CU-04 implica que la UI solicita datos al \texttt{AnaliticaController}, el cual obtiene el historial completo del \texttt{IHistorialRepository} y calcula las métricas en memoria."""

block4 = r"""\subsection{DCD para el CU-04: Panel de Analítica}
\label{subsec:dcd-cu04}

La Figura \ref{fig:dcd-analitica} muestra el DCD que incorpora el \texttt{AnaliticaController} y la actualización del \texttt{IHistorialRepository} para soportar la agregación de métricas.

\begin{figure}[H]
    \centering
    \includegraphics[width=1.0\textwidth]{Figuras/DCD_Analitica.png}
    \caption{DCD para CU-04. Fuente: Elaboración propia.}
    \label{fig:dcd-analitica}
\end{figure}"""

block5 = r"""\subsubsection{Technical Memo 4: Agregación de Métricas en Memoria vs. Base de Datos}
\textbf{Problema:} ¿Dónde deben calcularse las estadísticas de debilidades (CU-04)? \\
\textbf{Solución:} Se optó por extraer todas las evaluaciones y calcular los promedios en memoria dentro del \texttt{AnaliticaController}. \\
\textbf{Justificación (Patrones GRASP/SOLID):} Debido a la estructura de esquemas JSON estrictamente estructurados dentro de PostgreSQL y la necesidad de compatibilidad retroactiva, la lógica compleja en SQL (o \texttt{jsonb\_path\_query}) resultaba frágil. Siguiendo el principio de \textit{Protected Variations}, la base de datos se mantiene simple y la lógica de agregación reside en Python, permitiendo escalar a repositorios NoSQL o archivos estáticos en el futuro sin modificar la lógica de cálculo."""

lines = insert_after(lines, r"\subsection{SSD para el Caso de Uso CU-02", block1)
lines = insert_after(lines, r"\subsection{Contrato CO-02", block2)
lines = insert_after(lines, r"\subsection{Realización del CU-02", block3)
lines = insert_after(lines, r"\subsection{DCD para el CU-02", block4)
lines = insert_after(lines, r"\subsubsection{Technical Memo 3", block5)

with open("docs/Documento.tex", "w") as f:
    f.write("\n".join(lines))
