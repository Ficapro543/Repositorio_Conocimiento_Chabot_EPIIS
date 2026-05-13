# intent_matcher.py
# Motor de coincidencia de intents basado en keywords - Chatbot EPIIS-UNSAAC

import json
from knowledge_base_loader import get_corpus, get_by_intent
from pathlib import Path

def load_keywords() -> list:
    with open("Repositorio_Conocimiento/knowledge_base/keywords.json",
              encoding="utf-8") as f:
        return json.load(f)["keywords"]

def preprocess(text: str) -> list:
    """Tokeniza y normaliza el texto del usuario."""
    return text.lower().strip().split()

def match_intent(user_input: str) -> tuple[str | None, float]:
    """
    Busca el intent más probable dado el input del usuario.
    Retorna (intent_id, score) o (None, 0.0) si no hay coincidencia.
    """
    tokens = preprocess(user_input)
    keywords_db = load_keywords()
    best_intent = None
    best_score = 0.0

    for entry in keywords_db:
        all_kw = (entry["keywords_primarios"] +
                  entry["keywords_secundarios"] +
                  entry.get("sinonimos", []))
        # Score: fracción de keywords del intent encontradas en el input
        matches = sum(1 for kw in all_kw
                      if any(kw.lower() in token or token in kw.lower()
                             for token in tokens))
        score = matches / max(len(all_kw), 1)
        if score > best_score:
            best_score = score
            best_intent = entry["intent_id"]

    return (best_intent, best_score) if best_score > 0.1 else (None, 0.0)

def get_response(user_input: str) -> str:
    """Pipeline completo: input → intent → respuesta."""
    intent_id, score = match_intent(user_input)
    if intent_id is None:
        return ("Lo siento, no entendí tu consulta. Puedes preguntar sobre " 
                "tutorías, matrícula, titulación, prácticas, bienestar " 
                "o servicios universitarios.")
    entry = get_by_intent(intent_id)
    if entry:
        return entry["respuesta"]
    return "Consulta registrada pero respuesta no disponible en esta versión."

# --- Ejemplo de uso ---
if __name__ == "__main__":
    consultas = [
        "qué es la tutoría académica",
        "cuándo es la matrícula",
        "cómo me titulo en la EPIIS",
        "requisitos para prácticas"
    ]
    for q in consultas:
        print(f"Usuario: {q}")
        print(f"Bot: {get_response(q)}")
        print("-" * 60)
