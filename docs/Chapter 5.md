# CAPÍTULO V: ANÁLISIS Y DISEÑO DEL SISTEMA

## 5.1 Introducción
El presente capítulo detalla la fase de Análisis y Diseño del sistema de análisis biomecánico para la academia *Corpo e Mente*, siguiendo los lineamientos del Proceso Unificado (UP) propuesto por Craig Larman. El objetivo es transformar los requisitos funcionales y no funcionales (definidos en el Capítulo IV) en un modelo arquitectónico y de diseño robusto, aplicando patrones GRASP para garantizar alta cohesión y bajo acoplamiento, y las normas de Mannino para el diseño de la base de datos relacional en BCNF.

## 5.2 Modelo de Dominio
El modelo de dominio representa los conceptos del negocio de Jiu-Jitsu Brasileño y análisis biomecánico, independientemente de la implementación tecnológica.

```mermaid
classDiagram
    class Profesor {
        +String id_profesor
        +String nombre
        +String email
        +registrar_patron()
        +indexar_fuente()
    }
    class Alumno {
        +String id_alumno
        +String nombre
        +evaluar_ejecucion()
        +consultar_progreso()
    }
    class TecnicaPatron {
        +String id_tecnica
        +String nombre
        +MatrizEsqueletica patron_3d
        +Vector embedding
    }
    class EvaluacionAlumno {
        +String id_evaluacion
        +Date fecha
        +Boolean es_valido
        +JSONB consejo_pedagogico
        +Float score_similitud
    }
    class FuenteConocimiento {
        +String id_documento
        +String titulo
        +String chunk_texto
        +Vector embedding_2048d
    }
    class MatrizEsqueletica {
        +List~Punto3D~ keypoints
        +calcular_angulos()
    }

    Profesor "1" --> "*" TecnicaPatron : registra
    Profesor "1" --> "*" FuenteConocimiento : indexa
    Alumno "1" --> "*" EvaluacionAlumno : realiza
    TecnicaPatron "1" --> "*" EvaluacionAlumno : es evaluada en
    EvaluacionAlumno "*" --> "*" FuenteConocimiento : se apoya en (RAG)
    TecnicaPatron "1" --> "1" MatrizEsqueletica : contiene