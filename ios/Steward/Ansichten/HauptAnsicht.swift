import SwiftUI

struct HauptAnsicht: View {
    @EnvironmentObject var einstellungen: Einstellungen

    var body: some View {
        TabView {
            DashboardAnsicht()
                .tabItem {
                    Label("Heute", systemImage: "sun.horizon")
                }

            ChatAnsicht()
                .tabItem {
                    Label("Eingabe", systemImage: "text.bubble")
                }

            TodoAnsicht()
                .tabItem {
                    Label("Aufgaben", systemImage: "checklist")
                }

            ErnaehrungAnsicht()
                .tabItem {
                    Label("Ernaehrung", systemImage: "fork.knife")
                }

            EinstellungenAnsicht()
                .tabItem {
                    Label("Einstellungen", systemImage: "gearshape")
                }
        }
    }
}
