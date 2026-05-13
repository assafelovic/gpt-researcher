# Scraping-Optionen

GPT Researcher unterstützt mehrere Arten von Web-Scraping: statisches Scraping mit BeautifulSoup, dynamisches Scraping mit Selenium sowie skalierbares Scraping mit Tavily Extract oder FireCrawl. Diese Seite erklärt, wann du welche Methode verwenden solltest.

## Scraping-Methode konfigurieren

Du kannst die gewünschte Methode über die Umgebungsvariable `SCRAPER` festlegen:

1. **BeautifulSoup** für statisches Scraping:
   ```bash
   export SCRAPER="bs"
   ```

2. **Browser-Scraping** mit Selenium:
   ```bash
   export SCRAPER="browser"
   ```

   Oder mit NoDriver / ZenDriver:
   ```bash
   export SCRAPER="nodriver"
   pip install zendriver
   ```

3. **Produktionseinsatz** mit Tavily Extract oder FireCrawl:
   ```bash
   export SCRAPER="tavily_extract"
   ```

   ```bash
   export SCRAPER="firecrawl"
   ```

Wenn du keine Methode setzt, verwendet GPT Researcher standardmäßig BeautifulSoup.

## Die Methoden im Überblick

### BeautifulSoup

`SCRAPER="bs"` eignet sich für statische Seiten. Der Scraper:

- lädt die Seite per HTTP-Request
- parst den statischen HTML-Inhalt
- extrahiert Text und Daten aus dem HTML

**Vorteile**
- schnell und leichtgewichtig
- keine zusätzliche Einrichtung nötig
- gut für einfache, statische Websites

**Nachteile**
- kein Umgang mit dynamischen Inhalten aus JavaScript
- interaktive Inhalte können fehlen

### Selenium

`SCRAPER="browser"` eignet sich für dynamische Seiten. Der Scraper:

- öffnet einen echten Browser
- lädt die Seite und führt JavaScript aus
- wartet auf dynamische Inhalte
- extrahiert Text aus der vollständig gerenderten Seite

**Vorteile**
- kann dynamisch geladene Inhalte erfassen
- simuliert echte Nutzerinteraktionen
- gut für komplexe, JavaScript-lastige Websites

**Nachteile**
- langsamer als statisches Scraping
- benötigt mehr Ressourcen
- erfordert zusätzliche Einrichtung

### NoDriver

Alternativ zu Selenium kannst du NoDriver / ZenDriver verwenden:

```bash
pip install zendriver
```

### Tavily Extract

`SCRAPER="tavily_extract"` nutzt Tavilys Extract-API für skalierbares Web-Scraping. Diese Variante:

- verarbeitet Websites auf robuster Infrastruktur
- kann CAPTCHAs, JavaScript-Rendering und Anti-Bot-Maßnahmen abfedern
- liefert sauber strukturierte Inhalte

**Geeignet für**
- Produktion
- hohe Zuverlässigkeit
- weniger manuellen Infrastrukturaufwand

**Einrichtung**
1. Tavily-Konto auf [app.tavily.com](https://app.tavily.com) anlegen
2. API-Key aus dem Dashboard holen
3. Tavily SDK installieren:
   ```bash
   pip install tavily-python
   ```
4. API-Key setzen:
   ```bash
   export TAVILY_API_KEY="dein-api-key"
   ```

### FireCrawl

`SCRAPER="firecrawl"` nutzt die FireCrawl-Scrape-API und liefert Inhalte in Markdown. Diese Variante:

- skaliert gut
- kann auch von einem selbst gehosteten FireCrawl-Server profitieren
- unterstützt robuste Extraktion trotz dynamischer Inhalte

**Einrichtung mit Cloud-Service**
1. FireCrawl-Konto auf [firecrawl.dev/app](https://www.firecrawl.dev/app) anlegen
2. API-Key aus dem Dashboard holen
3. SDK installieren:
   ```bash
   pip install firecrawl-py
   ```
4. API-Key setzen:
   ```bash
   export FIRECRAWL_API_KEY=<dein-firecrawl-api>
   ```

**Einrichtung mit Self-Hosted Server**
1. FireCrawl selbst hosten
2. Server-URL und API-Key notieren
3. SDK installieren:
   ```bash
   pip install firecrawl-py
   ```
4. API-Key setzen:
   ```bash
   export FIRECRAWL_API_KEY=<dein-firecrawl-api>
   ```
5. Server-URL setzen:
   ```bash
   export FIRECRAWL_SERVER_URL=<deine-firecrawl-url>
   ```

`FIRECRAWL_API_KEY` kann leer bleiben, wenn du deinen Self-Hosted-Server ohne Auth betreibst. `FIRECRAWL_SERVER_URL` muss für Self-Hosted-Setups gesetzt sein, sonst wird die Cloud-URL verwendet.

## Zusätzliche Einrichtung für Selenium

Wenn du Selenium (`SCRAPER="browser"`) verwenden möchtest:

1. Selenium installieren:
   ```bash
   pip install selenium
   ```

2. Passenden WebDriver herunterladen:
   - Chrome: [ChromeDriver](https://sites.google.com/a/chromium.org/chromedriver/downloads)
   - Firefox: [GeckoDriver](https://github.com/mozilla/geckodriver/releases)
   - Safari: bereits integriert

3. Stelle sicher, dass der WebDriver im `PATH` liegt.

## Die richtige Methode wählen

- **BeautifulSoup** für:
  - einfache Websites mit statischem Inhalt
  - Fälle, in denen Geschwindigkeit wichtig ist
  - Seiten, auf denen keine Interaktion nötig ist

- **Selenium** für:
  - JavaScript-lastige Inhalte
  - Seiten, die Scrollen oder Klicken erfordern
  - realistische Nutzerinteraktionen

## Fehlerbehebung

- Wenn Selenium nicht startet, prüfe den installierten WebDriver und den `PATH`.
- Wenn ein `ImportError` zu Selenium auftaucht, stelle sicher, dass Selenium installiert ist.
- Wenn Inhalte fehlen, wechsle zwischen statischem und dynamischem Scraping und prüfe, welche Methode für die Zielseite besser funktioniert.

Die Wahl zwischen statischem und dynamischem Scraping hat großen Einfluss auf Qualität und Vollständigkeit der gesammelten Daten. Wähle die Methode, die am besten zu deinem Research-Ziel und den Zielseiten passt.
