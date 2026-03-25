from flask import Flask, render_template, request, jsonify, redirect, session, url_for
import os
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "temp-secret-key")

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")


# ===================== DB HELPERS =====================

def get_conn():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    # users
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL,
        password VARCHAR(128) NOT NULL,
        role VARCHAR(20) DEFAULT 'operator'
    );
    """)

    # records
    cur.execute("""
    CREATE TABLE IF NOT EXISTS records (
        id SERIAL PRIMARY KEY,
        date TEXT,
        boiler_number INTEGER,
        boiler_location TEXT,
        boiler_contact TEXT,
        equipment_number INTEGER,
        boiler_model TEXT,
        burner_model TEXT,
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
        notes TEXT,
        downtime_today INTEGER DEFAULT 0,
        downtime_total INTEGER DEFAULT 0
    );
    """)

    # records_archive
    cur.execute("""
    CREATE TABLE IF NOT EXISTS records_archive (
        id SERIAL PRIMARY KEY,
        archive_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        original_id INTEGER,
        date TEXT,
        boiler_number INTEGER,
        boiler_location TEXT,
        boiler_contact TEXT,
        equipment_number INTEGER,
        boiler_model TEXT,
        burner_model TEXT,
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
        notes TEXT,
        downtime_today INTEGER DEFAULT 0,
        downtime_total INTEGER DEFAULT 0
    );
    """)

    # migrations for old DBs
    cur.execute("""
    ALTER TABLE records
    ADD COLUMN IF NOT EXISTS burner_model TEXT,
    ADD COLUMN IF NOT EXISTS downtime_today INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS downtime_total INTEGER DEFAULT 0;
    """)

    cur.execute("""
    ALTER TABLE records_archive
    ADD COLUMN IF NOT EXISTS burner_model TEXT,
    ADD COLUMN IF NOT EXISTS downtime_today INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS downtime_total INTEGER DEFAULT 0;
    """)

    # seed users
    cur.execute("SELECT COUNT(*) AS cnt FROM users")
    row = cur.fetchone()
    if row["cnt"] == 0:
        cur.execute("""
        INSERT INTO users (username, password, role) VALUES
        ('admin', '1313', 'admin'),
        ('admin2', '1313', 'admin'),
        ('user1', '1313', 'operator'),
        ('user2', '1313', 'operator'),
        ('user3', '1313', 'operator'),
        ('user4', '1313', 'operator'),
        ('user5', '1313', 'operator'),
        ('user6', '1313', 'operator'),
        ('user7', '1313', 'operator'),
        ('user8', '1313', 'operator')
        """)

    conn.commit()
    cur.close()
    conn.close()
    print("✅ База данных инициализирована")


# ===================== AUTH =====================

def auth():
    return "user_id" in session


def admin():
    if not auth():
        return False

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT role FROM users WHERE id = %s", (session["user_id"],))
    row = cur.fetchone()
    cur.close()
    conn.close()

    return bool(row and row["role"] == "admin")


def can_edit_record(user_id, boiler_number):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT username, role FROM users WHERE id = %s", (user_id,))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if not user:
        return False

    if user["role"] == "admin":
        return True

    if user["role"] == "operator" and user["username"].startswith("user"):
        try:
            user_num = int(user["username"][4:])
            return 1 <= user_num <= 4 and user_num == boiler_number
        except (ValueError, IndexError):
            return False

    return False


# ===================== ARCHIVE =====================

def archive_records():
    conn = get_conn()
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT INTO records_archive (
                original_id,
                date,
                boiler_number,
                boiler_location,
                boiler_contact,
                equipment_number,
                boiler_model,
                burner_model,
                equipment_year,
                time_interval,
                boilers_working,
                boilers_reserve,
                boilers_repair,
                pumps_working,
                pumps_reserve,
                pumps_repair,
                feed_pumps_working,
                feed_pumps_reserve,
                feed_pumps_repair,
                fuel_tanks_total,
                fuel_tank_volume,
                fuel_tanks_working,
                fuel_tanks_reserve,
                fuel_morning_balance,
                fuel_daily_consumption,
                fuel_tanks_repair,
                water_tanks_total,
                water_tank_volume,
                water_tanks_working,
                water_tanks_reserve,
                water_tanks_repair,
                temp_outdoor,
                temp_supply,
                temp_return,
                temp_graph_supply,
                temp_graph_return,
                pressure_supply,
                pressure_return,
                water_consumption_daily,
                staff_night,
                staff_day,
                notes,
                downtime_today,
                downtime_total,
                archive_date
            )
            SELECT
                id,
                date,
                boiler_number,
                boiler_location,
                boiler_contact,
                equipment_number,
                boiler_model,
                burner_model,
                equipment_year,
                time_interval,
                boilers_working,
                boilers_reserve,
                boilers_repair,
                pumps_working,
                pumps_reserve,
                pumps_repair,
                feed_pumps_working,
                feed_pumps_reserve,
                feed_pumps_repair,
                fuel_tanks_total,
                fuel_tank_volume,
                fuel_tanks_working,
                fuel_tanks_reserve,
                fuel_morning_balance,
                fuel_daily_consumption,
                fuel_tanks_repair,
                water_tanks_total,
                water_tank_volume,
                water_tanks_working,
                water_tanks_reserve,
                water_tanks_repair,
                temp_outdoor,
                temp_supply,
                temp_return,
                temp_graph_supply,
                temp_graph_return,
                pressure_supply,
                pressure_return,
                water_consumption_daily,
                staff_night,
                staff_day,
                notes,
                downtime_today,
                downtime_total,
                NOW() AT TIME ZONE 'Asia/Omsk'
            FROM records
        """)

        cur.execute("""
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
                notes = '',
                downtime_total = COALESCE(downtime_total, 0) + COALESCE(downtime_today, 0),
                downtime_today = 0
        """)

        conn.commit()
        print("✅ Суточная архивация выполнена")

    except Exception as e:
        conn.rollback()
        print("❌ Ошибка архивации:", e)
        raise
    finally:
        cur.close()
        conn.close()


