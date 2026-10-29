# Steward — Vollständiger Projektplan

**Stand: 2026-09-10. Noch NICHT umgesetzt — dies ist ausschließlich der Plan.**

Dieses Dokument ist so geschrieben, dass es allein steht: du (oder eine andere KI-Session, der du dieses Dokument gibst) sollte damit ohne weiteren Kontext direkt mit der Umsetzung loslegen können.

---

## 1. Überblick / Ziel

**Steward** ist ein dauerhaft laufender persönlicher KI-Agent, der wiederkehrende Alltagsaufgaben für Lorenz übernimmt — erreichbar über eine eigene iOS-App, die eigentliche Logik läuft auf einem Heimserver (altem PC zuhause).

**Wer setzt das um:** Lorenz, Schüler an der HTL BULME Graz (Wirtschaftsingenieurwesen), technischer Hintergrund u. a. in Python (Trading-Bot-Projekt, 84 Tests grün), C#/.NET mit ASP.NET Web API + Avalonia UI (Schul-Finanzapp), Netzwerkprotokolle (TCP/UDP, HTTP/S, DNS, MQTT), C++ (ESP32/PlatformIO-Projekte). Bevorzugt beim Programmieren explizite, ausführliche Syntax (kein `var`, kein LINQ, keine Expression-Bodies bei C#). Legt Wert auf Ordnung/Struktur und gründliche Umsetzung.

---

## 2. Rahmenbedingungen (fix vereinbart, nicht verhandelbar)

- **Steuerung ausschließlich über eine eigene iOS-App** (kein Telegram-Bot, keine Drittanbieter-Chat-App)
- **Komplett kostenlos**, mit genau einer Ausnahme: die Claude-API-Nutzung kostet ein paar Cent bis niedrige Euro-Beträge im Monat (Pay-per-Token). Alles andere — Server, Build-Pipeline, App-Signierung, VPN, Datenbanken — muss kostenlos bleiben
- **Kein Mac vorhanden** — die gesamte App-Build- und Signier-Kette muss ohne eigenen Mac funktionieren
- **Server = ein alter PC zuhause** (Heimserver), kein Cloud-Hosting
- Sensible/irreversible Aktionen (z. B. Mails absenden) werden **nie vollautomatisch** ausgeführt — der Agent schlägt vor, Lorenz bestätigt
- **Sparsamer Umgang mit KI-Tokens**: wo immer möglich Modellaufrufe minimieren (z. B. Mail-Check nur 1x täglich statt laufend, keine unnötigen Zusammenfassungen)
- **Vorab festgelegtes Ausgaben-Limit** für die Claude-API (Spending Cap in der Anthropic Console einrichten, bevor produktiv genutzt wird)
- **Offene/wichtige Fragen aktiv klären**: bei Unsicherheiten während der Umsetzung wird mit Lorenz Rücksprache gehalten statt eigenständig zu entscheiden
- **Design-Sprache der App**: klassischer iOS-Stil — minimalistisch, clean, modern (natives SwiftUI-Aussehen, System-Fonts/-Farben, kein Overdesign)

---

## 3. Architektur-Übersicht

```
[iOS App (SwiftUI)] 
      │  REST-API über HTTPS, per Tailscale-VPN erreichbar
      ▼
[Backend auf Heimserver (alter PC)]
      │
      ├─► [Claude API] — Sprachverständnis, Zusammenfassungen, Textparsing
      ├─► [SQLite-Datenbank] — Todos, Ernährungs-Log, Wasser-Log, Ziele
      ├─► [IMAP/SMTP] — direkter Mailzugriff (nicht über die iPhone-Mail-App)
      ├─► [Kalender-Anbindung] — siehe offene Entscheidung in Abschnitt 11
      ├─► [Open Food Facts API] — Nährwerte für Markenprodukte (kostenlos)
      └─► [USDA FoodData Central API] — Nährwerte für generische Zutaten (kostenlos)

Lokale Erinnerungen (Termine/Todos/Trink-Reminder) werden DIREKT in der 
iOS-App über UNUserNotificationCenter geplant — kein Umweg über den Server nötig.
```

**Warum kein Server-Push:** Echte Push-Benachrichtigungen (APNs) erfordern ein bezahltes Apple Developer Program ($99/Jahr) — das widerspricht der "komplett kostenlos"-Vorgabe. Stattdessen: lokale Notifications, die kostenlos funktionieren und für alle bisher besprochenen Erinnerungs-Use-Cases ausreichen.

