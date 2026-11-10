import SwiftUI

// Liste der offenen Aufgaben und Termine

struct TodoAnsicht: View {
    @EnvironmentObject var einstellungen: Einstellungen

    @State private var todos: [Todo] = []
    @State private var nurOffene = true
    @State private var laedt = false
    @State private var fehlertext = ""
    @State private var neuerText = ""
    @State private var zeigeNeuesTodo = false

    var body: some View {
        NavigationStack {
            Group {
                if !einstellungen.istEingerichtet {
                    NichtEingerichtetHinweis()
                } else {
                    List {
                        if !fehlertext.isEmpty {
                            FehlerKarte(text: fehlertext)
                        }

                        if todos.isEmpty && !laedt {
                            Text("Nichts offen")
                                .foregroundStyle(.secondary)
                        }

                        ForEach(todos) { todo in
                            TodoZeile(todo: todo, abhaken: {
                                Task { await abhaken(todo) }
                            })
                        }
                        .onDelete { stellen in
                            Task { await loeschen(stellen) }
                        }
                    }
                    .refreshable {
                        await laden()
                    }
                }
            }
            .navigationTitle("Aufgaben")
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    Picker("Anzeige", selection: $nurOffene) {
                        Text("Offen").tag(true)
                        Text("Alle").tag(false)
                    }
                    .pickerStyle(.segmented)
                    .onChange(of: nurOffene) {
                        Task { await laden() }
                    }
                }

                ToolbarItem(placement: .topBarTrailing) {
                    Button {
                        zeigeNeuesTodo = true
                    } label: {
                        Image(systemName: "plus")
                    }
                }
            }
            .sheet(isPresented: $zeigeNeuesTodo) {
                NeuesTodoAnsicht(fertig: {
                    Task { await laden() }
                })
            }
            .task {
                await laden()
            }
        }
    }

    private func laden() async {
        laedt = true
        fehlertext = ""

        var pfad = "/tasks"
        if !nurOffene {
            pfad = "/tasks?nur_offen=false"
        }

        do {
            todos = try await ApiClient.geteilt.holen(pfad)
        } catch {
            fehlertext = error.localizedDescription
        }

        laedt = false
    }

    private func abhaken(_ todo: Todo) async {
        do {
            var aenderung = TodoAenderung()
            aenderung.erledigt = !todo.istErledigt

            try await ApiClient.geteilt.schickenOhneAntwort("/tasks/\(todo.id)", methode: "PATCH", koerper: aenderung)
            Benachrichtigungen.geteilt.erinnerungLoeschen(kennung: "todo-\(todo.id)")
            await laden()
        } catch {
            fehlertext = error.localizedDescription
        }
    }

    private func loeschen(_ stellen: IndexSet) async {
        for stelle in stellen {
            let todo = todos[stelle]
            do {
                try await ApiClient.geteilt.loeschen("/tasks/\(todo.id)")
                Benachrichtigungen.geteilt.erinnerungLoeschen(kennung: "todo-\(todo.id)")
            } catch {
                fehlertext = error.localizedDescription
            }
        }
        await laden()
    }
}

struct TodoZeile: View {
    let todo: Todo
    let abhaken: () -> Void

    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            Button(action: abhaken) {
                if todo.istErledigt {
                    Image(systemName: "checkmark.circle.fill")
                        .foregroundStyle(.green)
                } else {
                    Image(systemName: "circle")
                        .foregroundStyle(.secondary)
                }
            }
            .buttonStyle(.plain)

            VStack(alignment: .leading, spacing: 2) {
                Text(todo.inhalt)
                    .strikethrough(todo.istErledigt)

                if todo.faelligAm != nil {
                    Text(datumUndZeitAusText(todo.faelligAm))
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }
        }
    }
}

// Neue Aufgabe per Freitext - das Backend zerlegt den Satz, die App plant daraus die Erinnerung
struct NeuesTodoAnsicht: View {
    let fertig: () -> Void

    @Environment(\.dismiss) private var schliessen
    @State private var text = ""
    @State private var laedt = false
    @State private var fehlertext = ""

    var body: some View {
        NavigationStack {
            Form {
                Section {
                    TextField("z.B. morgen um 3 zum Zahnarzt", text: $text, axis: .vertical)
                        .lineLimit(1...4)
                } footer: {
                    Text("Datum und Uhrzeit werden aus dem Satz erkannt, die Erinnerung stellt sich von selbst.")
                }

                if !fehlertext.isEmpty {
                    FehlerKarte(text: fehlertext)
                }
            }
            .navigationTitle("Neue Aufgabe")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Abbrechen") {
                        schliessen()
                    }
                }

                ToolbarItem(placement: .confirmationAction) {
                    Button("Anlegen") {
                        Task { await anlegen() }
                    }
                    .disabled(text.trimmingCharacters(in: .whitespaces).isEmpty || laedt)
                }
            }
        }
    }

    private func anlegen() async {
        laedt = true
        fehlertext = ""

        do {
            let zerlegt: ZerlegterText = try await ApiClient.geteilt.schicken("/tasks/parse", koerper: FreitextAnfrage(text: text))

            let angelegt: Todo = try await ApiClient.geteilt.schicken(
                "/tasks",
                koerper: TodoAnfrage(inhalt: zerlegt.inhalt, faelligAm: zerlegt.faelligAm, quelle: "text")
            )

            if let zeitpunkt = Benachrichtigungen.geteilt.zeitpunktAusText(angelegt.faelligAm) {
                Benachrichtigungen.geteilt.terminErinnerungPlanen(
                    kennung: "todo-\(angelegt.id)",
                    text: angelegt.inhalt,
                    zeitpunkt: zeitpunkt
                )
            }

            fertig()
            schliessen()
        } catch {
            fehlertext = error.localizedDescription
        }

        laedt = false
    }
}
