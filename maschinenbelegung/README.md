# Maschinenbelegung – Ausbildungswerkstatt

Buchungssystem für 12 Dreh- und 12 Fräsmaschinen. FastAPI + Jinja2, keine externe
Datenbank nötig, um es zu starten.

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

| Adresse            | Zweck |
|--------------------|-------|
| `/`                | Buchungsformular |
| `/m/DRE-01`        | Ziel des QR-Codes, Maschine schon ausgewählt |
| `/buchungen`       | alle Buchungen, Filter, Storno |
| `/auslastung`      | Quote je Maschine für einen Zeitraum |
| `/tafel`           | Bildschirm in der Werkstatt, rot/grün, ohne Anmeldung |
| `/api/tafel`       | derselbe Stand als JSON |
| `/qr`              | Druckvorlage aller 24 Aufkleber |

## Aufbau

```
app/config.py     Regeln: 6 Monate Vorlauf, Betriebszeiten, Zwecke
app/machines.py   Maschinenstammdaten          -> TODO DB-ANBINDUNG
app/models.py     Buchung
app/store.py      Repository, In-Memory        -> TODO DB-ANBINDUNG (inkl. Schema)
app/auth.py       Anmeldung, Ausweis           -> TODO ANMELDUNG / TODO AUSWEIS
app/services.py   Prüfungen, Konflikte, Auslastung
app/main.py       Routen
tools/qr_export.py  QR-Codes als PNG-Dateien exportieren
```

Alle offenen Stellen sind im Code mit `# === TODO ... ===` markiert:
`grep -rn "TODO" app/`

## Was noch fehlt

**Datenbank.** Läuft komplett im Arbeitsspeicher, Neustart löscht alles. In
`store.py` steht das vorgeschlagene Schema; anzubinden ist nur `DbRepository`,
danach in `main.py` eine Zeile tauschen. Wichtig dabei: die Prüfung auf
Überschneidung läuft aktuell in Python – bei mehreren Workern gehört sie
zusätzlich in die Datenbank, sonst kann dieselbe Maschine doppelt belegt werden.

**Anmeldung.** Der Login nimmt jede Kennung ohne Prüfung an. Sinnvoll ist
Kerberos über den Webserver (Kennung kommt als `REMOTE_USER`) oder Entra ID per
OIDC; die Rolle „ausbilder" sollte aus einer AD-Gruppe kommen statt aus einem
Auswahlfeld.

**Ausweis scannen.** Vor dem Bauen zu klären: welcher Kartentyp im Einsatz ist,
ob die Karten-UID überhaupt gelesen werden darf (personenbezogen, Betriebsrat)
und ob es eine Zuordnung Karte → Personalnummer → HD-Account gibt. Wenn ja, ist
ein USB-Leser im Keyboard-Wedge-Modus der kleinste Weg: er tippt die UID in ein
Eingabefeld, `/api/ausweis` ist dafür schon angelegt.

**QR-Codes.** Vor dem Druck `MB_BASE_URL` auf die endgültige Adresse setzen,
sonst sind alle 24 Aufkleber wertlos. Die URL sollte kurz und stabil sein.

## Offene Fragen an die Ausbildung

- Darf ein Azubi ohne Ausbilder buchen, oder braucht es eine Freigabe?
- Maximale Buchungsdauer und Buchungen pro Person und Woche begrenzen?
- Was passiert mit einer Buchung, zu der niemand erscheint – nach 15 Minuten
  automatisch frei?
- Sollen Rüst- und Wartungszeiten als eigene Buchungsart mitlaufen?
