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

        # Группируем по equipment_number (марка котла)
        equipment_groups = {}
        for r in rows:
            eq_num = r['equipment_number']
            equipment_groups.setdefault(eq_num, []).append(r)

        # Создаём структуру для каждой котельной
        boiler_data = {
            "number": boiler_number,
            "date": date,
            "location": rows[0]['boiler_location'],
            "contact": rows[0]['boiler_contact'],
            "models": []  # Список марок котлов
        }

        for eq_num in sorted(equipment_groups.keys()):
            eq_rows = equipment_groups[eq_num]
            
            # Информация о марке котла
            model_info = {
                "model": eq_rows[0]['boiler_model'],
                "year": eq_rows[0]['equipment_year'],
                "times": [r['time_interval'] for r in eq_rows],
                "boilers": {
                    "work": [r['boilers_working'] for r in eq_rows],
                    "reserve": [r['boilers_reserve'] for r in eq_rows],
                    "repair": eq_rows[0]['boilers_repair']
                },
                "pumps": {
                    "work": [r['pumps_working'] for r in eq_rows],
                    "reserve": [r['pumps_reserve'] for r in eq_rows],
                    "repair": eq_rows[0]['pumps_repair']
                },
                "feed_pumps": {
                    "work": [r['feed_pumps_working'] for r in eq_rows],
                    "reserve": [r['feed_pumps_reserve'] for r in eq_rows],
                    "repair": eq_rows[0]['feed_pumps_repair']
                },
                "temps": [(r['temp_outdoor'], r['temp_supply'], r['temp_return']) for r in eq_rows],
                "graph_temps": [(r['temp_graph_supply'], r['temp_graph_return']) for r in eq_rows],
                "pressure": [(r['pressure_supply'], r['pressure_return']) for r in eq_rows],
                "water_consumption": eq_rows[0]['water_consumption_daily'],
                "staff": {
                    "night": eq_rows[0]['staff_night'],
                    "day": eq_rows[0]['staff_day']
                },
                "notes": eq_rows[0]['notes']
            }
            
            boiler_data["models"].append(model_info)

        boilers.append(boiler_data)

    return boilers


# ===================== ROUTES =====================

@app.route('/')
def index():
    if not auth():
        return redirect(url_for('login'))
    
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
    error = None
    if request.method == 'POST':
        c = get_conn().cursor()
        c.execute("SELECT * FROM users WHERE username=%s", (request.form['username'],))
        u = c.fetchone()
        c.connection.close()

        # Простая проверка пароля (без хеширования)
        if u and request.form['password'] == u['password']:
            session['user_id'] = u['id']
            return redirect(url_for('index'))
        else:
            error = 'Неверный логин или пароль'

    # Показываем форму входа
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))


@app.route('/update', methods=['POST'])
def update():
    if not admin():
        return jsonify({'status': 'error', 'message': 'Нет прав'})

    d = request.get_json()
    
    # Безопасный список полей для обновления
    allowed_fields = [
        'boiler_model', 'equipment_year', 'time_interval',
        'boilers_working', 'boilers_reserve', 'boilers_repair',
        'pumps_working', 'pumps_reserve', 'pumps_repair',
        'feed_pumps_working', 'feed_pumps_reserve', 'feed_pumps_repair',
        'fuel_tanks_total', 'fuel_tank_volume', 'fuel_tanks_working',
        'fuel_tanks_reserve', 'fuel_morning_balance', 'fuel_daily_consumption',
        'fuel_tanks_repair', 'water_tanks_total', 'water_tank_volume',
        'water_tanks_working', 'water_tanks_reserve', 'water_tanks_repair',
        'temp_outdoor', 'temp_supply', 'temp_return',
        'temp_graph_supply', 'temp_graph_return',
        'pressure_supply', 'pressure_return',
        'water_consumption_daily', 'staff_night', 'staff_day', 'notes'
    ]

    if d['field'] not in allowed_fields:
        return jsonify({'status': 'error', 'message': 'Недопустимое поле'})

    c = get_conn().cursor()
    c.execute(f"UPDATE records SET {d['field']}=%s WHERE id=%s", (d['value'], d['id']))
    c.connection.commit()
    c.connection.close()
    return jsonify({'status': 'ok'})


