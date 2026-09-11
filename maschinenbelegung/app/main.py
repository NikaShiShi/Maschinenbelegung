"""Maschinenbelegung - Ausbildungswerkstatt.

Start:  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"""

import io
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import auth, config, machines, services
from .models import BuchungsFehler
from .store import InMemoryRepository

BASIS = Path(__file__).parent

app = FastAPI(title="Maschinenbelegung")
app.mount("/static", StaticFiles(directory=BASIS / "static"), name="static")
vorlagen = Jinja2Templates(directory=str(BASIS / "templates"))

# === TODO DB-ANBINDUNG: hier später DbRepository(dsn) einsetzen ============
repo = InMemoryRepository()
# ==========================================================================


def _seite(request: Request, name: str, **kontext) -> HTMLResponse:
    benutzer = auth.aktueller_benutzer(request)
    return vorlagen.TemplateResponse(
        request=request,
        name=name,
        context={
            "benutzer": benutzer,
            "cfg": config,
            "jetzt": datetime.now(),
            **kontext,
        },
    )


def _anmeldung_noetig(request: Request) -> RedirectResponse:
    return RedirectResponse(f"/login?weiter={request.url.path}", status_code=303)


# ------------------------------------------------------------ Anmeldung ----
@app.get("/login", response_class=HTMLResponse)
def login_form(request: Request, weiter: str = "/"):
    return _seite(request, "login.html", weiter=weiter, fehler=None)


@app.post("/login")
def login(kennung: str = Form(...), rolle: str = Form("azubi"), weiter: str = Form("/")):
    # === TODO ANMELDUNG: keine Passwortprüfung, reiner Platzhalter =========
    antwort = RedirectResponse(weiter or "/", status_code=303)
    antwort.set_cookie(auth.COOKIE, f"{kennung.strip()}|{rolle}", max_age=60 * 60 * 10,
                       httponly=True, samesite="lax")
    return antwort


@app.get("/logout")
def logout():
    antwort = RedirectResponse("/login", status_code=303)
    antwort.delete_cookie(auth.COOKIE)
    return antwort


# --------------------------------------------------------------- Buchen ----
@app.get("/", response_class=HTMLResponse)
def start(request: Request, maschine: str = ""):
    benutzer = auth.aktueller_benutzer(request)
    if benutzer is None:
        return _anmeldung_noetig(request)
    return _formular(request, maschine)


@app.get("/m/{maschine_id}", response_class=HTMLResponse)
def per_qr(request: Request, maschine_id: str):
    """Ziel des QR-Codes an der Maschine."""
    if auth.aktueller_benutzer(request) is None:
        return RedirectResponse(f"/login?weiter=/m/{maschine_id}", status_code=303)
    return _formular(request, maschine_id, ueber_qr=True)


def _formular(request: Request, maschine_id: str = "", ueber_qr: bool = False,
              fehler: str | None = None, werte: dict | None = None):
    gewaehlt = machines.holen(maschine_id) if maschine_id else None
    naechste = None
    if gewaehlt:
        naechste = repo.suchen(maschine_id=gewaehlt.id, von=datetime.now(),
                               bis=datetime.now() + timedelta(days=14))[:8]
    vorschlag = datetime.now().replace(second=0, microsecond=0)
    vorschlag += timedelta(minutes=(15 - vorschlag.minute % 15) % 15)
    return _seite(
        request,
        "buchen.html",
        gewaehlt=gewaehlt,
        ueber_qr=ueber_qr,
        drehen=machines.alle("Drehen"),
        fraesen=machines.alle("Fräsen"),
        naechste=naechste,
        fehler=fehler,
        werte=werte or {},
        vorschlag_start=vorschlag,
        vorschlag_ende=vorschlag + timedelta(hours=2),
        max_ende=services.spaetestes_ende(),
    )


@app.post("/buchen", response_class=HTMLResponse)
def buchen(
    request: Request,
    maschine_id: str = Form(...),
    start: str = Form(...),
    ende: str = Form(...),
    zweck: str = Form(...),
    bemerkung: str = Form(""),
):
    benutzer = auth.aktueller_benutzer(request)
    if benutzer is None:
        return _anmeldung_noetig(request)
    werte = {"start": start, "ende": ende, "zweck": zweck, "bemerkung": bemerkung}
    try:
        b = services.buchen(
            repo, benutzer, maschine_id,
            datetime.fromisoformat(start), datetime.fromisoformat(ende),
            zweck, bemerkung,
        )
    except ValueError:
        return _formular(request, maschine_id, fehler="Zeitangabe unvollständig.", werte=werte)
    except BuchungsFehler as e:
        return _formular(request, maschine_id, fehler=str(e), werte=werte)
    return RedirectResponse(f"/buchungen?neu={b.id}", status_code=303)


