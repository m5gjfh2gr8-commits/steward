# Design-Brief: Steward iOS-App

## Worum es geht
Steward ist mein persönlicher KI-Assistent, der auf einem Heimserver läuft. Er startet nach Zeitplan sogenannte **Module** (z. B. Systemcheck, Tagesaktuelles, Tradingbot, Gelegenheiten). Jedes Modul liefert **Berichte**. Die iPhone-App ist meine Schnittstelle zu Steward: Module und Berichte ansehen, Todos verwalten, Steward Fragen stellen oder Aufgaben geben.

## Stil (wichtigste Vorgabe)
- Konsequent **nativer iOS-Stil** (aktuelles iOS 26): minimalistisch, clean, modern – soll aussehen wie eine Apple-eigene App (Vorbilder: Erinnerungen, Einstellungen, Wetter, Fitness).
- **Farblich schlicht:** neutrale System-Hintergründe und -Grautöne, **genau eine Akzentfarbe** (Standard: System-Blau). Keine Verläufe, keine bunten Flächen, keine Deko.
- Nur Standard-Bedienelemente und **SF Symbols**, System-Schrift (SF Pro), große Titel (Large Titles), gruppierte Listen.
- **Hell- und Dunkelmodus** folgen der iPhone-Einstellung – bitte beide Varianten entwerfen.
- Kompakt: auf einen Blick nur das Wichtigste, Details erst nach Antippen.

## Navigation
Tab-Leiste unten mit 5 Tabs:
1. **Module** (Startseite) – SF Symbol `square.grid.2x2`
2. **Todos** – `checklist`
3. **Steward** (Mitte, Eingabe) – `bubble.left.and.text.bubble.right` o. ä.
4. **Kosten** – `chart.bar`
5. **Einstellungen** – `gearshape`

## Bildschirme

### 1. Module (Startseite)
- Large Title „Steward“, darunter eine graue Statuszeile: z. B. „Alles ruhig · 3 neue Berichte“.
- Liste, eine Zeile pro Modul: Symbol links, Modulname, darunter einzeilig die Kurzfassung des letzten Berichts (grau), rechts ein Ungelesen-Punkt mit Zahl in Akzentfarbe, Chevron.
- Modul mit Fehler: rotes Warnsymbol statt Punkt, steht ganz oben.
- Pull-to-refresh.
- Beispieldaten:
  - Systemcheck – „Alles ruhig, alle Module laufen“ – 1 neu
  - Tagesaktuelles – „5 Meldungen zu KI, Börse und Österreich“ – 3 neu
  - Tradingbot – „Sleeve +2,4 % · 6 offene Positionen“ – 0 neu
  - Gelegenheiten – Fehler: „Lauf fehlgeschlagen um 06:00“

### 2. Modul-Detail
- Titel = Modulname. Oben eine kleine Zustands-Gruppe: Zustand (ok/Fehler), letzter Lauf, nächster Lauf.
- Darunter Liste der Berichte, neuester oben: Titel, Kurzfassung, Uhrzeit/Datum. Ungelesene mit Punkt.
- Berichte werden beim Öffnen automatisch als gelesen markiert.
- Toolbar oben rechts: „Jetzt ausführen“ (`play`) und „Vorlesen“ (`speaker.wave.2`).

### 3. Bericht-Detail (eine Ansicht für alle Module)
- Titel, darunter die Kurzfassung (ein Satz).
- **Kennzahlen** als kleine, schlichte Kacheln im Raster (Bezeichnung klein/grau, Wert groß): z. B. „Platte frei · 213,6 GB“, „Datenbank · 0,05 MB“, „Tokens heute · 0“.
- **Einträge** als Liste: Titel, 1–2 Zeilen Text, ggf. Quelle; Antippen öffnet den Link.
- Toolbar: Vorlesen, Teilen.

### 4. Steward (Eingabe)
- Chat-Ansicht: Verlauf meiner Eingaben (rechts, Akzentfarbe) und Stewards Antworten (links, neutral grau).
- Unten Eingabeleiste: Textfeld „Frag Steward oder gib eine Aufgabe…“ und Mikrofon-Knopf; während der Spracheingabe dezente Pegel-Animation.
- Erkennt Steward eine Aufgabe, kommt eine kompakte Bestätigungskarte „✓ Todo angelegt: Bewerbung abschicken“ mit Link „Zu den Todos“.
- Leerzustand mit 2–3 Beispiel-Vorschlägen als dezente Chips.

### 5. Todos
- Stil wie Apple „Erinnerungen“: Kreis zum Abhaken, Text, optional Fälligkeit in Grau.
- Wischen zum Löschen, „+“ oben rechts, neue Aufgabe inline eintippen.
- Erledigte ausgeblendet, über „Erledigte anzeigen“ einblendbar.
- Leerzustand: „Keine offenen Aufgaben“.

### 6. Kosten
- Oben große Zahl: Tokens heute, darunter ein schlichter Fortschrittsbalken zum Tagesdeckel („12 % vom Tageslimit“).
- Balkendiagramm der letzten 14 Tage (Swift-Charts-Stil, einfarbig Akzentfarbe).
- Liste: Verbrauch pro Modul heute.

### 7. Einstellungen (gruppierte Liste wie iOS-Einstellungen)
- **Verbindung:** Server-Adresse, Steward-Key (verdeckt), Knopf „Verbindung testen“ mit Ergebnis (grünes Häkchen / rotes X + Meldung).
- **Darstellung:** **Akzentfarbe wählen** – Reihe aus ca. 6–8 runden Farbpunkten (Blau [Standard], Indigo, Petrol/Teal, Grün, Orange, Rot, Rosa, Graphit), die gewählte mit Häkchen; die Farbe ändert sofort die ganze App.
- **Vorlesen:** Stimme, Geschwindigkeit (Slider).
- **Benachrichtigungen:** Schalter „Hintergrund-Hinweise“ (Standard aus) mit Fußnote, dass iOS den Zeitpunkt selbst bestimmt; Schalter „Zähler am App-Symbol“ (Standard an).
- **Info:** App-Version, Server-Version.

## Zustände, die mitentworfen werden sollen
- **Offline:** Server nicht erreichbar → dezente Hinweis-Leiste oben „Steward nicht erreichbar – Tailscale an?“, zuletzt geladene Daten bleiben normal sichtbar.
- **Laden:** Standard-Spinner bzw. Platzhalter-Zeilen.
- **Leerzustände** für Module ohne Berichte, Todos, Chat.
- **Fehler** eines Moduls (siehe Startseite).
- **Erster Start:** kurzer Einrichtungsbildschirm „Server-Adresse und Steward-Key eingeben“ → Verbindung testen → fertig.

## Was ich vom Design brauche
- Alle oben genannten Bildschirme im iPhone-Format, jeweils **hell und dunkel**.
- Einheitliche Abstände, Schriftgrößen und Farben nach Apples Human Interface Guidelines, damit es sich 1:1 in SwiftUI umsetzen lässt (Standard-Komponenten: NavigationStack, List, TabView, Toolbar, Charts).
- Kein eigenes Logo nötig; App-Symbol darf schlicht sein (z. B. SF-Symbol-artiges Motiv auf neutralem Grund in Akzentfarbe).
