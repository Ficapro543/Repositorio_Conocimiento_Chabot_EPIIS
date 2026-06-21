"""
calibrador_confianza.py
=======================
Módulo auxiliar de calibración de confianza mínima por intent.
Chatbot Académico EPIIS-UNSAAC — versión 1.0

Metodología:
  1. Para cada intent se definen 3–5 consultas de validación representativas
     (extraídas de las frases_trigger y variaciones del corpus).
  2. Se ejecuta el scorer del IntentMatcher (keyword-overlap) sobre cada consulta.
  3. Se toma el score mínimo correcto (score_minimo_correcto).
  4. Se aplica un margen de seguridad del 10 % hacia abajo, con piso en 0.50.
  5. El resultado se redondea a 2 decimales y se clampea al rango [0.50, 0.95].

Criterios de calibración por categoría (justificación):
  - MAT (Matrícula): umbral alto (≥0.75) — consultas muy específicas, léxico único.
  - TIT (Titulación): umbral alto (≥0.72) — terminología técnica precisa.
  - PPP (Prácticas): umbral alto (≥0.70) — léxico especializado consistente.
  - TUT/TTUT (Tutorías): umbral medio (≥0.60) — léxico compartido entre subtipos.
  - CUR (Cursos): umbral medio (≥0.65) — términos académicos comunes.
  - ESP (Especialidades): umbral medio (≥0.62) — overlap entre especialidades.
  - BIE (Bienestar): umbral medio (≥0.65) — variedad de servicios.
  - SER (Servicios): umbral medio (≥0.65) — variedad de trámites.
  - MOV (Movilidad): umbral conservador (≥0.55) — léxico poco frecuente en el corpus.

Compatible con: Python 3.8+, Google Colab, ejecución local.
Sin dependencias externas (solo stdlib).
"""

import json
import csv
import math
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTES DE CALIBRACIÓN
# ─────────────────────────────────────────────────────────────────────────────

MARGEN_SEGURIDAD = 0.10          # Factor de reducción sobre score_min_correcto
PISO_ABSOLUTO    = 0.50          # Confianza mínima permitida en cualquier caso
TECHO_ABSOLUTO   = 0.95          # Techo para evitar thresholds imposibles de alcanzar
VERSION_CALIBRACION = "1.0.0"    # Versión de esta calibración

# Piso por categoría (justificado en docstring del módulo)
PISO_CATEGORIA: Dict[str, float] = {
    "TUT":  0.60,
    "TTUT": 0.60,
    "CUR":  0.65,
    "ESP":  0.62,
    "PPP":  0.70,
    "BIE":  0.65,
    "MOV":  0.55,
    "MAT":  0.75,
    "TIT":  0.72,
    "SER":  0.65,
}

# ─────────────────────────────────────────────────────────────────────────────
# CONSULTAS DE VALIDACIÓN (3–5 por intent)
# Extraídas de frases_trigger y variaciones del corpus_general.json
# ─────────────────────────────────────────────────────────────────────────────

