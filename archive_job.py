from db import get_conn

def archive_records():
    conn = get_conn()
    c = conn.cursor()

    try:
        c.execute("""
            INSERT INTO records_archive (
                original_id, date, boiler_number, boiler_location, boiler_contact,
                equipment_number, boiler_model, equipment_year,
                time_interval, boilers_working, boilers_reserve, boilers_repair,
                pumps_working, pumps_reserve, pumps_repair,
                feed_pumps_working, feed_pumps_reserve, feed_pumps_repair,
                fuel_tanks_total, fuel_tank_volume, fuel_tanks_working,
                fuel_tanks_reserve, fuel_morning_balance, fuel_daily_consumption,
                fuel_tanks_repair, water_tanks_total, water_tank_volume,
                water_tanks_working, water_tanks_reserve, water_tanks_repair,
                temp_outdoor, temp_supply, temp_return,
                temp_graph_supply, temp_graph_return,
                pressure_supply, pressure_return,
                water_consumption_daily, staff_night, staff_day,
                notes, archive_date
            )
            SELECT
                id, date, boiler_number, boiler_location, boiler_contact,
                equipment_number, boiler_model, equipment_year,
                time_interval, boilers_working, boilers_reserve, boilers_repair,
                pumps_working, pumps_reserve, pumps_repair,
                feed_pumps_working, feed_pumps_reserve, feed_pumps_repair,
                fuel_tanks_total, fuel_tank_volume, fuel_tanks_working,
                fuel_tanks_reserve, fuel_morning_balance, fuel_daily_consumption,
                fuel_tanks_repair, water_tanks_total, water_tank_volume,
                water_tanks_working, water_tanks_reserve, water_tanks_repair,
                temp_outdoor, temp_supply, temp_return,
                temp_graph_supply, temp_graph_return,
                pressure_supply, pressure_return,
                water_consumption_daily, staff_night, staff_day,
                notes, NOW()
            FROM records
        """)

        c.execute("""
            UPDATE records SET
                time_interval = '',
                boilers_working = '',
                boilers_reserve = '',
                boilers_repair = '',
                pumps_working = '',
                pumps_reserve = '',
                pumps_repair = '',
                feed_pumps_working = '',
                feed_pumps_reserve = '',
                feed_pumps_repair = '',
                fuel_tanks_total = '',
                fuel_tank_volume = '',
                fuel_tanks_working = '',
                fuel_tanks_reserve = '',
                fuel_morning_balance = '',
                fuel_daily_consumption = '',
                fuel_tanks_repair = '',
                water_tanks_total = '',
                water_tank_volume = '',
                water_tanks_working = '',
                water_tanks_reserve = '',
                water_tanks_repair = '',
                temp_outdoor = '',
                temp_supply = '',
                temp_return = '',
                temp_graph_supply = '',
                temp_graph_return = '',
                pressure_supply = '',
                pressure_return = '',
                water_consumption_daily = '',
                staff_night = '',
                staff_day = '',
                notes = ''
        """)

        conn.commit()
        print("✅ Архивация выполнена")

    except Exception as e:
        conn.rollback()
        print("❌ Ошибка архивации:", e)

    finally:
        conn.close()


if __name__ == '__main__':
    archive_records()

