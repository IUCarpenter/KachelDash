\## KachelDash - Projektarbeit für IU ##


https://github.com/IUCarpenter/KachelDash


Dieses Projekt implementiert ein Dashboard in Python und Flask anhand einer im Rahmen eines IU-Projekts

entwickelten Architektur.

Ziel: Studienfortschritt darstellen und abschließen aller nötigen Kurse visualisieren.





Diese README Datei dient als INSTALLATIONSANLEITUNG

---



\## FUNKTION ##



\- Übersicht als Kachelansicht

\- Modulstatus (Ampel-Logik):

  - grün: Kurs ist bestanden

  - rot: Kurs leider nicht bestanden

  - gelb: Der Kurs ist belegt (in Bearbeitung)

  - grau: nicht belegt und keine Note

\- Kennzahlen:

  - ECTS (Erkämpfte Credits)

  - MEAN (Notendurchschnitt)

\- Persistenz über "data.json" (wird beim ersten Start automatisch erzeugt)



Sonderregel Note 0.0 (Anerkennung):

\- zählt als vestanden (ECTS werden also addiert),

\- zählt nicht in den Notendurchschnitt (MEAN)





Das Dashboard ist intuitiv, zum bearbeiten einzelner Kacheln müssen

die Kacheln mit der linken maustaste ausgewählt werden.

---





\_\_INSTALLATIONSANLEITUNG\_\_



\## Voraussetzungen für beide Methoden##



\- Python 3.10+ muss auf dem System installiert sein!!

\- Projektdatein müssen lokal im projektverzeichnis liegen



Für die Installation bietet KachelDash 2 Methoden an:

 

 	Methode 1:

 

 		- CLI im projektverzeichnis starten

 

 		Folgende Kommandos ausführen:

 		- python -m venv dashenv

 		- dashenv\\scripts\\activate

 		- pip install flask

 		- python dash.py



 		Das Dashboard ist gestartet und kann über:

 		http://127.0.0.1:5000 aufgerufen werden





 	Methode 2:



 		- install.bat im Projektverzeichnis aufrufen

 		- KachelDash wird installiert

 		- KachelDash wird gestartet



 		Das Dashboard ist gestartet und kann über:

 		http://127.0.0.1:5000 aufgerufen werden