CONSULTAS_VALIDACION: Dict[str, List[str]] = {
    # ── TUT ──────────────────────────────────────────────────────────────────
    "consulta_tutoria_definicion": [
        "que es la tutoria academica",
        "en que consiste la tutoria",
        "como funciona la tutoria universitaria",
        "que significa tutoria en la universidad",
    ],
    "consulta_tutoria_frecuencia": [
        "con que frecuencia debo asistir tutoria",
        "cuantas veces al mes es la tutoria",
        "cada cuanto tiempo son las sesiones",
        "que tan seguido hay reuniones tutor",
    ],
    "consulta_tutoria_contacto_tutor": [
        "quien es mi tutor asignado",
        "como puedo contactar a mi tutor",
        "donde encuentro el nombre de mi tutor",
        "como saber quien es mi tutor academico",
    ],
    "consulta_tutoria_temas": [
        "que temas se tratan en tutoria",
        "sobre que se habla en la tutoria",
        "de que tratan las reuniones con el tutor",
        "que contenidos aborda la tutoria",
    ],
    "consulta_tutoria_obligatoriedad": [
        "la asistencia a tutoria es obligatoria",
        "es opcional asistir a tutoria",
        "puedo faltar a las sesiones de tutoria",
        "me pueden sancionar si no voy tutoria",
    ],
    "consulta_tutoria_registro_asistencia": [
        "como se registra la asistencia a tutoria",
        "hay lista de asistencia en tutoria",
        "como se controla la asistencia en tutoria",
        "como saber si se registro mi asistencia",
    ],
    "consulta_tutoria_cambio_tutor": [
        "puedo cambiar de tutor si tengo dificultades",
        "como solicito cambio de tutor",
        "es posible pedir otro tutor academico",
        "que hago si no me llevo bien con mi tutor",
    ],
    "consulta_tutoria_reglamento": [
        "existe reglamento que regule el proceso de tutorias",
        "hay un reglamento de tutorias unsaac",
        "donde puedo leer las normas de tutoria",
        "que documento regula las tutorias",
    ],
    "consulta_tutoria_materiales_sesion": [
        "que debo llevar a una sesion de tutoria",
        "que necesito para la reunion con mi tutor",
        "tengo que preparar algo para la tutoria",
        "que documentos piden en tutoria",
    ],
    "consulta_tutoria_confidencialidad": [
        "las sesiones de tutoria son confidenciales",
        "el tutor puede compartir lo que le digo",
        "es privada la informacion en tutoria",
        "que tan confidencial es la tutoria",
    ],
    # ── TTUT ─────────────────────────────────────────────────────────────────
    "consulta_tipos_tutoria_general": [
        "cuales son los tipos de tutoria que ofrece la escuela",
        "que modalidades de tutoria existen",
        "cuantas clases de tutoria hay",
        "de que tipos es la tutoria en la unsaac",
    ],
    "consulta_tipos_tutoria_individual": [
        "en que consiste la tutoria individual",
        "que es la tutoria uno a uno",
        "como funciona la tutoria personalizada",
        "cuando se da la tutoria individual",
    ],
    "consulta_tipos_tutoria_grupal": [
        "que es la tutoria grupal y como se organiza",
        "como son las tutorias grupales",
        "cuantas personas van a la tutoria grupal",
        "con quienes comparto la tutoria grupal",
    ],
    "consulta_tipos_tutoria_pares": [
        "que es la tutoria entre pares",
        "que es el tutoreo entre companeros",
        "quienes son los tutores pares",
        "como funciona la tutoria entre estudiantes",
    ],
    "consulta_tipos_tutoria_virtual": [
        "existe tutoria en linea o virtual",
        "hay tutoria a distancia",
        "puedo hacer tutoria por videoconferencia zoom",
        "las tutorias son presenciales o tambien virtuales",
    ],
    "consulta_tipos_tutoria_vs_psicologia": [
        "diferencia entre tutoria academica y orientacion psicologica",
        "la tutoria incluye apoyo psicologico",
        "cuando debo ir al psicologo en vez del tutor",
        "el tutor es psicologo",
    ],
    "consulta_tipos_tutoria_ingresantes": [
        "que es la tutoria de ingresantes",
        "hay tutoria especial para los nuevos alumnos",
        "que tutoria reciben los que recien entran a la universidad",
        "como se atiende a alumnos de primer semestre adaptacion",
    ],
    "consulta_tipos_tutoria_riesgo_academico": [
        "existe tutoria para estudiantes con bajo rendimiento",
        "hay tutoria especial si mis notas son bajas",
        "que pasa si estoy en riesgo academico tutoria",
        "me asignan tutoria si jalo muchos cursos",
    ],
    "consulta_tipos_tutoria_vs_asesoria_tesis": [
        "que diferencia hay entre tutoria y asesoria de tesis",
        "mi asesor de tesis es mi tutor",
        "la tutoria incluye apoyo en la tesis",
        "el tutor me ayuda con la tesis",
    ],
    "consulta_tipos_tutoria_vocacional": [
        "la tutoria cubre orientacion vocacional y de carrera",
        "el tutor me ayuda a saber que especialidad elegir",
        "puedo hablar con mi tutor sobre mi futuro profesional",
        "la tutoria incluye orientacion laboral",
    ],
    # ── CUR ──────────────────────────────────────────────────────────────────
    "consulta_cursos_duracion_carrera": [
        "cuantos semestres tiene la carrera ingenieria informatica",
        "cuantos ciclos tiene la carrera sistemas",
        "cuantos anos dura la carrera",
        "que duracion tiene la carrera de sistemas unsaac",
    ],
    "consulta_cursos_total_creditos": [
        "cuantos creditos son necesarios para culminar la carrera",
        "cuantos creditos necesito para acabar la carrera",
        "cual es el total de creditos del plan de estudios",
        "creditos titulacion epiis",
    ],
    "consulta_cursos_primer_semestre": [
        "cuales son los cursos del primer semestre",
        "que cursos llevo en el primer ciclo",
        "cuales son las materias de inicio de carrera",
        "que se estudia en el primer semestre de sistemas",
    ],
    "consulta_cursos_adelanto_semestres": [
        "puedo llevar cursos de otro semestre si aprobe prerrequisitos",
        "puedo adelantar cursos de ciclos superiores",
        "es posible llevar materias de semestres mas avanzados",
        "cursos avanzados prerrequisitos autorizacion",
    ],
    "consulta_cursos_desaprobacion": [
        "que pasa si desapruebo un curso",
        "que consecuencias tiene jalar un curso",
        "cuantas veces puedo llevar un curso desaprobacion",
        "que hago si repruebo una materia",
    ],
    "consulta_cursos_areas_plan_estudios": [
        "como esta organizado el plan de estudios por areas",
        "que areas tiene el curriculo de la carrera",
        "en que grupos se dividen los cursos",
        "como se clasifican las materias de la carrera",
    ],
    "consulta_cursos_electivos": [
        "cuantos cursos electivos debo llevar durante la carrera",
        "cuantas materias optativas son obligatorias",
        "cuantos electivos exige el plan de estudios",
        "puedo elegir mis cursos libremente creditos",
    ],
    "consulta_cursos_horario_clases": [
        "donde puedo ver el horario de clases del semestre",
        "como consulto mis horarios en el sistema virtual",
        "donde estan los horarios del semestre clases",
        "en que plataforma veo mis clases y aulas",
    ],
    "consulta_cursos_creditos_definicion": [
        "que son los creditos academicos y como se calculan",
        "que significa un credito academico",
        "como funciona el sistema de creditos",
        "un credito equivale a cuantas horas",
    ],
    "consulta_cursos_promedio_ponderado": [
        "como se calcula el promedio ponderado semestral",
        "como se saca el promedio del semestre",
        "que es el promedio ponderado notas",
        "como calcula el sistema mi promedio",
    ],
    # ── ESP ──────────────────────────────────────────────────────────────────
    "consulta_esp_listado_especialidades": [
        "cuales son las especialidades que ofrece la escuela ingenieria",
        "que especializaciones hay en la carrera epiis",
        "en que areas me puedo especializar sistemas",
        "cuantas especialidades tiene la carrera",
    ],
    "consulta_esp_cuando_elegir": [
        "cuando debo elegir mi especialidad",
        "en que semestre escojo especialidad",
        "a partir de que ciclo elijo especializacion",
        "cuando me especializo en la carrera",
    ],
    "consulta_esp_demanda_laboral": [
        "que especialidad tiene mas demanda laboral en la region",
        "cual especialidad tiene mas trabajo cusco",
        "que especializacion es mas solicitada en el mercado",
        "que especialidad conviene mas elegir",
    ],
    "consulta_esp_cursos_ingenieria_software": [
        "cuales son los cursos de la especialidad ingenieria de software",
        "que materias llevo en software",
        "que cursos tiene la especialidad de software epiis",
        "que se aprende en ingenieria de software",
    ],
    "consulta_esp_cambio_especialidad": [
        "puedo cambiar de especialidad una vez que la elegi",
        "es posible cambiar de especializacion",
        "que pasa si quiero otra especialidad",
        "puedo arrepentirme de la especialidad que elegi",
    ],
    "consulta_esp_cursos_redes_telecom": [
        "que cursos incluye la especialidad redes y telecomunicaciones",
        "que materias son de redes telecom",
        "que se estudia en telecomunicaciones epiis",
        "que aprendo en la especialidad de redes",
    ],
    "consulta_esp_ia_ciencia_datos": [
        "que es la especialidad de inteligencia artificial y ciencia de datos",
        "que es la especialidad de ia",
        "que cubro en ciencia de datos machine learning",
        "que se estudia en la especialidad de machine learning",
    ],
    "consulta_esp_seguridad_certificaciones": [
        "la especialidad de seguridad informatica tiene certificaciones",
        "en seguridad informatica hay certificados",
        "la especialidad de ciberseguridad prepara para certificaciones",
        "puedo obtener certificados en la especialidad de seguridad",
    ],
    "consulta_esp_convenios_practicas": [
        "las especialidades tienen convenios con empresas para practicas",
        "las especialidades tienen empresas colaboradoras convenio",
        "hay convenios de practicas por especialidad epiis",
        "las empresas contratan segun mi especialidad",
    ],
    "consulta_esp_electivos_cruzados": [
        "puedo llevar cursos de otras especialidades como electivos",
        "es posible tomar materias de otra especializacion",
        "puedo cruzar cursos de diferentes especialidades",
        "electivos de otras especialidades disponibles",
    ],
    # ── PPP ──────────────────────────────────────────────────────────────────
    "consulta_ppp_requisitos_inicio": [
        "cuales son los requisitos para iniciar las practicas pre profesionales",
        "que necesito para empezar las practicas ppp",
        "requisitos inicio practicas pre profesionales epiis",
        "como inicio las practicas preprofesionales",
    ],
    "consulta_ppp_horas_acumuladas": [
        "cuantas horas de practicas debo acumular",
        "cuantas horas ppp se requieren",
        "horas acumuladas practicas pre profesionales",
        "cuantas horas minimo de practicas",
    ],
    "consulta_ppp_empresa_convenio": [
        "la empresa donde hago practicas debe tener convenio con la universidad",
        "necesito empresa con convenio para practicas",
        "la empresa de practicas debe estar registrada en la unsaac",
        "convenio empresa practicas pre profesionales",
    ],
    "consulta_ppp_carta_presentacion": [
        "como consigo la carta de presentacion para las practicas",
        "donde solicito carta de presentacion practicas",
        "como tramito la carta de presentacion ppp",
        "solicitar carta presentacion practicas epiis",
    ],
    "consulta_ppp_informe_final": [
        "que es el informe de practicas y cuando debo presentarlo",
        "cuando presento el informe final de practicas",
        "que contiene el informe de practicas pre profesionales",
        "plazo entrega informe practicas",
    ],
    "consulta_ppp_remuneracion": [
        "las practicas pre profesionales son remuneradas",
        "pagan por las practicas preprofesionales",
        "las practicas tienen pago o son gratuitas",
        "remuneracion practicas pre profesionales",
    ],
    "consulta_ppp_sector_publico": [
        "puedo hacer mis practicas en una empresa publica o institucion del estado",
        "puedo hacer practicas en entidades publicas",
        "las practicas pueden ser en sector publico gobierno",
        "instituciones del estado aceptan practicantes epiis",
    ],
    "consulta_ppp_supervision_universidad": [
        "quien supervisa y evalua mis practicas desde la universidad",
        "quien es el supervisor de practicas de la epiis",
        "como evalua la universidad mis practicas pre profesionales",
        "docente supervisor practicas unsaac",
    ],
    "consulta_ppp_trabajo_actual": [
        "puedo hacer las practicas en la misma empresa donde trabajo actualmente",
        "puedo convalidar mi trabajo actual como practicas",
        "si ya tengo trabajo puedo usarlo como practicas",
        "empresa actual contar como practicas pre profesionales",
    ],
    "consulta_ppp_requisito_titulacion": [
        "las practicas pre profesionales son un requisito para titularse",
        "necesito practicas para graduarme",
        "las ppp son obligatorias para la titulacion",
        "sin practicas puedo titularme epiis",
    ],
    # ── BIE ──────────────────────────────────────────────────────────────────
    "consulta_bie_servicios_generales": [
        "que servicios de bienestar ofrece la unsaac a sus estudiantes",
        "que ofrece bienestar universitario unsaac",
        "que servicios de apoyo estudiantil hay en la unsaac",
        "cuales son los servicios de bienestar universitario",
    ],
    "consulta_bie_atencion_psicologica": [
        "como puedo acceder a la atencion psicologica gratuita",
        "hay atencion psicologica gratis en la unsaac",
        "donde pido cita con el psicologo en la universidad",
        "como acceder al servicio psicologico unsaac",
    ],
    "consulta_bie_beca_alimentacion": [
        "que es la beca de alimentacion y como la solicito",
        "como solicito la beca de comedor universitario",
        "requisitos beca alimentacion unsaac estudiantes",
        "como obtener beca comedor universitario",
    ],
    "consulta_bie_apoyo_economico": [
        "existe apoyo economico para estudiantes en situacion de vulnerabilidad",
        "hay apoyo economico para estudiantes de bajos recursos",
        "como solicitar apoyo economico en la unsaac",
        "beneficios economicos para estudiantes vulnerables unsaac",
    ],
    "consulta_bie_seguro_estudiantil": [
        "como funciona el seguro estudiantil de la unsaac",
        "que cubre el seguro universitario",
        "tengo seguro de salud por ser estudiante unsaac",
        "seguro estudiantil accidentes unsaac",
    ],
    "consulta_bie_deportes_cultura": [
        "que deportes y actividades culturales puedo practicar en la unsaac",
        "que actividades deportivas ofrece la universidad",
        "hay talleres culturales y deportivos en la unsaac",
        "actividades extracurriculares deportes cultura unsaac",
    ],
    "consulta_bie_residencia_universitaria": [
        "la unsaac tiene residencia universitaria para estudiantes de provincia",
        "hay dormitorios universitarios en la unsaac",
        "donde me alojo si soy de provincia en la unsaac",
        "residencia estudiantil unsaac disponible",
    ],
    "consulta_bie_certificado_socioeconomico": [
        "como solicito un certificado de situacion socioeconomica",
        "donde tramito el certificado socioeconomico unsaac",
        "como pido el certificado de situacion economica",
        "tramite certificado pobreza bienestar universitario",
    ],
    "consulta_bie_comedor_acceso": [
        "el comedor universitario esta disponible para todos los estudiantes",
        "todos los alumnos pueden usar el comedor unsaac",
        "como accedo al comedor universitario",
        "quien puede ir al comedor universitario unsaac",
    ],
    "consulta_bie_contacto_oficina": [
        "a que numero o correo puedo comunicarme con bienestar universitario",
        "como contacto la oficina de bienestar unsaac",
        "cual es el telefono de bienestar universitario",
        "correo de bienestar universitario unsaac contacto",
    ],
    # ── MOV ──────────────────────────────────────────────────────────────────
    "consulta_mov_programas_disponibles": [
        "que programas de movilidad estudiantil ofrece la unsaac",
        "que programas de intercambio estudiantil hay",
        "la unsaac tiene programas de intercambio internacional",
        "programas movilidad estudiantil disponibles unsaac",
    ],
    "consulta_mov_requisitos_intercambio": [
        "cuales son los requisitos minimos para participar en un programa de intercambio",
        "que necesito para postular al intercambio estudiantil",
        "requisitos para movilidad estudiantil unsaac",
        "condiciones para participar en intercambio internacional",
    ],
    "consulta_mov_convalidacion_cursos": [
        "los cursos llevados en el intercambio se convalidan en la unsaac",
        "como se convalidan los cursos del intercambio",
        "reconocen los creditos del intercambio en la unsaac",
        "convalidacion cursos movilidad estudiantil",
    ],
    "consulta_mov_apoyo_economico": [
        "hay apoyo economico para los estudiantes que van de intercambio",
        "la unsaac apoya economicamente a los estudiantes de movilidad",
        "hay becas para el intercambio estudiantil unsaac",
        "financiamiento movilidad estudiantil beca",
    ],
    "consulta_mov_estudiantes_entrantes": [
        "puedo recibir estudiantes de intercambio de otras universidades",
        "la unsaac recibe estudiantes extranjeros de intercambio",
        "como postular para venir a la unsaac de intercambio",
        "estudiantes entrantes movilidad unsaac",
    ],
    "consulta_mov_convocatorias": [
        "donde puedo enterarme de las convocatorias de movilidad estudiantil",
        "cuando son las convocatorias de intercambio unsaac",
        "como me entero de los programas de movilidad",
        "convocatorias intercambio estudiantil donde ver",
    ],
    "consulta_mov_documentos_postulacion": [
        "que documentos necesito para postular a la movilidad estudiantil",
        "que papeles piden para el intercambio estudiantil",
        "documentos requeridos para postular movilidad",
        "requisitos documentarios intercambio estudiantil unsaac",
    ],
    "consulta_mov_impacto_titulacion": [
        "el intercambio afecta mi proceso de titulacion o retrasa mi egreso",
        "si voy de intercambio me retraso en la carrera",
        "el intercambio estudiantil afecta mi graduacion",
        "impacto titulacion intercambio estudiantil",
    ],
    "consulta_mov_requisito_idioma": [
        "necesito dominar otro idioma para participar en la movilidad",
        "debo hablar ingles para el intercambio estudiantil",
        "requisito de idioma para movilidad estudiantil unsaac",
        "que nivel de idioma necesito para intercambio",
    ],
    "consulta_mov_universidades_convenio": [
        "la unsaac tiene convenios con universidades reconocidas internacionalmente",
        "con que universidades tiene convenio la unsaac para intercambio",
        "universidades socias de la unsaac para movilidad",
        "convenios internacionales unsaac intercambio estudiantil",
    ],
    # ── MAT ──────────────────────────────────────────────────────────────────
    "consulta_mat_fechas_matricula": [
        "cuando se realizan las matriculas en la unsaac",
        "cuales son las fechas de matricula unsaac",
        "cuando es el periodo de matricula en sistemas",
        "fechas matricula semestre unsaac calendario",
    ],
    "consulta_mat_proceso_virtual": [
        "como me matriculo en el portal virtual unsaac",
        "como hago la matricula virtual en la unsaac",
        "proceso de matricula en linea paso a paso",
        "matricula online como funciona",
    ],
    "consulta_mat_requisitos": [
        "cuales son los requisitos para poder matricularme",
        "que necesito para matricularme en la unsaac",
        "requisitos matricula semestre unsaac epiis",
        "condiciones para matricularse en la carrera",
    ],
    "consulta_mat_modalidad_presencial": [
        "puedo hacer la matricula de forma presencial",
        "la matricula puede ser presencial en secretaria",
        "hay matricula presencial en la unsaac",
        "donde hago la matricula en persona",
    ],
    "consulta_mat_fuera_de_plazo": [
        "que hago si no pude matricularme dentro del plazo establecido",
        "se me paso la fecha de matricula que hago",
        "matricula extemporanea fuera de plazo unsaac",
        "como matricularme si se vencio el plazo",
    ],
    "consulta_mat_creditos_maximo": [
        "cuantos creditos maximos puedo llevar por semestre",
        "cual es la carga maxima de creditos por semestre",
        "maximo creditos matricula semestre epiis",
        "puedo llevar mas de 24 creditos por semestre",
    ],
    "consulta_mat_retiro_curso": [
        "puedo retirar un curso despues de matricularme",
        "como retiro un curso de mi matricula",
        "es posible darse de baja en un curso ya matriculado",
        "retiro de curso matriculado plazo proceso",
    ],
    "consulta_mat_condicional": [
        "que es la matricula condicional y cuando aplica",
        "que significa matricula condicional en la unsaac",
        "cuando me ponen matricula condicional",
        "matricula condicional bajo rendimiento unsaac",
    ],
    "consulta_mat_costo": [
        "cuanto cuesta la matricula en la unsaac",
        "cual es el costo de la matricula en sistemas",
        "hay que pagar para matricularse en la unsaac",
        "arancel o costo matricula unsaac epiis",
    ],
    "consulta_mat_seguro_activacion": [
        "que es el seguro universitario y cuando se activa con la matricula",
        "el seguro estudiantil se activa al matricularme",
        "cuando empieza el seguro universitario unsaac",
        "seguro activacion matricula unsaac",
    ],
    # ── TIT ──────────────────────────────────────────────────────────────────
    "consulta_tit_modalidades": [
        "cuales son las modalidades de titulacion disponibles en la epiis",
        "que formas de titulacion existen en la carrera",
        "modalidades de graduacion titulacion epiis unsaac",
        "como puedo titularme en ingenieria informatica unsaac",
    ],
    "consulta_tit_requisitos_inicio": [
        "cuales son los requisitos para iniciar el proceso de titulacion",
        "que necesito para comenzar a titularme",
        "requisitos para iniciar titulacion epiis unsaac",
        "condiciones para empezar proceso de grado",
    ],
    "consulta_tit_grado_bachiller": [
        "como obtengo el grado de bachiller",
        "que necesito para obtener el bachillerato en sistemas",
        "proceso para graduarse bachiller epiis",
        "como tramitar el grado de bachiller unsaac",
    ],
    "consulta_tit_plazo_titulacion": [
        "cuanto tiempo tengo para titularme despues de terminar los cursos",
        "hay un plazo limite para titularme despues de egresar",
        "cuando vence el plazo para titularse en la unsaac",
        "tiempo limite titulacion egresados unsaac",
    ],
    "consulta_tit_suficiencia_profesional": [
        "que es un trabajo de suficiencia profesional",
        "que es la suficiencia profesional como modalidad de titulacion",
        "como funciona el trabajo de suficiencia profesional epiis",
        "suficiencia profesional titulacion unsaac",
    ],
    "consulta_tit_eleccion_asesor": [
        "como escojo a mi asesor de tesis",
        "como elijo mi asesor de titulacion",
        "proceso para elegir asesor de tesis epiis",
        "requisitos asesor tesis unsaac",
    ],
    "consulta_tit_duracion_proceso": [
        "cuanto tiempo toma habitualmente el proceso de titulacion",
        "cuanto demora titularse en la epiis",
        "tiempo promedio proceso de titulacion unsaac",
        "cuanto dura el tramite de titulacion sistemas",
    ],
    "consulta_tit_jurado_sustentacion": [
        "en que consiste el jurado de sustentacion",
        "quienes conforman el jurado de tesis epiis",
        "como se forma el jurado para la sustentacion",
        "que es el jurado de sustentacion de titulacion",
    ],
    "consulta_tit_desaprobacion_sustentacion": [
        "que pasa si desapruebo la sustentacion",
        "que consecuencias hay si jalo la sustentacion de tesis",
        "puedo repetir la sustentacion si la desapruebo",
        "segunda oportunidad sustentacion tesis epiis",
    ],
    "consulta_tit_registro_sunedu": [
        "donde debo registrar mi titulo una vez obtenido",
        "como registro mi titulo en sunedu",
        "tramite registro titulo sunedu unsaac",
        "donde se registra el titulo profesional obtenido",
    ],
    # ── SER ──────────────────────────────────────────────────────────────────
    "consulta_ser_biblioteca": [
        "como accedo a los recursos de la biblioteca universitaria",
        "como uso la biblioteca de la unsaac",
        "acceso biblioteca universitaria unsaac recursos digitales",
        "servicios biblioteca unsaac estudiantes",
    ],
    "consulta_ser_correo_institucional": [
        "como obtengo mi correo institucional de la unsaac",
        "como creo mi correo universitario unsaac",
        "tramite correo institucional estudiantes unsaac",
        "donde solicito mi correo de la universidad",
    ],
    "consulta_ser_certificados_constancias": [
        "donde solicito mis certificados y constancias academicas",
        "como tramito una constancia de estudios unsaac",
        "como pido un certificado de notas en la epiis",
        "tramite constancia matricula certificado academico",
    ],
    "consulta_ser_aula_virtual": [
        "como puedo acceder al aula virtual de la unsaac",
        "como entro al aula virtual campus virtual unsaac",
        "donde accedo al moodle de la unsaac",
        "aula virtual plataforma educativa unsaac acceso",
    ],
    "consulta_ser_laboratorios_computo": [
        "la unsaac cuenta con laboratorios de computo disponibles para estudiantes",
        "hay laboratorios de computacion en la epiis",
        "puedo usar los laboratorios de computo de la unsaac",
        "acceso laboratorios informatica computadoras epiis",
    ],
    "consulta_ser_carta_presentacion": [
        "como solicito una carta de presentacion para eventos o concursos",
        "donde tramito carta de presentacion para eventos",
        "carta de presentacion para concursos externos epiis",
        "solicitar carta presentacion actividades academicas",
    ],
    "consulta_ser_impresion_campus": [
        "existe un servicio de impresion o fotocopiado dentro del campus",
        "hay servicio de impresion en la unsaac campus",
        "donde puedo imprimir en la universidad unsaac",
        "fotocopiado impresion campus universitario unsaac",
    ],
    "consulta_ser_record_notas": [
        "como puedo obtener mi record de notas oficial",
        "donde tramito mi record de notas oficial unsaac",
        "como solicito el historial de notas epiis",
        "record academico notas tramite secretaria",
    ],
    "consulta_ser_tupa": [
        "que es el tupa y donde puedo consultarlo",
        "donde encuentro el tupa de la unsaac",
        "que es el texto unico de procedimientos administrativos unsaac",
        "como consultar el tupa tramites unsaac",
    ],
    "consulta_ser_contacto_secretaria": [
        "como me comunico con la secretaria de la escuela de ingenieria",
        "cual es el telefono de la secretaria de la epiis",
        "correo o telefono de la secretaria de sistemas unsaac",
        "contacto secretaria epiis ingenieria informatica",
    ],
}


