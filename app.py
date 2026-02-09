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

    CREATE TABLE IF NOT EXISTS records_archive (
        id SERIAL PRIMARY KEY,
        archive_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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
    """)

    # Создаём админов и операторов
    admin_password = '1313'
    user_password = '1313'
    
    cur.execute("""
    INSERT INTO users (username, password, role)
    SELECT 'admin', %s, 'admin'
    WHERE NOT EXISTS (SELECT 1 FROM users WHERE username='admin')
    """, (admin_password,))
    
    cur.execute("""
    INSERT INTO users (username, password, role)
    SELECT 'admin2', %s, 'admin'
    WHERE NOT EXISTS (SELECT 1 FROM users WHERE username='admin2')
    """, (admin_password,))

    for i in range(1, 9):
        cur.execute("""
        INSERT INTO users (username, password, role)
        SELECT %s, %s, 'operator'
        WHERE NOT EXISTS (SELECT 1 FROM users WHERE username=%s)
        """, (f'user{i}', user_password, f'user{i}'))

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


# ===================== ROUTES =====================

@app.route('/')
def index():
    if not auth():
        return redirect(url_for('login'))
    
    c = get_conn().cursor()
    c.execute("""
        SELECT * FROM records
        ORDER BY date, boiler_number, equipment_number, time_interval
    """)
    records = c.fetchall()

    c.execute("SELECT username, role FROM users WHERE id=%s", (session['user_id'],))
    user = c.fetchone()
    c.connection.close()

    # Преобразуем данные в структуру, подходящую для index.html
    data = {}
    for r in records:
        key = r['id']  # Используем id записи как ключ для data-id
        data[key] = r
    print("Data keys:", list(data.keys()))
    return render_template('index.html', data=data, user=user)


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
    c.execute("SELECT MAX(id) AS m FROM records")
    new_id = (c.fetchone()['m'] or 0) + 1

    c.execute("""
        INSERT INTO records (
            date, boiler_number, boiler_location, boiler_contact,
            equipment_number, boiler_model, equipment_year, time_interval
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, ('30.01.2026', 1, 'Белоярск', '83499323373', 1, '', '', '00:00'))

    c.connection.commit()
    c.connection.close()
    return jsonify({'status': 'ok'})


@app.route('/archive', methods=['POST'])
def archive():
    if not admin():
        return jsonify({'status': 'error', 'message': 'Нет прав'})

    c = get_conn().cursor()
    
    try:
        # Копируем в архив (включая burner_model)
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
        
        # Очищаем ВСЕ ячейки
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
                fuel_tanks_total = '',
                fuel_tank_volume = '',
                fuel_tanks_working = '',
                fuel_tanks_reserve = '',
                fuel_morning_balance = '',
                fuel_daily_consumption = '',
                fuel_tanks_repair = '',
                water_tanks_total = '',
                water_tank_volume = '',
                water_tanks_working = '',
                water_tanks_reserve = '',
                water_tanks_repair = '',
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
        return jsonify({'status': 'ok', 'message': 'Данные архивированы'})
    
    except Exception as e:
        c.connection.rollback()
        c.connection.close()
        return jsonify({'status': 'error', 'message': str(e)})


@app.route('/archive/view')
def view_archive():
    if not admin():
        return redirect(url_for('login'))
    
    c = get_conn().cursor()
    # Получаем уникальные даты архивации
    c.execute("""
        SELECT DISTINCT archive_date 
        FROM records_archive 
        ORDER BY archive_date DESC
    """)
    dates = c.fetchall()
    
    c.connection.close()
    
    return render_template('archive_dates.html', dates=dates)


@app.route('/archive/data/<date>')
def archive_data(date):
    if not admin():
        return redirect(url_for('login'))
    
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
        SELECT * FROM records_archive 
        WHERE archive_date::date = %s
        ORDER BY date, boiler_number, equipment_number, time_interval
    """, (date,))

    records = c.fetchall()
    conn.close()
    
    data = {r['original_id']: r for r in records}
    return render_template('archive_table.html', data=data, selected_date=date)


# ===================== START =====================
if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
