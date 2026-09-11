"""Alle QR-Codes als PNG in einen Ordner schreiben (für den Aufkleberdruck).

    python tools/qr_export.py --url https://maschinen.hdm.local --ziel qr/
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import qrcode

from app import machines


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--url", default="http://localhost:8000", help="Basis-URL der Anwendung")
    p.add_argument("--ziel", default="qr", help="Zielordner")
    a = p.parse_args()

    ziel = Path(a.ziel)
    ziel.mkdir(parents=True, exist_ok=True)
    for m in machines.alle():
        code = qrcode.QRCode(box_size=10, border=2)
        code.add_data(f"{a.url.rstrip('/')}/m/{m.id}")
        code.make(fit=True)
        code.make_image().save(ziel / f"{m.id}.png")
    print(f"{len(machines.alle())} QR-Codes in {ziel.resolve()}")


if __name__ == "__main__":
    main()