# ─────────────────────────────────────────────────────────────────────────────
# LÓGICA DEL SCORER (replicada del IntentMatcher original para trazabilidad)
# ─────────────────────────────────────────────────────────────────────────────

def _preprocess(text: str) -> List[str]:
    """Tokeniza y normaliza el texto del usuario (idéntico al matcher original)."""
    return text.lower().strip().split()


def _score_intent(user_tokens: List[str], kw_entry: Dict) -> float:
    """
    Calcula el score de coincidencia entre tokens y keywords de un intent.
    Replica la lógica del IntentMatcher original para garantizar trazabilidad.
    """
    all_kw = (
        kw_entry.get("keywords_primarios", []) +
        kw_entry.get("keywords_secundarios", []) +
        kw_entry.get("sinonimos", [])
    )
    matches = sum(
        1 for kw in all_kw
        if any(kw.lower() in token or token in kw.lower()
               for token in user_tokens)
    )
    return matches / max(len(all_kw), 1)


def _score_query_on_intent(query: str, intent_id: str, keywords_db: List[Dict]) -> float:
    """Retorna el score de una consulta para un intent específico."""
    tokens = _preprocess(query)
    for entry in keywords_db:
        if entry["intent_id"] == intent_id:
            return _score_intent(tokens, entry)
    return 0.0


