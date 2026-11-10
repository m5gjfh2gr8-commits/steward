import AVFoundation
import Foundation
import Speech

// Diktieren statt tippen, läuft über Apples eigenes Speech-Framework
// Kostet nichts und braucht keinen externen Dienst
// "pegel" (0 bis 1) treibt die kleine Pegel-Animation in der Eingabeleiste

class Spracheingabe: ObservableObject {
    @Published var laeuft: Bool = false
    @Published var erkannterText: String = ""
    @Published var fehlertext: String = ""
    @Published var pegel: Double = 0.0

    private let erkenner: SFSpeechRecognizer? = SFSpeechRecognizer(locale: Locale(identifier: "de-AT"))
    private let motor: AVAudioEngine = AVAudioEngine()
    private var anfrage: SFSpeechAudioBufferRecognitionRequest?
    private var aufgabe: SFSpeechRecognitionTask?

    func starten() {
        if laeuft {
            return
        }

        SFSpeechRecognizer.requestAuthorization { status in
            DispatchQueue.main.async {
                if status != .authorized {
                    self.fehlertext = "Keine Erlaubnis für die Spracherkennung"
                    return
                }

                AVAudioApplication.requestRecordPermission { erlaubt in
                    DispatchQueue.main.async {
                        if erlaubt == false {
                            self.fehlertext = "Keine Erlaubnis für das Mikrofon"
                            return
                        }
                        self.aufnahmeStarten()
                    }
                }
            }
        }
    }

    private func aufnahmeStarten() {
        erkannterText = ""
        fehlertext = ""

        guard let erkenner = erkenner else {
            fehlertext = "Spracherkennung auf Deutsch nicht verfügbar"
            return
        }

        if erkenner.isAvailable == false {
            fehlertext = "Spracherkennung gerade nicht verfügbar"
            return
        }

        do {
            let sitzung: AVAudioSession = AVAudioSession.sharedInstance()
            try sitzung.setCategory(.record, mode: .measurement, options: .duckOthers)
            try sitzung.setActive(true, options: .notifyOthersOnDeactivation)
        } catch {
            fehlertext = "Mikrofon lässt sich nicht öffnen"
            return
        }

        let neueAnfrage: SFSpeechAudioBufferRecognitionRequest = SFSpeechAudioBufferRecognitionRequest()
        neueAnfrage.shouldReportPartialResults = true
        anfrage = neueAnfrage

        let eingang: AVAudioInputNode = motor.inputNode
        let format: AVAudioFormat = eingang.outputFormat(forBus: 0)

        eingang.installTap(onBus: 0, bufferSize: 1024, format: format) { puffer, _ in
            neueAnfrage.append(puffer)

            let neuerPegel: Double = Spracheingabe.pegelBerechnen(puffer: puffer)
            DispatchQueue.main.async {
                self.pegel = neuerPegel
            }
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
                let text: String = ergebnis.bestTranscription.formattedString
                DispatchQueue.main.async {
                    self.erkannterText = text
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
        pegel = 0.0
    }

    // Lautstärke eines Audio-Stücks als Zahl zwischen 0 und 1 (Effektivwert, verstärkt)
    private static func pegelBerechnen(puffer: AVAudioPCMBuffer) -> Double {
        guard let kanaele = puffer.floatChannelData else {
            return 0.0
        }

        let werte: UnsafeMutablePointer<Float> = kanaele[0]
        let anzahl: Int = Int(puffer.frameLength)
        if anzahl == 0 {
            return 0.0
        }

        var summe: Float = 0.0
        var index: Int = 0
        while index < anzahl {
            summe = summe + werte[index] * werte[index]
            index = index + 1
        }

        let effektivwert: Float = (summe / Float(anzahl)).squareRoot()
        let verstaerkt: Double = Double(effektivwert) * 12.0

        if verstaerkt > 1.0 {
            return 1.0
        }
        return verstaerkt
    }
}
