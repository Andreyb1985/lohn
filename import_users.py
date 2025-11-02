import pandas as pd
import sqlite3
from werkzeug.security import generate_password_hash

def import_from_excel(excel_path='employees.xlsx', db_path='employees.db'):
    df = pd.read_excel(excel_path)
    conn = sqlite3.connect(db_path)
    conn.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        employee_number TEXT,
        role TEXT
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS news (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        content TEXT
    )""")

    for _, row in df.iterrows():
        username = str(row.get('username','')).strip()
        password = str(row.get('password','')).strip()
        employee_number = str(row.get('employee_number','')).strip()
        role = str(row.get('role','user')).strip() or 'user'
        if not username:
            continue
        hashed = generate_password_hash(password)
        try:
            conn.execute("INSERT OR IGNORE INTO users (username, password, employee_number, role) VALUES (?, ?, ?, ?)", (username, hashed, employee_number, role))
        except Exception as e:
            print('Error inserting', username, e)

    conn.commit()
    conn.close()

if __name__ == '__main__':
    import_from_excel()
