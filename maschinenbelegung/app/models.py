"""Datenmodell."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Buchung:
    id: str
    maschine_id: str
    benutzer_id: str          # HD-Account (z. B. Windows-/AD-Kennung)
    benutzer_name: str
    start: datetime
    ende: datetime
    zweck: str                # Auswahl aus config.ZWECKE
    bemerkung: str = ""
    erstellt_am: datetime = field(default_factory=datetime.now)
    storniert_am: datetime | None = None
    storniert_von: str | None = None

    @property
    def storniert(self) -> bool:
        return self.storniert_am is not None

    @property
    def dauer_min(self) -> int:
        return int((self.ende - self.start).total_seconds() // 60)

    def laeuft(self, jetzt: datetime) -> bool:
        return not self.storniert and self.start <= jetzt < self.ende

    def ueberschneidet(self, start: datetime, ende: datetime) -> bool:
        return not self.storniert and self.start < ende and start < self.ende


class BuchungsFehler(Exception):
    """Fachlicher Fehler, wird dem Benutzer im Formular angezeigt."""