# ─────────────────────────────────────────────────────────────────────────────
# CARGADORES DE DATOS
# ─────────────────────────────────────────────────────────────────────────────

def _find_project_root() -> Path:
    """
    Encuentra la raíz del proyecto buscando hacia arriba desde este archivo.
    Compatible con ejecución local y Google Colab.
    """
    # En Colab, el usuario debe montar el drive y ajustar BASE_OVERRIDE
    env_override = os.environ.get("EPIIS_PROJECT_ROOT")
    if env_override:
        return Path(env_override)

    # Búsqueda automática desde el directorio de este script
    start = Path(__file__).resolve().parent  # tools/
    for candidate in [start.parent, start.parent.parent, Path.cwd()]:
        if (candidate / "knowledge_base" / "intents.json").exists():
            return candidate

    # Fallback: directorio de trabajo actual
    return Path.cwd()


def load_keywords_db(project_root: Optional[Path] = None) -> List[Dict]:
    """Carga keywords.json y retorna la lista de entradas."""
    root = project_root or _find_project_root()
    path = root / "knowledge_base" / "keywords.json"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data["keywords"]


def load_intents(project_root: Optional[Path] = None) -> List[Dict]:
    """Carga intents.json y retorna la lista de intents."""
    root = project_root or _find_project_root()
    path = root / "knowledge_base" / "intents.json"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data["intents"]


