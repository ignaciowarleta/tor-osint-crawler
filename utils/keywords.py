KEYWORDS = [
    "login", "password", "admin", "account",
    "bitcoin", "wallet", "market", "cart", "order",
    "forum", "thread", "post", "reply",
    "secure", "contact", "email", "support",
    "leak", "database", "dump",
    "index", "search", "links", "directory",
]


def extract_keywords(text: str) -> dict:
    text_lower = text.lower()
    found = {}

    for keyword in KEYWORDS:
        count = text_lower.count(keyword)
        if count > 0:
            found[keyword] = count

    return found