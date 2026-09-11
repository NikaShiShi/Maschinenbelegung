"""Maschinenstammdaten.

# === TODO DB-ANBINDUNG =====================================================
# Diese Liste ist ein Platzhalter. Später aus der Stammdatentabelle laden:
#   SELECT maschine_id, bezeichnung, typ, standort, aktiv FROM maschine
# Solange die Liste hier steht, sind Inventarnummer/Standort frei erfunden.
# ===========================================================================
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Maschine:
    id: str
    bezeichnung: str
    typ: str          # "Drehen" | "Fräsen"
    standort: str
    aktiv: bool = True


def _bauen() -> list[Maschine]:
    liste: list[Maschine] = []
    for i in range(1, 13):
        liste.append(
            Maschine(
                id=f"DRE-{i:02d}",
                bezeichnung=f"Drehmaschine {i:02d}",
                typ="Drehen",
                standort=f"Halle 3 · Reihe A · Platz {i:02d}",
            )
        )
    for i in range(1, 13):
        liste.append(
            Maschine(
                id=f"FRA-{i:02d}",
                bezeichnung=f"Fräsmaschine {i:02d}",
                typ="Fräsen",
                standort=f"Halle 3 · Reihe B · Platz {i:02d}",
            )
        )
    return liste


MASCHINEN: list[Maschine] = _bauen()
NACH_ID: dict[str, Maschine] = {m.id: m for m in MASCHINEN}


def alle(typ: str | None = None) -> list[Maschine]:
    return [m for m in MASCHINEN if m.aktiv and (typ is None or m.typ == typ)]


def holen(maschine_id: str) -> Maschine | None:
    return NACH_ID.get(maschine_id.upper().strip())
