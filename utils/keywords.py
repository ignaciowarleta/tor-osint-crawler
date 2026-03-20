KEYWORDS = [
    "login", "password", "admin", "account",
    "bitcoin", "wallet", "market",
    "forum", "thread", "post",
    "secure", "contact", "email",
    "leak", "database"
]


def extract_keywords(text: str) -> dict:
    text_lower = text.lower()
    found = {}

    for keyword in KEYWORDS:
        count = text_lower.count(keyword)
        if count > 0:
            found[keyword] = count

    return found