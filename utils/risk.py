def calculate_risk_score(
    keywords: dict,
    category: str,
    has_form: bool,
    external_onion_links: int,
    clearnet_links: int,
    total_links: int,
) -> tuple[int, str]:
    score = 0

    sensitive_keywords = {
        "login": 8,
        "password": 10,
        "admin": 6,
        "account": 5,
        "bitcoin": 8,
        "wallet": 8,
        "market": 8,
        "leak": 15,
        "database": 12,
        "dump": 12,
    }

    for keyword, weight in sensitive_keywords.items():
        score += keywords.get(keyword, 0) * weight

    if has_form:
        score += 10

    category_bonus = {
        "login_portal": 20,
        "forum": 10,
        "marketplace": 20,
        "leak_site": 25,
        "directory": 8,
        "service": 5,
        "general": 0,
        "unknown": 0,
    }
    score += category_bonus.get(category, 0)

    if external_onion_links >= 5:
        score += 10
    elif external_onion_links >= 2:
        score += 5

    if clearnet_links >= 3:
        score += 3

    if total_links >= 20:
        score += 5

    score = min(score, 100)

    if score >= 70:
        label = "High"
    elif score >= 40:
        label = "Medium"
    else:
        label = "Low"

    return score, label