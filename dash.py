import json
from pathlib import Path

from flask import Flask, render_template, request, jsonify

# INHALT #
# - Entitätenschicht
# - Darstellungsschicht
# - Orchestrierungsschicht
# - Persistenzschicht
# - App-Setup



######################################################################################################################
# ENTITÄTENSCHICHT
######################################################################################################################

class Studiengang:
    def __init__(self, module):
        self.module = module

    def kurs_auslesen(self, mid):       # Für das Auslesen einzelner Kurse mit ihrer ID "mid"
        for m in self.module:
            if m.id == mid:
                return m
        return None


    def metrics_mean(self):             # Gibt den Notendurchschnitt aus
        noten = []
        for m in self.module:
            if m.pruefungsleistung is not None and m.pruefungsleistung.note > 0:
                # Wichtig, weil durch Eingabe von 0 der Kurs bestanden ist, aber nicht für den Durchschnitt zählt (Anerkennung).
                # Credits müssen addiert werden, aber der Durchschnitt würde verfälscht werden, wenn 0 mit in mean einfließen würde.
                noten.append(m.pruefungsleistung.note)
        if noten:
            return round(sum(noten) / len(noten), 2)
        return None

    def metrics_ects(self):         # Berechnet das Paar bestandene ECTS und nötige ects_max
        ects_max = 0
        ects = 0

        for m in self.module:
            ects_max += m.ects
            # Summe ALLER Modulcredits

            if m.kursstatus_bestanden():
                ects += m.ects
                # Summe BESTANDENER Modulcredits

        return ects, ects_max


class Semester:
    def __init__(self, anzahl):
        self.anzahl = anzahl   # anzahl ist eher als "Semesternummer" zu verstehen - also quasi die Semester-ID


class Kurs:
    def __init__(self, id, titel, ects, semester, belegt=False, pruefungsleistung=None):
        self.id = id
        self.titel = titel
        self.ects = ects
        self.semester = semester
        self.belegt = belegt
        self.pruefungsleistung = pruefungsleistung

    def kursstatus_belegt(self):                # Wird von Dashboard.build_dashboard_datapackage() genutzt
        return self.belegt

    def kursstatus_bestanden(self):            # Zählt als bestanden, wenn eine Prüfungsleistung existiert und diese <= 4 ist
        if self.pruefungsleistung is None:
            return False

        return self.pruefungsleistung.note is not None and self.pruefungsleistung.note <= 4.0


class Pruefungsleistung:
    def __init__(self, note=None):
        self.note = note


######################################################################################################################
# DARSTELLUNGSSCHICHT (API)
######################################################################################################################

# API-Klasse verwaltet hier die ganzen Routen für die Flask-App

class API:
    def __init__(self, dashboard, template_folder="."):
        self.dashboard = dashboard
        self.app = Flask(__name__, template_folder=template_folder)

        self.app.add_url_rule("/", view_func=self.get_index_route, methods=["GET"])
        self.app.add_url_rule(
            "/api/module/<int:mid>",
            view_func=self.get_module_route,
            methods=["GET"],
        )
        self.app.add_url_rule(
            "/api/module/<int:mid>",
            view_func=self.post_module_route,
            methods=["POST"],
        )

    def get_index_route(self):
        data = self.dashboard.build_dashboard_datapackage()
        return render_template("index.html", grid=data["grid"], metrics=data["metrics"])

    def get_module_route(self, mid):
        m = self.dashboard.module_get(mid)
        if not m:
            return jsonify({"error": "not found"}), 404

        note_val = None
        if m.pruefungsleistung is not None:
            note_val = m.pruefungsleistung.note

        return jsonify(
            {
                "id": m.id,
                "titel": m.titel,
                "ects": m.ects,
                "semester": m.semester,
                "belegt": m.belegt,
                "note": note_val,
            }
        )

    def post_module_route(self, mid):
        data = request.get_json(force=True) or {}

        try:
            m = self.dashboard.module_update(mid, data)
        except Exception as e:
            return jsonify({"error": str(e)}), 400

        if m is None:
            return jsonify({"error": "not found"}), 404

        n = None
        if m.pruefungsleistung is not None:
            n = m.pruefungsleistung.note

        if n is not None:
            status = "gruen" if m.kursstatus_bestanden() else "rot"
            label = f"{n:.1f}"
        elif m.kursstatus_belegt():
            status, label = "gelb", "?"
        else:
            status, label = "grau", ""

        ects, ects_max = self.dashboard.studiengang.metrics_ects()

        metrics = {"ECTS": ects, "MEAN": self.dashboard.studiengang.metrics_mean(), "ECTS_MAX": ects_max}

        return jsonify(
            {
                "id": m.id,
                "status": status,
                "label": label,
                "titel": m.titel,
                "metrics": metrics,
            }
        )


######################################################################################################################
# ORCHESTRIERUNGSSCHICHT (Dashboard)
######################################################################################################################

