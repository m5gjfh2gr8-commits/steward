"""
Claude-Client (Anthropic API)

Standard ist Haiku, weil billig. Nur wo es wirklich um Textqualität geht wird mit
gross=True auf das größere Modell umgeschaltet
"""

import anthropic

from app.config import EINSTELLUNGEN
from app.llm.basis import ModellBasis, ModellFehler


class ClaudeClient(ModellBasis):
    def __init__(self):
        if EINSTELLUNGEN.anthropic_api_key == "":
            raise ModellFehler("ANTHROPIC_API_KEY fehlt in der Konfiguration")
        self.client = anthropic.Anthropic(api_key=EINSTELLUNGEN.anthropic_api_key)

    def _aufruf(self, system_anweisung, benutzer_text, max_tokens, gross):
        if gross:
            modell = EINSTELLUNGEN.claude_modell_gross
        else:
            modell = EINSTELLUNGEN.claude_modell_standard

        try:
            antwort = self.client.messages.create(
                model=modell,
                max_tokens=max_tokens,
                system=system_anweisung,
                messages=[{"role": "user", "content": benutzer_text}],
            )
        except Exception as fehler:
            raise ModellFehler("Claude-Aufruf fehlgeschlagen: " + str(fehler))

        gesammelt = ""
        for block in antwort.content:
            if block.type == "text":
                gesammelt = gesammelt + block.text

        tokens_ein = 0
        tokens_aus = 0
        if antwort.usage is not None:
            tokens_ein = antwort.usage.input_tokens
            tokens_aus = antwort.usage.output_tokens

        return gesammelt, tokens_ein, tokens_aus
