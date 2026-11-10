import BackgroundTasks
import SwiftUI

// Einstiegspunkt der App
// Beim ersten Start kommt die Einrichtung, danach die Tab-Leiste mit den fünf Bereichen

@main
struct StewardApp: App {
    @StateObject private var einstellungen: Einstellungen = Einstellungen.geteilt
    @StateObject private var daten: AppDaten = AppDaten()
    @StateObject private var chat: ChatVerlauf = ChatVerlauf()
    @Environment(\.scenePhase) private var phase

    var body: some Scene {
        WindowGroup {
            Group {
                if einstellungen.einrichtungAbgeschlossen {
                    HauptAnsicht()
                } else {
                    ErsteinrichtungAnsicht()
                }
            }
            .environmentObject(einstellungen)
            .environmentObject(daten)
            .environmentObject(chat)
            .tint(einstellungen.akzent.farbe)
            .task {
                _ = await Benachrichtigungen.geteilt.erlaubnisHolen()
            }
        }
        .onChange(of: phase) { _, neuePhase in
            // Sobald die App in den Hintergrund geht, den nächsten Hintergrund-Blick anmelden
            if neuePhase == .background {
                Hintergrund.naechstenBlickPlanen()
            }
        }
        .backgroundTask(.appRefresh(Hintergrund.kennung)) {
            await Hintergrund.ausfuehren()
        }
    }
}
