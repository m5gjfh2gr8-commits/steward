import SwiftUI

// Startseite: alle Module mit Zustand und Ungelesen-Zähler
// Module mit Fehler stehen oben, Antippen öffnet die Berichte des Moduls

struct ModuleAnsicht: View {
    @EnvironmentObject var daten: AppDaten
    @Environment(\.scenePhase) private var phase

    var body: some View {
        NavigationStack {
            List {
                Section {
                    ForEach(daten.sortierteModule) { modul in
                        NavigationLink(value: ModulZiel(name: modul.name)) {
                            ModulZeile(modul: modul)
                        }
                    }
                } header: {
                    Text(daten.statuszeile)
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                        .textCase(nil)
                } footer: {
                    if let zeit = daten.zuletztAktualisiert {
                        Text("Aktualisiert um " + Zeitformat.uhrzeit(zeit))
                    }
                }
            }
            .listStyle(.insetGrouped)
            .navigationTitle("Steward")
            .navigationDestination(for: ModulZiel.self) { ziel in
                ModulDetailAnsicht(name: ziel.name)
            }
            .refreshable {
                await daten.moduleLaden()
            }
            .overlay {
                leerOderLaden
            }
            .safeAreaInset(edge: .top) {
                if daten.offline {
                    OfflineHinweis()
                }
            }
        }
        .task {
            await daten.moduleLaden()
        }
        .onChange(of: phase) { _, neuePhase in
            // Beim Zurückkommen in die App gleich frisch holen
            if neuePhase == .active {
                Task {
                    await daten.moduleLaden()
                }
            }
        }
    }

    @ViewBuilder
    private var leerOderLaden: some View {
        if daten.module.isEmpty {
            if daten.laedt {
                ProgressView()
            } else if daten.fehlertext.isEmpty == false {
                ContentUnavailableView {
                    Label("Keine Verbindung", systemImage: "wifi.slash")
                } description: {
                    Text(daten.fehlertext)
                } actions: {
                    Button("Erneut versuchen") {
                        Task {
                            await daten.moduleLaden()
                        }
                    }
                }
            } else {
                ContentUnavailableView("Keine Module", systemImage: "square.grid.2x2", description: Text("Am Server ist noch kein Modul eingetragen."))
            }
        }
    }
}

struct ModulZeile: View {
    let modul: ModulZustand

    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: modul.symbolName)
                .font(.title3)
                .foregroundStyle(.tint)
                .frame(width: 30)

            VStack(alignment: .leading, spacing: 2) {
                Text(modul.anzeigename)
                Text(modul.unterzeile)
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
                    .lineLimit(1)
            }

            Spacer(minLength: 8)

            if modul.hatFehler {
                Image(systemName: "exclamationmark.triangle.fill")
                    .foregroundStyle(.red)
                    .accessibilityLabel("Fehler")
            } else if modul.ungelesen > 0 {
                UngelesenZaehler(anzahl: modul.ungelesen)
            }
        }
        .padding(.vertical, 4)
    }
}
