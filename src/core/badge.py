def get_badge_url(level: str) -> str:
    BADGE_URLS = {
        "WIP": "https://img.shields.io/badge/DevOps%20Maturity-WIP-blue.svg",
        "PASSING": "https://img.shields.io/badge/DevOps%20Maturity-PASSING-green.svg",
        "BRONZE": "https://img.shields.io/badge/DevOps%20Maturity-BRONZE-yellow.svg",
        "SILVER": "https://img.shields.io/badge/DevOps%20Maturity-SILVER-silver.svg",
        "GOLD": "https://img.shields.io/badge/DevOps%20Maturity-GOLD-gold.svg",
    }
    return BADGE_URLS.get(level.upper(), BADGE_URLS["WIP"])
