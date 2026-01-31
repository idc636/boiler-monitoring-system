import sqlite3

def init_db():
    conn = sqlite3.connect('monitoring.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
    
    conn.commit()
    conn.close()
    print("✅ БД инициализирована.")

def insert_sample_data():
    conn = sqlite3.connect('monitoring.db')
    cursor = conn.cursor()
    
    # ТОЧНО 41 значение в каждой строке
    sample_data = [
        ("30.01.2026", 1, "Белоярск №1 ул. Набережная 8", "83499323373", 1, "КСВ-3,0/PG93 UNIGAS", "", "2007", "00:00", "1.3", "2", "", "1,2,4", "", "3", "1", "2", "", "2", "25", "1.2", "", "16008", "6031", "", "1", "50", "1", "", "", "-34", "86", "64", "86", "64.5", "5.5", "3.8", "0", "Витязев Кожевников", "Канев Нагибин", ""),
        ("30.01.2026", 1, "Белоярск №1 ул. Набережная 8", "83499323373", 1, "КСВ-3,0/PG93 UNIGAS", "", "2007", "03:00", "1.3", "2", "", "1,2,4", "", "", "1", "2", "", "", "", "", "", "", "", "", "", "", "", "", "", "-36", "88", "67", "88", "65.8", "5.5", "3.8", "", "", "", ""),
        ("30.01.2026", 2, "Белоярск №2 ул. Юбилейная 11", "83499323387", 1, "KBA-3,2/PG93 UNIGAS", "", "2010", "00:00", "2,3,4", "1", "", "2,3,4", "1", "", "2", "1", "", "2", "25", "1.2", "", "17589", "12023", "-", "1", "50", "1", "", "", "-35", "87", "65", "87", "65.2", "5.5", "4.5", "10", "Витязев Лаптандер", "Терентеев Подронхасов", ""),
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
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', sample_data)
    
    conn.commit()
    conn.close()
    print("✅ Демо-данные добавлены. Всего строк:", len(sample_data))

if __name__ == '__main__':
    init_db()
    insert_sample_data()