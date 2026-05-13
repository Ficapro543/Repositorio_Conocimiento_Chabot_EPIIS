
# knowledge_base_loader.py
# Módulo de carga del repositorio de conocimientos - Chatbot EPIIS-UNSAAC

import json
import os
from pathlib import Path

BASE_DIR = Path("Repositorio_Conocimiento")

def load_json(filepath: str) -> dict | list:
    """Carga un archivo JSON del repositorio."""
    full_path = BASE_DIR / filepath
    with open(full_path, "r", encoding="utf-8") as f:
        return json.load(f)

def get_corpus() -> list:
    """Retorna el corpus completo de 100 entradas."""
    return load_json("corpus/corpus_general.json")

def get_by_category(categoria_id: str) -> list:
    """Filtra entradas del corpus por categoría (TUT, MAT, etc.)."""
    corpus = get_corpus()
    return [e for e in corpus if e["categoria"] == categoria_id]

def get_by_intent(intent_id: str) -> dict | None:
    """Recupera una entrada específica por su intent."""
    faq = load_json("knowledge_base/faq_index.json")
    mapa = faq["busqueda_rapida"]["mapa_muestra"]
    if intent_id in mapa:
        entry_id = mapa[intent_id]
        corpus = get_corpus()
        return next((e for e in corpus if e["id"] == entry_id), None)
    return None

def get_keywords(intent_id: str) -> list:
    """Retorna las keywords asociadas a un intent."""
    kw_data = load_json("knowledge_base/keywords.json")
    for kw in kw_data["keywords"]:
        if kw["intent_id"] == intent_id:
            return kw["keywords_primarios"] + kw["keywords_secundarios"]
    return []
