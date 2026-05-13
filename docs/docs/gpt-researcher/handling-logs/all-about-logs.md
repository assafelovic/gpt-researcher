# Alles über Logs

Dieses Dokument erklärt, wie du die Logdateien interpretierst, die für jeden Report erzeugt werden. Sie geben einen detaillierten Überblick über den Research-Prozess: von der ersten Aufgabenplanung über das Sammeln von Informationen bis hin zum Schreiben des Reports. Reports können sich im Laufe der Zeit ändern, wenn neue Funktionen hinzukommen.

## Überblick über die Logdateien

Die Logdatei ist eine JSON-Datei mit einer Liste aller Ereignisse, die während der Recherche passiert sind. Jedes Ereignis ist ein Objekt mit Zeitstempel, Typ und Daten. Die Daten enthalten die konkreten Informationen zum Ereignis.

Die Logdatei findest du im Ordner `outputs`.

Alternativ kannst du sie direkt auf der Report-Seite über den Button **Logs herunterladen** öffnen.

Für diesen Fork ist `outputs` das kanonische Artefaktverzeichnis. Die JSON-Ereignislogs, Markdown-Reports, PDFs, DOCX-Dateien und Screenshots werden dort abgelegt. Unten findest du die Details dazu.

## Wichtige Bestandteile

* `timestamp`: Zeitstempel im Format `YYYY-MM-DDTHH:MM:SS.ffffff` im ISO-Format. Der Hauptzeitstempel beschreibt die Erstellung der Datei selbst. Die Ereignis-Zeitstempel zeigen, wann ein bestimmter Schritt während der Recherche passiert ist.
* `events`: Ein Array mit allen geloggten Ereignissen während der Recherche.
* `timestamp`: Der konkrete Zeitpunkt des Ereignisses.
* `type`: Der Typ ist aktuell immer `event`.
* `data`: Enthält spezifische Informationen zum Ereignis. Dazu gehören:
* `type`: Beschreibt die allgemeine Ereigniskategorie, zum Beispiel `"logs"`.
* `content`: Eine Kurzbeschreibung dessen, was das Tool gerade tut, zum Beispiel `"starting_research"`, `"running_subquery_research"` oder `"scraping_content"`.
* `output`: Eine ausführlichere Nachricht, die oft auch visuelle Hinweise wie Emojis enthält und an den Nutzer gesendet wird.
* `metadata`: Zusätzliche Daten zum Ereignis. Das kann `null` sein oder ein Array mit relevanten Informationen wie URLs enthalten.

## Ereignistypen und ihre Bedeutung

Hier ist eine vollständige Übersicht über die wichtigsten `content`-Typen und ihre Bedeutung:

