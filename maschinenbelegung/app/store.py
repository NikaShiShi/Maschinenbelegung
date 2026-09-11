"""Datenhaltung.

Aktuell läuft alles im Arbeitsspeicher (Neustart = Daten weg).
Die Anwendung greift ausschließlich über das Protokoll `Repository` zu -
für die echte Datenbank muss nur `DbRepository` unten ausgefüllt und in
`main.py` statt `InMemoryRepository` gesetzt werden.
"""

import threading
import uuid
from datetime import datetime
from typing import Protocol

from .models import Buchung


class Repository(Protocol):
    def anlegen(self, b: Buchung) -> Buchung: ...
    def holen(self, buchung_id: str) -> Buchung | None: ...
    def stornieren(self, buchung_id: str, durch: str) -> Buchung | None: ...
    def suchen(
        self,
        maschine_id: str | None = None,
        benutzer_id: str | None = None,
        von: datetime | None = None,
        bis: datetime | None = None,
        mit_stornierten: bool = False,
    ) -> list[Buchung]: ...


def neue_id() -> str:
    return uuid.uuid4().hex[:12]


class InMemoryRepository:
    """Platzhalter-Speicher für Entwicklung und Demo."""

    def __init__(self) -> None:
        self._daten: dict[str, Buchung] = {}
        self._lock = threading.Lock()

    def anlegen(self, b: Buchung) -> Buchung:
        with self._lock:
            self._daten[b.id] = b
        return b

    def holen(self, buchung_id: str) -> Buchung | None:
        return self._daten.get(buchung_id)

    def stornieren(self, buchung_id: str, durch: str) -> Buchung | None:
        with self._lock:
            b = self._daten.get(buchung_id)
            if b is None or b.storniert:
                return b
            b.storniert_am = datetime.now()
            b.storniert_von = durch
            return b

    def suchen(
        self,
        maschine_id: str | None = None,
        benutzer_id: str | None = None,
        von: datetime | None = None,
        bis: datetime | None = None,
        mit_stornierten: bool = False,
    ) -> list[Buchung]:
        treffer = []
        for b in self._daten.values():
            if not mit_stornierten and b.storniert:
                continue
            if maschine_id and b.maschine_id != maschine_id:
                continue
            if benutzer_id and b.benutzer_id != benutzer_id:
                continue
            if von and b.ende <= von:
                continue
            if bis and b.start >= bis:
                continue
            treffer.append(b)
        return sorted(treffer, key=lambda x: x.start)


# === TODO DB-ANBINDUNG =====================================================
# Vorgeschlagenes Schema (MS SQL / PostgreSQL):
#
#   CREATE TABLE buchung (
#       id            CHAR(12)     PRIMARY KEY,
#       maschine_id   VARCHAR(10)  NOT NULL REFERENCES maschine(maschine_id),
#       benutzer_id   VARCHAR(64)  NOT NULL,   -- HD-Account / AD-sAMAccountName
#       benutzer_name VARCHAR(128) NOT NULL,
#       start_zeit    DATETIME2    NOT NULL,
#       end_zeit      DATETIME2    NOT NULL,
#       zweck         VARCHAR(64)  NOT NULL,
#       bemerkung     VARCHAR(500) NULL,
#       erstellt_am   DATETIME2    NOT NULL DEFAULT SYSDATETIME(),
#       storniert_am  DATETIME2    NULL,
#       storniert_von VARCHAR(64)  NULL
#   );
#   CREATE INDEX ix_buchung_maschine_zeit ON buchung (maschine_id, start_zeit, end_zeit);
#
# Wichtig: Die Überschneidungsprüfung in services.py läuft aktuell in Python.
# Bei mehreren Web-Workern gehört sie zusätzlich in die DB - entweder per
# Transaktion mit SERIALIZABLE oder als Constraint/Trigger, sonst können zwei
# gleichzeitige Buchungen dieselbe Maschine belegen.
# ===========================================================================
class DbRepository:
    """Noch nicht angebunden - hier kommt SQLAlchemy/pyodbc rein."""

    def __init__(self, dsn: str) -> None:
        self.dsn = dsn
        raise NotImplementedError("DB-Anbindung offen - siehe TODO in store.py")

    def anlegen(self, b: Buchung) -> Buchung:          # pragma: no cover
        raise NotImplementedError

    def holen(self, buchung_id: str) -> Buchung | None:  # pragma: no cover
        raise NotImplementedError

    def stornieren(self, buchung_id: str, durch: str) -> Buchung | None:  # pragma: no cover
        raise NotImplementedError

    def suchen(self, **kwargs) -> list[Buchung]:       # pragma: no cover
        raise NotImplementedError
