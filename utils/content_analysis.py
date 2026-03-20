def detect_language(text: str) -> str:
    text_lower = text.lower()

    english_markers = ["the", "and", "search", "privacy", "contact", "login"]
    spanish_markers = ["el", "la", "de", "buscar", "privacidad", "contacto", "iniciar"]

    en_score = sum(text_lower.count(word) for word in english_markers)
    es_score = sum(text_lower.count(word) for word in spanish_markers)

    if en_score > es_score and en_score > 0:
        return "en"
    if es_score > en_score and es_score > 0:
        return "es"
    return "unknown"