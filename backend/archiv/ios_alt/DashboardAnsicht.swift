import SwiftUI

// Startbildschirm: Briefing, Fortschritt bei Kalorien/Wasser, Mail-Badge

struct DashboardAnsicht: View {
    @EnvironmentObject var einstellungen: Einstellungen
    @StateObject private var vorlesen = Vorlesen.geteilt

    @State private var briefing: Briefing?
    @State private var essenHeute: EssenTag?
    @State private var wasserHeute: WasserStand?
    @State private var mails: MailUebersicht?

    @State private var laedt = false
    @State private var fehlertext = ""

    var body: some View {
        NavigationStack {
            Group {
                if !einstellungen.istEingerichtet {
                    NichtEingerichtetHinweis()
                } else {
                    List {
                        if laedt && briefing == nil {
                            LadeAnzeige(text: "Briefing wird geholt")
                        }

                        if !fehlertext.isEmpty {
                            Section {
                                FehlerKarte(text: fehlertext)
                            }
                        }

                        fortschrittsAbschnitt
                        termineAbschnitt
                        todoAbschnitt
                        mailAbschnitt
                        newsAbschnitt
                    }
                    .refreshable {
                        await allesLaden(neuLaden: true)
                    }
                }
            }
            .navigationTitle(briefing?.begruessung ?? "Heute")
            .toolbar {
                if briefing != nil {
                    Button {
                        vorlesenUmschalten()
                    } label: {
                        if vorlesen.laeuft {
                            Image(systemName: "stop.circle")
                        } else {
                            Image(systemName: "speaker.wave.2")
                        }
                    }
                }
            }
            .task {
                if briefing == nil {
                    await allesLaden(neuLaden: false)
                }
            }
        }
    }

    private var fortschrittsAbschnitt: some View {
        Section("Heute") {
            if let essen = essenHeute {
                FortschrittsBalken(titel: "Kalorien", aktuell: essen.summe.kcal, ziel: essen.ziele.kcalZiel, einheit: "kcal", farbe: .orange)
                FortschrittsBalken(titel: "Eiweiss", aktuell: essen.summe.eiweissG, ziel: essen.ziele.eiweissZielG, einheit: "g", farbe: .red)
            }

            if let wasser = wasserHeute {
                FortschrittsBalken(titel: "Wasser", aktuell: Double(wasser.summeMl), ziel: Double(wasser.zielMl), einheit: "ml", farbe: .blue)

                HStack(spacing: 10) {
                    Button("+250") {
                        Task { await wasserEintragen(250) }
                    }
                    Button("+500") {
                        Task { await wasserEintragen(500) }
                    }
                    Spacer()
                }
                .buttonStyle(.bordered)
            }
        }
    }

    @ViewBuilder
    private var termineAbschnitt: some View {
        if let briefing = briefing, !briefing.termine.isEmpty {
            Section("Termine") {
                ForEach(briefing.termine) { termin in
                    HStack(alignment: .top) {
                        if termin.ganztaegig {
                            Text("ganztags")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                                .frame(width: 60, alignment: .leading)
                        } else {
                            Text(uhrzeitAusText(termin.beginn))
                                .font(.callout.monospacedDigit())
                                .frame(width: 60, alignment: .leading)
                        }

                        VStack(alignment: .leading, spacing: 2) {
                            Text(termin.titel)
                            if !termin.ort.isEmpty {
                                Text(termin.ort)
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                            }
                        }
                    }
                }
            }
        }
    }

    @ViewBuilder
    private var todoAbschnitt: some View {
        if let briefing = briefing, !briefing.todos.isEmpty {
            Section("Offen") {
                ForEach(briefing.todos) { todo in
                    Text(todo.inhalt)
                }
            }
        }
    }

    @ViewBuilder
    private var mailAbschnitt: some View {
        if let mails = mails, !mails.mails.isEmpty {
            Section("Mail") {
                NavigationLink {
                    MailAnsicht(uebersicht: mails)
                } label: {
                    HStack {
                        Text("\(mails.anzahlWichtig) wichtig, \(mails.anzahlInteressant) interessant")
                        Spacer()
                    }
                }
            }
        }
    }

