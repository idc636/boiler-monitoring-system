# import_excel.py
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import sys

# ===== НАСТРОЙКИ — ЗАМЕНИ НА СВОИ =====
EXCEL_FILE = "boilers.xlsx"          # имя твоего Excel файла
SHEET_NAME = "Sheet1"                # имя листа (может быть "Лист1" или другое)
DB_URL = "postgresql://postgres:TzhRuKuliqaGilBouUfRjGtqZnBnubMN@switchback.proxy.rlwy.net:57256/railway"
# ======================================

def import_data():
    # 1. Читаем Excel
    print("📄 Читаю Excel файл...")
    df = pd.read_excel(EXCEL_FILE, sheet_name=SHEET_NAME, header=None)
    print(f"✅ Загружено {len(df)} строк")

    # 2. Подключаемся к БД
    print("🔌 Подключаюсь к базе данных...")
    conn = psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)
    cursor = conn.cursor()
    print("✅ Подключение установлено")

    # 3. Очищаем старые данные (опционально)
    cursor.execute("DELETE FROM records")
    conn.commit()
    print("🧹 Старые данные удалены")

    # 4. Обрабатываем строки
    current_date = None
    current_boiler_num = None
    current_boiler_loc = None
    current_boiler_contact = None
    current_equipment_num = None
    current_boiler_model = None
    current_burner_model = None
    current_equipment_year = None

    inserted = 0

    for idx, row in df.iterrows():
        # Пропускаем пустые строки
        if row.isnull().all():
            continue

        # Строка с датой (дата в первой колонке, остальное пустое)
        if pd.notna(row[0]) and str(row[0]).replace('.', '').isdigit() and len(str(row[0])) in [8, 10]:
            current_date = str(row[0]).strip()
            # Контакт может быть в последней колонке
            if pd.notna(row.iloc[-1]):
                current_boiler_contact = str(row.iloc[-1]).strip()
            continue

        # Строка с заголовками — пропускаем
        if "котельная" in str(row[1]).lower() or "марка котла" in str(row[1]).lower():
            continue

        # Строка с началом новой котельной: "Котельная №1", "Белоярск..."
        if pd.notna(row[1]) and "котельная" in str(row[1]).lower():
            # Извлекаем номер котельной
            boiler_text = str(row[1]).strip()
            try:
                current_boiler_num = int(''.join(filter(str.isdigit, boiler_text.split('№')[1])))
            except:
                current_boiler_num = 1
            
            # Местоположение — колонка 2
            if pd.notna(row[2]):
                current_boiler_loc = str(row[2]).strip()
            
            # Контакт — последняя колонка
            if pd.notna(row.iloc[-1]):
                current_boiler_contact = str(row.iloc[-1]).strip()
            
            # Сбрасываем номер оборудования для новой котельной
            current_equipment_num = 0
            continue

        # Строка с записью оборудования (есть временной интервал в колонке 3 или 4)
        time_col = None
        for col_idx in [3, 4, 5]:
            if pd.notna(row[col_idx]) and (':' in str(row[col_idx]) or '.' in str(row[col_idx])):
                time_col = col_idx
                break
        
        if time_col is not None:
            current_equipment_num += 1
            
            # Извлекаем данные
            boiler_model = str(row[1]).strip() if pd.notna(row[1]) else ""
            equipment_year = str(row[2]).strip() if pd.notna(row[2]) else ""
            time_interval = str(row[time_col]).strip()
            
            # Определяем колонки для параметров (смещение зависит от структуры)
            offset = time_col + 1
            boilers_working = str(row[offset]).strip() if pd.notna(row[offset]) else ""
            boilers_reserve = str(row[offset+1]).strip() if pd.notna(row[offset+1]) else ""
            boilers_repair = str(row[offset+2]).strip() if pd.notna(row[offset+2]) else ""
            pumps_working = str(row[offset+3]).strip() if pd.notna(row[offset+3]) else ""
            pumps_reserve = str(row[offset+4]).strip() if pd.notna(row[offset+4]) else ""
            pumps_repair = str(row[offset+5]).strip() if pd.notna(row[offset+5]) else ""
            feed_pumps_working = str(row[offset+6]).strip() if pd.notna(row[offset+6]) else ""
            feed_pumps_reserve = str(row[offset+7]).strip() if pd.notna(row[offset+7]) else ""
            feed_pumps_repair = str(row[offset+8]).strip() if pd.notna(row[offset+8]) else ""

            # Вставляем в БД
            cursor.execute('''
                INSERT INTO records (
                    date, boiler_number, boiler_location, boiler_contact,
                    equipment_number, boiler_model, equipment_year, time_interval,
                    boilers_working, boilers_reserve, boilers_repair,
                    pumps_working, pumps_reserve, pumps_repair,
                    feed_pumps_working, feed_pumps_reserve, feed_pumps_repair
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                current_date, current_boiler_num, current_boiler_loc, current_boiler_contact,
                current_equipment_num, boiler_model, equipment_year, time_interval,
                boilers_working, boilers_reserve, boilers_repair,
                pumps_working, pumps_reserve, pumps_repair,
                feed_pumps_working, feed_pumps_reserve, feed_pumps_repair
            ))
            inserted += 1

    conn.commit()
    conn.close()
    print(f"✅ Успешно загружено {inserted} записей!")

if __name__ == "__main__":
    try:
        import_data()
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
