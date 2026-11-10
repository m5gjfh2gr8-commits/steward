import SwiftUI

// Der Steward-Tab: Fragen stellen oder Aufgaben geben, wie in einem Chat
// Erkennt Steward eine Aufgabe, legt er ein Todo an und die App zeigt eine Bestätigung

struct StewardAnsicht: View {
    @EnvironmentObject var chat: ChatVerlauf
    @EnvironmentObject var daten: AppDaten
    @StateObject private var sprache: Spracheingabe = Spracheingabe()

    @State private var eingabe: String = ""
    @FocusState private var eingabeAktiv: Bool

    private let vorschlaege: [String] = [
        "Was gibt es Neues?",
        "Erinnere mich morgen um 9 an die Bewerbung",
        "Läuft alles?",
    ]

    var body: some View {
        NavigationStack {
            ScrollViewReader { leser in
                ScrollView {
                    LazyVStack(spacing: 12) {
                        if chat.nachrichten.isEmpty {
                            leererZustand
                        }

                        ForEach(chat.nachrichten) { nachricht in
                            NachrichtZeile(nachricht: nachricht) {
                                daten.ausgewaehlterBereich = Bereich.todos
                            }
                            .id(nachricht.id)
                        }

                        if chat.wartet {
                            HStack {
                                ProgressView()
                                    .padding(.horizontal, 16)
                                    .padding(.vertical, 12)
                                    .background(Color(.secondarySystemBackground), in: RoundedRectangle(cornerRadius: 20, style: .continuous))
                                Spacer()
                            }
                            .id("wartet")
                        }
                    }
                    .padding(.horizontal, 16)
                    .padding(.vertical, 12)
                }
                .scrollDismissesKeyboard(.interactively)
                .onChange(of: chat.nachrichten.count) { _, _ in
                    nachUntenScrollen(leser)
                }
                .onChange(of: chat.wartet) { _, _ in
                    nachUntenScrollen(leser)
                }
                .onAppear {
                    nachUntenScrollen(leser)
                }
            }
            .safeAreaInset(edge: .bottom) {
                eingabeleiste
            }
            .navigationTitle("Steward")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Menu {
                        Button(role: .destructive) {
                            chat.leeren()
                        } label: {
                            Label("Verlauf löschen", systemImage: "trash")
                        }
                    } label: {
                        Image(systemName: "ellipsis")
                    }
                    .disabled(chat.nachrichten.isEmpty)
                    .accessibilityLabel("Mehr")
                }
            }
            .onChange(of: sprache.erkannterText) { _, neuerText in
                if sprache.laeuft {
                    eingabe = neuerText
                }
            }
        }
    }

    private var leererZustand: some View {
        VStack(spacing: 16) {
            Image(systemName: "bubble.left.and.text.bubble.right")
                .font(.system(size: 44))
                .foregroundStyle(.tint)
            Text("Frag Steward etwas")
                .font(.title3.weight(.semibold))
            Text("oder gib ihm eine Aufgabe – er erkennt selbst, was gemeint ist.")
                .font(.subheadline)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)

            VStack(spacing: 8) {
                ForEach(vorschlaege, id: \.self) { vorschlag in
                    Button {
                        Task {
                            await chat.senden(vorschlag)
                        }
                    } label: {
                        Text(vorschlag)
                            .font(.subheadline)
                            .padding(.horizontal, 14)
                            .padding(.vertical, 8)
                            .background(Color(.secondarySystemBackground), in: Capsule())
                    }
                    .buttonStyle(.plain)
                }
            }
            .padding(.top, 8)
        }
        .padding(.top, 80)
        .frame(maxWidth: .infinity)
    }

    private var eingabeleiste: some View {
        VStack(spacing: 4) {
            if sprache.fehlertext.isEmpty == false {
                Text(sprache.fehlertext)
                    .font(.footnote)
                    .foregroundStyle(.red)
            }

            HStack(alignment: .bottom, spacing: 8) {
                TextField("Frag Steward oder gib eine Aufgabe …", text: $eingabe, axis: .vertical)
                    .lineLimit(1...5)
                    .focused($eingabeAktiv)
                    .padding(.horizontal, 16)
                    .padding(.vertical, 10)
                    .background(Color(.secondarySystemBackground), in: RoundedRectangle(cornerRadius: 22, style: .continuous))

                if sprache.laeuft {
                    Button {
                        sprache.stoppen()
                    } label: {
                        PegelAnzeige(pegel: sprache.pegel)
                            .frame(width: 44, height: 44)
                            .background(Circle().fill(.tint))
                    }
                    .accessibilityLabel("Aufnahme beenden")
                } else if eingabe.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
                    Button {
                        eingabeAktiv = false
                        sprache.starten()
                    } label: {
                        Image(systemName: "mic.fill")
                            .font(.title3)
                            .frame(width: 44, height: 44)
                            .background(Color(.secondarySystemBackground), in: Circle())
                    }
                    .accessibilityLabel("Spracheingabe")
                } else {
                    Button {
                        abschicken()
                    } label: {
                        Image(systemName: "arrow.up")
                            .font(.title3.weight(.semibold))
                            .foregroundStyle(.white)
                            .frame(width: 44, height: 44)
                            .background(Circle().fill(.tint))
                    }
                    .disabled(chat.wartet)
                    .accessibilityLabel("Senden")
                }
            }
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 8)
        .background(.bar)
    }

    private func abschicken() {
        let text: String = eingabe
        eingabe = ""
        Task {
            await chat.senden(text)
        }
    }

    private func nachUntenScrollen(_ leser: ScrollViewProxy) {
        withAnimation {
            if chat.wartet {
                leser.scrollTo("wartet", anchor: .bottom)
            } else if let letzte = chat.nachrichten.last {
                leser.scrollTo(letzte.id, anchor: .bottom)
            }
        }
    }
}

