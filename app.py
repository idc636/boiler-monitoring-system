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

def get_db_connection():
    try:
        return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    except Exception:
        print("❌ Ошибка подключения к БД:")
        print(traceback.format_exc())
        return None

def ensure_tables_and_admin():
    """Создаём таблицы и админа, если их нет"""
    conn = get_db_connection()
    if not conn:
        return
    cursor = conn.cursor()
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
    # Создаём админа если нет
    cursor.execute("SELECT id FROM users WHERE username = 'admin'")
    if cursor.fetchone() is None:
        password_hash = bcrypt.hashpw("1234".encode('utf-8'), bcrypt.gensalt())
        cursor.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)",
            ('admin', password_hash.decode('utf-8'), 'admin')
        )
        print("✅ Админ создан: login=admin, password=1234")

    conn.commit()
    conn.close()


# --- Аутентификация и роли ---
def check_auth():
    return 'user_id' in session

def current_user():
    if not check_auth():
        return None
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, role FROM users WHERE id = %s", (session['user_id'],))
    user = cursor.fetchone()
    conn.close()
    return user

def require_admin(f):
    def wrapper(*args, **kwargs):
        user = current_user()
        if not user or user['role'] != 'admin':
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper


# --- Маршруты ---
@app.route('/')
def index():
    if not check_auth():
        return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM records ORDER BY id")
    records = cursor.fetchall()
    conn.close()
    user = current_user()
    return render_template('index.html', records=records, user=user)

@app.route('/update', methods=['POST'])
@require_admin
def update_cell():
    data = request.json
    field = data.get('field')
    value = data.get('value')
    record_id = data.get('id')
    allowed_fields = [
        "boilers_working","boilers_reserve","boilers_repair",
        "pumps_working","pumps_reserve","pumps_repair",
        "feed_pumps_working","feed_pumps_reserve","feed_pumps_repair",
        "fuel_tanks_total","fuel_tank_volume","fuel_tanks_working","fuel_tanks_reserve",
        "fuel_morning_balance","fuel_daily_consumption","fuel_tanks_repair",
        "water_tanks_total","water_tank_volume","water_tanks_working","water_tanks_reserve","water_tanks_repair",
        "temp_outdoor","temp_supply","temp_return","temp_graph_supply","temp_graph_return",
        "pressure_supply","pressure_return","water_consumption_daily",
        "staff_night","staff_day","notes"
    ]
    if field not in allowed_fields:
        return jsonify({"status":"error","msg":"Поле недоступно для редактирования"})
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"UPDATE records SET {field}=%s WHERE id=%s", (value, record_id))
    conn.commit()
    conn.close()
    return jsonify({"status":"ok"})

@app.route('/login', methods=['GET','POST'])
def login():
    error = None
    if request.method=='POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
        user = cursor.fetchone()
        conn.close()
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
            session['user_id'] = user['id']
            return redirect(url_for('index'))
        else:
            error = 'Неверный логин или пароль'
    return render_template('login.html', error=error)

@app.route('/register', methods=['GET','POST'])
def register():
    error = None
    if request.method=='POST':
        username = request.form['username']
        password = request.form['password']
        confirm = request.form['confirm_password']
        if password != confirm:
            error = "Пароли не совпадают"
        else:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE username=%s", (username,))
            if cursor.fetchone():
                error = "Пользователь уже существует"
            else:
                hash_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                cursor.execute(
                    "INSERT INTO users (username,password_hash) VALUES (%s,%s)",
                    (username, hash_pw.decode('utf-8'))
                )
                conn.commit()
                conn.close()
                return redirect(url_for('login'))
            conn.close()
    return render_template('register.html', error=error)

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/add_row', methods=['POST'])
@require_admin
def add_row():
    """Добавление новой строки котельной"""
    conn = get_db_connection()
    cursor = conn.cursor()
    # вставляем пустую строку (значения можно редактировать)
    cursor.execute('''
        INSERT INTO records (
            date, boiler_number, boiler_location, boiler_contact, equipment_number, 
            boiler_model, burner_model, equipment_year, time_interval
        ) VALUES (CURRENT_DATE, 0, '', '', 0, '', '', '', '')
    ''')
    conn.commit()
    conn.close()
    return redirect(url_for('index'))


if __name__ == "__main__":
    ensure_tables_and_admin()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