# ===================== ROUTES =====================

@app.route("/")
def index():
    if not auth():
        return redirect(url_for("login"))

    try:
        conn = get_conn()
        cur = conn.cursor()

        cur.execute("SELECT * FROM records ORDER BY date, boiler_number, equipment_number, time_interval")
        records = cur.fetchall()

        cur.execute("SELECT username, role FROM users WHERE id = %s", (session["user_id"],))
        user = cur.fetchone()

        cur.close()
        conn.close()

    except psycopg2.errors.UndefinedTable:
        return render_template(
            "index.html",
            data={},
            user=None,
            db_error="База данных не готова. Таблицы не созданы."
        )
    except Exception as e:
        print(f"❌ DB Error in /index: {e}")
        return render_template(
            "index.html",
            data={},
            user=None,
            db_error=f"Ошибка БД: {e}"
        )

    data = {}
    for r in records:
        data[r["id"]] = r

    return render_template("index.html", data=data, user=user)


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s", (request.form["username"],))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user and request.form["password"] == user["password"]:
            session["user_id"] = user["id"]
            return redirect(url_for("index"))
        else:
            error = "Неверный логин или пароль"

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect(url_for("login"))


ALLOWED_FIELDS = {
    "boiler_model", "burner_model", "equipment_year", "time_interval",
    "boilers_working", "boilers_reserve", "boilers_repair",
    "pumps_working", "pumps_reserve", "pumps_repair",
    "feed_pumps_working", "feed_pumps_reserve", "feed_pumps_repair",
    "fuel_tanks_total", "fuel_tank_volume", "fuel_tanks_working",
    "fuel_tanks_reserve", "fuel_morning_balance", "fuel_daily_consumption",
    "fuel_tanks_repair", "water_tanks_total", "water_tank_volume",
    "water_tanks_working", "water_tanks_reserve", "water_tanks_repair",
    "temp_outdoor", "temp_supply", "temp_return",
    "temp_graph_supply", "temp_graph_return",
    "pressure_supply", "pressure_return",
    "water_consumption_daily", "staff_night", "staff_day", "notes",
    "downtime_today", "downtime_total",
    "boiler_location", "boiler_contact",
    "date", "boiler_number", "equipment_number"
}


