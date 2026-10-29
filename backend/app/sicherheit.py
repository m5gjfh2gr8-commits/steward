"""
Einfache API-Key-Prüfung

Die iOS-App schickt den Key im Header "X-API-Key" mit, alles ohne gültigen Key wird abgelehnt
Reicht für ein Einzelnutzer-Projekt hinter dem Tailscale-VPN
"""

import hmac

from fastapi import Header, HTTPException

from app.config import EINSTELLUNGEN


def api_key_pruefen(x_api_key: str = Header(default="")):
    if EINSTELLUNGEN.api_key == "":
        raise HTTPException(status_code=500, detail="STEWARD_API_KEY ist am Server nicht gesetzt")

    # compare_digest statt == damit die Laufzeit nichts über den Key verrät
    if not hmac.compare_digest(x_api_key, EINSTELLUNGEN.api_key):
        raise HTTPException(status_code=401, detail="Falscher oder fehlender API-Key")

    return True