---

## 4. Technologie-Stack

| Bereich | Empfehlung | Begründung |
|---|---|---|
| Backend-Sprache | **Python (FastAPI)** | Lorenz hat Python-Erfahrung vom Trading-Bot; FastAPI ist leichtgewichtig, gut für REST-APIs, große Ökosystem-Unterstützung für LLM-Tool-Calling |
| Datenbank | **SQLite** | Dateibasiert, kein separater DB-Server nötig, für Einzelnutzer-Projekt völlig ausreichend |
| Server-OS | **Linux (z. B. Ubuntu Server)** | Kostenlos, ressourcenschonend, Standard für dauerhaft laufende Dienste — *Empfehlung, noch nicht bestätigt, falls der alte PC bereits ein OS hat, das entscheidet, was Sinn ergibt* |
| Fernzugriff | **Tailscale (VPN)** | Kostenlos für Privatgebrauch, kein Port-Forwarding nötig, iPhone erreicht den Server wie im selben WLAN |
| LLM | **Anthropic API, Modell Claude Haiku 4.5** als Standard (günstig, $1/$5 pro Mio. Token input/output), bei Bedarf Sonnet 5 für komplexere Zusammenfassungen | Abgewogen gegen 100%-kostenlose Alternative: lokales Modell via **Ollama** auf dem Server (kein Token-Preis, nur Stromkosten, aber schwächer/langsamer) — **Entscheidung noch offen, siehe Abschnitt 11** |
| iOS-App | **SwiftUI** | Native iOS-Entwicklung, Lorenz kennt das UI-Framework+Backend-API-Konzept bereits aus der Avalonia/ASP.NET-Finanzapp |
| Auth (App ↔ Server) | Einfacher statischer API-Key im Request-Header | Reicht für ein Einzelnutzer-Projekt, kein OAuth-Overhead nötig |

---

## 5. Kostenübersicht

| Posten | Kosten |
|---|---|
| Server (alter PC) | 0 € (bereits vorhanden, nur Stromverbrauch) |
| Tailscale VPN | 0 € (privates Nutzungskontingent kostenlos) |
| GitHub Actions (App-Build in der Cloud) | 0 € bei öffentlichem Repository |
| SideStore/AltServer (App-Signierung) | 0 € |
| Apple-ID (kein Developer Program) | 0 € |
| Open Food Facts / USDA FoodData Central | 0 € (offene Datenbanken) |
| Claude API | **Einzige laufende Kosten** — Pay-per-Token, realistisch wenige Cent bis niedrige Euro-Beträge/Monat bei Haiku 4.5 |
| *(Alternative: Ollama lokal)* | 0 € — falls Lorenz sich für die 100%-kostenlose Variante entscheidet |

---

## 6. iOS-App: Build & Deployment ohne Mac

Das ist der technisch heikelste Teil, deshalb ausführlich:

1. **Code in einem öffentlichen GitHub-Repository** ablegen (öffentlich ist wichtig für kostenlose macOS-Build-Minuten)
2. **GitHub Actions mit macOS-Runner** baut bei jedem Push automatisch die App — kein eigener Mac nötig, der Build läuft in der Cloud
3. **Signierung mit der eigenen (kostenlosen) Apple-ID** statt bezahltem Developer Account
4. **Installation & 7-Tage-Zertifikatsproblem lösen ohne Mac:** **SideStore** (Fork von AltStore) auf einem Windows-PC einmalig einrichten. Danach erneuert SideStore die App-Signatur automatisch alle 7 Tage über einen VPN-Trick direkt am iPhone — kein Computer mehr nötig bei jeder Erneuerung
5. **Wichtige Einschränkungen der kostenlosen Variante, die von Anfang an mitgeplant werden müssen:**
   - Maximal 3 sideload-fähige Apps gleichzeitig auf dem Gerät (für Steward allein kein Problem)
   - Keine echten Push-Benachrichtigungen (siehe Abschnitt 3) — im Xcode-Projekt darf die "Push Notifications"-Capability NICHT aktiviert werden, sonst schlägt die Signierung mit dem Gratis-Account fehl
   - Community-Tooling (SideStore/AltStore), keine offizielle Apple-Lösung — kann bei größeren iOS-Updates kurzzeitig brechen, bis die Tools nachziehen. Falls das langfristig zu nervig wird: $99/Jahr Apple Developer Program entfernt alle diese Einschränkungen (1 Jahr gültige Zertifikate, kein 3-App-Limit, echte Push-Notifications)