1. **`starting_research`**:
* Zeigt an, dass die Recherche für eine Aufgabe begonnen hat.
* `output`: Enthält den Text der Recherche-Anfrage.
2. **`agent_generated`**:
* Kennzeichnet, welcher Agent für diese Aufgabe verwendet wird.
* `output`: Zeigt den Namen des Agents.
3. **`planning_research`**:
* Zeigt, dass das Tool zunächst browsed, um den Umfang der Anfrage zu verstehen und zu planen.
* `output`: Gibt an, ob gerade gebrowst oder initial geplant wird.
4. **`subqueries`**:
* Zeigt, dass das Tool Unteranfragen erzeugt hat, die für die Recherche genutzt werden.
* `output`: Listet alle Subqueries auf, die ausgeführt werden.
* `metadata`: Ein Array mit den Subqueries.
5. **`running_subquery_research`**:
* Zeigt an, dass eine bestimmte Subquery bearbeitet wird.
* `output`: Zeigt die gerade laufende Subquery.
6. **`added_source_url`**:
* Kennzeichnet eine URL, die als relevante Informationsquelle identifiziert wurde.
* `output`: Zeigt die URL mit einem Häkchen an.
* `metadata`: Enthält die tatsächlich hinzugefügte URL.
7. **`researching`**:
* Zeigt an, dass das Tool aktiv über mehrere Quellen hinweg recherchiert.
* `output`: Allgemeine Nachricht zur laufenden Recherche.
8. **`scraping_urls`**:
* Zeigt, dass das Tool mit dem Scraping einer URL-Gruppe beginnt.
* `output`: Gibt an, wie viele URLs gescraped werden.
9. **`scraping_content`**:
* Zeigt an, dass Inhalte erfolgreich aus den URLs gescraped wurden.
* `output`: Zeigt an, wie viele Seiten erfolgreich ausgelesen wurden.
10. **`scraping_images`**:
* Zeigt an, dass während des Scrapings Bilder gefunden und ausgewählt wurden.
* `output`: Zeigt die Anzahl neuer Bilder und die Gesamtzahl gefundener Bilder.
* `metadata`: Enthält die URLs der ausgewählten Bilder.
11. **`scraping_complete`**:
* Zeigt an, dass das Scraping für die URLs abgeschlossen ist.
* `output`: Meldung, dass der Scraping-Prozess abgeschlossen ist.
12. **`fetching_query_content`**:
* Zeigt an, dass Inhalte zu einer bestimmten Query abgerufen werden.
* `output`: Die konkrete Query, für die Inhalte geholt werden.
13. **`subquery_context_window`**:
* Zeigt, dass für eine Subquery ein Kontextfenster erstellt wird.
* `output`: Meldung, dass das Kontextfenster erstellt wurde.
14. **`research_step_finalized`**:
* Zeigt an, dass ein Research-Schritt abgeschlossen wurde.
* `output`: Meldung, dass die Recherche beendet ist.
15. **`generating_subtopics`**:
* Zeigt, dass Unterthemen erzeugt werden, um den Report zu strukturieren.
* `output`: Meldung zur Erzeugung der Unterthemen.
16. **`subtopics_generated`**:
* Zeigt an, dass Unterthemen erzeugt wurden.
* `output`: Meldung, dass die Unterthemen fertig sind.
17. **`writing_introduction`**:
* Zeigt an, dass die Einleitung des Reports geschrieben wird.
* `output`: Meldung, dass das Schreiben der Einleitung begonnen hat.
18. **`introduction_written`**:
* Zeigt an, dass die Einleitung fertig ist.
* `output`: Meldung, dass die Einleitung geschrieben wurde.
19. **`generating_draft_sections`**:
* Zeigt, dass Entwurfsabschnitte für den Report erzeugt werden.
* `output`: Meldung, dass die Entwurfsabschnitte erstellt werden.
20. **`draft_sections_generated`**:
* Zeigt an, dass die Entwurfsabschnitte erzeugt wurden.
* `output`: Meldung, dass die Entwurfsabschnitte fertig sind.
21. **`fetching_relevant_written_content`**:
* Zeigt, dass relevantes geschriebenes Material für den Report abgerufen wird.
* `output`: Meldung, dass relevante Inhalte geholt werden.
22. **`writing_report`**:
* Zeigt an, dass das Tool gerade den Research-Report zusammenstellt.
* `output`: Meldung, dass die Report-Erzeugung begonnen hat.
23. **`report_written`**:
* Zeigt an, dass der Report fertig ist.
* `output`: Meldung, dass die Report-Erzeugung abgeschlossen ist.
24. **`relevant_contents_context`**:
* Zeigt, dass ein Kontextfenster für relevante Inhalte erstellt wurde.
* `output`: Meldung, dass ein Kontextfenster erstellt wurde.
25. **`writing_conclusion`**:
* Zeigt an, dass das Fazit des Reports geschrieben wird.
* `output`: Meldung, dass das Fazit geschrieben wird.
26. **`conclusion_written`**:
* Zeigt an, dass das Fazit geschrieben wurde.
* `output`: Meldung, dass das Fazit fertig ist.

## So nutzt du die Logs

