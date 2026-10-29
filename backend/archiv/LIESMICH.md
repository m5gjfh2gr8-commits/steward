# Archiv

Hier liegt Code, der am 2026-10-18 aus Steward rausgenommen wurde, weil die
Bereiche Mail-Triage, Kalender und Fitness (Ernährung/Wasser) gestrichen sind.

Nicht gelöscht, weil die Bereiche später zurückkommen können. Zum Wiederbeleben:
Datei zurück an ihren Platz, Router in `app/main.py` registrieren, Tabellen in
`app/datenbank.py` wieder ins Schema, Tests zurück nach `tests/`.

- `dienste/mail.py` — IMAP über mehrere Postfächer, Klassifizierung, Tageszwischenspeicher
- `dienste/kalender.py` — CalDAV lesend (iCloud)
- `dienste/ernaehrung.py`, `dienste/naehrwerte.py` — Kalorien-/Makro-Tracker, Open Food Facts + USDA
- `dienste/wasser.py`, `dienste/ziele.py` — Flüssigkeits-Counter, Tagesziele
- `dienste/briefing.py` — Morning Briefing (löst sich in die Modul-Berichte auf)
- `router/*` — die zugehörigen Endpunkte
- `tests/*` — die zugehörigen Tests
- `config/postfaecher.json.example` — IMAP-Zugänge
- `ios_ansichten/*` — Ernährungs- und Mail-Ansicht der App