# ----------------------------------------------------------- Buchungen -----
@app.get("/buchungen", response_class=HTMLResponse)
def buchungen(request: Request, maschine: str = "", nur_meine: str = "",
              zeigen: str = "kommend", neu: str = ""):
    benutzer = auth.aktueller_benutzer(request)
    if benutzer is None:
        return _anmeldung_noetig(request)
    von = datetime.now() if zeigen == "kommend" else None
    liste = repo.suchen(
        maschine_id=machines.holen(maschine).id if machines.holen(maschine) else None,
        benutzer_id=benutzer.id if nur_meine else None,
        von=von,
        mit_stornierten=(zeigen == "alle"),
    )
    return _seite(request, "buchungen.html", liste=liste, maschinen=machines.alle(),
                  maschine=maschine, nur_meine=nur_meine, zeigen=zeigen, neu=neu,
                  fehler=None)


@app.post("/buchungen/{buchung_id}/storno")
def storno(request: Request, buchung_id: str):
    benutzer = auth.aktueller_benutzer(request)
    if benutzer is None:
        return _anmeldung_noetig(request)
    try:
        services.stornieren(repo, benutzer, buchung_id)
    except BuchungsFehler as e:
        return _seite(request, "buchungen.html", liste=repo.suchen(von=datetime.now()),
                      maschinen=machines.alle(), maschine="", nur_meine="",
                      zeigen="kommend", neu="", fehler=str(e))
    return RedirectResponse("/buchungen", status_code=303)


# ---------------------------------------------------------- Auslastung -----
@app.get("/auslastung", response_class=HTMLResponse)
def auslastung(request: Request, von: str = "", bis: str = ""):
    if auth.aktueller_benutzer(request) is None:
        return _anmeldung_noetig(request)
    heute = datetime.now().date()
    v = datetime.fromisoformat(von) if von else datetime.combine(heute - timedelta(days=heute.weekday()), config.BETRIEB_START)
    b = datetime.fromisoformat(bis) if bis else datetime.combine(v.date() + timedelta(days=6), config.BETRIEB_ENDE)
    return _seite(request, "auslastung.html",
                  zeilen=services.auslastung(repo, v, b),
                  von=v.date().isoformat(), bis=b.date().isoformat())


# ---------------------------------------------------------------- Tafel ----
@app.get("/tafel", response_class=HTMLResponse)
def tafel(request: Request):
    """Bildschirm in der Werkstatt - ohne Anmeldung erreichbar."""
    return _seite(request, "tafel.html", zeilen=services.tafel(repo))


@app.get("/api/tafel")
def api_tafel():
    daten = [
        {
            "maschine": z["maschine"].id,
            "bezeichnung": z["maschine"].bezeichnung,
            "typ": z["maschine"].typ,
            "belegt": z["belegt"],
            "bis": z["aktuell"].ende.isoformat() if z["aktuell"] else None,
            "durch": z["aktuell"].benutzer_name if z["aktuell"] else None,
            "zweck": z["aktuell"].zweck if z["aktuell"] else None,
        }
        for z in services.tafel(repo)
    ]
    return JSONResponse({"stand": datetime.now().isoformat(), "maschinen": daten})


# -------------------------------------------------------------- QR-Code ----
@app.get("/qr/{maschine_id}.png")
def qr_png(maschine_id: str):
    import qrcode

    m = machines.holen(maschine_id)
    if m is None:
        return Response(status_code=404)
    bild = qrcode.make(f"{config.BASE_URL}/m/{m.id}")
    puffer = io.BytesIO()
    bild.save(puffer, format="PNG")
    return Response(puffer.getvalue(), media_type="image/png")


@app.get("/qr", response_class=HTMLResponse)
def qr_blaetter(request: Request):
    """Druckvorlage: ein Aufkleber je Maschine."""
    return _seite(request, "qr.html", maschinen=machines.alle())


# -------------------------------------------------------------- Ausweis ----
@app.post("/api/ausweis")
def ausweis(uid: str = Form(...)):
    benutzer = auth.benutzer_von_ausweis(uid)
    if benutzer is None:
        # === TODO AUSWEIS: siehe auth.benutzer_von_ausweis ==================
        return JSONResponse({"fehler": "Ausweisleser noch nicht angebunden."}, status_code=501)
    return JSONResponse({"kennung": benutzer.id, "name": benutzer.name})
