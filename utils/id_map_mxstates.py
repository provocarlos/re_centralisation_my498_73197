import unicodedata
import re


def _normalize(text: str) -> str:
    """Strip accents, punctuation, and extra whitespace from a string."""
    # Equivalent to stri_trans_general(x, "latin-ascii")
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    # Remove punctuation (equivalent to stri_replace_all regex "[:punct:]")
    text = re.sub(r"[^\w\s]", "", text)
    # Remove all whitespace (equivalent to stri_replace_all regex "[:blank:]")
    text = re.sub(r"\s+", "", text)
    return text


def abr_to_state_name(x: str) -> str:
    """
    Convert a Mexican state abbreviation to its full official name.
    Handles multiple common abbreviation variants and is accent/punctuation tolerant.

    Parameters
    ----------
    x : str
        State abbreviation (e.g. 'JAL', 'CDMX', 'mich.').

    Returns
    -------
    str
        Full state name, or the normalized input if no match is found.
    """
    y = _normalize(x).upper()

    mapping = {
        "AGS":    "Aguascalientes",
        "BJC":    "Baja California",
        "BC":     "Baja California",
        "BCS":    "Baja California Sur",
        "CAM":    "Campeche",
        "CAMP":   "Campeche",
        "CHS":    "Chiapas",
        "CHIS":   "Chiapas",
        "CHA":    "Chihuahua",
        "CHIH":   "Chihuahua",
        "CDM":    "Ciudad de México",
        "CDMX":   "Ciudad de México",
        "COA":    "Coahuila",
        "COAH":   "Coahuila",
        "COL":    "Colima",
        "DUR":    "Durango",
        "DGO":    "Durango",
        "MEX":    "México",
        "EDOMEX": "México",
        "GUA":    "Guanajuato",
        "GTO":    "Guanajuato",
        "GUE":    "Guerrero",
        "GRO":    "Guerrero",
        "HID":    "Hidalgo",
        "HGO":    "Hidalgo",
        "JAL":    "Jalisco",
        "MIC":    "Michoacán",
        "MICH":   "Michoacán",
        "MOR":    "Morelos",
        "NAY":    "Nayarit",
        "NOL":    "Nuevo León",
        "NL":     "Nuevo León",
        "OAX":    "Oaxaca",
        "PUE":    "Puebla",
        "QUE":    "Querétaro",
        "QRO":    "Querétaro",
        "QROO":   "Quintana Roo",
        "QUI":    "Quintana Roo",
        "SLP":    "San Luis Potosí",
        "SIN":    "Sinaloa",
        "SON":    "Sonora",
        "TAB":    "Tabasco",
        "TAM":    "Tamaulipas",
        "TAMPS":  "Tamaulipas",
        "TLA":    "Tlaxcala",
        "TLAX":   "Tlaxcala",
        "VER":    "Veracruz",
        "YUC":    "Yucatán",
        "ZAC":    "Zacatecas",
        "NAC":    "Nacional",
        "REP":    "Nacional",
    }

    return mapping.get(y, y)


def _normalize_title(text: str) -> str:
    """Strip accents and punctuation, then apply title case."""
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^\w\s]", "", text)
    return text.title()