* **Fehlersuche:** Wenn die Ergebnisse unerwartet sind, helfen die Logs, die exakten Schritte des Tools zu verstehen.
* **Transparenz:** Die Logs zeigen genau, welche URLs besucht wurden, welche Bilder ausgewählt wurden und wie der Report entstanden ist.
* **Prozessverständnis:** Die Logs geben einen Überblick darüber, was das Tool tut und wie die einzelnen Schritte aussehen.
* **Reproduzierbarkeit:** Mit den Logdateien kannst du den genauen Ablauf nachvollziehen.

## Beispielnutzung

Anhand der Zeitstempel kannst du den Verlauf einer Research-Aufgabe nachvollziehen. Die Logs zeigen dir die genutzten Subqueries, alle verwendeten URLs, eventuelle Bilder und alle Schritte, die zur Report-Erzeugung nötig waren.

## Logs für Entwickler

Zusätzlich zu den nutzerorientierten Logdateien erzeugt die Anwendung zwei Entwickler-Artefakte:

1. Eine `.log`-Datei für gestreamte Event-Logs
2. Eine `.json`-Datei für strukturierte Ereignis- und Inhaltsdaten

Du findest die Logs im Ordner `outputs`.

### Einfache Logdatei (.log)

* **Format:** Klartext. Jede Zeile ist ein Log-Eintrag.
* **Inhalt:**
	* Zeitstempel mit Millisekundenauflösung
	* Log-Level, meist `INFO`, in komplexeren Setups auch `DEBUG`, `WARNING` oder `ERROR`
	* Modulname, zum Beispiel `research`
	* Beschreibende Meldungen zu verschiedenen Prozessen
	* Enthält Daten zu:
		* Start und Ende von Research-Aufgaben
		* ausgeführten Web-Suchen
		* Planung der Recherche
		* erzeugten Subqueries und deren Ergebnissen
		* Größen der gescrapten Daten
		* Größe der Inhalte aus Subqueries
		* der finalen Gesamtgröße des gefundenen Kontexts
* **Anwendungsfälle für Entwickler:**
	* **Live-Monitoring:** Zum Beobachten der Tool-Aktivität in Echtzeit
	* **Debugging:** Zum Auffinden von Problemen über den chronologischen Ablauf
	* **Analyse der Performance:** Zeitstempel helfen beim Erkennen von Engpässen
	* **Überblick:** Zeigt schnell, welche Schritte ausgeführt wurden und wie viel Inhalt gesammelt wurde
* **Unterschiede zu Nutzerlogs:**
	* Weniger strukturiert und mehr für Entwickler gedacht
	* Enthält technische Informationen, die für Nicht-Entwickler meist nicht relevant sind
	* Keine Emojis oder vereinfachte Sprache
	* Keine Informationen zu gesammelten Bildern
	* Screenshot-Debug-Artefakte werden, wenn aktiviert, unter `outputs/screenshots` gespeichert

### JSON-Logdatei (.json)

* **Format:** Strukturierte JSON-Datei
* **Inhalt:**
	* Zeitstempel wie in allen Logdateien
	* `type`-Feld, das enthalten kann:
		* `sub_query`: enthält den Subquery-String plus `scraped_data_size`
		* `content_found`: enthält `sub_query` und `content_size`
		* Ein `content`-Feld mit einer Momentaufnahme der Gesamt-Recherche, inklusive des finalen Kontexts und der gefundenen Quellen
* **Anwendungsfälle für Entwickler:**
	* **Detaillierte Analyse:** Zeigt, wie das Tool im Detail läuft
	* **Prozessverständnis:** Macht sichtbar, welche Subqueries liefen und wie viel Inhalt sie erzeugt haben
	* **Dateninspektion:** Nützlich zum Prüfen der erzeugten Queries und Inhaltsgrößen
* **Unterschiede zu Nutzerlogs:**
	* Stark strukturiert und auf Subquery-Ausführung fokussiert
	* Keine vereinfachte Sprache, keine Emojis, keine hohen Abstraktionen
	* Keine Informationen zum Gesamt-Kontext oder zu Bildern, sondern Fokus auf den Subquery-Prozess