**Geheimnisse (API-Keys etc.) niemals ins öffentliche Repository committen** — über GitHub Actions Secrets verwalten.

---

## 7. Datenmodell (Grundgerüst)

```
todos
  id, content, due_datetime, done (bool), source (text/voice), created_at

food_log
  id, timestamp, description_raw, kcal, protein_g, carbs_g, fat_g,
  source ("database" | "estimated"), edited (bool)

water_log
  id, timestamp, amount_ml

daily_goals
  kcal_target, protein_target_g, carbs_target_g, fat_target_g, water_target_ml

interest_profile
  id, topic_keyword, active (bool)

news_feedback
  id, story_id_or_hash, timestamp, rating ("up" | "down")
```

Mail und Kalender werden **nicht** in einer eigenen Tabelle gespiegelt, sondern bei Bedarf live abgefragt (IMAP für Mail; zur Kalenderquelle siehe offene Entscheidung Abschnitt 11).

---

## 8. Backend API-Endpunkte (Grundgerüst)

```
GET  /briefing/morning          → generiert das Morning Briefing (Text)
GET  /mail/important             → wichtige/interessante Mails über alle Postfächer (kompakt, ohne Antwortvorschläge)
POST /tasks/parse                → Freitext/Sprache rein → strukturiertes 
                                    Todo/Termin-Objekt raus (App plant daraus 
                                    selbst die lokale Notification)
GET  /tasks                      → offene Todos/Termine
POST /tasks                      → neuen Todo/Termin anlegen
POST /food/log                   → Freitext rein → kcal/Makros raus 
                                    (inkl. Datenbank-Abgleich)
GET  /food/today                 → heutige Summe vs. Tagesziel
GET  /food/history                → Verlauf über Zeit
POST /water/log                  → Trinkmenge erfassen
GET  /water/today                → heutiger Stand vs. Ziel
GET  /goals                      → aktuelle Tagesziele
POST /goals                      → Tagesziele setzen/ändern
GET  /profile/interests          → aktuelles Interessensprofil
POST /profile/interests          → Interessensprofil bearbeiten
POST /news/feedback              → Daumen hoch/runter zu einer Meldung
```

---

## 9. iOS-App: Screens (Grundgerüst)

- **Dashboard/Home** — Morning-Briefing-Karte, Fortschrittsübersicht (kcal/Makros/Wasser als Balken oder Ring)
- **Chat/Eingabe** — Freitext- oder Sprachfeld für Termine, Todos, Essenseinträge (ein einziges Eingabefeld, das Backend erkennt anhand des Inhalts, worum es geht)
- **Todos/Termine** — Liste offener Einträge
- **Mail-Anzeige** — kompakte Liste/Badge wichtiger oder interessanter ungelesener Mails über alle Postfächer hinweg
- **Ernährung** — Tagesübersicht, Verlauf/Historie, Einträge editierbar
- **Einstellungen** — Tagesziele, Server-Adresse/API-Key, Verbindungsstatus

---

## 10. Feature-Spezifikationen im Detail

### 10.1 Morning Briefing
Kompakte, kurze Zusammenfassung der für Lorenz relevanten Tagesnews — Ziel: nur die paar Meldungen, die ihn wirklich interessieren, keine komplette Newsletter-Länge. Kalender/Todos bleiben als eigener Teil derselben täglichen Nachricht (siehe Architektur Abschnitt 3), aber inhaltlich getrennt von den News.

**Quellen:**
- Bestehendes Gratis-Newsletter-Abo (kommt per Mail um 6 Uhr, wird über den ohnehin vorhandenen Mail-Zugriff ausgelesen)
- Zusätzliche kostenlose RSS-Feeds, Vorschlag (final mit Lorenz abzustimmen): **Der Standard** und **ORF.at** (Österreich-Bezug), **Spiegel** (D/international), **Heise/Golem** (Tech/KI), optional **TechCrunch** (englischsprachig, Startup/Tech) — alle bieten offizielle, kostenlose RSS-Feeds an

**Relevanz-Filter:**
- Filtert zunächst gegen Lorenz' bekanntes Interessensprofil (u. a. KI/Halbleiter, Wirtschaft/Unternehmensführung) — die genaue abgeleitete Liste wird ihm vor dem ersten Einsatz zur Kontrolle/Anpassung vorgelegt (siehe Abschnitt 11)
- Lernt danach laufend weiter: zu jeder Meldung kann er per Daumen hoch/runter Feedback geben, das fließt in künftige Filterung ein

