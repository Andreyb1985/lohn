# employee_site_v4_de - bereit für Render

Dieses Projekt ist für Render vorbereitet und enthält:
- Automatischen Import von Benutzern aus employees.xlsx, falls employees.db fehlt.
- PDF-Anzeige mit PDF.js.
- Adminbereich und Nachrichten-Funktionalität.
- Mehrstufige Ordnerstruktur in uploads/.

## Schnellstart lokal
1. Virtuelle Umgebung erstellen:
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
2. Abhängigkeiten installieren:
   pip install -r requirements.txt
3. Benutzer importieren (optional):
   python import_users.py
4. Starten:
   python app.py
5. Im Browser öffnen: http://127.0.0.1:5000/login
   Test-Admin: admin / admin123

## Deployment auf Render
1. Repository auf GitHub pushen.
2. In Render eine neue Web Service anlegen und Repo verbinden.
3. Start Command: `gunicorn app:app --workers 2 --timeout 120`
4. Empfohlene Environment Variable: SECRET_KEY
5. Hinweis: Render hat ein ephemeres Dateisystem. Verwenden Sie für persistente Speicherung S3/Supabase/Postgres.