class Dashboard:
    def __init__(self, speicher, eingabe):
        self.speicher = speicher
        self.eingabe = eingabe
        self.studiengang = self.speicher.lesen()

    def build_dashboard_datapackage(self):
        # Stellt ein Datenpaket für das Frontend zusammen:
        # grid => Semester-Modul-Kachel-Darstellung
        # metrics => Darstellung Kennzahlen im oberen Bereich

        grid = []
        for sem in range(1, 7):     # Filterung der Module - Welches Modul gehört in welches Semester?
            module_in_semester = [m for m in self.studiengang.module if m.semester == sem]
            row = []
            for m in sorted(module_in_semester, key=lambda modul: modul.id):  # lambda gibt Sortierschlüssel aus

                if m.pruefungsleistung is not None:
                    n = m.pruefungsleistung.note
                else:
                    n = None

                # Gleiche Statuslogik wie bei API wegen Konsistenz - könnte in zukünftigen Iterationen noch gekapselt werden.
                if n is not None:
                    status = "gruen" if m.kursstatus_bestanden() else "rot"
                    label = f"{n:.1f}"
                elif m.kursstatus_belegt():
                    status, label = "gelb", "?"
                else:
                    status, label = "grau", ""

                row.append(
                    {
                        "id": m.id,
                        "titel": m.titel,
                        "ects": m.ects,
                        "status": status,
                        "label": label,
                    }
                )
            grid.append({"sem": sem, "module": row})
            # Jede grid-Zeile repräsentiert dann genau ein Semester

        ects, ects_max = self.studiengang.metrics_ects()
        metrics = {"ECTS": ects, "MEAN": self.studiengang.metrics_mean(), "ECTS_MAX": ects_max}

        return {"grid": grid, "metrics": metrics}


    def module_get(self, mid):
        return self.studiengang.kurs_auslesen(mid)

    def module_update(self, mid, neue_daten):
        m = self.studiengang.kurs_auslesen(mid)
        if not m:
            return None

        if "titel" in neue_daten:
            m.titel = self.eingabe.valid_kursname(neue_daten["titel"])

        if "belegt" in neue_daten:
            m.belegt = bool(neue_daten["belegt"])

        if "note" in neue_daten:
            n = self.eingabe.valid_note(neue_daten["note"])
            if n is None:  # None "löscht" Prüfungsleistung also über Garbage Collector (keine Referenz mehr)
                m.pruefungsleistung = None
            else:
                if m.pruefungsleistung is None:
                    m.pruefungsleistung = Pruefungsleistung(n)
                else:
                    m.pruefungsleistung.note = n

        self.speicher.speichern(self.studiengang)
        return m



class Eingabe:  # Einfache Validierungschecks für Titel und Note durch Nutzereingabe
    @staticmethod  # StaticMethod als wichtiger Aspekt. Muss nicht über Instanz aufgerufen werden.
    def valid_kursname(titel):
        try:
            titel_clean = titel.strip()
        except AttributeError:
            titel_clean = ""

        if titel_clean == "":
            raise ValueError("Titel darf nicht leer sein!")
        return titel_clean


    @staticmethod
    def valid_note(value):
        if value in (None, "", "null"):
            return None

        n = str(value).strip().replace(",", ".")
        try:
            note_clean = float(n)
        except ValueError:
            raise ValueError("Diese Note ist nicht möglich!")

        if not (0.0 <= note_clean <= 6.0):
            raise ValueError("Wer gibt denn solche Noten? (0.0–6.0 möglich)")

        return note_clean


######################################################################################################################
# PERSISTENZSCHICHT
######################################################################################################################

class Speicher:  # Speichert den Studiengang (Objekt) wieder als JSON-Struktur
    def __init__(self, path):  # beim Lesen umgekehrt (baut Objekt aus JSON-Struktur)
        self.path = path.absolute()

        if not self.path.exists():  # Wenn noch keine data.json existiert, wird sie jetzt erzeugt
            factory = KursFactory()
            module = factory.kurse_erzeugen()
            sg = Studiengang(module=module)
            self.speichern(sg)

    def lesen(self):
        # Deserialisierung -> JSON wird zu Python-Objekt
        with self.path.open("r", encoding="utf-8") as f:
            raw = json.load(f)

        sg_raw = raw.get("studiengang", {})
        module_raw = sg_raw.get("module", [])

        module = []
        for m in module_raw:
            note_json = m.get("note")
            pl = None
            if note_json is not None:
                pl = Pruefungsleistung(float(note_json))

            kurs = Kurs(
                id=int(m["id"]),
                titel=str(m["titel"]),
                ects=int(m["ects"]),
                semester=int(m["semester"]),
                belegt=bool(m["belegt"]),
                pruefungsleistung=pl,
            )
            module.append(kurs)

        return Studiengang(module=module)

    def speichern(self, sg):
        # Serialisierung -> Python-Objekt wird zu JSON
        data_module = []
        for m in sg.module:
            note_val = None
            if m.pruefungsleistung is not None:
                note_val = m.pruefungsleistung.note
            data_module.append(
                {
                    "id": m.id,
                    "titel": m.titel,
                    "ects": m.ects,
                    "semester": m.semester,
                    "belegt": m.belegt,
                    "note": note_val,
                }
            )

        data = {"studiengang": {"module": data_module}}
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)



class KursFactory:
    def kurse_erzeugen(self, anzahl_semester=6, module_pro_semester=6, standard_ects=5):
        module = []
        mid = 1

        semester_liste = [Semester(anzahl=s) for s in range(1, anzahl_semester + 1)]

        for sem in semester_liste:
            for i in range(1, module_pro_semester + 1):
                module.append(
                    Kurs(
                        id=mid,
                        titel=f"Modul {sem.anzahl}.{i}",
                        ects=standard_ects,
                        semester=sem.anzahl,  # Kommt aus dem Semester-Objekt
                        belegt=False,
                        pruefungsleistung=None,
                    )
                )
                mid += 1

        return module


######################################################################################################################
# APP-SETUP
######################################################################################################################

def create_app():
    speicher = Speicher(Path("data.json"))
    eingabe = Eingabe()
    dashboard = Dashboard(speicher, eingabe)
    api = API(dashboard, template_folder=".")
    return api.app


if __name__ == "__main__":
    app = create_app()
    app.run(host="127.0.0.1", port=5000, debug=False)
    # Für netzwerkweiten Zugriff host="0.0.0.0"
