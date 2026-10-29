import SwiftUI

// Tagesuebersicht, Verlauf und die Moeglichkeit jeden Eintrag nachzubessern

struct ErnaehrungAnsicht: View {
    @EnvironmentObject var einstellungen: Einstellungen

    @State private var heute: EssenTag?
    @State private var wasser: WasserStand?
    @State private var verlauf: [VerlaufsTag] = []
    @State private var eingabe = ""
    @State private var laedt = false
    @State private var fehlertext = ""
    @State private var zuBearbeiten: EssenEintrag?

    var body: some View {
        NavigationStack {
            Group {
                if !einstellungen.istEingerichtet {
                    NichtEingerichtetHinweis()
                } else {
                    List {
                        eingabeAbschnitt
                        summenAbschnitt
                        wasserAbschnitt
                        eintraegeAbschnitt
                        verlaufsAbschnitt
                    }
                    .refreshable {
                        await laden()
                    }
                }
            }
            .navigationTitle("Ernaehrung")
            .sheet(item: $zuBearbeiten) { eintrag in
                EintragBearbeitenAnsicht(eintrag: eintrag, fertig: {
                    Task { await laden() }
                })
            }
            .task {
                await laden()
            }
        }
    }

    private var eingabeAbschnitt: some View {
        Section {
            HStack {
                TextField("z.B. 2 Scheiben Schwarzbrot mit Nutella", text: $eingabe, axis: .vertical)
                    .lineLimit(1...3)

                Button {
                    Task { await eintragen() }
                } label: {
                    Image(systemName: "plus.circle.fill")
                        .font(.title3)
                }
                .disabled(eingabe.trimmingCharacters(in: .whitespaces).isEmpty || laedt)
            }

            if laedt {
                LadeAnzeige(text: "Naehrwerte werden gesucht")
            }

            if !fehlertext.isEmpty {
                FehlerKarte(text: fehlertext)
            }
        }
    }

    @ViewBuilder
    private var summenAbschnitt: some View {
        if let heute = heute {
            Section("Heute") {
                FortschrittsBalken(titel: "Kalorien", aktuell: heute.summe.kcal, ziel: heute.ziele.kcalZiel, einheit: "kcal", farbe: .orange)
                FortschrittsBalken(titel: "Eiweiss", aktuell: heute.summe.eiweissG, ziel: heute.ziele.eiweissZielG, einheit: "g", farbe: .red)
                FortschrittsBalken(titel: "Kohlenhydrate", aktuell: heute.summe.kohlenhydrateG, ziel: heute.ziele.kohlenhydrateZielG, einheit: "g", farbe: .yellow)
                FortschrittsBalken(titel: "Fett", aktuell: heute.summe.fettG, ziel: heute.ziele.fettZielG, einheit: "g", farbe: .purple)
            }
        }
    }

    @ViewBuilder
    private var wasserAbschnitt: some View {
        if let wasser = wasser {
            Section("Trinken") {
                FortschrittsBalken(titel: "Wasser", aktuell: Double(wasser.summeMl), ziel: Double(wasser.zielMl), einheit: "ml", farbe: .blue)

                HStack(spacing: 10) {
                    Button("+250") {
                        Task { await wasserEintragen(250) }
                    }
                    Button("+500") {
                        Task { await wasserEintragen(500) }
                    }
                    Button("+750") {
                        Task { await wasserEintragen(750) }
                    }
                }
                .buttonStyle(.bordered)
            }
        }
    }

    @ViewBuilder
    private var eintraegeAbschnitt: some View {
        if let heute = heute, !heute.eintraege.isEmpty {
            Section("Eintraege heute") {
                ForEach(heute.eintraege) { eintrag in
                    Button {
                        zuBearbeiten = eintrag
                    } label: {
                        EssenZeile(eintrag: eintrag)
                    }
                    .buttonStyle(.plain)
                }
                .onDelete { stellen in
                    Task { await eintraegeLoeschen(stellen) }
                }
            }
        }
    }

    @ViewBuilder
    private var verlaufsAbschnitt: some View {
        if !verlauf.isEmpty {
            Section("Verlauf") {
                ForEach(verlauf) { tag in
                    HStack {
                        Text(tag.datum)
                            .font(.callout.monospacedDigit())
                        Spacer()
                        Text("\(Int(tag.kcal)) kcal")
                            .foregroundStyle(.secondary)
                    }
                }
            }
        }
    }

    private func laden() async {
        fehlertext = ""
        do {
            heute = try await ApiClient.geteilt.holen("/food/today")
            wasser = try await ApiClient.geteilt.holen("/water/today")

            let geladen: Verlauf = try await ApiClient.geteilt.holen("/food/history?tage=14")
            verlauf = geladen.verlauf
        } catch {
            fehlertext = error.localizedDescription
        }
    }

    private func eintragen() async {
        let text = eingabe.trimmingCharacters(in: .whitespaces)
        if text.isEmpty {
            return
        }

        laedt = true
        fehlertext = ""

        do {
            let _: EssenAntwort = try await ApiClient.geteilt.schicken("/food/log", koerper: FreitextAnfrage(text: text))
            eingabe = ""
            await laden()
        } catch {
            fehlertext = error.localizedDescription
        }

        laedt = false
    }

