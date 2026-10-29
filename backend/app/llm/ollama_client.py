"""
Ollama-Client (lokales Modell am Heimserver)

Gleiche Schnittstelle wie der Claude-Client, damit man in der Konfiguration einfach
STEWARD_LLM=ollama setzen kann ohne sonst irgendwas zu ändern

Tokens werden trotzdem mitgezählt, auch wenn sie hier nichts kosten - so bleibt
die Überwachung aussagekräftig
"""

import httpx

from app.config import EINSTELLUNGEN
from app.llm.basis import ModellBasis, ModellFehler


class OllamaClient(ModellBasis):
    def _aufruf(self, system_anweisung, benutzer_text, max_tokens, gross):
        adresse = EINSTELLUNGEN.ollama_url.rstrip("/") + "/api/chat"

        anfrage = {
            "model": EINSTELLUNGEN.ollama_modell,
            "stream": False,
            "options": {"num_predict": max_tokens},
            "messages": [
                {"role": "system", "content": system_anweisung},
                {"role": "user", "content": benutzer_text},
            ],
        }

        try:
            antwort = httpx.post(adresse, json=anfrage, timeout=300)
            antwort.raise_for_status()
        except Exception as fehler:
            raise ModellFehler("Ollama nicht erreichbar: " + str(fehler))

        daten = antwort.json()
        if "message" not in daten:
            raise ModellFehler("Unerwartete Ollama-Antwort: " + str(daten)[:200])

        tokens_ein = daten.get("prompt_eval_count", 0)
        tokens_aus = daten.get("eval_count", 0)

        return daten["message"]["content"], tokens_ein, tokens_aus
