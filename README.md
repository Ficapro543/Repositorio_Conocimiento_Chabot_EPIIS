# Chatbot EPIIS - Base de Conocimientos

Repositorio de conocimientos para el chatbot de la Escuela Profesional de Ingeniería Informática y de Sistemas (EPIIS) de la Universidad Nacional de San Antonio Abad del Cusco (UNSAAC).

Contiene un corpus curado de **100 preguntas frecuentes** organizadas en **10 categorías**, con respuestas extraídas de documentos oficiales UNSAAC.

## Características

- **100 entradas** (10 por categoría) con preguntas, respuestas, variaciones e intents
- **10 categorías**: CUR, ESP, MAT, TIT, PPP, TUT, TTUT, BIE, MOV, SER
- **Sistema de matching**: clasificación por intents + keywords con conjugaciones
- **Detección por alias**: escribe el nombre de una categoría para ver sus preguntas
- **Comandos especiales**: `ayuda`, `historial`, `reporte`, `salir`
- **Fuentes oficiales**: respaldado por PDFs de la UNSAAC (Reglamento Académico, Plan Curricular 2024, Malla 2025, Reglamento de Tutorías, etc.)
- **Test automático**: 41/41 tests de cobertura

## Categorías del corpus

| Código | Nombre | Preguntas | Fuente principal |
|--------|--------|-----------|------------------|
| CUR | Cursos y Semestres | 10 | Plan Curricular 2024, Malla 2025 |
| ESP | Estudios de Especialidad | 10 | Plan Curricular 2024 |
| MAT | Matrícula | 10 | Reglamento Académico (Título I) |
| TIT | Titulación | 10 | Reglamento Académico (Título V) |
| PPP | Prácticas Pre-Profesionales | 10 | Reglamento Académico (Arts. 112°-116°) |
| TUT | Proceso de Tutorías | 10 | Reglamento de Tutoría Académica |
| TTUT | Tipos de Tutoría | 10 | Reglamento de Tutoría Académica |
| BIE | Bienestar Universitario | 10 | Estatuto UNSAAC + MOF OBU |
| MOV | Movilidad Estudiantil | 10 | Reglamento Académico + OCTI |
| SER | Servicios Universitarios | 10 | Directivas DTI + DRAA |

## Fuentes documentales

| Archivo | Descripción |
|---------|-------------|
| `RegAcademicoUNSAAC2017(CU-093-2017-UNSAAC).pdf` | Reglamento Académico UNSAAC (MAT, TIT, PPP, MOV) |
| `reglamento_tutorias_CU-0220-2017.pdf` | Reglamento de Tutoría Académica (TUT, TTUT) |
| `CU-031-2025_Plan_Curricular_EPIIS_2024.pdf` | Plan Curricular 2024 EPIIS (CUR, ESP) |
| `Malla_Curricular_EPIIS_2025.pdf` | Malla Curricular 2025 (créditos, distribución) |
| `Estatuto_UNSAAC_actualizado_2022.pdf` | Estatuto UNSAAC 2022 (BIE) |
| `MOF_OBU.pdf` | MOF Oficina de Bienestar Universitario (BIE) |
| `Reglamento_Regimen_Disciplinario_Estudiante.pdf` | Régimen Disciplinario Estudiantil |
| `Reglamento_Servicios_Bibliotecas_UNSAAC.pdf` | Reglamento de Bibliotecas (SER) |
| `TUPA_UNSAAC_2025.pdf` | TUPA UNSAAC 2025 (costos y trámites) |
| `Plana_docente.pdf` | Plana docente EPIIS |

## Estructura del repositorio

```
REPOSITORIO_CONOCIMIENTO_CHATBOT_EPIIS/
├── corpus/
│   └── corpus_general.json
├── knowledge_base/
│   ├── intents.json
│   ├── keywords.json
│   ├── faq_index.json
│   └── category_map.json
├── knowledge_files/
│   ├── tutorias.json
│   ├── servicios.json
│   └── practicas.json
├── sources/
│   ├── RegAcademicoUNSAAC2017(CU-093-2017-UNSAAC).pdf
│   ├── reglamento_tutorias_CU-0220-2017.pdf
│   ├── CU-031-2025_Plan_Curricular_EPIIS_2024.pdf
│   ├── Malla_Curricular_EPIIS_2025.pdf
│   ├── Estatuto_UNSAAC_actualizado_2022.pdf
│   ├── MOF_OBU.pdf
│   ├── Reglamento_Regimen_Disciplinario_Estudiante.pdf
│   ├── Reglamento_Servicios_Bibliotecas_UNSAAC.pdf
│   ├── TUPA_UNSAAC_2025.pdf
│   └── Plana_docente.pdf
├── notebooks/
│   └── Chatbot_epiis_unsaac.ipynb
├── tools/
│   └── calibrador_confianza.py
├── docs/
│   ├── Chatbot_EPIIS_UNSAAC.pdf
│   └── Chatbot_EPIIS_UNSAAC.pptx
├── requirements.txt
└── README.md
```

## Instalación y uso

```bash
pip install -r requirements.txt
```

Abrir el notebook `notebooks/Chatbot_epiis_unsaac.ipynb` y ejecutar todas las celdas.

Comandos disponibles dentro del chatbot:
- `ayuda` — lista de categorías y comandos
- `historial` — historial de la conversación actual
- `reporte` — exporta la conversación a JSON
- `salir` — deshabilita la UI

Escribe el nombre de una categoría (ej: `matrícula`, `tutoría`, `cursos`) para ver la lista de preguntas disponibles.

## Tests

El notebook incluye 41 pruebas automáticas que verifican:
- Match de intents contra preguntas y variaciones (30 tests)
- Keyword matching (10 tests)
- Carga correcta del category map (1 test)

## Enlace

https://github.com/Ficapro543/Repositorio_Conocimiento_Chabot_EPIIS
