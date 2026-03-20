def classify_page(keywords: dict) -> str:
    if not keywords:
        return "unknown"

    if any(k in keywords for k in ["login", "password", "account"]):
        return "login_page"

    if any(k in keywords for k in ["forum", "thread", "post"]):
        return "forum"

    if any(k in keywords for k in ["market", "bitcoin", "wallet"]):
        return "marketplace"

    if any(k in keywords for k in ["secure", "contact", "email"]):
        return "service"

    if any(k in keywords for k in ["leak", "database"]):
        return "leak_site"

    return "general"