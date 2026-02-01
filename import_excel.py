import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
import re

EXCEL_FILE = "boilers.xlsx"
DB_URL = "postgresql://postgres:TzhRuKuliqaGilBouUfRjGtqZnBnubMN@switchback.proxy.rlwy.net:57256/railway"

def import_data():
    print("📄 Читаю Excel файл...")
    df = pd.read_excel(EXCEL_FILE, header=None)
    print(f"✅ Загружено {len(df)} строк")

    conn = psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)
    cursor = conn.cursor()
    print("🔌 Подключение установлено")
    
    cursor.execute("DELETE FROM records")
    conn.commit()
    print("🧹 Старые данные удалены")

    current_date = None
    current_boiler_num = None
    current_boiler_loc = None
    current_boiler_contact = None
    current_equipment_num = 0
    inserted = 0

    for idx, row in df.iterrows():
        if idx < 3 or row.isnull().all(): continue
        
        # Дата
        if pd.notna(row[0]) and re.match(r'\d{1,2}\.\d{1,2}\.\d{4}', str(row[0])):
            current_date = str(row[0]).strip()
            if pd.notna(row.iloc[-1]): current_boiler_contact = str(row.iloc[-1]).strip()
            continue
        
        # Новая котельная
        if pd.notna(row[1]) and 'котельная' in str(row[1]).lower():
            num_match = re.search(r'№\s*(\d+)', str(row[1]))
            current_boiler_num = int(num_match.group(1)) if num_match else 1
            current_boiler_loc = str(row[2]).strip() if pd.notna(row[2]) else ""
            if pd.notna(row.iloc[-1]): current_boiler_contact = str(row.iloc[-1]).strip()
            current_equipment_num = 0
            continue
        
        # Пропускаем заголовки
        if pd.notna(row[1]) and any(x in str(row[1]).lower() for x in ['марка котла', 'год оборуд', 'время']):
            continue
        
        # Данные записи
        time_val = None
        for col in [3,4,5,6]:
            if pd.notna(row[col]) and re.match(r'\d{1,2}[:.]\d{2}', str(row[col])):
                time_val = str(row[col]).replace('.', ':').strip()
                time_col = col
                break
        
        if time_val and current_boiler_num:
            if pd.notna(row[0]) and str(row[0]).strip().isdigit():
                current_equipment_num = int(str(row[0]).strip())
            else:
                current_equipment_num += 1
            
            def g(i): return str(row[i]).strip() if pd.notna(row[i]) else ""
            
            cursor.execute('''
                INSERT INTO records (
                    date, boiler_number, boiler_location, boiler_contact,
                    equipment_number, boiler_model, equipment_year, time_interval,
                    boilers_working, boilers_reserve, boilers_repair,
                    pumps_working, pumps_reserve, pumps_repair,
                    feed_pumps_working, feed_pumps_reserve, feed_pumps_repair
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ''', (
                current_date, current_boiler_num, current_boiler_loc, current_boiler_contact,
                current_equipment_num, g(1), g(2), time_val,
                g(time_col+1), g(time_col+2), g(time_col+3),
                g(time_col+4), g(time_col+5), g(time_col+6),
                g(time_col+7), g(time_col+8), g(time_col+9)
            ))
            inserted += 1

    conn.commit()
    conn.close()
    print(f"✅ Успешно загружено {inserted} записей!")

if __name__ == "__main__":
    import_data()
