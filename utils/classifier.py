def classify_page(keywords: dict, has_form: bool, internal_links: int, external_onion_links: int, clearnet_links: int) -> tuple[str, float]:
    if not keywords:
        return "unknown", 0.2

    login_hits = sum(keywords.get(k, 0) for k in ["login", "password", "account", "admin"])
    forum_hits = sum(keywords.get(k, 0) for k in ["forum", "thread", "post", "reply"])
    market_hits = sum(keywords.get(k, 0) for k in ["market", "bitcoin", "wallet", "cart", "order"])
    leak_hits = sum(keywords.get(k, 0) for k in ["leak", "database", "dump"])
    service_hits = sum(keywords.get(k, 0) for k in ["secure", "contact", "email", "support"])
    directory_hits = sum(keywords.get(k, 0) for k in ["index", "search", "links", "directory"])

    if has_form and login_hits >= 2:
        return "login_portal", 0.9

    if forum_hits >= 2:
        return "forum", 0.85

    if market_hits >= 2:
        return "marketplace", 0.85

    if leak_hits >= 1:
        return "leak_site", 0.9

    if directory_hits >= 2 and (external_onion_links >= 3 or internal_links >= 5):
        return "directory", 0.8

    if service_hits >= 2:
        return "service", 0.7

    return "general", 0.5