    @ViewBuilder
    private var newsAbschnitt: some View {
        if let briefing = briefing, !briefing.news.isEmpty {
            Section("News") {
                ForEach(briefing.news) { meldung in
                    NavigationLink {
                        MeldungsAnsicht(meldung: meldung)
                    } label: {
                        VStack(alignment: .leading, spacing: 4) {
                            Text(meldung.titel)
                                .font(.subheadline.weight(.medium))
                            Text(meldung.zusammenfassung)
                                .font(.footnote)
                                .foregroundStyle(.secondary)
                            Text(meldung.quelle)
                                .font(.caption2)
                                .foregroundStyle(.tertiary)
                        }
                    }
                }
            }
        }
    }

    private func vorlesenUmschalten() {
        if vorlesen.laeuft {
            vorlesen.stoppen()
        } else if let briefing = briefing {
            vorlesen.starten(text: briefing.vorlesetext)
        }
    }

    private func allesLaden(neuLaden: Bool) async {
        laedt = true
        fehlertext = ""

        var zusatz = ""
        if neuLaden {
            zusatz = "?neu_laden=true"
        }

        do {
            briefing = try await ApiClient.geteilt.holen("/briefing/morning" + zusatz)
        } catch {
            fehlertext = error.localizedDescription
        }

        do {
            essenHeute = try await ApiClient.geteilt.holen("/food/today")
            wasserHeute = try await ApiClient.geteilt.holen("/water/today")
        } catch {
            // Fortschritt ist nicht kritisch, der Fehler vom Briefing reicht
        }

        do {
            mails = try await ApiClient.geteilt.holen("/mail/important")
        } catch {
            // Mail kann ohne eingerichtete Postfaecher fehlschlagen, das ist ok
        }

        laedt = false
    }

    private func wasserEintragen(_ menge: Int) async {
        do {
            let stand: WasserStand = try await ApiClient.geteilt.schicken("/water/log", koerper: WasserAnfrage(mengeMl: menge))
            wasserHeute = stand

            if einstellungen.trinkErinnerungAn {
                Benachrichtigungen.geteilt.trinkErinnerungPlanen(inStunden: einstellungen.trinkErinnerungStunden)
            }
        } catch {
            fehlertext = error.localizedDescription
        }
    }
}

// Einzelne Meldung mit Daumen hoch/runter und Nachfrage-Moeglichkeit
struct MeldungsAnsicht: View {
    let meldung: Meldung

    @State private var vertiefung = ""
    @State private var laedt = false
    @State private var bewertet = ""

    var body: some View {
        List {
            Section {
                Text(meldung.titel)
                    .font(.headline)
                Text(meldung.zusammenfassung)
                Text(meldung.quelle)
                    .font(.caption)
                    .foregroundStyle(.secondary)

                if let url = URL(string: meldung.link), !meldung.link.isEmpty {
                    Link("Zur Quelle", destination: url)
                }
            }

            Section("Passt das?") {
                HStack(spacing: 20) {
                    Button {
                        Task { await bewerten("up") }
                    } label: {
                        Label("Mehr davon", systemImage: "hand.thumbsup")
                    }

                    Button {
                        Task { await bewerten("down") }
                    } label: {
                        Label("Weniger", systemImage: "hand.thumbsdown")
                    }
                }
                .buttonStyle(.bordered)

                if !bewertet.isEmpty {
                    Text(bewertet)
                        .font(.footnote)
                        .foregroundStyle(.secondary)
                }
            }

            Section("Tiefere Einblicke") {
                if laedt {
                    LadeAnzeige(text: "Wird ausfuehrlicher zusammengefasst")
                } else if vertiefung.isEmpty {
                    Button("Mehr dazu") {
                        Task { await vertiefen() }
                    }
                } else {
                    Text(vertiefung)
                }
            }
        }
        .navigationTitle("Meldung")
        .navigationBarTitleDisplayMode(.inline)
    }

    private func bewerten(_ bewertung: String) async {
        do {
            try await ApiClient.geteilt.schickenOhneAntwort("/news/feedback", koerper: FeedbackAnfrage(titel: meldung.titel, bewertung: bewertung))
            bewertet = "Gemerkt"
        } catch {
            bewertet = error.localizedDescription
        }
    }

    private func vertiefen() async {
        laedt = true
        do {
            let antwort: VertiefungsAntwort = try await ApiClient.geteilt.schicken(
                "/news/vertiefen",
                koerper: VertiefenAnfrage(titel: meldung.titel, zusammenfassung: meldung.zusammenfassung)
            )
            vertiefung = antwort.text
        } catch {
            vertiefung = error.localizedDescription
        }
        laedt = false
    }
}
