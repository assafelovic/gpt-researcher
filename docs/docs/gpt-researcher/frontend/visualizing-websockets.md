# WebSockets visualisieren

Das GPTR-Frontend wird über WebSockets mit dem Backend versorgt. Dadurch bekommst du Echtzeit-Updates zum Status deiner Rechercheaufgaben und kannst direkt vom Frontend aus mit dem Backend interagieren.

## WebSockets prüfen

Wenn du Reports über das Frontend startest, kannst du die WebSocket-Nachrichten im Network-Tab deines Browsers ansehen.

So geht's:

![image](https://github.com/user-attachments/assets/15fcb5a4-77ea-4b3b-87d7-55d4b6f80095)

## Läuft die richtige URL an?

Wenn du vermutest, dass dein Frontend nicht den richtigen API-Endpunkt ansteuert, prüfe die URL im Network-Tab.

Klicke auf die WS-Anfrage und öffne den Reiter **Headers**:

![image](https://github.com/user-attachments/assets/dbd58c1d-3506-411a-852b-e1b133b6f5c8)

Zum Debuggen kannst du dir auch die [getHost-Funktion](https://github.com/assafelovic/gpt-researcher/blob/master/frontend/nextjs/helpers/getHost.ts) ansehen.
