import SwiftUI

// Die Tab-Leiste unten mit den fünf Bereichen
// Jeder Tab hat seinen eigenen Navigationsstapel, damit "Zurück" pro Tab funktioniert

struct HauptAnsicht: View {
    @EnvironmentObject var daten: AppDaten

    var body: some View {
        TabView(selection: $daten.ausgewaehlterBereich) {
            ModuleAnsicht()
                .tabItem {
                    Label("Module", systemImage: "square.grid.2x2")
                }
                .tag(Bereich.module)

            TodosAnsicht()
                .tabItem {
                    Label("Todos", systemImage: "checklist")
                }
                .tag(Bereich.todos)

            StewardAnsicht()
                .tabItem {
                    Label("Steward", systemImage: "bubble.left.and.text.bubble.right")
                }
                .tag(Bereich.steward)

            KostenAnsicht()
                .tabItem {
                    Label("Kosten", systemImage: "chart.bar")
                }
                .tag(Bereich.kosten)

            EinstellungenAnsicht()
                .tabItem {
                    Label("Einstellungen", systemImage: "gearshape")
                }
                .tag(Bereich.einstellungen)
        }
    }
}
