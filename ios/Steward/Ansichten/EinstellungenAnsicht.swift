import AVFoundation
import SwiftUI

// Einstellungen als gruppierte Liste, wie in der iOS-Einstellungen-App

struct EinstellungenAnsicht: View {
    @EnvironmentObject var einstellungen: Einstellungen

    @State private var test: TestErgebnis = TestErgebnis.keins
    @State private var serverVersion: String = "–"

    private let stimmen: [AVSpeechSynthesisVoice] = Vorlesen.deutscheStimmen()

    var body: some View {
        NavigationStack {
            Form {
                Section {
                    LabeledContent("Adresse") {
                        TextField("name.tailnet.ts.net", text: $einstellungen.serverAdresse)
                            .multilineTextAlignment(.trailing)
                            .textInputAutocapitalization(.never)
                            .autocorrectionDisabled()
                            .keyboardType(.URL)
                    }
                    LabeledContent("Steward-Key") {
                        SecureField("Pflicht", text: $einstellungen.apiKey)
                            .multilineTextAlignment(.trailing)
                    }
                    Button("Verbindung testen") {
                        Task {
                            await testen()
                        }
                    }
                } header: {
                    Text("Verbindung")
                } footer: {
                    TestErgebnisAnzeige(ergebnis: test)
                }

                Section {
                    AkzentAuswahl(auswahl: $einstellungen.akzent)
                } header: {
                    Text("Darstellung")
                } footer: {
                    Text("Die Akzentfarbe gilt für die ganze App.")
                }

                Section("Vorlesen") {
                    Picker("Stimme", selection: $einstellungen.vorleseStimme) {
                        Text("Standard").tag("")
                        ForEach(stimmen, id: \.identifier) { stimme in
                            Text(stimme.name + " (" + stimme.language + ")").tag(stimme.identifier)
                        }
                    }

                    VStack(alignment: .leading, spacing: 4) {
                        Text("Geschwindigkeit")
                        Slider(value: $einstellungen.vorleseTempo, in: 0.35...0.6) {
                            Text("Geschwindigkeit")
                        } minimumValueLabel: {
                            Image(systemName: "tortoise")
                        } maximumValueLabel: {
                            Image(systemName: "hare")
                        }
                    }
                    .padding(.vertical, 4)

                    Button("Probe hören") {
                        Vorlesen.geteilt.umschalten(text: "Hallo Lorenz, so klinge ich.")
                    }
                }

                Section {
                    Toggle("Hintergrund-Hinweise", isOn: $einstellungen.hintergrundHinweise)
                    Toggle("Zähler am App-Symbol", isOn: $einstellungen.zaehlerAmSymbol)
                } header: {
                    Text("Benachrichtigungen")
                } footer: {
                    Text("Ohne Push-Dienst schaut die App ab und zu im Hintergrund selbst nach. Wann, entscheidet iOS – Hinweise können deshalb verspätet kommen.")
                }

                Section("Info") {
                    LabeledContent("App-Version", value: appVersion)
                    LabeledContent("Server-Version", value: serverVersion)
                }
            }
            .navigationTitle("Einstellungen")
            .task {
                await versionHolen()
            }
            .onChange(of: einstellungen.zaehlerAmSymbol) { _, _ in
                Task {
                    let zahl: Int = UserDefaults.standard.integer(forKey: "zuletztBekanntUngelesen")
                    await Benachrichtigungen.geteilt.zaehlerSetzen(zahl)
                }
            }
        }
    }

    private var appVersion: String {
        let info: [String: Any] = Bundle.main.infoDictionary ?? [:]
        let version: String = info["CFBundleShortVersionString"] as? String ?? "?"
        let build: String = info["CFBundleVersion"] as? String ?? "?"
        return version + " (" + build + ")"
    }

    private func testen() async {
        test = TestErgebnis.laeuft
        test = await verbindungPruefen()

        if case .ok(let version) = test {
            serverVersion = version
        }
    }

    private func versionHolen() async {
        do {
            let gesundheit: Gesundheit = try await ApiClient.geteilt.holen("/health")
            serverVersion = gesundheit.version ?? "?"
        } catch {
            serverVersion = "nicht erreichbar"
        }
    }
}

// Eine Reihe runder Farbpunkte, der gewählte hat ein Häkchen
struct AkzentAuswahl: View {
    @Binding var auswahl: Akzentfarbe

    var body: some View {
        HStack(spacing: 0) {
            ForEach(Akzentfarbe.allCases) { farbe in
                Button {
                    withAnimation(.easeInOut(duration: 0.2)) {
                        auswahl = farbe
                    }
                } label: {
                    ZStack {
                        Circle()
                            .fill(farbe.farbe)
                            .frame(width: 30, height: 30)
                        if auswahl == farbe {
                            Image(systemName: "checkmark")
                                .font(.footnote.weight(.bold))
                                .foregroundStyle(.white)
                        }
                    }
                    .frame(maxWidth: .infinity, minHeight: 44)
                }
                .buttonStyle(.plain)
                .accessibilityLabel(farbe.name)
                .accessibilityAddTraits(auswahl == farbe ? .isSelected : [])
            }
        }
    }
}
