# Steward

Persönlicher KI-Agent am Heimserver. Steward ist die **Schnittstelle und der Überwacher** —
die eigentliche Arbeit machen **Module**, die er nach Zeitplan startet und deren Berichte
er ausliefert (an die iOS-App und an den Browser am PC).

Stand: Grundgerüst steht und ist getestet. Die inhaltlichen Module (Tagesaktuelles,
Gelegenheiten, Finanzbot) kommen als Nächstes.

## Wie es funktioniert

Steward wartet **nicht** darauf, dass sich Module melden — er startet sie:

```
Planer (APScheduler)  --->  Modul.lauf()  --->  Bericht  --->  Tabelle berichte
      |                          |                                    |
      |                     Fehler? --->  Tabelle modul_laeufe   App + PC lesen
      |                                   (= die Überwachung)
   Uhr läuft 24/7
```

Ein Modul besteht aus vier Dingen: `name`, `anzeigename`, `zeitplan`, `lauf()`.
Mehr muss es nicht wissen. Protokollieren, Fehler fangen, Tokens zählen und Ausliefern
macht Steward.

## Ordner

```
backend/app/bots/          die Module + der Modul-Vertrag (basis.py) + verzeichnis.py
backend/app/planer.py      die Uhr, plus die Umklammerung jedes Modul-Laufs
backend/app/dienste/       berichte.py (Berichte/Läufe/Zustand), kosten.py (Kostenbremse)
backend/app/router/        Endpunkte für App; web.py ist die PC-Seite
backend/archiv/            ausgebauter Code (Mail, Kalender, Fitness) - nicht gelöscht
docs/SETUP.md              Server einrichten
docs/SICHERHEIT.md         Prüfliste zum Absichern
```

## Ein neues Modul anlegen

1. Datei in `backend/app/bots/` anlegen, von `Modul` erben, `lauf()` schreiben
2. In `backend/app/bots/verzeichnis.py` in die Liste `MODULE` eintragen

Das ist alles. Es erscheint danach automatisch in der API, auf der PC-Seite und
(sobald die App umgebaut ist) in der App — **ohne** dass die App neu gebaut werden muss.

```python
from app.bots.basis import Bericht, Modul


class MeinModul(Modul):
    name = "meinmodul"
    anzeigename = "Mein Modul"
    beschreibung = "Was es tut"
    zeitplan = {"hour": 6, "minute": 0}     # täglich 6:00, None = nur von Hand
    braucht_modell = False

    def lauf(self):
        bericht = Bericht(titel="Titel", kurzfassung="ein Satz")
        bericht.kennzahl_dazu("Geprüft", 42)
        bericht.eintrag_dazu(titel="Ein Fund", text="Erklärung", link="https://...")
        return bericht
```

## Endpunkte

```
GET  /health                      ohne Key: läuft der Server
GET  /status                      was ist eingerichtet, Verbrauch heute
GET  /kosten                      Token-Verbrauch heute + Verlauf

GET  /module                      alle Module mit Zustand, Ungelesen, letzter Bericht
GET  /module/zustand              Kurzüberblick für die Überwachung
GET  /module/{name}               ein Modul im Detail
GET  /module/{name}/berichte      Berichte, neueste zuerst
GET  /module/{name}/laeufe        Lauf-Protokoll inkl. Fehlern
POST /module/{name}/lauf          sofort laufen lassen
POST /module/{name}/gelesen       Gelesen-Markierung setzen

POST /chat                        ein Eingabefeld: Aufgabe oder Frage
GET  /tasks  POST /tasks  PATCH /tasks/{id}  DELETE /tasks/{id}
POST /tasks/parse                 Freitext -> Todo-Objekt (App plant die Erinnerung)

GET  /profile/interests  POST /profile/interests
POST /news/feedback               Daumen hoch/runter
POST /news/vertiefen              mehr zu einer Meldung

GET  /                            PC-Seite (Cookie-Login unter /anmelden)
```

## Lokal starten

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # STEWARD_API_KEY setzen
uvicorn app.main:anwendung --host 127.0.0.1 --port 8000
```

Dann `http://127.0.0.1:8000/` im Browser, Key eingeben.
Zum Entwickeln: `STEWARD_PLANER_AN=false` (nichts läuft von selbst),
`STEWARD_SWAGGER_AN=true` (dann gibt es `/docs`).

## Tests

```bash
cd backend
python -m pytest -v
```

76 Tests, laufen ohne API-Key, ohne Internet und ohne Planer.
(`pytest.ini` sorgt dafür, dass der `archiv/`-Ordner nicht mitgesammelt wird.)

## Selbsttest vor dem ersten Start

```bash
python -m app.selbsttest            # prüft Konfiguration, Datenbank, Module
python -m app.selbsttest --modell   # zusätzlich ein echter Modellaufruf
```

Gibt pro Punkt OK oder was fehlt, und einen Rückgabewert (0 = alles gut).
Der erste Befehl, den man am Server laufen lässt.

## Die zwei Grenzen, die eingebaut sind

**Kosten.** Jeder Modellaufruf geht durch `dienste/kosten.py`. Zwei harte Deckel
(`STEWARD_TOKENBUDGET_PRO_LAUF`, `STEWARD_TOKENBUDGET_PRO_TAG`) — wird einer erreicht,
wird der Aufruf abgelehnt und der Lauf als Fehler protokolliert, statt still teurer
zu werden. Der Verbrauch wird pro Modul gebucht, man sieht also wer wie viel kostet.

**Was das Modell darf.** Nichts außer Text produzieren. Es gibt keine Werkzeug-Schnittstelle,
keine Shell, keinen Dateizugriff, keinen Mailversand. Die Module lesen fremde Texte
aus dem Internet — die können absichtlich manipulativ geschrieben sein. Solange die
Modellantwort nur geparstes JSON ist, das der Code prüft, ist das Schlimmste ein
blöder Bericht. Diese Grenze bleibt.