    private func wasserEintragen(_ menge: Int) async {
        do {
            let stand: WasserStand = try await ApiClient.geteilt.schicken("/water/log", koerper: WasserAnfrage(mengeMl: menge))
            wasser = stand

            if einstellungen.trinkErinnerungAn {
                Benachrichtigungen.geteilt.trinkErinnerungPlanen(inStunden: einstellungen.trinkErinnerungStunden)
            }
        } catch {
            fehlertext = error.localizedDescription
        }
    }

    private func eintraegeLoeschen(_ stellen: IndexSet) async {
        guard let heute = heute else {
            return
        }

        for stelle in stellen {
            let eintrag = heute.eintraege[stelle]
            do {
                try await ApiClient.geteilt.loeschen("/food/\(eintrag.id)")
            } catch {
                fehlertext = error.localizedDescription
            }
        }

        await laden()
    }
}

struct EssenZeile: View {
    let eintrag: EssenEintrag

    var body: some View {
        VStack(alignment: .leading, spacing: 2) {
            HStack {
                Text(eintrag.beschreibung)
                Spacer()
                Text("\(Int(eintrag.kcal)) kcal")
                    .foregroundStyle(.secondary)
            }

            HStack(spacing: 8) {
                if let menge = eintrag.mengeText, !menge.isEmpty {
                    Text(menge)
                }
                Text("E \(Int(eintrag.eiweissG))g")
                Text("K \(Int(eintrag.kohlenhydrateG))g")
                Text("F \(Int(eintrag.fettG))g")

                if eintrag.quelle == "geschaetzt" {
                    Text("geschaetzt")
                        .foregroundStyle(.orange)
                }
            }
            .font(.caption)
            .foregroundStyle(.secondary)
        }
    }
}

// Jeder Eintrag muss nachbesserbar sein, die Schaetzung stimmt nie ganz
struct EintragBearbeitenAnsicht: View {
    let eintrag: EssenEintrag
    let fertig: () -> Void

    @Environment(\.dismiss) private var schliessen

    @State private var beschreibung: String
    @State private var mengeText: String
    @State private var kcal: String
    @State private var eiweiss: String
    @State private var kohlenhydrate: String
    @State private var fett: String
    @State private var fehlertext = ""

    init(eintrag: EssenEintrag, fertig: @escaping () -> Void) {
        self.eintrag = eintrag
        self.fertig = fertig

        _beschreibung = State(initialValue: eintrag.beschreibung)
        _mengeText = State(initialValue: eintrag.mengeText ?? "")
        _kcal = State(initialValue: String(Int(eintrag.kcal)))
        _eiweiss = State(initialValue: String(Int(eintrag.eiweissG)))
        _kohlenhydrate = State(initialValue: String(Int(eintrag.kohlenhydrateG)))
        _fett = State(initialValue: String(Int(eintrag.fettG)))
    }

    var body: some View {
        NavigationStack {
            Form {
                Section("Was") {
                    TextField("Beschreibung", text: $beschreibung)
                    TextField("Menge", text: $mengeText)
                }

                Section("Naehrwerte") {
                    HStack {
                        Text("Kalorien")
                        Spacer()
                        TextField("kcal", text: $kcal)
                            .keyboardType(.numberPad)
                            .multilineTextAlignment(.trailing)
                    }
                    HStack {
                        Text("Eiweiss")
                        Spacer()
                        TextField("g", text: $eiweiss)
                            .keyboardType(.numberPad)
                            .multilineTextAlignment(.trailing)
                    }
                    HStack {
                        Text("Kohlenhydrate")
                        Spacer()
                        TextField("g", text: $kohlenhydrate)
                            .keyboardType(.numberPad)
                            .multilineTextAlignment(.trailing)
                    }
                    HStack {
                        Text("Fett")
                        Spacer()
                        TextField("g", text: $fett)
                            .keyboardType(.numberPad)
                            .multilineTextAlignment(.trailing)
                    }
                }

                if !fehlertext.isEmpty {
                    FehlerKarte(text: fehlertext)
                }
            }
            .navigationTitle("Eintrag anpassen")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Abbrechen") {
                        schliessen()
                    }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Speichern") {
                        Task { await speichern() }
                    }
                }
            }
        }
    }

    private func speichern() async {
        var aenderung = EssenAenderung()
        aenderung.beschreibung = beschreibung
        aenderung.mengeText = mengeText
        aenderung.kcal = Double(kcal) ?? eintrag.kcal
        aenderung.eiweissG = Double(eiweiss) ?? eintrag.eiweissG
        aenderung.kohlenhydrateG = Double(kohlenhydrate) ?? eintrag.kohlenhydrateG
        aenderung.fettG = Double(fett) ?? eintrag.fettG

        do {
            try await ApiClient.geteilt.schickenOhneAntwort("/food/\(eintrag.id)", methode: "PATCH", koerper: aenderung)
            fertig()
            schliessen()
        } catch {
            fehlertext = error.localizedDescription
        }
    }
}