**Format:**
- Kurztext pro Meldung (ein bis zwei Sätze), keine vollständigen Artikel
- Optional zum Anhören über iOS-eigenes Text-to-Speech (kostenlos, kein externer Dienst)
- Bei Interesse an einer einzelnen Meldung: "tiefere Einblicke" direkt im Chat-Fenster erfragbar (Modell fasst ausführlicher zusammen bzw. verweist auf die Quelle)

### 10.2 Wichtige-Mail-Anzeige
Lorenz hat mehrere E-Mail-Adressen/Postfächer und checkt nicht alle regelmäßig. Kein KI-Antwortvorschlag mehr geplant — nur eine kompakte Anzeige. Backend fragt alle konfigurierten Postfächer nur **1x täglich** per IMAP ab (bewusst nicht häufiger, um Modell-Aufrufe/Tokens zu sparen), das Modell klassifiziert neue/ungelesene Mails nach "wichtig"/"interessant" (z. B. anhand Absender, Betreff, Anfang des Inhalts). Dashboard zeigt nur eine kompakte Liste/Badge der so markierten Mails (Absender, Betreff, welches Postfach) — kein Lesen des vollen Inhalts in der App nötig, keine Entwurfsfunktion.

### 10.3 Termin-/Todo-Erfassung per Text oder Sprache
1. Freitext oder Spracheingabe (z. B. über Apples eigenes Speech-Framework, kostenlos)
2. Text geht an `/tasks/parse` — Modell erkennt Datum/Uhrzeit/Inhalt, gibt strukturiertes Objekt zurück
3. App plant daraus direkt eine **lokale** Notification zur passenden Zeit (kein Server-Push nötig, funktioniert auch offline)

### 10.4 Kalorien-/Makro-Tracker
1. Freitext-Eingabe (z. B. "2 Scheiben Schwarzbrot mit Nutella")
2. Modell zerlegt den Text in Einzel-Items
3. Für jedes Item zuerst Abgleich gegen **Open Food Facts** (Markenprodukte) und **USDA FoodData Central** (generische Zutaten) — nur wenn nichts gefunden wird, schätzt das Modell selbst
4. Eintrag landet mit Zeitstempel in `food_log`
5. **Jeder Eintrag muss nachträglich editierbar sein** — KI-Schätzung ist nie perfekt
6. Tagesziele werden in den Einstellungen festgelegt, Fortschritt läuft gegen `daily_goals`
7. Historie/Trend-Ansicht über die Zeit

### 10.5 Flüssigkeits-Counter
Einfache Schnellauswahl-Buttons (+250ml, +500ml, custom), laufende Tagessumme gegen Ziel. Kein Modell-Aufruf nötig. Optional: lokale Erinnerung, wenn seit X Stunden nichts eingetragen wurde (nutzt dieselbe lokale-Notification-Technik wie 10.3).

---

## 11. Offene Entscheidungen (vor bzw. während der Umsetzung zu klären)

1. **Claude API vs. lokales Modell (Ollama)** — finale Entscheidung zwischen minimalen laufenden Kosten (Claude, bessere Qualität) und 100%-kostenlos (Ollama, schwächer/langsamer)
2. **Kalenderanbindung des Servers** — der Server hat keinen direkten Zugriff auf den iPhone-Kalender. Zwei Optionen:
   - **Option A (empfohlen):** Server greift direkt auf einen Cloud-Kalender zu (z. B. Google Calendar API oder CalDAV) — Server kann dann unabhängig vom Handy arbeiten, auch wenn die App gerade nicht offen ist. Voraussetzung: Lorenz nutzt/wechselt zu einem entsprechenden Cloud-Kalender
   - **Option B:** App liest den lokalen iPhone-Kalender über EventKit aus und synct die Daten zum Server — mehr Aufwand, App muss dafür offen sein/im Hintergrund laufen
3. **Mail-Zugangsdaten** — welche(r) Mail-Anbieter/IMAP-Zugänge werden angebunden (Lorenz hat mehrere Adressen/Postfächer, alle sollen erfasst werden)
4. **Server-Betriebssystem** — abhängig davon, was auf dem vorhandenen alten PC bereits läuft bzw. sinnvoll neu aufgesetzt wird
5. **GitHub Repository öffentlich** — nötig für kostenlose macOS-Build-Minuten; falls das nicht gewünscht ist, Alternativen (privates Repo mit eingeschränktem Gratis-Kontingent, oder gelegentlich geliehener Mac) nochmal abwägen
6. **Interessensprofil zur Kontrolle vorlegen** — vor dem ersten Einsatz muss Lorenz die abgeleitete Themenliste (KI/Halbleiter, Wirtschaft/Unternehmensführung, ...) durchsehen und anpassen
7. **Finale RSS-Quellenliste** — Vorschlag (Der Standard, ORF.at, Spiegel, Heise/Golem, optional TechCrunch) noch mit Lorenz abzustimmen, genaue Feed-URLs bei Umsetzung von den jeweiligen Seiten holen