def state_name_to_abr(state_name: str) -> str:
    """
    Convert a Mexican state full name to its standard abbreviation.
    Handles accent variations, alternate official names (e.g. 'Veracruz de
    Ignacio de la Llave'), and legacy names ('Distrito Federal').

    Parameters
    ----------
    state_name : str
        Full or partial state name (e.g. 'Jalisco', 'michoacán de ocampo').

    Returns
    -------
    str
        Two- or three-letter abbreviation, or the normalized input if no match
        is found.
    """
    y = _normalize_title(state_name)

    # Special case: substring match for Oaxaca variants
    # (mirrors stri_detect fixed="oaxaca", case_insensitive=TRUE)
    if "oaxaca" in state_name.lower():
        return "OAX"

    mapping = {
        "Tabasco":                        "TAB",
        "Nayarit":                        "NAY",
        "Durango":                        "DUR",
        "Oaxaca":                         "OAX",
        "Mexico":                         "MEX",
        "Edomex":                         "MEX",
        "Estado De Mexico":               "MEX",
        "Campeche":                       "CAM",
        "Zacatecas":                      "ZAC",
        "Quintana Roo":                   "QROO",
        "Sonora":                         "SON",
        "Cdmx":                           "CDMX",
        "Distrito Federal":               "CDMX",
        "Ciudad De Mexico":               "CDMX",
        "Veracruz De Ignacio De La Llave":"VER",
        "Veracruz":                       "VER",
        "Baja California Sur":            "BCS",
        "Morelos":                        "MOR",
        "Guanajuato":                     "GTO",
        "Jalisco":                        "JAL",
        "Tamaulipas":                     "TAMPS",
        "Guerrero":                       "GRO",
        "Baja California":                "BJC",
        "Nuevo Leon":                     "NL",
        "Chihuahua":                      "CHIH",
        "San Luis Potosi":                "SLP",
        "Tlaxcala":                       "TLAX",
        "Yucatan":                        "YUC",
        "Puebla":                         "PUE",
        "Coahuila De Zaragoza":           "COAH",
        "Coahuila":                       "COAH",
        "Colima":                         "COL",
        "Hidalgo":                        "HGO",
        "Queretaro":                      "QRO",
        "Sinaloa":                        "SIN",
        "Chiapas":                        "CHIS",
        "Michoacan De Ocampo":            "MICH",
        "Michoacan":                      "MICH",
        "Aguascalientes":                 "AGS",
        "Nacional":                       "NAC",
        "Nacion":                         "NAC",
        "Republica":                      "NAC",
        "Republica Federal":              "NAC",
    }

    return mapping.get(y, y)


# --- INEGI state_code mapping ---

# Canonical abbreviation → INEGI state_code (01–32), assigned alphabetically.
# All abbreviation variants are first resolved to the canonical key via
# abr_to_state_name(), so this dict only needs one entry per state.
_ABR_TO_STATE_CODE: dict[str, str] = {
    "AGS":  1,   # Aguascalientes
    "BJC":  2,   # Baja California
    "BCS":  3,   # Baja California Sur
    "CAM":  4,   # Campeche
    "COAH": 5,   # Coahuila de Zaragoza
    "COL":  6,   # Colima
    "CHIS": 7,   # Chiapas
    "CHIH": 8,   # Chihuahua
    "CDMX": 9,   # Ciudad de México
    "DGO":  10,  # Durango
    "GTO":  11,  # Guanajuato
    "GRO":  12,  # Guerrero
    "HGO":  13,  # Hidalgo
    "JAL":  14,  # Jalisco
    "MEX":  15,  # México
    "MICH": 16,  # Michoacán de Ocampo
    "MOR":  17,  # Morelos
    "NAY":  18,  # Nayarit
    "NL":   19,  # Nuevo León
    "OAX":  20,  # Oaxaca
    "PUE":  21,  # Puebla
    "QRO":  22,  # Querétaro
    "QROO": 23,  # Quintana Roo
    "SLP":  24,  # San Luis Potosí
    "SIN":  25,  # Sinaloa
    "SON":  26,  # Sonora
    "TAB":  27,  # Tabasco
    "TAMPS":28,  # Tamaulipas
    "TLAX": 29,  # Tlaxcala
    "VER":  30,  # Veracruz de Ignacio de la Llave
    "YUC":  31,  # Yucatán
    "ZAC":  32,  # Zacatecas
}

# Map every alternate abbreviation to its canonical key so variant inputs
# resolve correctly (e.g. "BC" → "BJC" → state_code 2).
_ABR_ALIASES: dict[str, str] = {
    "BC":     "BJC",
    "CAMP":   "CAM",
    "CHS":    "CHIS",
    "CHI":    "CHIH",
    "CDM":    "CDMX",
    "COAH":   "COAH",
    "COA":    "COAH",
    "DUR":    "DGO",
    "EDOMEX": "MEX",
    "GUA":    "GTO",
    "GUE":    "GRO",
    "HID":    "HGO",
    "MIC":    "MICH",
    "NOL":    "NL",
    "QUE":    "QRO",
    "QUI":    "QROO",
    "TAM":    "TAMPS",
    "TLA":    "TLAX",
}


def abr_to_state_code(x: str) -> int | None:
    """
    Map a Mexican state abbreviation (any supported variant) to its official
    INEGI state_code numeric identifier (01–32).

    Parameters
    ----------
    x : str
        State abbreviation in any supported variant (e.g. 'JAL', 'BC',
        'edomex', 'chis.').

    Returns
    -------
    int or None
        INEGI state_code (1–32), or None if the abbreviation is not recognised.

    """
    y = _normalize(x).upper()
    canonical = _ABR_ALIASES.get(y, y)
    return _ABR_TO_STATE_CODE.get(canonical, None)