@app.route("/update", methods=["POST"])
def update():
    if not auth():
        return jsonify({"status": "error", "message": "Не авторизован"}), 401

    data = request.get_json(silent=True) or {}
    record_id = data.get("id")
    field = data.get("field")
    value = data.get("value")
    if record_id is None or field is None or value is None:
        return jsonify({"status": "error", "message": "Отсутствуют обязательные поля"}), 400
    if field not in ALLOWED_FIELDS:
        return jsonify({"status": "error", "message": "Недопустимое поле"}), 400

    if field in ["downtime_today", "downtime_total"]:
        value = int(value or 0)

    conn = get_conn()
    cur = conn.cursor()

    try:
        cur.execute("SELECT * FROM records WHERE id = %s", (record_id,))
        row = cur.fetchone()

        if row:
            boiler_number = row.get("boiler_number") or 0
            if not can_edit_record(session["user_id"], boiler_number):
                return jsonify({"status": "error", "message": "Нет прав на редактирование"}), 403
        else:
            if not admin():
                return jsonify({"status": "error", "message": "Нет прав на создание записи"}), 403

            cur.execute("""
                INSERT INTO records (
                    id,
                    date,
                    boiler_number,
                    boiler_location,
                    boiler_contact,
                    equipment_number,
                    downtime_today,
                    downtime_total
                ) VALUES (
                    %s,
                    CURRENT_DATE::text,
                    0,
                    '',
                    '',
                    0,
                    0,
                    0
                )
            """, (record_id,))

        cur.execute(f"UPDATE records SET {field} = %s WHERE id = %s", (value, record_id))
        conn.commit()
        return jsonify({"status": "ok"})

    except Exception as e:
        conn.rollback()
        print("❌ Ошибка /update:", e)
        return jsonify({"status": "error", "message": str(e)}), 500

    finally:
        cur.close()
        conn.close()


@app.route("/add", methods=["POST"])
def add():
    if not admin():
        return jsonify({"status": "error", "message": "Нет прав"}), 403

    conn = get_conn()
    cur = conn.cursor()

    try:
        cur.execute("SELECT COALESCE(MAX(id), 0) + 1 AS new_id FROM records")
        new_id = cur.fetchone()["new_id"]

        cur.execute("""
            INSERT INTO records (
                id, date, boiler_number, boiler_location, boiler_contact,
                equipment_number, boiler_model, burner_model, equipment_year, time_interval,
                boilers_working, boilers_reserve, boilers_repair,
                pumps_working, pumps_reserve, pumps_repair,
                feed_pumps_working, feed_pumps_reserve, feed_pumps_repair,
                fuel_tanks_total, fuel_tank_volume, fuel_tanks_working,
                fuel_tanks_reserve, fuel_morning_balance, fuel_daily_consumption,
                fuel_tanks_repair, water_tanks_total, water_tank_volume,
                water_tanks_working, water_tanks_reserve, water_tanks_repair,
                temp_outdoor, temp_supply, temp_return,
                temp_graph_supply, temp_graph_return,
                pressure_supply, pressure_return,
                water_consumption_daily, staff_night, staff_day, notes,
                downtime_today, downtime_total
            ) VALUES (
                %s, CURRENT_DATE::text, 0, '', '',
                0, '', '', '', '',
                '', '', '',
                '', '', '',
                '', '', '',
                '', '', '', '', '', '',
                '', '', '', '', '', '',
                '', '', '', '', '', '',
                '', '', '',
                '', '', '', '',
                0, 0
            )
        """, (new_id,))

        conn.commit()
        return jsonify({"status": "ok", "id": new_id})

    except Exception as e:
        conn.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

    finally:
        cur.close()
        conn.close()


@app.route("/archive", methods=["POST"])
def archive():
    if not admin():
        return jsonify({"status": "error", "message": "Нет прав"}), 403

    try:
        archive_records()
        return jsonify({"status": "ok", "message": "Данные архивированы"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/archive/view")
def view_archive():
    if not admin():
        return redirect(url_for("login"))

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT
            archive_date,
            TO_CHAR(archive_date, 'YYYY-MM-DD HH24:MI:SS') AS formatted
        FROM records_archive
        WHERE archive_date IS NOT NULL
        ORDER BY archive_date DESC
    """)
    dates = cur.fetchall()
    cur.close()
    conn.close()

    return render_template("archive_dates.html", dates=dates)


@app.route("/cron/archive", methods=["GET"])
def trigger_archive():
    token = request.args.get("token")
    expected_token = os.environ.get("CRON_SECRET_TOKEN")

    if not expected_token or token != expected_token:
        return jsonify({"status": "error", "message": "Unauthorized"}), 403

    try:
        archive_records()
        return jsonify({"status": "ok", "message": "Архивация выполнена"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/archive/data/<date>")
def archive_data(date):
    if not admin():
        return redirect(url_for("login"))

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT *
        FROM records_archive
        WHERE archive_date::date = %s
        ORDER BY date, boiler_number, equipment_number, time_interval
    """, (date,))
    records = cur.fetchall()
    cur.close()
    conn.close()

    data = {}
    for r in records:
        data[r["original_id"]] = r

    return render_template("archive_table.html", data=data, selected_date=date)


# ===================== AUTO INIT =====================

# ===================== AUTO-INIT =====================
# try:
#     init_db()
#     print("✅ База данных инициализирована")
# except Exception as e:
#     print(f"⚠️ Ошибка инициализации БД: {e}")


# ===================== START =====================

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
