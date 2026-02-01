import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor

# ===== НАСТРОЙКИ =====
CSV_FILE = "boilers.csv"  # имя твоего CSV файла
DB_URL = "postgresql://postgres:TzhRuKuliqaGilBouUfRjGtqZnBnubMN@switchback.proxy.rlwy.net:57256/railway"
# =====================

def import_data():
    print("📄 Читаю CSV файл...")
    try:
        df = pd.read_csv(CSV_FILE, header=None, encoding='utf-8')
    except:
        df = pd.read_csv(CSV_FILE, header=None, encoding='cp1251')
    print(f"✅ Загружено {len(df)} строк")

    conn = psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)
    cursor = conn.cursor()
    print("🔌 Подключение установлено")

    # Очищаем старые данные
    cursor.execute("DELETE FROM records")
    conn.commit()
    print("🧹 Старые данные удалены")

    # Обрабатываем строки
    current_date = None
    current_boiler_num = None
    current_boiler_loc = None
    current_boiler_contact = None
    inserted = 0

    for idx, row in df.iterrows():
        if row.isnull().all():
            continue

        # Строка с датой
        if pd.notna(row[0]) and '.' in str(row[0]):
            current_date = str(row[0]).strip()
            if pd.notna(row.iloc[-1]):
                current_boiler_contact = str(row.iloc[-1]).strip()
            continue

        # Строка с котельной
        if pd.notna(row[1]) and 'котельная' in str(row[1]).lower():
            try:
                num_part = str(row[1]).split('№')[1].split()[0]
                current_boiler_num = int(''.join(filter(str.isdigit, num_part)))
            except:
                current_boiler_num = 1
            if pd.notna(row[2]):
                current_boiler_loc = str(row[2]).strip()
            if pd.notna(row.iloc[-1]):
                current_boiler_contact = str(row.iloc[-1]).strip()
            continue

        # Строка с записью
        time_interval = str(row[3]).strip() if pd.notna(row[3]) else ""
        boiler_model = str(row[1]).strip() if pd.notna(row[1]) else ""
        equipment_year = str(row[2]).strip() if pd.notna(row[2]) else ""
        boilers_working = str(row[4]).strip() if pd.notna(row[4]) else ""
        boilers_reserve = str(row[5]).strip() if pd.notna(row[5]) else ""
        boilers_repair = str(row[6]).strip() if pd.notna(row[6]) else ""

        # Вставляем данные
        try:
            cursor.execute('''
                INSERT INTO records (
                    date, boiler_number, boiler_location, boiler_contact,
                    equipment_number, boiler_model, equipment_year, time_interval,
                    boilers_working, boilers_reserve, boilers_repair
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                current_date, current_boiler_num, current_boiler_loc, current_boiler_contact,
                idx, boiler_model, equipment_year, time_interval,
                boilers_working, boilers_reserve, boilers_repair
            ))
            inserted += 1
        except Exception as e:
            print(f"⚠️ Ошибка в строке {idx}: {e}")

    conn.commit()
    conn.close()
    print(f"✅ Успешно загружено {inserted} записей!")

if __name__ == "__main__":
    try:
        import_data()
    except Exception as e:
        print(f"❌ Ошибка: {e}")
