# Steward am Server aufsetzen

Stand 2026-11-19. Gilt für das **Grundgerüst** — Mail, Kalender und Fitness sind
gestrichen, dafür ist nichts einzurichten.

Was hier steht, kann keine KI für dich machen: Hardware aufsetzen, Accounts anlegen,
Passwörter erzeugen. Reihenfolge einhalten, jeder Abschnitt endet mit einem **Test**.

Zum Absichern gibt es eine eigene Prüfliste: [SICHERHEIT.md](SICHERHEIT.md).

---

## 0. Vorher: Ausgaben-Limit setzen

1. [console.anthropic.com](https://console.anthropic.com) → Settings → Limits
2. Monatliches Limit setzen, z. B. **5 €**
3. Erst danach weitermachen

Das ist die Absicherung von außen. Im Code gibt es zusätzlich einen Tagesdeckel
(siehe Abschnitt 4), der greift schneller und sagt dir auch, welches Modul schuld war.

---

## 1. Heimserver aufsetzen

**Ubuntu Server 24.04 LTS** (kostenlos, läuft auf alter Hardware). Falls schon Linux
drauf ist, das behalten.

1. Per USB-Stick installieren, beim Setup **OpenSSH-Server** mitnehmen
2. Benutzer anlegen (unten wird `lorenz` als dein Login angenommen)
3. Danach:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-venv python3-pip git sqlite3
```

4. Damit der PC bei zugeklapptem Deckel nicht einschläft:

```bash
sudo systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target
```

**Test:** `python3 --version` zeigt **3.10 oder höher**. Bei älterem Python steigt
Steward aus (Typangaben und `zoneinfo`).

---

## 2. Tailscale einrichten

Am Server:

```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
```

Der Befehl zeigt einen Link — im Browser öffnen, anmelden (Google/GitHub reicht,
privat kostenlos). Dann:

1. **Tailscale-App am iPhone** installieren, gleicher Account
2. Tailscale auch am Windows-PC installieren
3. Im Admin-Panel für den Server **„Disable key expiry"** setzen — sonst läuft der
   Schlüssel irgendwann ab und Steward ist ohne Vorwarnung weg
4. Im Admin-Panel unter **Machines** dem Server einen **neutralen Namen** geben
   (z. B. `heimserver`). Der Name landet mit dem HTTPS-Zertifikat in öffentlichen
   Zertifikats-Verzeichnissen — also kein Nachname, nichts Persönliches
5. Im Admin-Panel unter **DNS**: **MagicDNS** an, bei **HTTPS Certificates** auf
   **Enable HTTPS**

**Test:** Vom iPhone aus den Server in der Tailscale-App anpingen.

---

## 3. GitHub-Repository anlegen

1. Auf github.com ein **öffentliches** Repository `steward` anlegen (öffentlich ist
   nötig für die kostenlosen macOS-Build-Minuten später)
2. Am Windows-PC die Workflow-Dateien an ihren Platz schieben: aus `ci/` nach
   `.github/workflows/` (die konnte ich nicht direkt dorthin schreiben)
3. Hochladen:

```bash
cd C:\Users\loren\Claude\Projects\Steward
git init
git add .
git commit -m "Steward Grundgeruest"
git branch -M main
git remote add origin https://github.com/DEIN-NAME/steward.git
git push -u origin main
```

**Vor dem Push prüfen:**

```bash
git status --short
```

Wenn dort `.env` oder eine `.db` auftaucht: **stoppen** und `.gitignore` kontrollieren.

**Test:** Auf GitHub unter **Actions** läuft „Backend Tests" grün durch.

---

## 4. Backend installieren

```bash
sudo mkdir -p /opt/steward /opt/steward/daten /etc/steward
sudo chown $USER:$USER /opt/steward
git clone https://github.com/DEIN-NAME/steward.git /opt/steward
cd /opt/steward/backend

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Dienstbenutzer anlegen und den Datenordner übergeben:

```bash
sudo useradd --system --no-create-home --shell /usr/sbin/nologin steward
sudo chown -R steward:steward /opt/steward/daten
```

Konfiguration anlegen — **nicht** im Projektordner, sondern in `/etc/steward`:

```bash
sudo cp .env.example /etc/steward/steward.env
sudo nano /etc/steward/steward.env
```

Mindestens diese vier Zeilen:

| Eintrag | Wert |
|---|---|
| `STEWARD_API_KEY` | selbst erzeugen: `openssl rand -hex 32` |
| `ANTHROPIC_API_KEY` | Console → API Keys → Create Key, **eigener Key nur für Steward** |
| `STEWARD_DB_PFAD` | `/opt/steward/daten/steward.db` — **absolut**, sonst startet der Dienst nicht |
| `STEWARD_SWAGGER_AN` | `false` lassen |

Die Tokendeckel (`STEWARD_TOKENBUDGET_PRO_TAG`, `..._PRO_LAUF`) sind bewusst hoch
voreingestellt — als Reißleine, nicht als Alltagsgrenze. Wenn du es strenger willst,
jetzt runtersetzen.

Rechte setzen:

```bash
sudo chown root:steward /etc/steward/steward.env
sudo chmod 640 /etc/steward/steward.env
```

**Test — der wichtigste Befehl im ganzen Setup:**

```bash
cd /opt/steward/backend
sudo -u steward bash -c 'set -a; . /etc/steward/steward.env; set +a; .venv/bin/python -m app.selbsttest'
```

Der prüft Python-Version, API-Key, Zeitzone, ob die Datenbank am richtigen Ort
beschreibbar ist, ob die Zeitpläne aller Module gültig sind, ob der Modell-Client
aufgebaut werden kann — und lässt den Systemcheck einmal wirklich laufen.

Erwartet: alle Zeilen `OK`. Jede `FEHLER`-Zeile sagt, was fehlt. **Erst weitermachen,
wenn alles grün ist.**

Wenn du auch den Modellaufruf selbst testen willst (kostet Bruchteile eines Cents):

```bash
sudo -u steward bash -c 'set -a; . /etc/steward/steward.env; set +a; .venv/bin/python -m app.selbsttest --modell'
```

---

## 5. Als Dienst einrichten

```bash
sudo cp /opt/steward/backend/steward.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now steward
sudo systemctl status steward
```

Steward lauscht nur am Server selbst (`127.0.0.1:8000`). Nach außen bringt ihn
Tailscale, mit HTTPS und echtem Zertifikat — das braucht iOS, sonst blockiert es die
Verbindung:

```bash
sudo tailscale serve --bg 8000
tailscale serve status
```

Beim ersten Mal kann statt dessen „Serve is not enabled on your tailnet" mit einem
Link kommen: den Link am PC öffnen, bestätigen, Befehl noch einmal. `--bg` heißt: läuft
dauerhaft und kommt nach einem Neustart von selbst wieder.

`serve status` zeigt die Adresse, z. B. `https://heimserver.tailXXXX.ts.net`.

**Test:**

```bash
curl http://127.0.0.1:8000/health
```

Muss `{"status":"ok",...}` liefern. Dann neu starten (`sudo reboot`) und denselben
Befehl noch einmal — Steward muss von selbst wieder da sein.

Ein Modul von Hand starten (praktisch zum Testen):

```bash
KEY=$(sudo grep STEWARD_API_KEY /etc/steward/steward.env | cut -d= -f2)
curl -s -X POST -H "X-API-Key: $KEY" http://127.0.0.1:8000/module/systemcheck/lauf
```

Logs mitlesen, wenn etwas nicht geht:

```bash
journalctl -u steward -f
```

---

## 6. Absichern

Jetzt die Prüfliste [SICHERHEIT.md](SICHERHEIT.md) durchgehen — Firewall, SSH,
automatische Updates. Dauert eine halbe Stunde und ist der Teil, den man
sonst „später" macht und dann nie.

Dazu das nächtliche Backup: Anleitung in [server/backup/LIESMICH.md](../server/backup/LIESMICH.md).
Und im BIOS „After Power Loss" (heisst je nach Hersteller auch „Restore on AC Power
Loss" o. ä.) auf **Power On** stellen, ErP/EuP aus — dann fährt der Server nach einem
Stromausfall von selbst wieder hoch.

Das Wichtigste in zwei Befehlen:

```bash
sudo ufw default deny incoming
sudo ufw allow in on tailscale0
sudo ufw enable
```

---

## 7. Erster Blick vom PC

Am Windows-PC im Browser (Tailscale muss laufen) die Adresse aus `tailscale serve status`:

```
https://heimserver.tailXXXX.ts.net/
```

Du landest auf der Anmeldeseite, gibst den `STEWARD_API_KEY` ein, und siehst danach
die Module mit ihrem letzten Bericht. Die Seite hat bewusst noch kein Design.

Am iPhone geht dasselbe in Safari (Tailscale-App an). Mit **Teilen → Zum
Home-Bildschirm** wird daraus ein Symbol wie bei einer App.

**Test:** Der Systemcheck zeigt „letzter Erfolg" und „nächster Lauf". Nach einer
Stunde ist ein zweiter Bericht da, ohne dass du etwas getan hast — dann arbeitet der
Planer.

---

## 8. RSS-Quellen durchschauen

In `/opt/steward/backend/config/feeds.json` stehen ORF, Standard, Spiegel, heise,
Golem und TechCrunch. Rausnehmen was nicht passt. Wird erst gebraucht, wenn das
Tagesaktuell-Modul kommt — jetzt schon möglich, nicht nötig.

---

## Was noch nicht dran ist

- **Module**: Systemcheck und Tradingbot laufen. Tagesaktuelles und Gelegenheiten
  sind noch nicht gebaut
- **Tradingbot**: eigenes Projekt unter `/opt/trading-bot` (Benutzer `tradingbot`,
  Dienst `tradingbot`). Er schreibt alle 15 Minuten `data/steward_status.json`, das
  Steward-Modul liest nur diese Datei. Anderer Ort: `STEWARD_TRADINGBOT_STATUS` in
  `/etc/steward/steward.env`
- **Die iOS-App**: Abschnitte zum App-Bauen (GitHub Actions, SideStore) kommen in
  diese Anleitung, wenn das dran ist

---

## Wenn was nicht geht

| Symptom | Wahrscheinliche Ursache |
|---|---|
| Dienst startet nicht, Log sagt „error while attempting to bind" | Port 8000 schon belegt (`sudo ss -ltnp \| grep 8000`) |
| Dienst startet nicht, Log sagt „unable to open database file" | `STEWARD_DB_PFAD` ist relativ oder zeigt nicht nach `/opt/steward/daten` |
| Selbsttest: „Paket für claude fehlt" | `pip install -r requirements.txt` im venv vergessen |
| Selbsttest: „STEWARD_API_KEY ist nicht gesetzt" | Dienst liest `/etc/steward/steward.env` — Datei leer oder falscher Pfad in der Unit |
| `https://…ts.net` antwortet nicht | Tailscale am anderen Gerät aus, oder `tailscale serve status` zeigt „No serve config" → `sudo tailscale serve --bg 8000` |
| Tradingbot-Modul rot: „Keine Statusdatei" / „meldet sich nicht mehr" | `systemctl status tradingbot`, Log: `journalctl -u tradingbot -f` |
| Browser zeigt „Key passt nicht" | Key in der Unit-Umgebung und Eingabe unterscheiden sich — auf Leerzeichen am Ende achten |

Logs: `journalctl -u steward -f`
