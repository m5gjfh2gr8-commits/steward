import SwiftUI

// Erster Start: Server-Adresse und Steward-Key eingeben, Verbindung testen, fertig
// "Fertig" geht erst, wenn der Test geklappt hat - so landet man nie in einer leeren App

struct ErsteinrichtungAnsicht: View {
    @EnvironmentObject var einstellungen: Einstellungen

    @State private var test: TestErgebnis = TestErgebnis.keins

    private var testOk: Bool {
        if case .ok = test {
            return true
        }
        return false
    }

    var body: some View {
        VStack(spacing: 0) {
            Form {
                Section {
                    VStack(spacing: 12) {
                        Image(systemName: "bubble.left.and.text.bubble.right")
                            .font(.system(size: 40))
                            .foregroundStyle(.tint)
                            .frame(width: 80, height: 80)
                            .background(Color(.secondarySystemGroupedBackground), in: RoundedRectangle(cornerRadius: 18, style: .continuous))

                        Text("Steward einrichten")
                            .font(.title.bold())

                        Text("Gib die Adresse deines Servers und deinen Steward-Key ein.")
                            .foregroundStyle(.secondary)
                            .multilineTextAlignment(.center)
                    }
                    .frame(maxWidth: .infinity)
                    .padding(.top, 40)
                    .listRowBackground(Color.clear)
                }

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
                }

                Section {
                    Button("Verbindung testen") {
                        Task {
                            test = TestErgebnis.laeuft
                            test = await verbindungPruefen()
                        }
                    }
                } footer: {
                    TestErgebnisAnzeige(ergebnis: test)
                }
            }

            Button {
                einstellungen.einrichtungAbgeschlossen = true
            } label: {
                Text("Fertig")
                    .font(.headline)
                    .frame(maxWidth: .infinity, minHeight: 52)
            }
            .buttonStyle(.borderedProminent)
            .buttonBorderShape(.capsule)
            .disabled(testOk == false)
            .padding(.horizontal, 16)
            .padding(.bottom, 16)
            .background(Color(.systemGroupedBackground))
        }
        .background(Color(.systemGroupedBackground))
        .onChange(of: einstellungen.serverAdresse) { _, _ in
            test = TestErgebnis.keins
        }
        .onChange(of: einstellungen.apiKey) { _, _ in
            test = TestErgebnis.keins
        }
    }
}
