"""Fachlogik: Buchen, Stornieren, Auslastung, Tafel-Status."""

from datetime import date, datetime, timedelta
from typing import Iterator

from . import config, machines
from .auth import Benutzer
from .models import Buchung, BuchungsFehler
from .store import Repository, neue_id


# --------------------------------------------------------------- Buchen ----
def spaetestes_ende() -> datetime:
    """Ende des Buchungsfensters: heute + 6 Monate."""
    heute = date.today()
    monat = heute.month - 1 + config.VORLAUF_MONATE
    jahr = heute.year + monat // 12
    monat = monat % 12 + 1
    tag = min(heute.day, [31, 29 if jahr % 4 == 0 and (jahr % 100 != 0 or jahr % 400 == 0)
                          else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][monat - 1])
    return datetime.combine(date(jahr, monat, tag), config.BETRIEB_ENDE)


def buchen(
    repo: Repository,
    benutzer: Benutzer,
    maschine_id: str,
    start: datetime,
    ende: datetime,
    zweck: str,
    bemerkung: str = "",
) -> Buchung:
    maschine = machines.holen(maschine_id)
    if maschine is None:
        raise BuchungsFehler("Diese Maschine gibt es nicht.")
    if ende <= start:
        raise BuchungsFehler("Das Ende liegt vor dem Beginn.")

    dauer = (ende - start).total_seconds() / 60
    if dauer < config.MIN_DAUER_MIN:
        raise BuchungsFehler(f"Mindestens {config.MIN_DAUER_MIN} Minuten buchen.")
    if dauer > config.MAX_DAUER_STD * 60:
        raise BuchungsFehler(f"Höchstens {config.MAX_DAUER_STD} Stunden am Stück buchen.")
    if ende < datetime.now():
        raise BuchungsFehler("Der Zeitraum liegt in der Vergangenheit.")
    if ende > spaetestes_ende():
        raise BuchungsFehler(
            f"Buchbar bis {spaetestes_ende():%d.%m.%Y} - {config.VORLAUF_MONATE} Monate im Voraus."
        )
    if zweck not in config.ZWECKE:
        raise BuchungsFehler("Bitte einen Verwendungszweck auswählen.")

    for vorhanden in repo.suchen(maschine_id=maschine.id, von=start, bis=ende):
        if vorhanden.ueberschneidet(start, ende):
            raise BuchungsFehler(
                f"{maschine.bezeichnung} ist am {vorhanden.start:%d.%m.} von "
                f"{vorhanden.start:%H:%M} bis {vorhanden.ende:%H:%M} schon belegt."
            )

    return repo.anlegen(
        Buchung(
            id=neue_id(),
            maschine_id=maschine.id,
            benutzer_id=benutzer.id,
            benutzer_name=benutzer.name,
            start=start,
            ende=ende,
            zweck=zweck,
            bemerkung=bemerkung.strip()[:500],
        )
    )


def stornieren(repo: Repository, benutzer: Benutzer, buchung_id: str) -> Buchung:
    b = repo.holen(buchung_id)
    if b is None:
        raise BuchungsFehler("Buchung nicht gefunden.")
    if b.storniert:
        raise BuchungsFehler("Diese Buchung ist bereits storniert.")
    if b.benutzer_id != benutzer.id and not benutzer.ist_ausbilder:
        raise BuchungsFehler("Fremde Buchungen kann nur ein Ausbilder stornieren.")
    if b.ende < datetime.now():
        raise BuchungsFehler("Vergangene Buchungen lassen sich nicht mehr stornieren.")
    return repo.stornieren(buchung_id, benutzer.id)


# ---------------------------------------------------------------- Tafel ----
def tafel(repo: Repository, jetzt: datetime | None = None) -> list[dict]:
    """Status aller Maschinen für den Bildschirm in der Werkstatt."""
    jetzt = jetzt or datetime.now()
    fenster_ende = jetzt + timedelta(days=1)
    zeilen = []
    for m in machines.alle():
        buchungen = repo.suchen(maschine_id=m.id, von=jetzt, bis=fenster_ende)
        aktuell = next((b for b in buchungen if b.laeuft(jetzt)), None)
        naechste = next((b for b in buchungen if b.start > jetzt), None)
        zeilen.append(
            {
                "maschine": m,
                "belegt": aktuell is not None,
                "aktuell": aktuell,
                "naechste": naechste,
                "frei_bis": naechste.start if aktuell is None and naechste else None,
            }
        )
    return zeilen


# ----------------------------------------------------------- Auslastung ----
def _betriebsfenster(von: datetime, bis: datetime) -> Iterator[tuple[datetime, datetime]]:
    tag = von.date()
    while tag <= bis.date():
        if tag.weekday() in config.BETRIEB_TAGE:
            start = max(datetime.combine(tag, config.BETRIEB_START), von)
            ende = min(datetime.combine(tag, config.BETRIEB_ENDE), bis)
            if start < ende:
                yield start, ende
        tag += timedelta(days=1)


def auslastung(repo: Repository, von: datetime, bis: datetime) -> list[dict]:
    """Belegte Minuten je Maschine im Verhältnis zur Werkstattzeit."""
    fenster = list(_betriebsfenster(von, bis))
    verfuegbar = sum((e - s).total_seconds() / 60 for s, e in fenster) or 1

    ergebnis = []
    for m in machines.alle():
        belegt = 0.0
        buchungen = repo.suchen(maschine_id=m.id, von=von, bis=bis)
        for b in buchungen:
            for s, e in fenster:
                start = max(b.start, s)
                ende = min(b.ende, e)
                if start < ende:
                    belegt += (ende - start).total_seconds() / 60
        ergebnis.append(
            {
                "maschine": m,
                "anzahl": len(buchungen),
                "stunden": round(belegt / 60, 1),
                "quote": round(belegt / verfuegbar * 100),
            }
        )
    return ergebnis
