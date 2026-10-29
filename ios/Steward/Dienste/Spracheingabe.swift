import AVFoundation
import Foundation
import Speech

// Diktieren statt tippen, laeuft ueber Apples eigenes Speech-Framework
// Kostet nichts und braucht keinen externen Dienst

class Spracheingabe: ObservableObject {
    @Published var laeuft = false
    @Published var erkannterText = ""
    @Published var fehlertext = ""

    private let erkenner = SFSpeechRecognizer(locale: Locale(identifier: "de-AT"))
    private let motor = AVAudioEngine()
    private var anfrage: SFSpeechAudioBufferRecognitionRequest?
    private var aufgabe: SFSpeechRecognitionTask?

    func erlaubnisHolen(fertig: @escaping (Bool) -> Void) {
        SFSpeechRecognizer.requestAuthorization { status in
            DispatchQueue.main.async {
                if status == .authorized {
                    fertig(true)
                } else {
                    fertig(false)
                }
            }
        }
    }

    func starten() {
        if laeuft {
            return
        }

        erlaubnisHolen { erlaubt in
            if !erlaubt {
                self.fehlertext = "Keine Erlaubnis fuer Spracherkennung"
                return
            }
            self.aufnahmeStarten()
        }
    }

    private func aufnahmeStarten() {
        erkannterText = ""
        fehlertext = ""

        guard let erkenner = erkenner else {
            fehlertext = "Spracherkennung auf Deutsch nicht verfuegbar"
            return
        }

        if !erkenner.isAvailable {
            fehlertext = "Spracherkennung gerade nicht verfuegbar"
            return
        }

        do {
            let sitzung = AVAudioSession.sharedInstance()
            try sitzung.setCategory(.record, mode: .measurement, options: .duckOthers)
            try sitzung.setActive(true, options: .notifyOthersOnDeactivation)
        } catch {
            fehlertext = "Mikrofon laesst sich nicht oeffnen"
            return
        }

        let neueAnfrage = SFSpeechAudioBufferRecognitionRequest()
        neueAnfrage.shouldReportPartialResults = true
        anfrage = neueAnfrage

        let eingang = motor.inputNode
        let format = eingang.outputFormat(forBus: 0)

        eingang.installTap(onBus: 0, bufferSize: 1024, format: format) { puffer, zeit in
            neueAnfrage.append(puffer)
        }

        motor.prepare()

        do {
            try motor.start()
        } catch {
            fehlertext = "Aufnahme startet nicht"
            return
        }

        laeuft = true

        aufgabe = erkenner.recognitionTask(with: neueAnfrage) { ergebnis, fehler in
            if let ergebnis = ergebnis {
                DispatchQueue.main.async {
                    self.erkannterText = ergebnis.bestTranscription.formattedString
                }
            }

            if fehler != nil {
                DispatchQueue.main.async {
                    self.stoppen()
                }
            }
        }
    }

    func stoppen() {
        if motor.isRunning {
            motor.stop()
            motor.inputNode.removeTap(onBus: 0)
        }

        anfrage?.endAudio()
        aufgabe?.cancel()
        anfrage = nil
        aufgabe = nil
        laeuft = false
    }
}