// Eine Nachricht: meine rechts in der Akzentfarbe, Stewards links in Grau
struct NachrichtZeile: View {
    let nachricht: ChatNachricht
    let zuDenTodos: () -> Void

    var body: some View {
        HStack {
            if nachricht.vonMir {
                Spacer(minLength: 48)
                Text(nachricht.text)
                    .foregroundStyle(.white)
                    .padding(.horizontal, 14)
                    .padding(.vertical, 10)
                    .background(RoundedRectangle(cornerRadius: 20, style: .continuous).fill(.tint))
                    .textSelection(.enabled)
            } else if nachricht.art == "aufgabe" {
                aufgabenKarte
                Spacer(minLength: 48)
            } else {
                Text(nachricht.text)
                    .foregroundStyle(nachricht.art == "fehler" ? Color.red : Color.primary)
                    .padding(.horizontal, 14)
                    .padding(.vertical, 10)
                    .background(Color(.secondarySystemBackground), in: RoundedRectangle(cornerRadius: 20, style: .continuous))
                    .textSelection(.enabled)
                Spacer(minLength: 48)
            }
        }
    }

    private var aufgabenKarte: some View {
        VStack(alignment: .leading, spacing: 8) {
            Label {
                Text(nachricht.text)
            } icon: {
                Image(systemName: "checkmark.circle.fill")
                    .foregroundStyle(.green)
            }

            Button("Zu den Todos") {
                zuDenTodos()
            }
            .font(.subheadline)
        }
        .padding(.horizontal, 14)
        .padding(.vertical, 12)
        .background(Color(.secondarySystemBackground), in: RoundedRectangle(cornerRadius: 20, style: .continuous))
    }
}

// Fünf kleine Balken, die mit der Lautstärke mitwippen
struct PegelAnzeige: View {
    let pegel: Double

    private let gewichte: [Double] = [0.5, 0.8, 1.0, 0.8, 0.5]

    var body: some View {
        HStack(spacing: 3) {
            ForEach(0..<gewichte.count, id: \.self) { index in
                Capsule()
                    .fill(Color.white)
                    .frame(width: 3, height: balkenHoehe(index))
            }
        }
        .animation(.easeOut(duration: 0.12), value: pegel)
    }

    private func balkenHoehe(_ index: Int) -> CGFloat {
        let minimum: Double = 4.0
        let maximum: Double = 22.0
        let hoehe: Double = minimum + (maximum - minimum) * pegel * gewichte[index]
        return CGFloat(hoehe)
    }
}
