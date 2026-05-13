# Verifikation und Reasoning-Critic

Dieser Fork ergänzt die Report-Erzeugung jetzt um zwei Review-Schichten:

1. Eine Verifikationsschicht, die ein Claim-Ledger und einen Evidence-Graph erzeugt.
2. Einen Reasoning-Critic, der den Report gegen dieses Verifikations-Bundle prüft.

Das Ziel ist nicht, Wahrheit zu garantieren. Das Ziel ist, Unterstützung, Unsicherheit und Prüfbarkeit standardmäßig sichtbar zu machen.

## Verifikations-Review

Die Verifikationsschicht ist implementiert in:

- `gpt_researcher/actions/verification.py`
- `gpt_researcher/actions/report_generation.py`

Sie extrahiert Claims aus dem Report, vergleicht sie mit dem Research-Kontext und erzeugt:

- ein Claim-Ledger
- einen Evidence-Graph
- eine Support-Zusammenfassung
- eine Risikoklassifizierung

Das Risk-Gating konzentriert sich derzeit auf:

- health
- legal
- finance
- security
- politics

Wenn der Report höher riskante Themen berührt, wird die Ausgabe für eine menschliche Prüfung markiert.

## Reasoning-Critic

Der Reasoning-Critic ist implementiert in:

- `gpt_researcher/actions/reasoning_critic.py`
- `gpt_researcher/actions/report_generation.py`

Er liest den Report plus das Verifikations-Bundle und stellt eine engere Frage:

- Gibt es unbelegte Claims?
- Gibt es zu selbstsichere Aussagen?
- Fehlen wichtige Einschränkungen?
- Muss der Report manuell geprüft werden?

Der Critic liefert strukturiertes JSON und wird an den Report angehängt als:

- `## Verification Review`
- `## Reasoning Critic`

Die LLM-Antwort wird über den gemeinsamen JSON-Parser normalisiert, bevor der deterministic fallback greift. Dadurch überlebt der Critic auch code-fenced oder leicht beschädigte JSON-Payloads.

Wenn die LLM-Antwort fehlerhaft oder nicht verfügbar ist, fällt der Critic auf ein deterministisches Review auf Basis des Verifikations-Bundles zurück.

## Konfiguration

Die Review-Schichten sind standardmäßig aktiviert:

- `ENABLE_VERIFICATION_REVIEW`
- `ENABLE_REASONING_CRITIC`

Wenn du eine der Schichten vorübergehend deaktivieren möchtest, setze das entsprechende Flag in deiner Konfiguration oder Umgebung auf `false`.

## Was du im Report sehen wirst

Der finale Report kann jetzt enthalten:

- the main synthesis
- a verification appendix
- a critic appendix

Der Critic-Anhang enthält typischerweise:

- ein Urteil (`pass`, `revise` oder `high_risk`)
- einen Confidence-Score
- Stärken
- Probleme
- Empfehlungen

## Warum das wichtig ist

Dieser Review-Stack ist besonders nützlich, wenn die Research-Ausgabe verwendet wird für:

- technical comparisons
- product decisions
- operational analysis
- sensitive domains where unsupported claims are costly

Er ersetzt bei kritischen Themen keine menschliche Prüfung, macht die Fehlermodi aber wesentlich leichter sichtbar.

## Validierung

Die Review-Schichten werden abgedeckt durch:

- `tests/test_verification.py`
- `tests/test_reasoning_critic.py`

Diese Tests prüfen:

- Claim-Extraktion
- Erstellung des Evidence-Graphen
- Risikoerkennung
- Fallback-Verhalten des Critics
- Integration in den finalen Report
