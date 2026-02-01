from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import bcrypt

app = Flask(__name__)
app.secret_key = 'your-secret-key'

# Подключение к БД
DATABASE_URL = os.environ.get('DATABASE_URL') or "postgresql://postgres:TzhRuKuliqaGilBouUfRjGtqZnBnubMN@switchback.proxy.rlwy.net:57256/railway"

def ensure_tables():
    """Создаём таблицы при запуске"""
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    cursor = conn.cursor()
    
    # Таблица пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password_hash VARCHAR(128) NOT NULL,
            role VARCHAR(20) DEFAULT 'operator'
        )
    ''')
    
    # Таблица записей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS records (
            id SERIAL PRIMARY KEY,
            date TEXT NOT NULL,
            boiler_number INTEGER NOT NULL,
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
        )
    ''')
    
    # Создаём админа, если нет
    cursor.execute('SELECT id FROM users WHERE username = %s', ('admin',))
    if cursor.fetchone() is None:
        pwd = bcrypt.hashpw('1313'.encode('utf-8'), bcrypt.gensalt())
        cursor.execute('INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)', 
                      ('admin', pwd.decode('utf-8'), 'admin'))
        print('✅ Админ создан: admin / 1313')
    
    conn.commit()
    conn.close()


def get_db_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


def check_auth():
    return 'user_id' in session


def check_admin():
    if not check_auth():
        return False
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT role FROM users WHERE id = %s', (session['user_id'],))
    user = cursor.fetchone()
    conn.close()
    return user and user['role'] == 'admin'


@app.route('/')
def index():
    if not check_auth():
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM records ORDER BY id')
    records = cursor.fetchall()
    cursor.execute('SELECT username, role FROM users WHERE id = %s', (session['user_id'],))
    user = cursor.fetchone()
    conn.close()
    
    return render_template('index.html', records=records, user=user)


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
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
        
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            pwd_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            cursor.execute('INSERT INTO users (username, password_hash) VALUES (%s, %s)', (username, pwd_hash))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        except:
            conn.close()
            error = 'Логин уже занят'
    
    return render_template('register.html', error=error)


@app.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))


@app.route('/update', methods=['POST'])
def update():
    if not check_admin():
        return jsonify({'status': 'error', 'message': 'Нет прав'})
    
    data = request.get_json()
    field = data['field']
    value = data['value']
    record_id = data['id']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(f'UPDATE records SET {field} = %s WHERE id = %s', (value, record_id))
        conn.commit()
        conn.close()
        return jsonify({'status': 'ok'})
    except Exception as e:
        conn.close()
        return jsonify({'status': 'error', 'message': str(e)})


@app.route('/add', methods=['POST'])
def add():
    if not check_admin():
        return jsonify({'status': 'error', 'message': 'Нет прав'})
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO records (date, boiler_number, boiler_location, equipment_number, time_interval)
        VALUES (%s, %s, %s, %s, %s)
    ''', ('', 1, '', 1, ''))
    conn.commit()
    new_id = cursor.lastrowid if hasattr(cursor, 'lastrowid') else cursor.fetchone()['id']
    conn.close()
    return jsonify({'status': 'ok', 'new_id': new_id})


if __name__ == '__main__':
    ensure_tables()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