def save_intents(intents_data: Dict, project_root: Optional[Path] = None) -> Path:
    """Guarda intents.json actualizado."""
    root = project_root or _find_project_root()
    path = root / "knowledge_base" / "intents.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(intents_data, f, ensure_ascii=False, indent=2)
    return path


# ─────────────────────────────────────────────────────────────────────────────
# MOTOR DE CALIBRACIÓN
# ─────────────────────────────────────────────────────────────────────────────

def calibrar_intent(
    intent_id: str,
    categoria: str,
    keywords_db: List[Dict],
) -> Dict:
    """
    Ejecuta la calibración para un intent dado.

    Retorna un dict con:
      - intent_id, categoria
      - consultas_validacion (lista)
      - scores_observados (lista)
      - n_validacion (int)
      - score_minimo_correcto (float)
      - margen_aplicado (float)
      - piso_categoria (float)
      - confianza_minima (float)
      - criterio_calibracion (str)
      - observaciones (str)
    """
    consultas = CONSULTAS_VALIDACION.get(intent_id, [])
    n = len(consultas)

    if n == 0:
        # Sin consultas de validación: usar piso conservador de categoría
        piso = PISO_CATEGORIA.get(categoria, PISO_ABSOLUTO)
        return {
            "intent_id": intent_id,
            "categoria": categoria,
            "consultas_validacion": [],
            "scores_observados": [],
            "n_validacion": 0,
            "score_minimo_correcto": None,
            "margen_aplicado": None,
            "piso_categoria": piso,
            "confianza_minima": round(piso, 2),
            "criterio_calibracion": "piso_categoria_conservador",
            "observaciones": "Sin consultas de validación definidas; se usó el piso por categoría.",
        }

    # Calcular scores para cada consulta sobre el intent objetivo
    scores = [_score_query_on_intent(q, intent_id, keywords_db) for q in consultas]
    scores_correctos = [s for s in scores if s > 0.0]

    if not scores_correctos:
        # Ninguna consulta produjo score positivo; señal de keywords débiles
        piso = PISO_CATEGORIA.get(categoria, PISO_ABSOLUTO)
        return {
            "intent_id": intent_id,
            "categoria": categoria,
            "consultas_validacion": consultas,
            "scores_observados": [round(s, 4) for s in scores],
            "n_validacion": n,
            "score_minimo_correcto": 0.0,
            "margen_aplicado": MARGEN_SEGURIDAD,
            "piso_categoria": piso,
            "confianza_minima": round(piso, 2),
            "criterio_calibracion": "piso_categoria_por_score_cero",
            "observaciones": (
                "Ninguna consulta de validación produjo score > 0. "
                "Las keywords del intent pueden ser demasiado genéricas o ambiguas. "
                "Se usó piso de categoría como medida conservadora."
            ),
        }

    score_min = min(scores_correctos)
    # Aplicar margen de seguridad
    confianza_calculada = score_min * (1.0 - MARGEN_SEGURIDAD)
    piso_cat = PISO_CATEGORIA.get(categoria, PISO_ABSOLUTO)

    # Aplicar clamping: [max(piso_categoria, PISO_ABSOLUTO), TECHO_ABSOLUTO]
    piso_efectivo = max(piso_cat, PISO_ABSOLUTO)
    confianza_final = max(piso_efectivo, min(TECHO_ABSOLUTO, confianza_calculada))
    confianza_final = round(confianza_final, 2)

    # Determinar el criterio usado
    if confianza_calculada < piso_efectivo:
        criterio = "piso_categoria_aplicado"
        obs = (
            f"Score mínimo calculado ({confianza_calculada:.3f}) caía por debajo del "
            f"piso de categoría ({piso_efectivo:.2f}). Se elevó al piso."
        )
    elif confianza_calculada > TECHO_ABSOLUTO:
        criterio = "techo_aplicado"
        obs = (
            f"Score mínimo calculado ({confianza_calculada:.3f}) superaba el techo "
            f"({TECHO_ABSOLUTO}). Se limitó al techo."
        )
    else:
        criterio = "score_minimo_con_margen"
        obs = (
            f"Confianza calibrada desde score_min={score_min:.3f} "
            f"con margen de seguridad del {int(MARGEN_SEGURIDAD*100)}%."
        )

    return {
        "intent_id": intent_id,
        "categoria": categoria,
        "consultas_validacion": consultas,
        "scores_observados": [round(s, 4) for s in scores],
        "n_validacion": n,
        "score_minimo_correcto": round(score_min, 4),
        "margen_aplicado": MARGEN_SEGURIDAD,
        "piso_categoria": piso_cat,
        "confianza_minima": confianza_final,
        "criterio_calibracion": criterio,
        "observaciones": obs,
    }


