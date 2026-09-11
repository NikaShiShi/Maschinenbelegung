"""Zentrale Einstellungen der Maschinenbelegung."""

import os
from datetime import time

# Basis-URL, die in die QR-Codes an den Maschinen gedruckt wird.
BASE_URL = os.getenv("MB_BASE_URL", "http://localhost:8000")

# Buchungsregeln
VORLAUF_MONATE = 6          # so weit im Voraus darf gebucht werden
MIN_DAUER_MIN = 15          # kürzeste Buchung
MAX_DAUER_STD = 12          # längste Einzelbuchung
STORNO_FRIST_MIN = 0        # 0 = jederzeit stornierbar

# Werkstattzeiten - Grundlage für die Auslastungsberechnung
BETRIEB_START = time(6, 0)
BETRIEB_ENDE = time(16, 0)
BETRIEB_TAGE = {0, 1, 2, 3, 4}   # Mo-Fr

# Anzeige
BOARD_REFRESH_SEK = 30
ZEITZONE = "Europe/Berlin"

# Zwecke für das Auswahlfeld im Formular
ZWECKE = [
    "Ausbildung / Lehrgang",
    "Prüfungsvorbereitung",
    "Azubi-Projekt",
    "Fertigungsauftrag",
    "Instandhaltung / Rüsten",
    "Sonstiges",
]