@app.route('/add', methods=['POST'])
def add():
    if not admin():
        return jsonify({'status': 'error', 'message': 'Нет прав'})

    c = get_conn().cursor()
    c.execute("SELECT MAX(equipment_number) AS m FROM records WHERE boiler_number=1")
    num = (c.fetchone()['m'] or 0) + 1

    c.execute("""
        INSERT INTO records (
            date, boiler_number, boiler_location, boiler_contact,
            equipment_number, boiler_model, equipment_year, time_interval
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, ('30.01.2026', 1, 'Белоярск', '83499323373', num, '', '', '00:00'))

    c.connection.commit()
    c.connection.close()
    return jsonify({'status': 'ok'})


# ===================== START =====================
@app.route('/archive', methods=['POST'])
def archive():
    if not admin():
        return jsonify({'status': 'error', 'message': 'Нет прав'})

    c = get_conn().cursor()
    
    # Копируем все записи в архив
    c.execute("""
        INSERT INTO records_archive (
            original_id, date, boiler_number, boiler_location, boiler_contact,
            equipment_number, boiler_model, equipment_year, time_interval,
            boilers_working, boilers_reserve, boilers_repair,
            pumps_working, pumps_reserve, pumps_repair,
            feed_pumps_working, feed_pumps_reserve, feed_pumps_repair,
            fuel_tanks_total, fuel_tank_volume, fuel_tanks_working,
            fuel_tanks_reserve, fuel_morning_balance, fuel_daily_consumption, fuel_tanks_repair,
            water_tanks_total, water_tank_volume, water_tanks_working,
            water_tanks_reserve, water_tanks_repair,
            temp_outdoor, temp_supply, temp_return,
            temp_graph_supply, temp_graph_return,
            pressure_supply, pressure_return,
            water_consumption_daily, staff_night, staff_day, notes
        )
        SELECT 
            id, date, boiler_number, boiler_location, boiler_contact,
            equipment_number, boiler_model, equipment_year, time_interval,
            boilers_working, boilers_reserve, boilers_repair,
            pumps_working, pumps_reserve, pumps_repair,
            feed_pumps_working, feed_pumps_reserve, feed_pumps_repair,
            fuel_tanks_total, fuel_tank_volume, fuel_tanks_working,
            fuel_tanks_reserve, fuel_morning_balance, fuel_daily_consumption, fuel_tanks_repair,
            water_tanks_total, water_tank_volume, water_tanks_working,
            water_tanks_reserve, water_tanks_repair,
            temp_outdoor, temp_supply, temp_return,
            temp_graph_supply, temp_graph_return,
            pressure_supply, pressure_return,
            water_consumption_daily, staff_night, staff_day, notes
        FROM records
    """)
    
    # Очищаем значения в ячейках (оставляем структуру)
    c.execute("""
        UPDATE records SET
            time_interval = '',
            boilers_working = '',
            boilers_reserve = '',
            boilers_repair = '',
            pumps_working = '',
            pumps_reserve = '',
            pumps_repair = '',
            feed_pumps_working = '',
            feed_pumps_reserve = '',
            feed_pumps_repair = '',
            temp_outdoor = '',
            temp_supply = '',
            temp_return = '',
            temp_graph_supply = '',
            temp_graph_return = '',
            pressure_supply = '',
            pressure_return = '',
            water_consumption_daily = '',
            staff_night = '',
            staff_day = '',
            notes = ''
    """)
    
    c.connection.commit()
    c.connection.close()
    
    return jsonify({'status': 'ok', 'message': 'Данные успешно архивированы'})
    
    @app.route('/archive/view')
def view_archive():
    if not admin():
        return redirect(url_for('login'))
    
    c = get_conn().cursor()
    c.execute("""
        SELECT * FROM records_archive
        ORDER BY archive_date DESC, date DESC, boiler_number, time_interval
    """)
    records = c.fetchall()
    c.connection.close()
    
    return render_template('archive.html', records=records)
if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