def ejecutar_calibracion(project_root: Optional[Path] = None) -> List[Dict]:
    """
    Ejecuta la calibración completa para todos los intents definidos en intents.json.
    Retorna una lista de resultados de calibración.
    """
    root = project_root or _find_project_root()
    keywords_db = load_keywords_db(root)
    intents = load_intents(root)

    resultados = []
    for intent in intents:
        iid = intent["intent_id"]
        cat = intent["categoria"]
        display = intent.get("display_name", "")
        corpus_ref = intent.get("corpus_ref", "")
        prioridad = intent.get("prioridad", "")

        res = calibrar_intent(iid, cat, keywords_db)
        res["display_name"] = display
        res["corpus_ref"] = corpus_ref
        res["prioridad"] = prioridad
        res["confianza_minima_anterior"] = intent.get("confianza_minima", None)
        resultados.append(res)

    return resultados


# ─────────────────────────────────────────────────────────────────────────────
# ACTUALIZACIÓN DE intents.json
# ─────────────────────────────────────────────────────────────────────────────

def actualizar_intents_json(
    resultados: List[Dict],
    project_root: Optional[Path] = None,
) -> Path:
    """
    Actualiza intents.json con los nuevos valores de confianza_minima
    y añade campos de trazabilidad de calibración.
    No elimina ningún intent ni cambia intent_id, display_name, categoria,
    corpus_ref ni prioridad.
    """
    root = project_root or _find_project_root()
    path = root / "knowledge_base" / "intents.json"

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    # Construir mapa intent_id → resultado de calibración
    mapa = {r["intent_id"]: r for r in resultados}

    for intent in data["intents"]:
        iid = intent["intent_id"]
        if iid not in mapa:
            continue
        r = mapa[iid]
        # Actualizar confianza_minima
        intent["confianza_minima"] = r["confianza_minima"]
        # Añadir campos de trazabilidad (mínimos y compatibles)
        intent["calibracion"] = {
            "version": VERSION_CALIBRACION,
            "n_validacion": r["n_validacion"],
            "score_minimo_correcto": r["score_minimo_correcto"],
            "margen_aplicado": r["margen_aplicado"],
            "criterio": r["criterio_calibracion"],
            "observaciones": r["observaciones"],
        }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return path


