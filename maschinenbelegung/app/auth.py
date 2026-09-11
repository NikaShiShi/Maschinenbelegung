"""Anmeldung.

# === TODO ANMELDUNG (HD-Account) ==========================================
# Aktuell: Platzhalter-Login ohne Passwortprüfung, Kennung landet in einem
# Cookie. Reicht zum Testen, ist aber KEIN Zugriffsschutz.
#
# Ziel-Varianten (mit IT abstimmen):
#   a) Kerberos/NTLM über den IIS- bzw. Nginx-Vorschalter -> Kennung kommt im
#      Header REMOTE_USER an, hier nur noch auslesen.
#   b) Entra ID / Azure AD per OIDC (msal / authlib), Gruppen aus dem Token
#      auf die Rollen unten mappen.
# Rollen: "azubi" darf eigene Buchungen anlegen/stornieren,
#         "ausbilder" darf alles stornieren und sieht die Auslastung.
# ===========================================================================
"""

from dataclasses import dataclass

from fastapi import Request

COOKIE = "mb_benutzer"


@dataclass
class Benutzer:
    id: str
    name: str
    rolle: str = "azubi"      # "azubi" | "ausbilder"
    abteilung: str = ""

    @property
    def ist_ausbilder(self) -> bool:
        return self.rolle == "ausbilder"


def aktueller_benutzer(request: Request) -> Benutzer | None:
    """Liest den angemeldeten Benutzer.

    # === TODO ANMELDUNG: hier später REMOTE_USER-Header bzw. OIDC-Token
    # auswerten statt des Cookies.
    """
    roh = request.cookies.get(COOKIE)
    if not roh:
        return None
    kennung, _, rolle = roh.partition("|")
    if not kennung:
        return None
    return Benutzer(id=kennung, name=_name_zu(kennung), rolle=rolle or "azubi")


def _name_zu(kennung: str) -> str:
    """Klarname zur Kennung.

    # === TODO ANMELDUNG: aus dem AD/Entra-Verzeichnis lesen (displayName).
    """
    return kennung.replace(".", " ").title()


def benutzer_von_ausweis(uid: str) -> Benutzer | None:
    """Werksausweis am Terminal.

    # === TODO AUSWEIS (offen, muss geklärt werden) =========================
    # Frage an die Zutrittskontrolle/Werkschutz:
    #   1. Welche Karte ist im Einsatz (Mifare DESFire, Legic, HID)?
    #   2. Darf die Karten-UID gelesen werden oder nur eine abgeleitete
    #      Personalnummer? UID ist personenbezogen -> Betriebsrat einbinden.
    #   3. Gibt es eine Schnittstelle Karte -> Personalnummer -> HD-Account?
    # Technisch: USB-Leser im Keyboard-Wedge-Modus schickt die UID einfach als
    # Tastatureingabe, dann genügt ein Eingabefeld auf dem Terminal.
    # ======================================================================
    """
    return None
