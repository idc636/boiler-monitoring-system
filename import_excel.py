# import_excel.py — для CSV-файлов
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor

# ===== НАСТРОЙКИ =====
CSV_FILE = "boilers.csv"  # имя твоего CSV файла
DB_URL = "postgresql://postgres:TzhRuKuliqaGilBouUfRjGnBouUfRjGtqZnBnubMN@switchback.proxy.rlwy.net:57256/railway"
# =====================

def import_data():
    # 1. Читаем CSV
    print("📄 Читаю CSV файл...")
    try:
        df = pd.read_csv(CSV_FILE, header=None, encoding='utf-8')
    except UnicodeDecodeError:
        # Если ошибка кодировки — пробуем cp1251 (Windows)
        df = pd.read_csv(CSV_FILE, header=None, encoding='cp1251')
    print(f"✅ Загружено {len(df)} строк")

    # 2. Подключаемся к БД
    print("🔌 Подключаюсь к базе данных...")
    conn = psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)
    cursor = conn.cursor()
    print("✅ Подключение установлено")

    # 3. Очищаем старые данные
    cursor.execute("DELETE FROM records")
    conn.commit()
    print("🧹 Старые данные удалены")

    # 4. Обрабатываем строки
    current_date = None
    current_boiler_num = None
    current_boiler_loc = None
    current_boiler_contact = None
    current_equipment_num = 0

    inserted = 0

    for idx, row in df.iterrows():
        # Пропускаем пустые строки
        if row.isnull().all() or (row.astype(str).str.strip() == '').all():
            continue

        # Строка с датой (дата в первой колонке)
        cell0 = str(row[0]).strip() if pd.notna(row[0]) else ''
        if cell0 and ('.' in cell0) and any(c.isdigit() for c in cell0):
            # Проверяем, похоже ли на дату (30.01.2026)
            parts = cell0.split('.')
            if len(parts) in [2, 3] and all(p.isdigit() for p in parts if p):
                current_date = cell0
                # Контакт может быть в последней колонке
                if pd.notna(row.iloc[-1]) and str(row.iloc[-1]).strip():
                    current_boiler_contact = str(row.iloc[-1]).strip()
                continue

        # Строка с заголовками — пропускаем
        cell1 = str(row[1]).strip().lower() if pd.notna(row[1]) else ''
        if 'котельная' in cell1 or 'марка котла' in cell1 or 'год оборуд' in cell1:
            continue

        # Строка с началом новой котельной: "Котельная №1", "Белоярск..."
        if 'котельная' in cell1 and '№' in cell1:
            # Извлекаем номер котельной
            try:
                num_part = cell1.split('№')[1].split()[0]
                current_boiler_num = int(''.join(filter(str.isdigit, num_part)))
            except:
                current_boiler_num = 1
            
            # Местоположение — колонка 2
            if pd.notna(row[2]) and str(row[2]).strip():
                current_boiler_loc = str(row[2]).strip()
            
            # Контакт — последняя колонка
            if pd.notna(row.iloc[-1]) and str(row.iloc[-1]).strip():
                current_boiler_contact = str(row.iloc[-1]).strip()
            
            # Сбрасываем номер оборудования
            current_equipment_num = 0
            continue

        # Строка с записью (есть временной интервал в колонке 3-5)
        time_val = None
        time_col_idx = None
        for col_idx in [3, 4, 5, 6]:
            if pd.notna(row[col_idx]):
                val = str(row[col_idx]).strip()
                if (':' in val or ('.' in val and len(val) <= 5)) and any(c.isdigit() for c in val):
                    time_val = val
                    time_col_idx = col_idx
                    break
        
        if time_val:
            current_equipment_num += 1
            
            # Извлекаем данные (смещение от колонки времени)
            offset = time_col_idx + 1
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
            try:
                cursor.execute('''
                    INSERT INTO records (
                        date, boiler_number, boiler_location, boiler_contact,
                        equipment_number, time_interval,
                        boilers_working, boilers_reserve, boilers_repair,
                        pumps_working, pumps_reserve, pumps_repair,
                        feed_pumps_working, feed_pumps_reserve, feed_pumps_repair
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', (
                    current_date, current_boiler_num, current_boiler_loc, current_boiler_contact,
                    current_equipment_num, time_val,
                    boilers_working, boilers_reserve, boilers_repair,
                    pumps_working, pumps_reserve, pumps_repair,
                    feed_pumps_working, feed_pumps_reserve, feed_pumps_repair
                ))
                inserted += 1
            except Exception as e:
                print(f"⚠️ Ошибка вставки строки {idx}: {e}")
                continue

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