# ─────────────────────────────────────────────────────────────────────────────
# EXPORTACIÓN DE RESULTADOS
# ─────────────────────────────────────────────────────────────────────────────

def exportar_json(resultados: List[Dict], output_path: Path) -> None:
    """Exporta el informe completo de calibración en JSON."""
    export = {
        "version_calibracion": VERSION_CALIBRACION,
        "margen_seguridad": MARGEN_SEGURIDAD,
        "piso_absoluto": PISO_ABSOLUTO,
        "techo_absoluto": TECHO_ABSOLUTO,
        "pisos_por_categoria": PISO_CATEGORIA,
        "total_intents": len(resultados),
        "resultados": resultados,
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(export, f, ensure_ascii=False, indent=2)


def exportar_csv(resultados: List[Dict], output_path: Path) -> None:
    """Exporta el resumen de calibración en CSV para análisis posterior."""
    campos = [
        "intent_id", "display_name", "categoria", "corpus_ref",
        "confianza_minima", "confianza_minima_anterior",
        "criterio_calibracion", "n_validacion",
        "score_minimo_correcto", "margen_aplicado", "observaciones",
    ]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campos, extrasaction="ignore")
        writer.writeheader()
        for r in resultados:
            writer.writerow(r)


def resumen_por_categoria(resultados: List[Dict]) -> List[Dict]:
    """Genera tabla resumen por categoría."""
    from collections import defaultdict

    grupos: Dict[str, List[float]] = defaultdict(list)
    criterios: Dict[str, set] = defaultdict(set)

    for r in resultados:
        cat = r["categoria"]
        grupos[cat].append(r["confianza_minima"])
        criterios[cat].add(r["criterio_calibracion"])

    resumen = []
    for cat in sorted(grupos.keys()):
        vals = grupos[cat]
        resumen.append({
            "categoria": cat,
            "n_intents": len(vals),
            "confianza_min": round(min(vals), 2),
            "confianza_max": round(max(vals), 2),
            "confianza_promedio": round(sum(vals) / len(vals), 3),
            "criterios_usados": sorted(criterios[cat]),
        })
    return resumen


