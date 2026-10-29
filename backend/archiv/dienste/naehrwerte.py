"""
Nährwert-Suche in den beiden kostenlosen Datenbanken

Open Food Facts -> Markenprodukte (Nutella, Milka, Spar-Eigenmarke, ...)
USDA FoodData Central -> generische Zutaten (Haferflocken, Huhn, Apfel, ...)

Beide liefern Werte pro 100 g, das Hochrechnen auf die tatsaechliche Menge passiert
erst in ernaehrung.py
"""

import httpx

from app.config import EINSTELLUNGEN

OFF_URL = "https://world.openfoodfacts.org/cgi/search.pl"
USDA_URL = "https://api.nal.usda.gov/fdc/v1/foods/search"

# USDA-Nummern der vier Werte, die uns interessieren
USDA_NUMMERN = {"1008": "kcal", "1003": "eiweiss_g", "1005": "kohlenhydrate_g", "1004": "fett_g"}


def zahl_oder_null(wert):
    if wert is None:
        return 0.0
    try:
        return float(wert)
    except (TypeError, ValueError):
        return 0.0


def open_food_facts_suchen(suchbegriff):
    """
    Eingabe: Suchbegriff, möglichst der Produktname wie am Etikett
    Ausgabe: {"name":..., "kcal":..., "eiweiss_g":..., "kohlenhydrate_g":..., "fett_g":...} pro 100 g
             oder None wenn nichts Brauchbares gefunden wurde
    """
    parameter = {
        "search_terms": suchbegriff,
        "search_simple": 1,
        "action": "process",
        "json": 1,
        "page_size": 5,
        "fields": "product_name,nutriments",
    }

    try:
        antwort = httpx.get(OFF_URL, params=parameter, timeout=15, headers={"User-Agent": "Steward/1.0"})
        antwort.raise_for_status()
        daten = antwort.json()
    except Exception:
        return None

    produkte = daten.get("products", [])

    for produkt in produkte:
        naehrwerte = produkt.get("nutriments", {})
        kcal = zahl_oder_null(naehrwerte.get("energy-kcal_100g"))
        if kcal <= 0:
            continue

        name = produkt.get("product_name", "")
        if name.strip() == "":
            name = suchbegriff

        return {
            "name": name,
            "kcal": kcal,
            "eiweiss_g": zahl_oder_null(naehrwerte.get("proteins_100g")),
            "kohlenhydrate_g": zahl_oder_null(naehrwerte.get("carbohydrates_100g")),
            "fett_g": zahl_oder_null(naehrwerte.get("fat_100g")),
        }

    return None


def usda_suchen(suchbegriff):
    """
    Eingabe: englischer Suchbegriff, USDA kennt kein Deutsch
    Ausgabe: gleiche Struktur wie open_food_facts_suchen, oder None
    """
    parameter = {
        "query": suchbegriff,
        "pageSize": 3,
        "api_key": EINSTELLUNGEN.usda_api_key,
        "dataType": "Foundation,SR Legacy",
    }

    try:
        antwort = httpx.get(USDA_URL, params=parameter, timeout=15)
        antwort.raise_for_status()
        daten = antwort.json()
    except Exception:
        return None

    treffer = daten.get("foods", [])

    for eintrag in treffer:
        gefunden = {"kcal": 0.0, "eiweiss_g": 0.0, "kohlenhydrate_g": 0.0, "fett_g": 0.0}

        for naehrstoff in eintrag.get("foodNutrients", []):
            nummer = str(naehrstoff.get("nutrientNumber", ""))
            if nummer in USDA_NUMMERN:
                schluessel = USDA_NUMMERN[nummer]
                gefunden[schluessel] = zahl_oder_null(naehrstoff.get("value"))

        if gefunden["kcal"] <= 0:
            continue

        name = eintrag.get("description", suchbegriff)
        gefunden["name"] = name
        return gefunden

    return None


def nachschlagen(suchbegriff_deutsch, suchbegriff_englisch, ist_markenprodukt):
    """
    Fragt beide Datenbanken der Reihe nach, Reihenfolge hängt davon ab ob es
    ein Markenprodukt ist oder eine generische Zutat

    Ausgabe: (werte_pro_100g oder None, "open_food_facts" / "usda" / None)
    """
    if ist_markenprodukt:
        reihenfolge = ["off", "usda"]
    else:
        reihenfolge = ["usda", "off"]

    for quelle in reihenfolge:
        if quelle == "off":
            gefunden = open_food_facts_suchen(suchbegriff_deutsch)
            if gefunden is not None:
                return gefunden, "open_food_facts"
        else:
            if suchbegriff_englisch.strip() != "":
                gefunden = usda_suchen(suchbegriff_englisch)
                if gefunden is not None:
                    return gefunden, "usda"

    return None, None
