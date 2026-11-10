import SwiftUI

// Das eine Eingabefeld: tippen oder diktieren, das Backend erkennt selbst,
// ob es eine Aufgabe, ein Essenseintrag, Trinken oder eine Frage ist

struct Nachricht: Identifiable {
    let id = UUID()
    let vonMir: Bool
    let text: String
}

struct ChatAnsicht: View {
    @EnvironmentObject var einstellungen: Einstellungen
    @StateObject private var spracheingabe = Spracheingabe()

    @State private var eingabe = ""
    @State private var verlauf: [Nachricht] = []
    @State private var laedt = false

    var body: some View {
        NavigationStack {
            Group {
                if !einstellungen.istEingerichtet {
                    NichtEingerichtetHinweis()
                } else {
                    VStack(spacing: 0) {
                        verlaufsListe
                        Divider()
                        eingabeZeile
                    }
                }
            }
            .navigationTitle("Eingabe")
        }
    }

    private var verlaufsListe: some View {
        ScrollViewReader { leser in
            ScrollView {
                LazyVStack(alignment: .leading, spacing: 10) {
                    if verlauf.isEmpty {
                        Text("Schreib oder sag einfach was an - zum Beispiel \"morgen um 3 zum Zahnarzt\", \"2 Semmeln mit Butter gegessen\" oder \"wie schaut mein Tag aus\".")
                            .font(.footnote)
                            .foregroundStyle(.secondary)
                            .padding()
                    }

                    ForEach(verlauf) { nachricht in
                        NachrichtenBlase(nachricht: nachricht)
                            .id(nachricht.id)
                    }

                    if laedt {
                        LadeAnzeige(text: "Denkt nach")
                    }
                }
                .padding()
            }
            .onChange(of: verlauf.count) {
                if let letzte = verlauf.last {
                    withAnimation {
                        leser.scrollTo(letzte.id, anchor: .bottom)
                    }
                }
            }
        }
    }

    private var eingabeZeile: some View {
        HStack(spacing: 10) {
            Button {
                mikrofonUmschalten()
            } label: {
                if spracheingabe.laeuft {
                    Image(systemName: "mic.fill")
                        .foregroundStyle(.red)
                } else {
                    Image(systemName: "mic")
                }
            }
            .font(.title3)

            TextField("Was ist los?", text: $eingabe, axis: .vertical)
                .textFieldStyle(.roundedBorder)
                .lineLimit(1...4)

            Button {
                Task { await abschicken() }
            } label: {
                Image(systemName: "arrow.up.circle.fill")
                    .font(.title2)
            }
            .disabled(eingabe.trimmingCharacters(in: .whitespaces).isEmpty || laedt)
        }
        .padding()
    }

    private func mikrofonUmschalten() {
        if spracheingabe.laeuft {
            spracheingabe.stoppen()
            if !spracheingabe.erkannterText.isEmpty {
                eingabe = spracheingabe.erkannterText
            }
        } else {
            spracheingabe.starten()
        }
    }

    private func abschicken() async {
        let text = eingabe.trimmingCharacters(in: .whitespaces)
        if text.isEmpty {
            return
        }

        verlauf.append(Nachricht(vonMir: true, text: text))
        eingabe = ""
        laedt = true

        do {
            let antwort: ChatAntwort = try await ApiClient.geteilt.schicken("/chat", koerper: FreitextAnfrage(text: text))
            verlauf.append(Nachricht(vonMir: false, text: antwort.antwort))

            if antwort.art == "aufgabe" {
                await erinnerungFuerLetzteAufgabePlanen()
            }
        } catch {
            verlauf.append(Nachricht(vonMir: false, text: error.localizedDescription))
        }

        laedt = false
    }

    // Die lokale Erinnerung plant die App selbst, dafuer wird das frisch angelegte Todo geholt
    private func erinnerungFuerLetzteAufgabePlanen() async {
        do {
            let offene: [Todo] = try await ApiClient.geteilt.holen("/tasks")
            for todo in offene {
                if let zeitpunkt = Benachrichtigungen.geteilt.zeitpunktAusText(todo.faelligAm) {
                    Benachrichtigungen.geteilt.terminErinnerungPlanen(
                        kennung: "todo-\(todo.id)",
                        text: todo.inhalt,
                        zeitpunkt: zeitpunkt
                    )
                }
            }
        } catch {
            // ohne Erinnerung ist das Todo trotzdem angelegt, also nicht weiter schlimm
        }
    }
}

struct NachrichtenBlase: View {
    let nachricht: Nachricht

    var body: some View {
        HStack {
            if nachricht.vonMir {
                Spacer(minLength: 40)
                Text(nachricht.text)
                    .padding(10)
                    .background(Color.accentColor.opacity(0.15))
                    .clipShape(RoundedRectangle(cornerRadius: 12))
            } else {
                Text(nachricht.text)
                    .padding(10)
                    .background(Color(.secondarySystemBackground))
                    .clipShape(RoundedRectangle(cornerRadius: 12))
                Spacer(minLength: 40)
            }
        }
    }
}
