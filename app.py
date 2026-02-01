from flask import Flask, render_template, request, jsonify, redirect, session
import psycopg2
from psycopg2.extras import RealDictCursor
import os, bcrypt

app = Flask(__name__)
app.secret_key = 'secret'

DATABASE_URL = os.environ.get('DATABASE_URL') or \
    "postgresql://postgres:TzhRuKuliqaGilBouUfRjGtqZnBnubMN@switchback.proxy.rlwy.net:57256/railway"


# ===================== DB INIT =====================

def init_db():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL,
        password_hash VARCHAR(128) NOT NULL,
        role VARCHAR(20) DEFAULT 'operator'
    );

    CREATE TABLE IF NOT EXISTS records (
        id SERIAL PRIMARY KEY,
        date TEXT,
        boiler_number INTEGER,
        boiler_location TEXT,
        boiler_contact TEXT,

        equipment_number INTEGER,
        boiler_model TEXT,
        equipment_year TEXT,
        time_interval TEXT,

        boilers_working TEXT,
        boilers_reserve TEXT,
        boilers_repair TEXT,

        pumps_working TEXT,
        pumps_reserve TEXT,
        pumps_repair TEXT,

        feed_pumps_working TEXT,
        feed_pumps_reserve TEXT,
        feed_pumps_repair TEXT
    );
    """)

    cur.execute("""
    INSERT INTO users (username, password_hash, role)
    SELECT 'admin', %s, 'admin'
    WHERE NOT EXISTS (SELECT 1 FROM users WHERE username='admin')
    """, (bcrypt.hashpw('1313'.encode(), bcrypt.gensalt()).decode(),))

    conn.commit()
    conn.close()


def get_conn():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


def auth():
    return 'user_id' in session


def admin():
    if not auth():
        return False
    c = get_conn().cursor()
    c.execute("SELECT role FROM users WHERE id=%s", (session['user_id'],))
    r = c.fetchone()
    c.connection.close()
    return r and r['role'] == 'admin'


# ===================== DATA BUILDER =====================

def build_boilers_view(records):
    groups = {}

    for r in records:
        key = (r['date'], r['boiler_number'])
        groups.setdefault(key, []).append(r)

    boilers = []

    for (date, boiler_number), rows in groups.items():
        rows.sort(key=lambda x: x['time_interval'])

        times = [r['time_interval'] for r in rows]

        # ---- equipment years (rowspan)
        years = []
        last = None
        start = 0

        for i, r in enumerate(rows):
            y = r['equipment_year']
            if y != last:
                if last is not None:
                    years.append({
                        "year": last,
                        "start": start,
                        "span": i - start
                    })
                last = y
                start = i

        if last is not None:
            years.append({
                "year": last,
                "start": start,
                "span": len(rows) - start
            })

        def col(name):
            return [r[name] for r in rows]

        boilers.append({
            "number": boiler_number,
            "date": date,
            "location": rows[0]['boiler_location'],
            "rows": len(rows),
            "years": years,
            "times": times,

            "boilers": {
                "work": col("boilers_working"),
                "reserve": col("boilers_reserve"),
                "repair": rows[0]["boilers_repair"]
            },

            "network_pumps": {
                "work": col("pumps_working"),
                "reserve": col("pumps_reserve"),
                "repair": rows[0]["pumps_repair"]
            },

            "feed_pumps": {
                "work": col("feed_pumps_working"),
                "reserve": col("feed_pumps_reserve"),
                "repair": rows[0]["feed_pumps_repair"]
            },

            # пока пустые — структура готова
            "fuel": {"total": "", "volume": "", "work": "", "reserve": "", "balance": "", "daily": "", "repair": ""},
            "water": {"total": "", "volume": "", "work": "", "reserve": "", "repair": ""},

            "temps": [("", "", "") for _ in rows],
            "water_consumption": "",
            "staff": {"night": "", "day": ""},
            "notes": ""
        })

    return boilers


# ===================== ROUTES =====================

@app.route('/')
def index():
    if not auth():
        return redirect('/login')

    c = get_conn().cursor()
    c.execute("""
        SELECT * FROM records
        ORDER BY date, boiler_number, time_interval
    """)
    records = c.fetchall()

    c.execute("SELECT username, role FROM users WHERE id=%s", (session['user_id'],))
    user = c.fetchone()
    c.connection.close()

    boilers = build_boilers_view(records)

    return render_template('index.html', boilers=boilers, user=user)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        c = get_conn().cursor()
        c.execute("SELECT * FROM users WHERE username=%s", (request.form['username'],))
        u = c.fetchone()
        c.connection.close()

        if u and bcrypt.checkpw(request.form['password'].encode(), u['password_hash'].encode()):
            session['user_id'] = u['id']
            return redirect('/')

        return render_template('login.html', error='Неверный логин или пароль')

    return render_template('login.html')


@app.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return redirect('/login')


@app.route('/update', methods=['POST'])
def update():
    if not admin():
        return jsonify({'status': 'error'})

    d = request.get_json()
    c = get_conn().cursor()
    c.execute(f"UPDATE records SET {d['field']}=%s WHERE id=%s", (d['value'], d['id']))
    c.connection.commit()
    c.connection.close()
    return jsonify({'status': 'ok'})


@app.route('/add', methods=['POST'])
def add():
    if not admin():
        return jsonify({'status': 'error'})

    c = get_conn().cursor()
    c.execute("SELECT MAX(equipment_number) AS m FROM records WHERE boiler_number=1")
    num = (c.fetchone()['m'] or 0) + 1

    c.execute("""
        INSERT INTO records (date, boiler_number, boiler_location, boiler_contact,
                             equipment_number, time_interval)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, ('30.01.2026', 1, 'Белоярск', '83499323373', num, '00:00'))

    c.connection.commit()
    c.connection.close()
    return jsonify({'status': 'ok'})


# ===================== START =====================

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
