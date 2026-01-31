from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import bcrypt
import traceback

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'

# Подключение к PostgreSQL
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:TzhRuKuliqaGilBouUfRjGtqZnBnubMN@postgres.railway.internal:5432/railway')

def ensure_tables_and_admin():
    """Создаем таблицы и админа, если их нет"""
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

    # Таблица записей котельных
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS records (
            id SERIAL PRIMARY KEY,
            date TEXT,
            boiler_number INTEGER,
            boiler_location TEXT,
            boiler_contact TEXT,
            equipment_number INTEGER,
            boiler_model TEXT,
            burner_model TEXT,
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
        )
    ''')

    # Проверка на администратора
    cursor.execute('SELECT id FROM users WHERE username=%s', ('admin',))
    if cursor.fetchone() is None:
        admin_password = bcrypt.hashpw('1234'.encode('utf-8'), bcrypt.gensalt())
        cursor.execute('''
            INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)
        ''', ('admin', admin_password.decode('utf-8'), 'admin'))
        print("✅ Создан администратор: login=admin, password=1234")

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
    cursor.execute('SELECT id FROM users WHERE id=%s', (session['user_id'],))
    return cursor.fetchone() is not None

def check_admin():
    if not check_auth():
        return False
    conn = get_db_connection()
    if not conn:
        return False
    cursor = conn.cursor()
    cursor.execute('SELECT role FROM users WHERE id=%s', (session['user_id'],))
    user = cursor.fetchone()
    return user and user['role'] == 'admin'

@app.route('/')
def index():
    if not check_auth():
        return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM records ORDER BY id')
    records = cursor.fetchall()
    cursor.execute('SELECT username, role FROM users WHERE id=%s', (session['user_id'],))
    user = cursor.fetchone()
    conn.close()
    return render_template('index.html', records=records, user=user, is_admin=check_admin())

@app.route('/update', methods=['POST'])
def update_cell():
    if not check_admin():
        return jsonify({'status': 'error', 'message': 'Нет прав'})

    data = request.json
    field = data.get('field')
    value = data.get('value')
    record_id = data.get('id')

    if not field or not record_id:
        return jsonify({'status': 'error', 'message': 'Некорректные данные'})

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(f'UPDATE records SET {field}=%s WHERE id=%s', (value, record_id))
        conn.commit()
        return jsonify({'status': 'ok'})
    except Exception as e:
        print(e)
        return jsonify({'status': 'error', 'message': 'Ошибка БД'})
    finally:
        conn.close()

@app.route('/add_record', methods=['POST'])
def add_record():
    if not check_admin():
        return jsonify({'status': 'error', 'message': 'Нет прав'})

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO records (date, boiler_number, boiler_location, equipment_number, time_interval)
        VALUES (CURRENT_DATE::text, 0, '', 0, '')
        RETURNING id
    ''')
    record_id = cursor.fetchone()['id']
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok', 'id': record_id})

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
        confirm = request.form['confirm_password']
        if password != confirm:
            error = 'Пароли не совпадают'
        else:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM users WHERE username=%s', (username,))
            if cursor.fetchone():
                error = 'Пользователь уже существует'
            else:
                password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                cursor.execute('INSERT INTO users (username, password_hash) VALUES (%s, %s)', (username, password_hash.decode('utf-8')))
                conn.commit()
            conn.close()
            if not error:
                return redirect(url_for('login'))
    return render_template('register.html', error=error)

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    ensure_tables_and_admin()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)), debug=True)
