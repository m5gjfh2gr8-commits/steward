import SwiftUI

// Ein Modul im Detail: Zustand oben, darunter die Berichte (neueste zuerst)
// Beim Öffnen werden die Berichte als gelesen markiert - die Punkte bleiben aber stehen,
// bis man die Seite wieder verlässt, damit man sieht, was neu war

struct ModulDetailAnsicht: View {
    let name: String

    @EnvironmentObject var daten: AppDaten
    @ObservedObject private var vorlesen: Vorlesen = Vorlesen.geteilt

    @State private var berichte: [Bericht] = []
    @State private var gelesenBis: Date?
    @State private var laedt: Bool = true
    @State private var fehlertext: String = ""
    @State private var laeuftGerade: Bool = false
    @State private var laufMeldung: String = ""

    private var modul: ModulZustand? {
        return daten.modul(mitName: name)
    }

    var body: some View {
        List {
            Section {
                LabeledContent("Zustand") {
                    ZustandsAnzeige(zustand: modul?.zustand ?? "neu")
                }
                LabeledContent("Letzter Lauf", value: Zeitformat.mitTag(text: modul?.letzterLauf?.start))
                LabeledContent("Nächster Lauf", value: naechsterLaufText)

                if let meldung = fehlermeldung {
                    Text(meldung)
                        .font(.footnote)
                        .foregroundStyle(.red)
                }
            } footer: {
                if laufMeldung.isEmpty == false {
                    Text(laufMeldung)
                }
            }

            Section("Berichte") {
                if berichte.isEmpty {
                    if laedt {
                        HStack {
                            Spacer()
                            ProgressView()
                            Spacer()
                        }
                    } else if fehlertext.isEmpty == false {
                        Text(fehlertext)
                            .foregroundStyle(.secondary)
                    } else {
                        Text("Noch keine Berichte")
                            .foregroundStyle(.secondary)
                    }
                }

                ForEach(berichte) { bericht in
                    NavigationLink(value: bericht) {
                        BerichtZeile(bericht: bericht, ungelesen: istUngelesen(bericht))
                    }
                }
            }
        }
        .listStyle(.insetGrouped)
        .navigationTitle(modul?.anzeigename ?? name)
        .navigationBarTitleDisplayMode(.large)
        .navigationDestination(for: Bericht.self) { bericht in
            BerichtDetailAnsicht(bericht: bericht, modulName: modul?.anzeigename ?? name)
        }
        .toolbar {
            ToolbarItemGroup(placement: .topBarTrailing) {
                Button {
                    Task {
                        await jetztAusfuehren()
                    }
                } label: {
                    if laeuftGerade {
                        ProgressView()
                    } else {
                        Image(systemName: "play.fill")
                    }
                }
                .disabled(laeuftGerade)
                .accessibilityLabel("Jetzt ausführen")

                Button {
                    vorlesen.umschalten(text: vorlesetext)
                } label: {
                    if vorlesen.laeuft {
                        Image(systemName: "stop.fill")
                    } else {
                        Image(systemName: "speaker.wave.2")
                    }
                }
                .disabled(berichte.isEmpty)
                .accessibilityLabel("Vorlesen")
            }
        }
        .refreshable {
            await berichteLaden(markieren: false)
        }
        .task {
            await berichteLaden(markieren: true)
        }
        .onDisappear {
            vorlesen.stoppen()
        }
    }

    private var naechsterLaufText: String {
        guard let text = modul?.naechsterLauf else {
            return "Nur von Hand"
        }
        return Zeitformat.mitTag(text: text)
    }

    private var fehlermeldung: String? {
        guard let modul = modul else {
            return nil
        }
        if modul.hatFehler == false {
            return nil
        }
        let meldung: String = modul.letzterLauf?.meldung ?? ""
        if meldung.isEmpty {
            return nil
        }
        return meldung
    }

    private func istUngelesen(_ bericht: Bericht) -> Bool {
        guard let grenze = gelesenBis else {
            return true
        }
        guard let zeit = bericht.datum else {
            return false
        }
        return zeit > grenze
    }

    // Vorgelesen werden die ungelesenen Berichte, sonst der neueste
    private var vorlesetext: String {
        var texte: [String] = []
        for bericht in berichte {
            if istUngelesen(bericht) {
                texte.append(bericht.vorlesetext)
            }
        }
        if texte.isEmpty {
            if let neuester = berichte.first {
                texte.append(neuester.vorlesetext)
            }
        }
        return texte.joined(separator: ". ")
    }

    private func berichteLaden(markieren: Bool) async {
        laedt = true

        do {
            let antwort: BerichteAntwort = try await ApiClient.geteilt.holen("/module/" + name + "/berichte?anzahl=30")
            berichte = antwort.berichte
            gelesenBis = Zeitformat.datum(aus: antwort.gelesenBis)
            fehlertext = ""

            if markieren && antwort.berichte.isEmpty == false {
                try await ApiClient.geteilt.schickenOhneAntwort("/module/" + name + "/gelesen", koerper: GelesenAnfrage(zeitpunkt: nil))
                await daten.gelesenGemeldet()
            }
        } catch {
            fehlertext = error.localizedDescription
        }

        laedt = false
    }

    private func jetztAusfuehren() async {
        laeuftGerade = true
        laufMeldung = ""

        do {
            try await ApiClient.geteilt.schickenOhneAntwort("/module/" + name + "/lauf", koerper: LeererKoerper(), langsam: true)
            laufMeldung = "Lauf um " + Zeitformat.uhrzeit(Date()) + " abgeschlossen"
        } catch {
            laufMeldung = error.localizedDescription
        }

        await daten.moduleLaden()
        await berichteLaden(markieren: true)
        laeuftGerade = false
    }
}

struct BerichtZeile: View {
    let bericht: Bericht
    let ungelesen: Bool

    var body: some View {
        HStack(alignment: .top, spacing: 10) {
            Circle()
                .fill(.tint)
                .frame(width: 9, height: 9)
                .padding(.top, 7)
                .opacity(ungelesen ? 1 : 0)
                .accessibilityHidden(ungelesen == false)
                .accessibilityLabel("Ungelesen")

            VStack(alignment: .leading, spacing: 2) {
                Text(bericht.titel)
                    .fontWeight(ungelesen ? .semibold : .regular)
                if bericht.kurzfassung.isEmpty == false {
                    Text(bericht.kurzfassung)
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                        .lineLimit(1)
                }
            }

            Spacer(minLength: 8)

            if let zeit = bericht.datum {
                Text(Zeitformat.knapp(zeit))
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            }
        }
    }
}