---

## 12. Empfohlene Umsetzungs-Reihenfolge

- **Phase 0 — Setup:** Server-OS aufsetzen, GitHub-Repo anlegen, Tailscale einrichten, Apple-ID vorbereiten, SideStore/AltServer auf dem Windows-PC einrichten, Claude-API-Key holen (oder Ollama installieren)
- **Phase 1 — Backend-Grundgerüst:** REST-API-Skelett (FastAPI), SQLite-Datenbank mit den Tabellen aus Abschnitt 7, einfache API-Key-Authentifizierung
- **Phase 2 — iOS-App-Grundgerüst:** SwiftUI-App, die sich mit dem Backend verbindet, einfaches Chat-/Eingabefenster
- **Phase 3 — Feature: Morning Briefing** (einfachster Einstieg, wie ursprünglich besprochen)
- **Phase 4 — Feature: Termin-/Todo-Erfassung per Text/Sprache + lokale Notifications**
- **Phase 5 — Feature: Mail-Triage**
- **Phase 6 — Feature: Kalorien-/Makro-Tracker + Flüssigkeits-Counter**
- **Phase 7 — Politur:** Fehlerbehandlung, Absicherung der API, Feinschliff der App-Oberfläche

Prinzip dabei: nicht alles gleichzeitig bauen, sondern jede Phase fertig und nutzbar machen, bevor die nächste beginnt.

---

## 13. Ideenpool / Backlog (nicht Teil des MVP, spätere Erweiterungen)

Diese Ideen wurden im Gespräch gesammelt, aber noch nicht konkret geplant oder priorisiert:

- Wetter + Vorlaufzeit bei auswärtigen Terminen im Morning Briefing
- "Fokus des Tages"-Einschätzung statt reiner Terminliste
- Evening Wrap-up (Gegenstück zum Morning Briefing)
- Siri Shortcuts / App Intents für Sprachsteuerung ohne App zu öffnen
- Kassenzettel-Foto → automatische Ausgaben-Erfassung (OCR)
- Abo-/Rechnungs-Überblick mit Preiserhöhungs-Warnung
- Lange Mails/Dokumente automatisch zusammenfassen
- Wochen-Review (Rückblick + Ausblick)
- Reise-Modus (erkennt Flüge/Hotelbuchungen automatisch aus Mails)
- System-Health-Check für andere eigene Projekte (z. B. Trading-Bot)
- Einkaufsliste per Zuruf
- "Wo hab ich das gespeichert"-Suche über eigene Notizen/Dokumente
- Paket-Tracking-Sammelstelle
- Artikel/Link-Zusammenfassung zum Später-Lesen
- Kontakt-Erinnerung ("seit X Monaten nicht gemeldet")
- Geburtstags-/Jahrestag-Reminder mit Geschenkidee
- Rezept-Vorschlag nach Kühlschrank-Foto
- Garantie-/Kaufbeleg-Tracker
- "Neue-Sache-lernen"-Assistent (strukturierte Unterstützung beim Einstieg in neue Hobbys/Sportarten, inkl. Ressourcen-Sammlung und Fortschritts-Tracking)
- Home-Bar-Assistent (Flaschenbestand, Cocktail-Vorschläge, Restock-Erinnerung)
- Allgemeiner Party-/Event-Planer (Gästeliste, Einkaufsliste, Zeitplan)

---

## 14. Hinweis für eine neue KI-Session

Falls dieses Dokument in eine neue Session eingefügt wird: alle Punkte in Abschnitt 2 sind fix vereinbart und nicht zu hinterfragen. Abschnitt 11 enthält die Punkte, die noch mit Lorenz geklärt werden müssen, bevor bzw. während der jeweilige Teil umgesetzt wird — bei diesen Punkten aktiv nachfragen statt selbst zu entscheiden. Alles unter "Ideenpool" (Abschnitt 13) ist explizit NICHT Teil des aktuellen Umsetzungsauftrags.
