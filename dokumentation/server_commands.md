# Server Befehl Kommunikation
Um zu kommunizieren verwenden der Client sowie der Server verschiedene Befehle die mittels der Socket Library gesendet werden. Diese Befehle unterteilen sich in zwei Kategorien.
- Server/Client GET-Befehle
- Server/Client SEND-Befehle
Die GET-Befehle dienen dazu Daten vom Kommunikationspartner abzurufen, erwarten somit eine Rückmeldung. SEND-Befehle hingegen geben einen Befehl oder übermitteln Daten, bei ihnen ist die Rückmeldung obtional.
Ein Befehl baut sich aus verschiedenen aneinandergereiten argumenten auf. Diese sind durch ein Semikolon (";") getrennt. Das erste Argument des Befehls dient dessen einordnung. Es beginnt je nach Art entweder mit "get_" oder send_" danach folgt der Befehl name. In den weiteren Argumenten können optionale / nicht optionale Daten mitgesendet werden.

Beispiel:
send_creds;{username};{password}
Dieser Befehl dient dazu den Clienten nach dem erstellen einer Connection mit abgleich zu den Server-Databases zu verifizieren. Da dieser Befehl nur zum serverseitigen ausführen eines Abgleichs dient, braucht dieser Befehl keine Response *(In manchen versionen sendet er aus Debug Gründen bei invaliden Credentials die nachicht "invalid" zurück.)*. Die Credentials (username und password) werden in den nachgestellten Argumenten mitgesendet. Da die Argumente durch ";" getrennt werden **dürfen sie selber keine semikolen enthalten**. 

## Liste an Server GET-Befehlen
## Liste an Server SEND-Befehlen
## Liste an Client GET-Befehlen
## Liste an Client SEND-Befehlen
### send_creds
**Syntax:**
send_creds;{username};{password}
**Response:** None
**Description:**
Der Befehl dient dazu den Clienten beim Server (intern) zu verifizieren, und ihm zugriff auf weitere Befehle (unteranderem das senden von nachichten) zu geben die nur ein verifizierter, mit der datenbank abgeglichener, Client ausführen darf.
