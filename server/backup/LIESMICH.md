# Backup vom Heimserver

Jede Nacht um 3:30 sichert `heimserver-backup` alles, was man nicht neu aufsetzen kann:

| Was | Woher |
|---|---|
| Steward-Datenbank | `/opt/steward/daten/steward.db` |
| Steward-Konfiguration inkl. Key | `/etc/steward/steward.env` |
| Tradingbot-Datenbank (Trades, Positionen, Verlauf) | `/opt/trading-bot/data/bot.sqlite3` |
| Tradingbot-Keys und Konfiguration | `/opt/trading-bot/.env`, `config.yaml` |
| Tradingbot-Berichte | `/opt/trading-bot/data/reports/` |

Der Code selbst ist nicht dabei, der liegt auf GitHub bzw. am PC.

Ziel: `/var/backups/heimserver/heimserver-JJJJ-MM-TT.tar.gz`, die letzten 14 Tage bleiben.
Die Archive enthalten die Keys, darum lesbar nur für root und lorenz.

## Installieren (einmalig, am Server)

```
cd /opt/steward
git pull
sudo install -m 755 server/backup/heimserver-backup /usr/local/sbin/heimserver-backup
sudo cp server/backup/heimserver-backup.service server/backup/heimserver-backup.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now heimserver-backup.timer
```

Gleich einmal von Hand testen:

```
sudo systemctl start heimserver-backup.service
ls -l /var/backups/heimserver/
systemctl list-timers heimserver-backup.timer
```

## Kopie auf den PC holen

Das Backup liegt auf derselben Platte wie die Daten. Hilft bei Fehlern und kaputten Dateien,
aber nicht, wenn die Platte stirbt. Darum ab und zu eine Kopie auf den PC (PowerShell):

```
scp "lorenz@pesenhofer-server.local:/var/backups/heimserver/heimserver-*.tar.gz" $HOME\Documents\Heimserver-Backup\
```

Achtung: die Archive enthalten die Alpaca- und Steward-Keys - nicht in OneDrive/iCloud legen.

## Wiederherstellen

Beispiel: Tradingbot-Datenbank vom 20.11. zurückholen

```
cd /tmp
sudo tar -xzf /var/backups/heimserver/heimserver-2026-11-20.tar.gz
sudo systemctl stop tradingbot
sudo cp /tmp/heimserver-2026-11-20/tradingbot.sqlite3 /opt/trading-bot/data/bot.sqlite3
sudo rm -f /opt/trading-bot/data/bot.sqlite3-wal /opt/trading-bot/data/bot.sqlite3-shm
sudo chown tradingbot:tradingbot /opt/trading-bot/data/bot.sqlite3
sudo systemctl start tradingbot
sudo rm -rf /tmp/heimserver-2026-11-20
```

Für Steward genauso: `sudo systemctl stop steward`, `steward.db` nach `/opt/steward/daten/` kopieren,
`-wal`/`-shm` daneben löschen, `chown steward:steward`, `sudo systemctl start steward`.
