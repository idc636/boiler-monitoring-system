from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import bcrypt

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'

# Подключение к PostgreSQL
DATABASE_URL = os.environ.get('DATABASE_URL')

def ensure_tables_and_admin():
    """Гарантирует, что таблицы и админ существуют"""
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
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
    cursor.execute('SELECT id, password_hash FROM users WHERE username = %s', ('admin',))
    admin_user = cursor.fetchone()
    
    if admin_user is None:
        # Создаём админа
        admin_password = bcrypt.hashpw('1234'.encode('utf-8'), bcrypt.gensalt())
        cursor.execute(
            'INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)',
            ('admin', admin_password.decode('utf-8'), 'admin')
        )
        print('✅ Администратор создан: login=admin, password=1234')
    else:
        # Проверим, правильный ли у него пароль
        expected_hash = bcrypt.hashpw('1234'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        if admin_user['password_hash'] != expected_hash:
            # Обновим пароль, если неправильный
            admin_password = bcrypt.hashpw('1234'.encode('utf-8'), bcrypt.gensalt())
            cursor.execute(
                'UPDATE users SET password_hash = %s WHERE username = %s',
                (admin_password.decode('utf-8'), 'admin')
            )
            print('🔐 Пароль администратора обновлён')
    
    # Проверяем, есть ли записи
    cursor.execute('SELECT COUNT(*) FROM records')
    count = cursor.fetchone()['count']
    
    if count == 0:
        # Загружаем демо-данные из Excel
        demo_data = [
            # Котельная №1 (Белоярск №1 ул. Набережная 8)
            ("30.01.2026", 1, "Белоярск №1 ул. Набережная 8", "83499323373 , сот. 89028575790, Начальниу участка ЦТС Климов И.В.89519857336", 1, "КСВ-3,0/PG93 \"UNIGAS\" №0805505", "", "2007", "00:00", "1.3", "2", "", "1,2,4", "", "3", "1", "2", "", "2", "25", "1.2", "", "16008", "6031", "", "1", "50", "1", "", "", "-34", "86", "64", "86", "64.5", "5.5", "3.8", "0", "Витязев, Кожевников", "Канев Нагибин", ""),
            ("30.01.2026", 1, "Белоярск №1 ул. Набережная 8", "83499323373 , сот. 89028575790, Начальниу участка ЦТС Климов И.В.89519857336", 1, "КСВ-3,0/PG93 \"UNIGAS\" №0805505", "", "2007", "03:00", "1.3", "2", "", "1,2,4", "", "", "1", "2", "", "", "", "", "", "", "", "", "", "", "", "", "", "-36", "88", "67", "88", "65.8", "5.5", "3.8", "", "", "", ""),
            ("30.01.2026", 1, "Белоярск №1 ул. Набережная 8", "83499323373 , сот. 89028575790, Начальниу участка ЦТС Климов И.В.89519857336", 1, "КСВ-3,0/PG93 \"UNIGAS\" №0805505", "", "2007", "06:00", "1.3", "2", "", "1,2,4", "", "", "1", "2", "", "", "", "", "", "", "", "", "", "", "", "", "", "-37", "89", "66", "89", "66.4", "5.5", "3.8", "", "", "", ""),
            ("30.01.2026", 1, "Белоярск №1 ул. Набережная 8", "83499323373 , сот. 89028575790, Начальниу участка ЦТС Климов И.В.89519857336", 2, "\"КИМАП-ИПАК\" -3,5/\"WEUSHAUPT\"", "", "2016", "09:00", "1.3", "2", "", "1,2,4", "", "", "1", "2", "", "", "", "", "", "", "", "", "", "", "", "", "", "-36", "88", "65", "88", "65.8", "5.5", "3.8", "", "", "", ""),
            ("30.01.2026", 1, "Белоярск №1 ул. Набережная 8", "83499323373 , сот. 89028575790, Начальниу участка ЦТС Климов И.В.89519857336", 2, "\"КИМАП-ИПАК\" -3,5/\"WEUSHAUPT\"", "", "2016", "12:00", "1.3", "2", "", "1,2,4", "", "", "1", "2", "", "", "", "", "", "", "", "", "", "", "", "", "", "-36", "88", "65", "88", "65.8", "5.5", "3.8", "", "", "", ""),
            ("30.01.2026", 1, "Белоярск №1 ул. Набережная 8", "83499323373 , сот. 89028575790, Начальниу участка ЦТС Климов И.В.89519857336", 3, "КВА 3,2/PG93\"UNIGAS\"№06140440", "", "2010", "15:00", "1.3", "2", "", "1,2,4", "", "", "1", "2", "", "", "", "", "", "", "", "", "", "", "", "", "", "-36", "88", "65", "88", "65.8", "5.5", "3.8", "", "", "", ""),
            ("30.01.2026", 1, "Белоярск №1 ул. Набережная 8", "83499323373 , сот. 89028575790, Начальниу участка ЦТС Климов И.В.89519857336", 3, "КВА 3,2/PG93\"UNIGAS\"№06140440", "", "2010", "18:00", "1.3", "2", "", "1,2,4", "", "", "1", "2", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "5.5", "3.8", "", "", "", ""),
            ("30.01.2026", 1, "Белоярск №1 ул. Набережная 8", "83499323373 , сот. 89028575790, Начальниу участка ЦТС Климов И.В.89519857336", 3, "КВА 3,2/PG93\"UNIGAS\"№06140440", "", "2010", "21:00", "1.3", "2", "", "1,2,4", "", "", "1", "2", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "5.5", "3.8", "", "", "", ""),
            
            # Котельная №2 (Белоярск №2 ул. Юбилейная 11)
            ("30.01.2026", 2, "Белоярск №2 ул. Юбилейная 11", "83499323387 , сот. 89028575687,", 1, "KBA-3,2/PG93\"UNIGAS\"№1009117", "", "2010", "00:00", "2,3,4", "1", "", "2,3,4", "1", "", "2", "1", "", "2", "25", "1.2", "", "17589", "12023", "-", "1", "50", "1", "", "", "-35", "87", "65", "87", "65.2", "5.5", "4.5", "10", "Витязев, Лаптандер", "Терентеев Подронхасов", ""),
            ("30.01.2026", 2, "Белоярск №2 ул. Юбилейная 11", "83499323387 , сот. 89028575687,", 1, "KBA-3,2/PG93\"UNIGAS\"№1009117", "", "2010", "03:00", "2,3,4", "1", "", "2,3,4", "1", "", "2", "1", "", "", "", "", "", "", "", "", "", "", "", "", "", "-36", "88", "66", "88", "65.8", "5.5", "4.5", "", "", "", ""),
            ("30.01.2026", 2, "Белоярск №2 ул. Юбилейная 11", "83499323387 , сот. 89028575687,", 2, "KBA-3,0/PG510\"UNIGAS\"", "", "2007", "06:00", "2,3,4", "1", "", "2,3,4", "1", "", "2", "1", "", "", "", "", "", "", "", "", "", "", "", "", "", "-35", "87", "66", "87", "65.2", "3.8", "4.5", "", "", "", "выкл 4"),
            ("30.01.2026", 2, "Белоярск №2 ул. Юбилейная 11", "83499323387 , сот. 89028575687,", 2, "KBA-3,0/PG510\"UNIGAS\"", "", "2007", "09:00", "2,3,4", "1", "", "2,3,4", "1", "", "2", "1", "", "", "", "", "", "", "", "", "", "", "", "", "", "-37", "89", "67", "89", "66.4", "5.5", "4.5", "", "", "", ""),
            ("30.01.2026", 2, "Белоярск №2 ул. Юбилейная 11", "83499323387 , сот. 89028575687,", 3, "KCBA-3,0/PG510\"UNIGAS\"", "", "2004", "12:00", "2,3,4", "1", "", "2,3,4", "1", "", "2", "1", "", "", "", "", "", "", "", "", "", "", "", "", "", "-34", "86", "65", "86", "64.5", "5.5", "4.5", "", "", "", ""),
            ("30.01.2026", 2, "Белоярск №2 ул. Юбилейная 11", "83499323387 , сот. 89028575687,", 3, "KCBA-3,0/PG510\"UNIGAS\"", "", "2004", "15:00", "2,3,4", "1", "", "2,3,4", "1", "", "2", "1", "", "", "", "", "", "", "", "", "", "", "", "", "", "-34", "86", "65", "86", "64.5", "5.5", "4.5", "", "", "", ""),
            ("30.01.2026", 2, "Белоярск №2 ул. Юбилейная 11", "83499323387 , сот. 89028575687,", 4, "KCBA-3,0/PG510\"UNIGAS\"", "", "2005", "18:00", "2,3,4", "1", "", "2,3,4", "1", "", "2", "1", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "5.5", "4.5", "", "", "", ""),
            ("30.01.2026", 2, "Белоярск №2 ул. Юбилейная 11", "83499323387 , сот. 89028575687,", 4, "KCBA-3,0/PG510\"UNIGAS\"", "", "2005", "21:00", "2,3,4", "1", "", "2,3,4", "1", "", "2", "1", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "5.5", "4.5", "", "", "", ""),
            
            # Котельная №3 (Щучье №3)
            ("30.01.2026", 3, "Щучье №3", "", 1, "Thermax Revoterm -2,68 Гкал", "", "", "00:00", "1", "2", "", "4", "1,2,3,5", "", "3", "1,2,4", "", "1", "1.2", "1", "1", "-", "2130", "0,2", "4", "4/100", "1/1000", "", "", "", "-42", "95", "70", "94", "69.4", "4.2", "3", "0.1", "Варцапов", "Худи", ""),
            ("30.01.2026", 3, "Щучье №3", "", 1, "Thermax Revoterm -2,68 Гкал", "", "", "03:00", "1", "2", "", "4", "1,2,3,5", "", "3", "1,2,4", "", "", "", "", "", "", "", "", "", "", "", "", "", "-42", "95", "70", "94", "69.4", "4.2", "3", "", "", "", ""),
            ("30.01.2026", 3, "Щучье №3", "", 1, "Thermax Revoterm -2,68 Гкал", "", "", "06:00", "1", "2", "", "4", "1,2,3,5", "", "3", "1,2,4", "", "", "", "", "", "", "", "", "", "", "", "", "", "-44", "95", "70", "94", "69.4", "4.2", "3", "", "", "", "Худи 89004029551"),
            ("30.01.2026", 3, "Щучье №3", "", 1, "Thermax Revoterm -2,68 Гкал", "", "", "09:00", "1", "2", "", "4", "1,2,3,5", "", "3", "1,2,4", "", "", "", "", "", "", "", "", "", "", "", "", "", "-44", "95", "70", "95", "70", "4.2", "3", "", "", "", ""),
            ("30.01.2026", 3, "Щучье №3", "", 2, "Thermax Revoterm -2,68 Гкал", "", "1985", "12:00", "1", "2", "", "4", "1,2,3,5", "", "3", "1,2,4", "", "", "", "", "", "", "", "", "", "", "", "", "", "-42", "95", "70", "94", "69.4", "4.2", "3", "", "", "", ""),
            ("30.01.2026", 3, "Щучье №3", "", 2, "Thermax Revoterm -2,68 Гкал", "", "1985", "15:00", "1", "2", "", "4", "1,2,3,5", "", "3", "1,2,4", "", "", "", "", "", "", "", "", "", "", "", "", "", "-40", "93", "69", "92", "68.2", "4.2", "3", "", "", "", ""),
            ("30.01.2026", 3, "Щучье №3", "", 2, "Thermax Revoterm -2,68 Гкал", "", "1985", "18:00", "1", "2", "", "4", "1,2,3,5", "", "3", "1,2,4", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "4.2", "3", "", "", "", ""),
            ("30.01.2026", 3, "Щучье №3", "", 2, "Thermax Revoterm -2,68 Гкал", "", "1985", "21:00", "1", "2", "", "4", "1,2,3,5", "", "3", "1,2,4", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "4.2", "3", "", "", "", ""),
            
            # Котельная №4 (Катравож №4 ул. Маслова б/2)
            ("30.01.2026", 4, "Катравож №4 ул. Маслова б/2", "", 1, "KСВ-3,0 PG93\"UNIGAS\"№0904745", "", "2022", "00:00", "2.3", "1", "", "1", "2,3,4", "", "1", "2", "", "1", "50", "1", "1", "-", "8693", "-", "1", "50", "1", "", "", "-36", "88", "65", "88", "65.8", "3.8", "2.8", "-", "Ковшин, Терентьев", "Серасхов Конев", ""),
            ("30.01.2026", 4, "Катравож №4 ул. Маслова б/2", "", 1, "KСВ-3,0 PG93\"UNIGAS\"№0904745", "", "2022", "03:00", "2.3", "1", "", "1", "2,3,4", "", "1", "2", "", "", "", "", "", "", "", "", "", "", "", "", "", "-38", "90", "67", "90", "67", "3.8", "2.8", "", "", "", ""),
            ("30.01.2026", 4, "Катравож №4 ул. Маслова б/2", "", 1, "KСВ-3,0 PG93\"UNIGAS\"№0904745", "", "2022", "06:00", "2.3", "1", "", "1", "2,3,4", "", "1", "2", "", "", "", "", "", "", "", "", "", "", "", "", "", "-39", "91", "67", "91", "67.6", "3.8", "2.8", "", "", "", ""),
            ("30.01.2026", 4, "Катравож №4 ул. Маслова б/2", "", 2, "КСВ -3,0/RG93R\"UNIGAS\"№0901048", "", "2014", "09:00", "2.3", "1", "", "1", "2,3,4", "", "1", "2", "", "", "", "", "", "", "", "", "", "", "", "", "", "-40", "92", "68", "92", "68.2", "3.8", "2.8", "", "", "", ""),
            ("30.01.2026", 4, "Катравож №4 ул. Маслова б/2", "", 2, "КСВ -3,0/RG93R\"UNIGAS\"№0901048", "", "2014", "12:00", "2.3", "1", "", "1", "2,3,4", "", "1", "2", "", "", "", "", "", "", "", "", "", "", "", "", "", "-37", "89", "66", "89", "66.4", "3.8", "2.8", "", "", "", ""),
            ("30.01.2026", 4, "Катравож №4 ул. Маслова б/2", "", 3, "ВК-22-3,2/PG93\"UNIGAS\"№1212515", "", "2006", "15:00", "2.3", "1", "", "1", "2,3,4", "", "1", "2", "", "", "", "", "", "", "", "", "", "", "", "", "", "-35", "87", "65", "87", "65.2", "3.8", "2.8", "", "", "", ""),
            ("30.01.2026", 4, "Катравож №4 ул. Маслова б/2", "", 3, "ВК-22-3,2/PG93\"UNIGAS\"№1212515", "", "2006", "18:00", "2.3", "1", "", "1", "2,3,4", "", "1", "2", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "3.8", "2.8", "", "", "", ""),
            ("30.01.2026", 4, "Катравож №4 ул. Маслова б/2", "", 3, "ВК-22-3,2/PG93\"UNIGAS\"№1212515", "", "2006", "21:00", "2.3", "1", "", "1", "2,3,4", "", "1", "2", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "3.8", "2.8", "", "", "", ""),
        ]
        
        cursor.executemany('''
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
        ''', demo_data)
        
        print(f'✅ Демо-данные загружены: {len(demo_data)} строк')
    
    conn.commit()
    conn.close()

def get_db_connection():
    """Подключение к PostgreSQL"""
    ensure_tables_and_admin()  # Проверяем таблицы и админа
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn

def check_auth():
    """Проверка авторизации"""
    if 'user_id' not in session:
        return False
    
    # Проверяем, существует ли пользователь в базе
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM users WHERE id = %s', (session['user_id'],))
    user_exists = cursor.fetchone() is not None
    conn.close()
    
    return user_exists

def check_role(required_role):
    """Проверка роли пользователя"""
    if not check_auth():
        return False
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT role FROM users WHERE id = %s', (session['user_id'],))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        if required_role == 'admin':
            return user['role'] == 'admin'
        return True  # Любой авторизованный пользователь может просматривать
    return False

@app.route('/')
def index():
    print('🔍 Вызван /index')
    if not check_auth():
        print('🔒 Не авторизован - редирект на login')
        return redirect(url_for('login'))
    
    print('👤 Пользователь авторизован')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Проверяем, сколько строк в базе
    cursor.execute('SELECT COUNT(*) FROM records')
    count = cursor.fetchone()['count']
    print(f'📊 Всего записей в базе: {count}')
    
    cursor.execute('''
        SELECT * FROM records 
        ORDER BY boiler_number, equipment_number, 
        CASE time_interval
            WHEN '00:00' THEN 1
            WHEN '03:00' THEN 2
            WHEN '06:00' THEN 3
            WHEN '09:00' THEN 4
            WHEN '12:00' THEN 5
            WHEN '15:00' THEN 6
            WHEN '18:00' THEN 7
            WHEN '21:00' THEN 8
        END
    ''')
    records = cursor.fetchall()
    print(f'📊 Найдено записей: {len(records)}')
    conn.close()
    
    # Получаем информацию о пользователе
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT username, role FROM users WHERE id = %s', (session['user_id'],))
    user_info = cursor.fetchone()
    print(f'👤 Информация о пользователе: {user_info}')
    conn.close()
    
    print(f'📊 Отправляем {len(records)} записей в шаблон')
    return render_template('index.html', records=records, user=user_info)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, username, password_hash, role FROM users WHERE username = %s', (username,))
        user = cursor.fetchone()
        conn.close()
        
        try:
            valid = bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8'))
        except (ValueError, AttributeError):
            valid = False
        
        if user and valid:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            print(f'🔑 Вход выполнен: {user["username"]} (ID: {user["id"]})')
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Неверный логин или пароль')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            return render_template('register.html', error='Пароли не совпадают')
        
        # Хешируем пароль
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO users (username, password_hash) VALUES (%s, %s)',
                (username, password_hash.decode('utf-8'))
            )
            conn.commit()
            conn.close()
            
            return redirect(url_for('login'))
        except Exception as e:
            return render_template('register.html', error='Пользователь уже существует')
    
    return render_template('register.html')

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/update', methods=['POST'])
def update_cell():
    if not check_auth():
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    field = data['field']
    value = data['value']
    record_id = data['id']
    
    # Проверяем, может ли пользователь редактировать
    if not check_role('operator'):
        return jsonify({'error': 'Access denied'}), 403
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = f'UPDATE records SET {field} = %s WHERE id = %s'
    cursor.execute(query, (value, record_id))
    conn.commit()
    conn.close()
    
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    ensure_tables_and_admin()  # Инициализируем при старте
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
