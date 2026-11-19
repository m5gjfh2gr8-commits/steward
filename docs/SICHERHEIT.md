# Steward absichern — Prüfliste

Der Server ist nur über Tailscale erreichbar, damit fällt die Hälfte der üblichen
Sorgen weg. Was bleibt, steht hier. Punkt für Punkt abhaken, jede Zeile ist eine
eigene Sache.

## 1. Nicht ins Internet hängen

- [ ] **Keine** Portweiterleitung im Router, **kein** DynDNS
- [ ] Firewall: nur das Tailscale-Netz darf rein

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow in on tailscale0
sudo ufw enable
sudo ufw status verbose
```

- [ ] uvicorn nur an `127.0.0.1` binden, nie an `0.0.0.0` (steht so in `steward.service`).
      Nach außen nur über `tailscale serve` — das ist nur im eigenen Tailnet erreichbar,
      **nicht** `tailscale funnel` verwenden (das wäre öffentlich im Internet)

## 2. Tailscale

- [ ] Im Admin-Panel für den Server **„Disable key expiry"** setzen. Sonst läuft der
      Schlüssel nach einigen Monaten ab, Steward ist plötzlich weg, und du suchst
      den Fehler im Code
- [ ] iPhone und PC im selben Tailnet
- [ ] Maschinenname ohne persönliche Daten (landet mit dem HTTPS-Zertifikat in
      öffentlichen Zertifikats-Logs)

## 3. Schlüssel

- [ ] `STEWARD_API_KEY` erzeugen mit `openssl rand -hex 32`
- [ ] Eigener Anthropic-Key **nur für Steward** (einzeln widerrufbar)
- [ ] Spending-Limit in der Anthropic Console gesetzt
- [ ] Beide Keys stehen in `/etc/steward/steward.env`, nicht im Projektordner

```bash
sudo chown root:steward /etc/steward/steward.env
sudo chmod 640 /etc/steward/steward.env
```

- [ ] Vor jedem Push prüfen: `git status --short` zeigt **keine** `.env`

Der Anthropic-Key verlässt den Server nie. Die App kennt nur den Steward-Key.
Wenn das iPhone verloren geht, ist das Anthropic-Konto nicht betroffen.

## 4. Benutzer und Dienst

- [ ] Eigener Benutzer ohne Shell: `sudo useradd --system --no-create-home --shell /usr/sbin/nologin steward`
- [ ] Der Dienst läuft **nicht** als root (`User=steward` in der Unit)
- [ ] Härtungszeilen in `steward.service` sind drin (NoNewPrivileges, ProtectSystem, …)
- [ ] `STEWARD_SWAGGER_AN=false` im Betrieb — `/docs` zeigt sonst ohne Key das ganze
      API-Schema

## 5. Betriebssystem

- [ ] SSH nur mit Schlüssel: in `/etc/ssh/sshd_config`
      `PasswordAuthentication no` und `PermitRootLogin no`
- [ ] Automatische Sicherheitsupdates: `sudo apt install unattended-upgrades`
- [ ] Kein Auto-Login in eine Desktop-Sitzung

## 6. Wenig Rechte für Steward selbst

- [ ] Wenn später wieder Zugänge dazukommen: immer app-spezifische Passwörter,
      niemals das Hauptpasswort eines Kontos
- [ ] Zugänge nur lesend einrichten, wo das möglich ist

## 7. Die Grenze, die nicht verschoben wird

Das Modell liest fremde Texte — Webseiten, Foren. Die können absichtlich so
geschrieben sein, dass sie das Modell manipulieren. Solange die Modellantwort nur
geparstes JSON ist, das der Code prüft und in einen Bericht schreibt, ist das
Schlimmste ein blöder Bericht.

- [ ] **Keine** Werkzeug-Schnittstelle fürs Modell: keine Shell-Befehle, keine
      Dateizugriffe, kein Mailversand, nichts was nach außen wirkt
- [ ] Modellantworten immer gegen eine erwartete Struktur prüfen, nie direkt
      weiterverwenden

## 8. Backup

- [ ] Nächtliches Backup eingerichtet: [server/backup/LIESMICH.md](../server/backup/LIESMICH.md)
- [ ] Ab und zu eine Kopie auf den PC holen (nicht in OneDrive/iCloud — enthält Keys)
- [ ] BIOS: nach Stromausfall automatisch einschalten

Ein alter PC stirbt irgendwann. Ohne Kopie woanders sind Berichte, Todos und der
Verlauf der Testphase des Tradingbots dann weg.

## 9. iOS und HTTPS

iOS blockiert einfaches `http://` standardmäßig (App Transport Security). Gelöst mit
`tailscale serve` (siehe SETUP.md Abschnitt 5): Tailscale holt das Zertifikat selbst
und erneuert es, die App ruft `https://heimserver.tailXXXX.ts.net` auf. Keine
ATS-Ausnahme nötig.

Verschlüsselt ist der Verkehr übrigens sowieso — Tailscale ist WireGuard. HTTPS
brauchst du nicht für die Sicherheit, sondern weil iOS darauf besteht.

## 10. Am iPhone

- [ ] Der Steward-Key gehört in die **Keychain**, nicht in `UserDefaults`
      (umgesetzt in `Dienste/Schluesselbund.swift`)
