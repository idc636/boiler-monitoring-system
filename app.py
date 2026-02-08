from flask import Flask, render_template, request, jsonify, redirect, session, url_for
import psycopg2
from psycopg2.extras import RealDictCursor
import os

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
            password VARCHAR(128) NOT NULL,
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
            feed_pumps_repair TEXT,
            fuel_tanks_total TEXT,
            fuel_tank_volume TEXT,
            fuel_tanks_working TEXT,
            fuel_tanks_reserve TEXT,
            fuel_morning_balance TEXT,
            fuel_daily_consumption TEXT,
            fuel_tanks_repair TEXT,
            water_tanks_total TEXT,
            water_tank_volume TEXT,
            water_tanks_working TEXT,
            water_tanks_reserve TEXT,
            water_tanks_repair TEXT,
            temp_outdoor TEXT,
            temp_supply TEXT,
            temp_return TEXT,
            temp_graph_supply TEXT,
            temp_graph_return TEXT,
            pressure_supply TEXT,
            pressure_return TEXT,
            water_consumption_daily TEXT,
            staff_night TEXT,
            staff_day TEXT,
            notes TEXT
        );
    """)
    # Добавим тестового пользователя
    cur.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING", 
                ('admin', 'admin', 'admin'))
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
    boilers = []
    for r in records:
        boilers.append({
            "number": r["boiler_number"],
            "date": r["date"],
            "location": r["boiler_location"],
            "contact": r["boiler_contact"],
            "rows": 1,
            "times": [r["time_interval"]],
            "boiler_models": [r["boiler_model"]],
            "boilers": {"work": [r["boilers_working"]], "reserve": [r["boilers_reserve"]], "repair": r["boilers_repair"]},
            "network_pumps": {"work": [r["pumps_working"]], "reserve": [r["pumps_reserve"]], "repair": r["pumps_repair"]},
            "feed_pumps": {"work": [r["feed_pumps_working"]], "reserve": [r["feed_pumps_reserve"]], "repair": r["feed_pumps_repair"]},
            "fuel": {"total": r["fuel_tanks_total"], "volume": r["fuel_tank_volume"], "work": r["fuel_tanks_working"], 
                     "reserve": r["fuel_tanks_reserve"], "balance": r["fuel_morning_balance"], "daily": r["fuel_daily_consumption"], "repair": r["fuel_tanks_repair"]},
            "water": {"total": r["water_tanks_total"], "volume": r["water_tank_volume"], "work": r["water_tanks_working"], 
                      "reserve": r["water_tanks_reserve"], "repair": r["water_tanks_repair"]},
            "temps": [(r["temp_outdoor"], r["temp_supply"], r["temp_return"])],
            "graph_temps": [(r["temp_graph_supply"], r["temp_graph_return"])],
            "pressure": [(r["pressure_supply"], r["pressure_return"])],
            "water_consumption": r["water_consumption_daily"],
            "staff": {"night": r["staff_night"], "day": r["staff_day"]},
            "notes": r["notes"]
        })
    return boilers

# ===================== ROUTES =====================
@app.route('/')
def index():
    if not auth():
        return redirect(url_for('login'))
    c = get_conn().cursor()
    c.execute("SELECT * FROM records ORDER BY date, boiler_number, time_interval")
    records = c.fetchall()
    c.execute("SELECT username, role FROM users WHERE id=%s", (session['user_id'],))
    user = c.fetchone()
    c.connection.close()
    boilers = build_boilers_view(records)
    return render_template('index.html', boilers=boilers, user=user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        c = get_conn().cursor()
        c.execute("SELECT * FROM users WHERE username=%s", (request.form['username'],))
        u = c.fetchone()
        c.connection.close()
        if u and request.form['password'] == u['password']:
            session['user_id'] = u['id']
            return redirect(url_for('index'))
        else:
            error = 'Неверный логин или пароль'
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

# Добавление тестовой записи
@app.route('/add', methods=['POST'])
def add():
    if not admin():
        return jsonify({'status': 'error', 'message': 'Нет прав'})
    c = get_conn().cursor()
    c.execute("INSERT INTO records (date, boiler_number, boiler_location, boiler_contact, equipment_number, boiler_model, equipment_year, time_interval) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
              ('30.01.2026', 1, 'Белоярск', '83499323373', 1, 'Модель1', '2020', '00:00'))
    c.connection.commit()
    c.connection.close()
    return jsonify({'status': 'ok'})

# ===================== START =====================
if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
