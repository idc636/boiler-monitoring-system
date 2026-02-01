from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import bcrypt
import traceback

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'

# Подключение к PostgreSQL
DATABASE_URL = os.environ.get('DATABASE_URL') or "postgresql://postgres:TzhRuKuliqaGilBouUfRjGtqZnBnubMN@postgres.railway.internal:5432/railway"

def ensure_tables_and_admin():
    """Создаём таблицы и админа, если их нет"""
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        cursor = conn.cursor()
    except Exception:
        print("❌ Ошибка подключения к БД:")
        print(traceback.format_exc())
        return

    # Таблица пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password_hash VARCHAR(128) NOT NULL,
            role VARCHAR(20) DEFAULT 'operator',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Таблица записей (котельные)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS records (
            id SERIAL PRIMARY KEY,
            date TEXT NOT NULL,
            boiler_number INTEGER NOT NULL,
            boiler_location TEXT NOT NULL,
            boiler_contact TEXT,
            equipment_number INTEGER NOT NULL,
            boiler_model TEXT,
            burner_model TEXT,
            equipment_year TEXT,
            time_interval TEXT NOT NULL,
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
        )
    ''')

    # Проверяем, есть ли админ
    cursor.execute('SELECT id FROM users WHERE username = %s', ('admin',))
    if cursor.fetchone() is None:
        admin_password = bcrypt.hashpw('1313'.encode('utf-8'), bcrypt.gensalt())
        cursor.execute(
            'INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)',
            ('admin', admin_password.decode('utf-8'), 'admin')
        )
        print('✅ Администратор создан: login=admin, password=1313')

    conn.commit()
    conn.close()


def get_db_connection():
    try:
        return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    except Exception:
        print("❌ Ошибка подключения к БД:")
        print(traceback.format_exc())
        return None


def check_auth():
    if 'user_id' not in session:
        return False
    conn = get_db_connection()
    if not conn:
        return False
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT id FROM users WHERE id = %s', (session['user_id'],))
        return cursor.fetchone() is not None
    finally:
        conn.close()


def check_role(required_role):
    if not check_auth():
        return False
    conn = get_db_connection()
    if not conn:
        return False
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT role FROM users WHERE id = %s', (session['user_id'],))
        user = cursor.fetchone()
        if user:
            if required_role == 'admin':
                return user['role'] == 'admin'
            return True
        return False
    finally:
        conn.close()


@app.route('/')
def index():
    if not check_auth():
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Запрос всех записей
    cursor.execute('SELECT * FROM records ORDER BY date, boiler_number, time_interval')
    records = cursor.fetchall()
    conn.close()

    # Группируем данные по котельным
    grouped = {}
    for record in records:
        key = f"{record['date']}|{record['boiler_number']}"
        if key not in grouped:
            grouped[key] = {
                'date': record['date'],
                'boiler_number': record['boiler_number'],
                'boiler_location': record['boiler_location'],
                'boiler_contact': record['boiler_contact'],
                'entries': []
            }
        grouped[key]['entries'].append(record)
    
    # Переводим в список для шаблона
    grouped_list = list(grouped.values())

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT username, role FROM users WHERE id=%s', (session['user_id'],))
    user = cursor.fetchone()
    conn.close()

    return render_template('index.html', grouped=grouped_list, user=user)


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username=%s', (username,))
        user = cursor.fetchone()
        conn.close()

        if user and bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
            session['user_id'] = user['id']
            return redirect(url_for('index'))
        else:
            error = 'Неверный логин или пароль'

    return render_template('login.html', error=error)


@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            error = 'Пароли не совпадают'
        else:
            conn = get_db_connection()
            cursor = conn.cursor()
            try:
                password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                cursor.execute('INSERT INTO users (username, password_hash) VALUES (%s, %s)', (username, password_hash))
                conn.commit()
                conn.close()
                return redirect(url_for('login'))
            except Exception:
                conn.close()
                error = 'Логин уже занят'

    return render_template('register.html', error=error)


@app.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))


@app.route('/update', methods=['POST'])
def update_cell():
    if not check_role('admin'):
        return jsonify({'status': 'error', 'message': 'Нет прав'})

    data = request.get_json()
    field = data['field']
    value = data['value']
    record_id = data['id']

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(f'UPDATE records SET {field}=%s WHERE id=%s', (value, record_id))
        conn.commit()
    except Exception as e:
        print(e)
        conn.close()
        return jsonify({'status': 'error'})
    conn.close()
    return jsonify({'status': 'ok'})


@app.route('/add', methods=['POST'])
def add_record():
    if not check_role('admin'):
        return jsonify({'status': 'error', 'message': 'Нет прав'})

    conn = get_db_connection()
    cursor = conn.cursor()
    # Добавляем пустую строку с минимальными данными
    cursor.execute('''
        INSERT INTO records (date, boiler_number, boiler_location, equipment_number, time_interval)
        VALUES ('', 1, '', 1, '')
    ''')
    conn.commit()
    new_id = cursor.lastrowid if hasattr(cursor, 'lastrowid') else cursor.fetchone()['id'] if cursor.fetchone() else 1
    conn.close()
    return jsonify({'status': 'ok', 'new_id': new_id})


if __name__ == '__main__':
    ensure_tables_and_admin()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
