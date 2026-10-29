import SwiftUI

// Server-Adresse, API-Key, Tagesziele, Interessensprofil und Verbindungsstatus

struct EinstellungenAnsicht: View {
    @EnvironmentObject var einstellungen: Einstellungen

    @State private var status: ServerStatus?
    @State private var statusText = ""
    @State private var pruefe = false

    @State private var ziele: Tagesziele?
    @State private var interessen: [Interesse] = []
    @State private var neuesInteresse = ""

    var body: some View {
        NavigationStack {
            Form {
                verbindungsAbschnitt
                zieleAbschnitt
                interessenAbschnitt
                erinnerungsAbschnitt
                infoAbschnitt
            }
            .navigationTitle("Einstellungen")
            .task {
                await ladenWennMoeglich()
            }
        }
    }

    private var verbindungsAbschnitt: some View {
        Section {
            TextField("http://steward:8000", text: $einstellungen.serverAdresse)
                .textInputAutocapitalization(.never)
                .autocorrectionDisabled()
                .keyboardType(.URL)

            SecureField("API-Key", text: $einstellungen.apiKey)

            Button {
                Task { await verbindungPruefen() }
            } label: {
                if pruefe {
                    LadeAnzeige(text: "Wird geprueft")
                } else {
                    Text("Verbindung pruefen")
                }
            }

            if !statusText.isEmpty {
                Text(statusText)
                    .font(.footnote)
                    .foregroundStyle(.secondary)
            }
        } header: {
            Text("Server")
        } footer: {
            Text("Die Adresse ist der Tailscale-Name des Heimservers. Ohne aktives Tailscale am iPhone ist der Server nicht erreichbar.")
        }
    }

    @ViewBuilder
    private var zieleAbschnitt: some View {
        if let ziele = ziele {
            Section("Tagesziele") {
                ZielZeile(titel: "Kalorien", einheit: "kcal", wert: ziele.kcalZiel) { neuerWert in
                    Task { await zielSpeichern(kcal: neuerWert) }
                }
                ZielZeile(titel: "Eiweiss", einheit: "g", wert: ziele.eiweissZielG) { neuerWert in
                    Task { await zielSpeichern(eiweiss: neuerWert) }
                }
                ZielZeile(titel: "Kohlenhydrate", einheit: "g", wert: ziele.kohlenhydrateZielG) { neuerWert in
                    Task { await zielSpeichern(kohlenhydrate: neuerWert) }
                }
                ZielZeile(titel: "Fett", einheit: "g", wert: ziele.fettZielG) { neuerWert in
                    Task { await zielSpeichern(fett: neuerWert) }
                }
                ZielZeile(titel: "Wasser", einheit: "ml", wert: Double(ziele.wasserZielMl)) { neuerWert in
                    Task { await zielSpeichern(wasser: Int(neuerWert)) }
                }
            }
        }
    }

    private var interessenAbschnitt: some View {
        Section {
            ForEach(interessen) { eintrag in
                Text(eintrag.stichwort)
            }
            .onDelete { stellen in
                Task { await interesseEntfernen(stellen) }
            }

            HStack {
                TextField("Neues Thema", text: $neuesInteresse)
                Button {
                    Task { await interesseHinzufuegen() }
                } label: {
                    Image(systemName: "plus.circle.fill")
                }
                .disabled(neuesInteresse.trimmingCharacters(in: .whitespaces).isEmpty)
            }
        } header: {
            Text("Interessen fuer die News")
        } footer: {
            Text("Danach filtert das Morning Briefing. Daumen hoch/runter bei einzelnen Meldungen justiert es zusaetzlich nach.")
        }
    }