def exportar_resumen_csv(resumen: List[Dict], output_path: Path) -> None:
    """Exporta la tabla resumen por categoría en CSV."""
    campos = [
        "categoria", "n_intents", "confianza_min", "confianza_max",
        "confianza_promedio", "criterios_usados",
    ]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        for row in resumen:
            row_out = dict(row)
            row_out["criterios_usados"] = " | ".join(row_out["criterios_usados"])
            writer.writerow(row_out)


# ─────────────────────────────────────────────────────────────────────────────
# PUNTO DE ENTRADA PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────

def main(project_root: Optional[Path] = None, output_dir: Optional[Path] = None):
    """
    Ejecuta la calibración completa end-to-end:
      1. Carga keywords e intents.
      2. Calibra todos los intents.
      3. Actualiza intents.json.
      4. Exporta JSON y CSV de resultados.
      5. Exporta resumen por categoría.
      6. Imprime reporte en consola.
    """
    root = project_root or _find_project_root()
    out_dir = output_dir or (root / "tools" / "calibracion_output")
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("  CALIBRADOR DE CONFIANZA MÍNIMA — Chatbot EPIIS-UNSAAC")
    print(f"  Versión: {VERSION_CALIBRACION}")
    print(f"  Directorio raíz: {root}")
    print("=" * 70)

    # Paso 1: Calibración
    print("\n[1/5] Ejecutando calibración de todos los intents...")
    resultados = ejecutar_calibracion(root)
    print(f"      → {len(resultados)} intents procesados.")

    # Paso 2: Actualizar intents.json
    print("\n[2/5] Actualizando knowledge_base/intents.json...")
    path_intents = actualizar_intents_json(resultados, root)
    print(f"      → Guardado en: {path_intents}")

    # Paso 3: Exportar JSON
    json_path = out_dir / "calibracion_resultados.json"
    print(f"\n[3/5] Exportando JSON detallado...")
    exportar_json(resultados, json_path)
    print(f"      → {json_path}")

    # Paso 4: Exportar CSV de resultados
    csv_path = out_dir / "calibracion_resultados.csv"
    print(f"\n[4/5] Exportando CSV de resultados...")
    exportar_csv(resultados, csv_path)
    print(f"      → {csv_path}")

    # Paso 5: Resumen por categoría
    resumen = resumen_por_categoria(resultados)
    resumen_csv_path = out_dir / "resumen_por_categoria.csv"
    exportar_resumen_csv(resumen, resumen_csv_path)
    print(f"\n[5/5] Exportando resumen por categoría...")
    print(f"      → {resumen_csv_path}")

    # Reporte en consola
    print("\n" + "=" * 70)
    print("  RESUMEN POR CATEGORÍA")
    print("=" * 70)
    print(f"{'Cat':<6} {'N':>4} {'Min':>6} {'Max':>6} {'Prom':>7}  Criterios")
    print("-" * 70)
    for r in resumen:
        crit = " | ".join(r["criterios_usados"])
        print(
            f"{r['categoria']:<6} {r['n_intents']:>4} "
            f"{r['confianza_min']:>6.2f} {r['confianza_max']:>6.2f} "
            f"{r['confianza_promedio']:>7.3f}  {crit}"
        )

    print("\n" + "=" * 70)
    print("  DETALLE POR INTENT (primeros 10 para verificación)")
    print("=" * 70)
    print(f"{'intent_id':<45} {'conf_ant':>8} {'conf_new':>8}  criterio")
    print("-" * 90)
    for r in resultados[:10]:
        ant = r.get("confianza_minima_anterior", "—")
        ant_str = f"{ant:.2f}" if isinstance(ant, float) else str(ant)
        print(
            f"{r['intent_id']:<45} {ant_str:>8} "
            f"{r['confianza_minima']:>8.2f}  {r['criterio_calibracion']}"
        )
    if len(resultados) > 10:
        print(f"  ... y {len(resultados) - 10} intents más (ver CSV).")

    print("\n✓ Calibración completada exitosamente.")
    return resultados, resumen


if __name__ == "__main__":
    main()
