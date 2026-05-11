# Fehlerbehebung

Wir arbeiten ständig daran, eine stabilere Version bereitzustellen. Wenn du auf Probleme stößt, schau dir zuerst die gelösten Issues an oder frag uns in unserer [Discord-Community](https://discord.gg/QgZXvJAccX).

### model: gpt-4 does not exist
Das hängt damit zusammen, dass du noch keine Berechtigung für `gpt-4` hast. Laut OpenAI wird das Modell [bis Ende Juli für alle breit verfügbar](https://help.openai.com/en/articles/7102672-how-can-i-access-gpt-4).

### cannot load library 'gobject-2.0-0'

Das Problem betrifft die Bibliothek WeasyPrint, die für die PDF-Erzeugung aus dem Research-Report verwendet wird. Folge zur Behebung dieser Anleitung: https://doc.courtbouillon.org/weasyprint/stable/first_steps.html

Alternativ kannst du das Paket manuell installieren.

Unter macOS kannst du die Bibliothek so installieren:
`brew install glib pango`
Falls es danach Probleme beim Linken gibt, versuche `brew link glib`.

Unter Linux kannst du die Bibliothek so installieren:
`sudo apt install libglib2.0-dev`

### cannot load library 'pango'

Unter macOS kannst du die Bibliothek so installieren:
`brew install pango`

Unter Linux kannst du die Bibliothek so installieren:
`sudo apt install libpango-1.0-0`

**Workaround für Mac-Nutzer mit M-Chip**

Wenn die obigen Lösungen nicht helfen, probiere Folgendes:
- Installiere eine frische Python-3.11-Version über Homebrew:
`brew install python@3.11`
- Installiere die benötigten Bibliotheken:
`brew install pango glib gobject-introspection`
- Installiere die benötigten GPT-Researcher-Python-Pakete:
`pip3.11 install -r requirements.txt`
- Starte die App mit Python 3.11 aus Homebrew:
`python3.11 -m uvicorn main:app --reload`

### Error processing the url

Wir nutzen [Selenium](https://www.selenium.dev) für das Scraping von Websites. Manche Seiten lassen sich nicht zuverlässig auslesen. In solchen Fällen hilft es oft, den Lauf neu zu starten.


### Chrome version issues

Viele Nutzer haben Probleme mit ihrem Chromedriver, weil die neueste Chrome-Version noch keinen kompatiblen Treiber hat.

Wenn du Chrome über [slimjet](https://www.slimjet.com/chrome/google-chrome-old-version.php) herunterstufen möchtest, gehe so vor: Öffne die Website und suche in der Liste nach einer älteren Chrome-Version. Wähle eine Version, die zu deinem Betriebssystem passt.
Sobald du die gewünschte Version ausgewählt hast, lade den Installer über den passenden Link herunter. Vor der Installation solltest du deine aktuelle Chrome-Version deinstallieren, um Konflikte zu vermeiden.

Wichtig ist außerdem, dass die gewählte Version einen verfügbaren Chromedriver auf der offiziellen [Chrome-Driver-Seite](https://chromedriver.chromium.org/downloads) hat.

**Wenn nichts davon hilft, kannst du unsere [gehostete Beta ausprobieren](https://app.tavily.com)**
