employee_site_v3
----------------
Contains a Flask app that lists folders (all levels) containing user's files, allows viewing files in a folder, and secure downloading.

How to run:
1. Unzip and open terminal in project folder.
2. (Optional) Create venv:
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
3. Install deps:
   pip install flask pandas werkzeug openpyxl
4. Import users to DB:
   python import_users.py
5. Run app:
   python app.py
6. Open http://127.0.0.1:5000/login
   Admin: admin / admin123
Notes:
- Replace placeholder .pdf files in uploads/ with real PDFs.
- For production, configure secret key, disable debug & use WSGI server.
