from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import bcrypt
import traceback

app = Flask(__name__)
app.secret_key = 'CHANGE_THIS_SECRET_KEY'

DATABASE_URL = os.environ.get(
    'DATABASE_URL',
    'postgresql://postgres:password@localhost:5432/postgres'
)

# ===============================
# КОТЕЛЬНЫЕ — СТРОГО ИЗ EXCEL
# ===============================
BOILERS = {
    1: {
        "name": "Котельная №1",
        "address": "Белоярск №1 ул. Набережная 8"
    },
    2: {
        "name": "Котельная №2",
        "address": "г. Белоярск ул. Юбилейная 11"
    },
    3: {
        "name": "Котельная №3",
        "address": "Щучье №3"
    },
    4: {
        "name": "Котельная №4",
        "address": "Катравож №4 ул. Маслова 6/2"
    }
}

# ===============================
# БД
# ===============================
def get_db_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


def ensure_tables_and_admin():
    conn = get_db_connection()
    cursor = conn.cursor()

    # --- USERS ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'operator'
        )
    """)

    # --- RECORDS ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS records (
            id SERIAL PRIMARY KEY,
            boiler_id INTEGER NOT NULL,
            sort_order INTEGER DEFAULT 0,

            col1 TEXT,
            col2 TEXT,
            col3 TEXT,
            col4 TEXT,
            col5 TEXT,
            col6 TEXT,
            col7 TEXT,
            col8 TEXT,
            col9 TEXT,
            col10 TEXT,
            col11 TEXT,
            col12 TEXT,
            col13 TEXT,
            col14 TEXT,
            col15 TEXT,
            col16 TEXT,
            col17 TEXT,
            col18 TEXT,
            col19 TEXT,
            col20 TEXT,
            col21 TEXT,
            col22 TEXT,
            col23 TEXT,
            col24 TEXT,
            col25 TEXT,
            col26 TEXT,
            col27 TEXT,
            col28 TEXT,
            col29 TEXT,
            col30 TEXT,
            col31 TEXT,
            col32 TEXT,
            col33 TEXT,
            col34 TEXT,
            col35 TEXT,
            col36 TEXT,
            col37 TEXT
        )
    """)

    # --- ADMIN ---
    cursor.execute("SELECT id FROM users WHERE username='admin'")
    if not cursor.fetchone():
        pwd = bcrypt.hashpw("1313".encode(), bcrypt.gensalt()).decode()
        cursor.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (%s,%s,%s)",
            ("admin", pwd, "admin")
        )

    conn.commit()
    conn.close()


# ===============================
# AUTH
# ===============================
def check_auth():
    return 'user_id' in session


def check_admin():
    if not check_auth():
        return False
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT role FROM users WHERE id=%s", (session['user_id'],))
    user = cur.fetchone()
    conn.close()
    return user and user['role'] == 'admin'


# ===============================
# ROUTES
# ===============================
@app.route('/')
def index():
    if not check_auth():
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM records ORDER BY boiler_id, sort_order, id")
    rows = cur.fetchall()

    cur.execute(
        "SELECT username, role FROM users WHERE id=%s",
        (session['user_id'],)
    )
    user = cur.fetchone()
    conn.close()

    records_grouped = []

    for boiler_id, boiler in BOILERS.items():
        boiler_rows = [r for r in rows if r['boiler_id'] == boiler_id]

        records_grouped.append({
            "boiler_name": boiler["name"],
            "address": boiler["address"],
            "records": boiler_rows
        })

    return render_template(
        'index.html',
        records_grouped=records_grouped,
        user=user
    )


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM users WHERE username=%s",
            (request.form['username'],)
        )
        user = cur.fetchone()
        conn.close()

        if user and bcrypt.checkpw(
            request.form['password'].encode(),
            user['password_hash'].encode()
        ):
            session['user_id'] = user['id']
            return redirect(url_for('index'))
        else:
            error = "Неверный логин или пароль"

    return render_template('login.html', error=error)


@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/update', methods=['POST'])
def update_cell():
    if not check_admin():
        return jsonify({"status": "error"})

    data = request.get_json()
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        f"UPDATE records SET {data['field']}=%s WHERE id=%s",
        (data['value'], data['id'])
    )

    conn.commit()
    conn.close()
    return jsonify({"status": "ok"})


@app.route('/add', methods=['POST'])
def add_row():
    if not check_admin():
        return jsonify({"status": "error"})

    conn = get_db_connection()
    cur = conn.cursor()

    last_boiler = max(BOILERS.keys())

    cur.execute(
        "SELECT COALESCE(MAX(sort_order),0)+1 AS n FROM records WHERE boiler_id=%s",
        (last_boiler,)
    )
    order = cur.fetchone()['n']

    cur.execute(
        "INSERT INTO records (boiler_id, sort_order) VALUES (%s,%s)",
        (last_boiler, order)
    )

    conn.commit()
    conn.close()
    return jsonify({"status": "ok"})


# ===============================
if __name__ == '__main__':
    ensure_tables_and_admin()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
