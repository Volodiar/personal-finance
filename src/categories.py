"""
categories.py - Category definitions and regex-based matching engine.

This module handles the automatic categorization of bank transactions
using predefined keyword patterns and user-learned mappings.
"""

import re
from typing import Optional

# Category definitions with keyword patterns (case-insensitive)
CATEGORIES = {
    "Housing & Bills": [
        r"alquiler", r"rent", r"hipoteca", r"mortgage", r"agua", r"water",
        r"luz", r"electric", r"gas", r"internet", r"telefono", r"phone",
        r"seguro.*hogar", r"home.*insurance", r"comunidad", r"impuesto",
        r"ibi", r"basura", r"garbage", r"utilities"
    ],
    "Groceries": [
        r"mercadona", r"carrefour", r"lidl", r"aldi", r"dia", r"eroski",
        r"alcampo", r"hipercor", r"supermercado", r"supermarket", r"grocery",
        r"alimentacion", r"frutas", r"verduras", r"primaprix", r"consum",
        r"bonarea", r"condis", r"ahorramas", r"simply"
    ],
    "Food & Dining": [
        r"restaurante", r"restaurant", r"bar ", r"cafe", r"cafeteria",
        r"mcdonalds", r"burger", r"pizza", r"kebab", r"sushi", r"wok",
        r"just.*eat", r"glovo", r"uber.*eats", r"deliveroo", r"takeaway",
        r"comida", r"cena", r"almuerzo", r"desayuno", r"tapas"
    ],
    "Subscriptions": [
        r"netflix", r"spotify", r"hbo", r"disney", r"amazon.*prime",
        r"youtube.*premium", r"apple.*music", r"icloud", r"google.*one",
        r"dropbox", r"notion", r"canva", r"adobe", r"microsoft.*365",
        r"gym.*member", r"gimnasio", r"suscripcion", r"subscription"
    ],
    "Transport": [
        r"gasolina", r"fuel", r"repsol", r"cepsa", r"bp ", r"shell",
        r"parking", r"aparcamiento", r"metro", r"bus ", r"autobus",
        r"renfe", r"tren", r"train", r"taxi", r"uber", r"cabify", r"bolt",
        r"blablacar", r"peaje", r"toll", r"itv", r"taller", r"mecanico"
    ],
    "Leisure & Entertainment": [
        r"cine", r"cinema", r"teatro", r"theater", r"concierto", r"concert",
        r"museo", r"museum", r"parque.*atracciones", r"zoo", r"aquarium",
        r"escape.*room", r"bolos", r"bowling", r"karaoke", r"discoteca",
        r"club", r"fiesta", r"party", r"viaje", r"travel", r"hotel",
        r"airbnb", r"booking", r"vuelo", r"flight", r"ryanair", r"vueling"
    ],
    "Shopping": [
        r"zara", r"hm", r"h&m", r"mango", r"primark", r"pull.*bear",
        r"bershka", r"stradivarius", r"massimo.*dutti", r"uniqlo",
        r"decathlon", r"mediamarkt", r"fnac", r"el.*corte.*ingles",
        r"amazon", r"aliexpress", r"ikea", r"leroy.*merlin", r"tienda",
        r"store", r"compra", r"purchase", r"ropa", r"clothes"
    ],
    "Health & Wellness": [
        r"farmacia", r"pharmacy", r"medico", r"doctor", r"hospital",
        r"clinica", r"clinic", r"dentista", r"dentist", r"optica",
        r"fisio", r"physio", r"psicologo", r"therapy", r"spa",
        r"peluqueria", r"hairdresser", r"estetica", r"beauty"
    ],
    "Financial": [
        r"transferencia", r"transfer", r"comision", r"commission", r"fee",
        r"interes", r"interest", r"prestamo", r"loan", r"credito", r"credit",
        r"inversion", r"investment", r"ahorro", r"savings", r"bizum",
        r"paypal", r"revolut", r"n26", r"wise"
    ]
}

# Special categories:
# - "Income" is auto-assigned to positive amounts (not expenses)
# - "Others" is a manual-only fallback for uncategorized expenses
ALL_CATEGORIES = list(CATEGORIES.keys()) + ["Income", "Others"]


def categorize_concept(concept: str, learned_mappings: dict) -> Optional[str]:
    """
    Categorize a transaction concept.
    
    Priority:
    1. Check learned mappings first (exact match, case-insensitive)
    2. Check predefined keyword patterns
    3. Return None if no match (user must manually select)
    
    Args:
        concept: The transaction concept/description
        learned_mappings: Dict of concept -> category from user corrections
        
    Returns:
        Category name or None if no match found
    """
    concept_lower = concept.lower().strip()
    
    # Priority 1: Check learned mappings (exact match)
    for learned_concept, category in learned_mappings.items():
        if learned_concept.lower() == concept_lower:
            return category
    
    # Priority 2: Check predefined keyword patterns
    for category, patterns in CATEGORIES.items():
        for pattern in patterns:
            if re.search(pattern, concept_lower, re.IGNORECASE):
                return category
    
    # No match found - user must manually categorize
    return None


def get_category_options() -> list:
    """Get list of all available categories for dropdown selection."""
    return ALL_CATEGORIES


def get_category_color(category: str) -> str:
    """Get a consistent color for each category (for charts)."""
    colors = {
        "Housing & Bills": "#FF6B6B",
        "Groceries": "#4ECDC4",
        "Food & Dining": "#FFE66D",
        "Subscriptions": "#95E1D3",
        "Transport": "#A8E6CF",
        "Leisure & Entertainment": "#DDA0DD",
        "Shopping": "#F7DC6F",
        "Health & Wellness": "#85C1E9",
        "Financial": "#BB8FCE",
        "Income": "#2ECC71",  # Green for income
        "Others": "#AEB6BF"
    }
    return colors.get(category, "#AEB6BF")
