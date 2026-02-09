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
        
        -- ДОБАВЛЕНО: таблица архива
        CREATE TABLE IF NOT EXISTS records_archive (
            id SERIAL PRIMARY KEY,
            archive_date DATE NOT NULL,
            original_id INTEGER,
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
        
        CREATE INDEX IF NOT EXISTS idx_records_archive_date ON records_archive(archive_date);
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
            "contact": rows[0]['boiler_contact'],
            "rows": len(rows),
            "years": years,
            "times": times,

            "boiler_models": col("boiler_model"),

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

            "fuel": {
                "total": rows[0]["fuel_tanks_total"],
                "volume": rows[0]["fuel_tank_volume"],
                "work": rows[0]["fuel_tanks_working"],
                "reserve": rows[0]["fuel_tanks_reserve"],
                "balance": rows[0]["fuel_morning_balance"],
                "daily": rows[0]["fuel_daily_consumption"],
                "repair": rows[0]["fuel_tanks_repair"]
            },

            "water": {
                "total": rows[0]["water_tanks_total"],
                "volume": rows[0]["water_tank_volume"],
                "work": rows[0]["water_tanks_working"],
                "reserve": rows[0]["water_tanks_reserve"],
                "repair": rows[0]["water_tanks_repair"]
            },

            "temps": list(zip(
                col("temp_outdoor"),
                col("temp_supply"),
                col("temp_return")
            )),

            "graph_temps": list(zip(
                col("temp_graph_supply"),
                col("temp_graph_return")
            )),

            "pressure": list(zip(
                col("pressure_supply"),
                col("pressure_return")
            )),

            "water_consumption": rows[0]["water_consumption_daily"],
            "staff": {
                "night": rows[0]["staff_night"],
                "day": rows[0]["staff_day"]
            },
            "notes": rows[0]["notes"]
        })

    return boilers
    def build_records_hierarchy(records):
    """Группировка записей по котельной и котлу, сортировка по времени"""
    hierarchy = {}

    for r in records:
        plant_key = f"Котельная №{r['boiler_number']} {r['boiler_location']}"
        boiler_key = r['boiler_model'] or f"Оборудование {r['equipment_number']}"

        if plant_key not in hierarchy:
            hierarchy[plant_key] = {}
        if boiler_key not in hierarchy[plant_key]:
            hierarchy[plant_key][boiler_key] = []

        hierarchy[plant_key][boiler_key].append(r)

    # сортируем по времени
    for plant in hierarchy:
        for boiler in hierarchy[plant]:
            hierarchy[plant][boiler].sort(key=lambda x: x['time_interval'] or '00:00')

    return hierarchy


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

hierarchy = build_records_hierarchy(records)
return render_template('index.html', hierarchy=hierarchy, user=user)


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
        return jsonify({'status': 'error', 'message': 'Нет прав'}), 403

    conn = get_conn()
    c = conn.cursor()

    try:
        # Проверяем, есть ли данные
        c.execute("SELECT COUNT(*) FROM records")
        count_before = c.fetchone()['count']

        if count_before == 0:
            return jsonify({
                'status': 'ok',
                'message': 'Таблица уже пустая'
            })

        # Архивируем
        c.execute("""
            INSERT INTO records_archive (
                archive_date,
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
                CURRENT_DATE,
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

        # Очищаем
        c.execute("DELETE FROM records")

        conn.commit()

        return jsonify({
            'status': 'ok',
            'message': f'Заархивировано и очищено записей: {count_before}'
        })

    except Exception as e:
        conn.rollback()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

    finally:
        conn.close()

    
    return jsonify({'status': 'ok', 'message': 'Архивация выполнена'})
# ⬆️ ДОБАВЬ ЭТОТ БЛОК СЮДА ⬆️

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
