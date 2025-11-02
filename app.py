from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, send_file, flash, abort
import os
import sqlite3
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps
import threading

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change_this_secret")
UPLOAD_FOLDER = "uploads"
DB_FILE = "employees.db"
EXCEL_FILE = "employees.xlsx"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def ensure_db_from_excel():
    if not os.path.exists(DB_FILE) and os.path.exists(EXCEL_FILE):
        try:
            import import_users as iu
            iu.import_from_excel(EXCEL_FILE, DB_FILE)
            print("Users aus Excel in DB importiert.")
        except Exception as e:
            print("Import fehlgeschlagen:", e)

def start_background_setup():
    t = threading.Thread(target=ensure_db_from_excel, daemon=True)
    t.start()

start_background_setup()

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for("login"))
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE username = ?", (session["username"],)).fetchone()
        conn.close()
        if not user or user["role"] != "admin":
            return "Zugriff verweigert", 403
        return f(*args, **kwargs)
    return wrapper

@app.route("/")
@login_required
def home():
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (session["username"],)).fetchone()
    conn.close()

    if not user:
        flash("Benutzer nicht gefunden.", "danger")
        return redirect(url_for("login"))

    employee_number = str(user["employee_number"])

    user_folders = set()
    for root_dir, dirs, filenames in os.walk(UPLOAD_FOLDER):
        for fname in filenames:
            if employee_number in fname:
                rel_dir = os.path.relpath(root_dir, UPLOAD_FOLDER)
                user_folders.add(rel_dir if rel_dir != "." else "")

    folders_sorted = sorted(list(user_folders), key=lambda p: (p.count(os.sep), p))

    return render_template("folders.html", folders=folders_sorted, username=user["username"], role=user["role"])

@app.route("/folder/", defaults={"subdir": ""})
@app.route("/folder/<path:subdir>")
@login_required
def view_folder(subdir):
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (session["username"],)).fetchone()
    conn.close()

    if not user:
        flash("Benutzer nicht gefunden.", "danger")
        return redirect(url_for("login"))

    employee_number = str(user["employee_number"])
    folder_path = os.path.join(UPLOAD_FOLDER, subdir) if subdir else UPLOAD_FOLDER
    if not os.path.isdir(folder_path):
        return "Ordner nicht gefunden", 404

    files = []
    for fname in os.listdir(folder_path):
        if os.path.isfile(os.path.join(folder_path, fname)) and employee_number in fname:
            rel_path = os.path.relpath(os.path.join(folder_path, fname), UPLOAD_FOLDER)
            files.append(rel_path)

    return render_template("files.html", files=files, username=user["username"], role=user["role"], folder=subdir)

@app.route("/downloads/<path:filename>")
@login_required
def download(filename):
    safe_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.isfile(safe_path):
        return "Datei nicht gefunden", 404

    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (session["username"],)).fetchone()
    conn.close()

    if user["role"] != "admin":
        if str(user["employee_number"]) not in os.path.basename(filename):
            return "Zugriff verweigert", 403

    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)

@app.route("/get_pdf/<path:filename>")
@login_required
def get_pdf(filename):
    safe_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.isfile(safe_path):
        return "Datei nicht gefunden", 404
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (session["username"],)).fetchone()
    conn.close()
    if user["role"] != "admin" and str(user["employee_number"]) not in os.path.basename(filename):
        return "Zugriff verweigert", 403
    return send_file(safe_path, mimetype="application/pdf")

@app.route("/pdf/<path:filename>")
@login_required
def pdf_viewer(filename):
    safe_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.isfile(safe_path):
        return "Datei nicht gefunden", 404
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (session["username"],)).fetchone()
    conn.close()
    if user["role"] != "admin" and str(user["employee_number"]) not in os.path.basename(filename):
        return "Zugriff verweigert", 403
    return render_template("pdf_viewer.html", filename=filename)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["username"] = user["username"]
            flash("Anmeldung erfolgreich.", "success")
            return redirect(url_for("home"))
        else:
            flash("Benutzername oder Passwort ist ungültig.", "danger")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/news")
@login_required
def news():
    conn = get_db_connection()
    news_list = conn.execute("SELECT * FROM news ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("news.html", news_list=news_list)

@app.route("/admin")
@admin_required
def admin_dashboard():
    conn = get_db_connection()
    users = conn.execute("SELECT * FROM users").fetchall()
    news = conn.execute("SELECT * FROM news ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("admin_dashboard.html", users=users, news=news)

@app.route("/admin/add_user", methods=["POST"])
@admin_required
def admin_add_user():
    username = request.form["username"].strip()
    password = request.form["password"].strip()
    employee_number = request.form["employee_number"].strip()
    role = request.form.get("role", "user").strip()

    hashed = generate_password_hash(password)
    conn = get_db_connection()
    try:
        conn.execute("INSERT INTO users (username, password, employee_number, role) VALUES (?, ?, ?, ?)",
                     (username, hashed, employee_number, role))
        conn.commit()
    except sqlite3.IntegrityError:
        flash("Ein Benutzer mit diesem Namen existiert bereits.", "warning")
    conn.close()
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/add_news", methods=["POST"])
@admin_required
def admin_add_news():
    title = request.form["title"].strip()
    content = request.form["content"].strip()
    conn = get_db_connection()
    conn.execute("INSERT INTO news (title, content) VALUES (?, ?)", (title, content))
    conn.commit()
    conn.close()
    return redirect(url_for("admin_dashboard"))

if __name__ == "__main__":
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    try:
        ensure_db_from_excel()
    except:
        pass
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
