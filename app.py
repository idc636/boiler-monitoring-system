from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import bcrypt
import traceback

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'

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
        admin_password = bcrypt.hashpw('1234'.encode('utf-8'), bcrypt.gensalt())
        cursor.execute(
            'INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)',
            ('admin', admin_password.decode('utf-8'), 'admin')
        )
        print('✅ Администратор создан: login=admin, password=1234')

    # Загружаем данные Excel только если таблица records пустая
    cursor.execute('SELECT COUNT(*) AS cnt FROM records')
    if cursor.fetchone()['cnt'] == 0:
        print('📦 Загружаем данные из Excel...')
        demo_data = [
            # Котельная №1
            ("30.01.2026", 1, "Белоярск №1 ул. Набережная 8", "83499323373 , сот. 89028575790, Начальник участка ЦТС Климов И.В.", 1, "КСВ-3,0/PG93 \"UNIGAS\" №0805505", "", "2007", "00.00", "1,3", "2", "", "1,2,4", "", "3", "1", "2", "", "2", "25", "1,2", "", "16008", "6031", "", "1", "50", "1", "", "", "-34", "86", "64", "86", "64,5", "5,5", "3,8", "0", "Витязев, Кожевников", "Канев Нагибин", ""),
            ("30.01.2026", 1, "Белоярск №1 ул. Набережная 8", "83499323373 , сот. 89028575790, Начальник участка ЦТС Климов И.В.", 1, "КСВ-3,0/PG93 \"UNIGAS\" №0805505", "", "2007", "03.00", "1,3", "2", "", "1,2,4", "", "1", "2", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "-36", "88", "67", "88", "65,8", "5,5", "3,8", "", "", "", ""),
            ("30.01.2026", 1, "Белоярск №1 ул. Набережная 8", "83499323373 , сот. 89028575790, Начальник участка ЦТС Климов И.В.", 1, "КСВ-3,0/PG93 \"UNIGAS\" №0805505", "", "2007", "06.00", "1,3", "2", "", "1,2,4", "", "1", "2", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "-37", "89", "66", "89", "66,4", "5,5", "3,8", "", "", "", ""),
            # Добавь сюда все остальные строки Excel по аналогии
        ]
        for row in demo_data:
            cursor.execute('''
                INSERT INTO records (
                    date, boiler_number, boiler_location, boiler_contact,
                    equipment_number, boiler_model, burner_model, equipment_year, time_interval,
                    boilers_working, boilers_reserve, boilers_repair,
                    pumps_working, pumps_reserve, pumps_repair,
                    feed_pumps_working, feed_pumps_reserve, feed_pumps_repair,
                    fuel_tanks_total, fuel_tank_volume, fuel_tanks_working, fuel_tanks_reserve,
                    fuel_morning_balance, fuel_daily_consumption, fuel_tanks_repair,
                    water_tanks_total, water_tank_volume, water_tanks_working, water_tanks_reserve, water_tanks_repair,
                    temp_outdoor, temp_supply, temp_return,
                    temp_graph_supply, temp_graph_return,
                    pressure_supply, pressure_return,
                    water_consumption_daily,
                    staff_night, staff_day, notes
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', row)
        print(f'✅ Загружено {len(demo_data)} строк данных.')

    conn.commit()
    conn.close()

def get_db_connection():
    try:
        return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    except Exception:
        print("❌ Ошибка подключения к БД:")
        print(traceback.format_exc())
        return None

# Проверка авторизации
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

# Проверка роли
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

# Инициализация
ensure_tables_and_admin()

# Дальше — маршруты: index, login, register, logout, update_cell
# Их можно взять из твоего старого кода, они будут работать с этим app
