import SwiftUI

@main
struct StewardApp: App {
    @StateObject private var einstellungen = Einstellungen.geteilt

    var body: some Scene {
        WindowGroup {
            HauptAnsicht()
                .environmentObject(einstellungen)
                .task {
                    _ = await Benachrichtigungen.geteilt.erlaubnisHolen()
                }
        }
    }
}
