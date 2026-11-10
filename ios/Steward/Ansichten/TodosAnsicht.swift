import SwiftUI

// Aufgabenliste im Stil von Apples "Erinnerungen"
// Kreis antippen = erledigt, wischen = löschen, "+" = neue Aufgabe direkt in der Liste tippen

struct TodosAnsicht: View {
    @State private var todos: [Todo] = []
    @State private var laedt: Bool = true
    @State private var fehlertext: String = ""
    @State private var zeigeErledigte: Bool = false
    @State private var neuAnlegen: Bool = false
    @State private var neuerText: String = ""
    @FocusState private var neuFokus: Bool

    private var sichtbare: [Todo] {
        var gefiltert: [Todo] = []
        for todo in todos {
            if zeigeErledigte || todo.istErledigt == false {
                gefiltert.append(todo)
            }
        }
        return gefiltert
    }

    var body: some View {
        NavigationStack {
            List {
                if neuAnlegen {
                    HStack(spacing: 12) {
                        Image(systemName: "circle")
                            .font(.title2)
                            .foregroundStyle(.secondary)
                        TextField("Neue Aufgabe", text: $neuerText)
                            .focused($neuFokus)
                            .submitLabel(.done)
                            .onSubmit {
                                Task {
                                    await anlegen()
                                }
                            }
                    }
                }

                ForEach(sichtbare) { todo in
                    TodoZeile(todo: todo) {
                        Task {
                            await umschalten(todo)
                        }
                    }
                }
                .onDelete { stellen in
                    loeschen(stellen)
                }

                if todos.isEmpty == false {
                    Section {
                        Button(zeigeErledigte ? "Erledigte ausblenden" : "Erledigte anzeigen") {
                            withAnimation {
                                zeigeErledigte.toggle()
                            }
                        }
                    }
                }
            }
            .listStyle(.insetGrouped)
            .navigationTitle("Todos")
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button {
                        neuAnlegen = true
                        neuFokus = true
                    } label: {
                        Image(systemName: "plus")
                    }
                    .accessibilityLabel("Neue Aufgabe")
                }
            }
            .overlay {
                leerOderFehler
            }
            .refreshable {
                await laden()
            }
            .task {
                await laden()
            }
            .onChange(of: neuFokus) { _, aktiv in
                // Tippt man woanders hin, verschwindet die leere Eingabezeile wieder
                if aktiv == false && neuerText.isEmpty {
                    neuAnlegen = false
                }
            }
        }
    }

    @ViewBuilder
    private var leerOderFehler: some View {
        if sichtbare.isEmpty && neuAnlegen == false {
            if laedt {
                ProgressView()
            } else if fehlertext.isEmpty == false {
                ContentUnavailableView {
                    Label("Keine Verbindung", systemImage: "wifi.slash")
                } description: {
                    Text(fehlertext)
                }
            } else {
                ContentUnavailableView("Keine offenen Aufgaben", systemImage: "checkmark.circle", description: Text("Tippe auf + oder sag Steward, was zu tun ist."))
            }
        }
    }

    private func laden() async {
        laedt = true
        do {
            todos = try await ApiClient.geteilt.holen("/tasks?nur_offen=false")
            fehlertext = ""
        } catch {
            fehlertext = error.localizedDescription
        }
        laedt = false
    }

    private func anlegen() async {
        let text: String = neuerText.trimmingCharacters(in: .whitespacesAndNewlines)
        neuerText = ""
        neuAnlegen = false

        if text.isEmpty {
            return
        }

        do {
            let neu: Todo = try await ApiClient.geteilt.schicken("/tasks", koerper: TodoAnfrage(inhalt: text, faelligAm: nil, quelle: "app"))
            todos.insert(neu, at: 0)
        } catch {
            fehlertext = error.localizedDescription
        }
    }

    private func umschalten(_ todo: Todo) async {
        let neuerWert: Bool = todo.istErledigt == false

        // Sofort in der Liste zeigen, dann dem Server Bescheid geben
        for index in 0..<todos.count {
            if todos[index].id == todo.id {
                withAnimation {
                    todos[index].erledigt = neuerWert ? 1 : 0
                }
            }
        }

        do {
            var aenderung: TodoAenderung = TodoAenderung()
            aenderung.erledigt = neuerWert
            let _: Todo = try await ApiClient.geteilt.schicken("/tasks/" + String(todo.id), methode: "PATCH", koerper: aenderung)
        } catch {
            fehlertext = error.localizedDescription
            await laden()
        }
    }

    private func loeschen(_ stellen: IndexSet) {
        var zuLoeschen: [Todo] = []
        for stelle in stellen {
            zuLoeschen.append(sichtbare[stelle])
        }

        for todo in zuLoeschen {
            var neueListe: [Todo] = []
            for vorhanden in todos {
                if vorhanden.id != todo.id {
                    neueListe.append(vorhanden)
                }
            }
            todos = neueListe

            Task {
                do {
                    try await ApiClient.geteilt.loeschen("/tasks/" + String(todo.id))
                } catch {
                    fehlertext = error.localizedDescription
                    await laden()
                }
            }
        }
    }
}

struct TodoZeile: View {
    let todo: Todo
    let abhaken: () -> Void

    var body: some View {
        HStack(spacing: 12) {
            Button {
                abhaken()
            } label: {
                if todo.istErledigt {
                    Image(systemName: "checkmark.circle.fill")
                        .font(.title2)
                        .foregroundStyle(.tint)
                } else {
                    Image(systemName: "circle")
                        .font(.title2)
                        .foregroundStyle(.secondary)
                }
            }
            .buttonStyle(.plain)
            .accessibilityLabel(todo.istErledigt ? "Als offen markieren" : "Als erledigt markieren")

            VStack(alignment: .leading, spacing: 2) {
                Text(todo.inhalt)
                    .strikethrough(todo.istErledigt)
                    .foregroundStyle(todo.istErledigt ? Color.secondary : Color.primary)

                if let faellig = Zeitformat.datum(aus: todo.faelligAm) {
                    Text(Zeitformat.mitTag(faellig))
                        .font(.subheadline)
                        .foregroundStyle(faellig < Date() && todo.istErledigt == false ? Color.red : Color.secondary)
                }
            }
        }
        .padding(.vertical, 2)
    }
}