    private var erinnerungsAbschnitt: some View {
        Section("Trink-Erinnerung") {
            Toggle("Erinnern wenn laenger nichts eingetragen", isOn: $einstellungen.trinkErinnerungAn)
                .onChange(of: einstellungen.trinkErinnerungAn) {
                    if einstellungen.trinkErinnerungAn {
                        Benachrichtigungen.geteilt.trinkErinnerungPlanen(inStunden: einstellungen.trinkErinnerungStunden)
                    } else {
                        Benachrichtigungen.geteilt.trinkErinnerungLoeschen()
                    }
                }

            if einstellungen.trinkErinnerungAn {
                Stepper("Nach \(einstellungen.trinkErinnerungStunden) Stunden", value: $einstellungen.trinkErinnerungStunden, in: 1...8)
            }
        }
    }

    @ViewBuilder
    private var infoAbschnitt: some View {
        if let status = status {
            Section("Server-Info") {
                LabeledContent("Modell", value: status.llmModellStandard)
                LabeledContent("Anbieter", value: status.llmAnbieter)

                if status.kalenderEingerichtet {
                    LabeledContent("Kalender", value: "verbunden")
                } else {
                    LabeledContent("Kalender", value: "nicht eingerichtet")
                }

                LabeledContent("Postfaecher", value: "\(status.postfaecher.count)")
                LabeledContent("Feeds", value: "\(status.feeds.count)")
            }
        }
    }

    private func ladenWennMoeglich() async {
        if !einstellungen.istEingerichtet {
            return
        }

        do {
            ziele = try await ApiClient.geteilt.holen("/goals")
            interessen = try await ApiClient.geteilt.holen("/profile/interests")
            status = try await ApiClient.geteilt.holen("/status")
        } catch {
            statusText = error.localizedDescription
        }
    }

    private func verbindungPruefen() async {
        pruefe = true
        statusText = ""

        do {
            status = try await ApiClient.geteilt.holen("/status")
            statusText = "Passt, Server antwortet"
            await ladenWennMoeglich()
        } catch {
            statusText = error.localizedDescription
        }

        pruefe = false
    }

    private func zielSpeichern(kcal: Double? = nil, eiweiss: Double? = nil, kohlenhydrate: Double? = nil, fett: Double? = nil, wasser: Int? = nil) async {
        var anfrage = ZieleAnfrage()
        anfrage.kcalZiel = kcal
        anfrage.eiweissZielG = eiweiss
        anfrage.kohlenhydrateZielG = kohlenhydrate
        anfrage.fettZielG = fett
        anfrage.wasserZielMl = wasser

        do {
            ziele = try await ApiClient.geteilt.schicken("/goals", koerper: anfrage)
        } catch {
            statusText = error.localizedDescription
        }
    }

    private func interesseHinzufuegen() async {
        var stichwoerter: [String] = []
        for eintrag in interessen {
            stichwoerter.append(eintrag.stichwort)
        }
        stichwoerter.append(neuesInteresse.trimmingCharacters(in: .whitespaces))

        await interessenSpeichern(stichwoerter)
        neuesInteresse = ""
    }

    private func interesseEntfernen(_ stellen: IndexSet) async {
        var stichwoerter: [String] = []
        var stelle = 0
        for eintrag in interessen {
            if !stellen.contains(stelle) {
                stichwoerter.append(eintrag.stichwort)
            }
            stelle = stelle + 1
        }

        await interessenSpeichern(stichwoerter)
    }

    private func interessenSpeichern(_ stichwoerter: [String]) async {
        do {
            interessen = try await ApiClient.geteilt.schicken("/profile/interests", koerper: InteressenAnfrage(stichwoerter: stichwoerter))
        } catch {
            statusText = error.localizedDescription
        }
    }
}

struct ZielZeile: View {
    let titel: String
    let einheit: String
    let wert: Double
    let gespeichert: (Double) -> Void

    @State private var text = ""

    var body: some View {
        HStack {
            Text(titel)
            Spacer()
            TextField(einheit, text: $text)
                .keyboardType(.numberPad)
                .multilineTextAlignment(.trailing)
                .frame(width: 80)
                .onSubmit {
                    if let neuerWert = Double(text) {
                        gespeichert(neuerWert)
                    }
                }
            Text(einheit)
                .foregroundStyle(.secondary)
        }
        .onAppear {
            text = String(Int(wert))
        }
    }
}
